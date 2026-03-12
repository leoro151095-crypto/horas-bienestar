import json
import logging
import secrets
from hmac import compare_digest
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Student, Activity, Attendance, AuditLog
from werkzeug.routing import BuildError
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import func
from config import Config
from qr_utils import generate_token, generate_qr_image, verify_token
from flask import send_file
from excel_utils import export_students_to_excel, import_students_from_excel, EXCEL_HEADERS, generate_template
from notifications import send_email, send_sms

app = Flask(__name__)
app.config.from_object(Config)
INSTITUTIONAL_DOMAIN = '@campusucc.edu.co'

if app.config.get('TRUST_PROXY_HEADERS', False):
    # Trust X-Forwarded-* headers from the first proxy hop.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

if app.config.get('REQUIRE_STRONG_SECRET_KEY', False):
    secret_key = app.config.get('SECRET_KEY', '')
    weak_defaults = {'dev_secret_key_change_this', 'changeme', 'secret', '123456'}
    if len(secret_key) < 32 or secret_key.lower() in weak_defaults:
        raise RuntimeError('SECRET_KEY insegura para este entorno. Define una clave fuerte de al menos 32 caracteres.')

logging.basicConfig(
    level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(app.config.get('LOG_FILE', 'app.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


def write_audit(action, entity, entity_id=None, details=None):
    actor_user_id = current_user.id if getattr(current_user, 'is_authenticated', False) else None
    ip_addr = request.remote_addr if request else None
    record = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        details_json=json.dumps(details or {}, ensure_ascii=False),
        ip_address=ip_addr,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(record)


def is_institutional_email(email):
    return bool(email) and email.strip().lower().endswith(INSTITUTIONAL_DOMAIN)


def get_last4_digits(value):
    digits = ''.join(ch for ch in (value or '') if ch.isdigit())
    if len(digits) < 4:
        return None
    return digits[-4:]


def get_csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': get_csrf_token}


@app.before_request
def protect_from_csrf():
    if not app.config.get('SECURITY_HARDENING_ENABLED', False):
        return None
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None
    if app.config.get('TESTING', False):
        return None
    if request.endpoint in {'static', 'login'}:
        return None

    sent_token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
    expected_token = session.get('_csrf_token')
    if not sent_token or not expected_token or not compare_digest(sent_token, expected_token):
        write_audit('csrf_failed', 'request', None, {
            'endpoint': request.endpoint,
            'method': request.method
        })
        db.session.commit()
        flash('Solicitud invalida (CSRF). Recarga la pagina e intenta de nuevo.', 'danger')
        return redirect(request.referrer or url_for('index'))
    return None


@app.after_request
def set_security_headers(response):
    if not app.config.get('SECURITY_HARDENING_ENABLED', False):
        return response
    # Basic browser-side hardening headers.
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-XSS-Protection', '0')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
    response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
    response.headers.setdefault('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';")

    # Prevent cached authenticated pages being reused from browser history.
    if getattr(current_user, 'is_authenticated', False):
        response.headers.setdefault('Cache-Control', 'no-store, max-age=0')

    # Emit HSTS only over HTTPS to avoid breaking local HTTP development.
    if request.is_secure:
        hsts_seconds = int(app.config.get('HSTS_SECONDS', 0) or 0)
        if hsts_seconds > 0:
            hsts = f'max-age={hsts_seconds}'
            if app.config.get('HSTS_INCLUDE_SUBDOMAINS', True):
                hsts += '; includeSubDomains'
            if app.config.get('HSTS_PRELOAD', False):
                hsts += '; preload'
            response.headers.setdefault('Strict-Transport-Security', hsts)
    return response


def _is_login_temporarily_blocked():
    if not app.config.get('SECURITY_HARDENING_ENABLED', False):
        return False
    blocked_until_raw = session.get('login_block_until')
    if not blocked_until_raw:
        return False
    try:
        blocked_until = datetime.fromisoformat(blocked_until_raw)
    except Exception:
        session.pop('login_block_until', None)
        return False
    return datetime.now(timezone.utc) < blocked_until


def _register_failed_login_attempt():
    if not app.config.get('SECURITY_HARDENING_ENABLED', False):
        return None
    failed = int(session.get('login_failed_attempts', 0)) + 1
    session['login_failed_attempts'] = failed
    if failed >= 5:
        block_until = datetime.now(timezone.utc) + timedelta(minutes=5)
        session['login_block_until'] = block_until.isoformat()


def _clear_login_attempt_tracking():
    if not app.config.get('SECURITY_HARDENING_ENABLED', False):
        return None
    session.pop('login_failed_attempts', None)
    session.pop('login_block_until', None)


@app.before_request
def enforce_session_inactivity_timeout():
    if not app.config.get('SECURITY_HARDENING_ENABLED', False):
        return None
    if not getattr(current_user, 'is_authenticated', False):
        session.pop('last_activity_at', None)
        return None

    timeout_minutes = int(app.config.get('SESSION_INACTIVITY_TIMEOUT_MINUTES', 30))
    if timeout_minutes <= 0:
        session['last_activity_at'] = datetime.now(timezone.utc).isoformat()
        return None

    now = datetime.now(timezone.utc)
    last_activity_raw = session.get('last_activity_at')
    if last_activity_raw:
        try:
            last_activity = datetime.fromisoformat(last_activity_raw)
            if now - last_activity > timedelta(minutes=timeout_minutes):
                user_id = current_user.id
                user_email = current_user.correo
                session.clear()
                logout_user()
                write_audit('session_timeout_logout', 'user', user_id, {'correo': user_email, 'timeout_minutes': timeout_minutes})
                db.session.commit()
                flash('Sesion cerrada por inactividad. Inicia sesion nuevamente.', 'warning')
                return redirect(url_for('login'))
        except Exception:
            # Reset malformed activity timestamp instead of breaking user flow.
            session.pop('last_activity_at', None)

    session['last_activity_at'] = now.isoformat()
    return None


def ensure_student_login(student, reset_password=False):
    correo = (student.correo_institucional or '').strip().lower()
    if not is_institutional_email(correo):
        return False, f'El correo institucional del estudiante debe terminar en {INSTITUTIONAL_DOMAIN}'

    initial_password = get_last4_digits(student.numero_documento)
    if not initial_password:
        return False, 'El número de documento debe tener al menos 4 dígitos para crear acceso'

    user = User.query.filter_by(correo=correo).first()
    if user and user.rol != 'estudiante':
        return False, 'Ya existe un usuario con ese correo y no es rol estudiante'

    if not user:
        user = User(nombre=f"{student.primer_nombre} {student.primer_apellido}".strip(), correo=correo, rol='estudiante')
        user.set_password(initial_password)
        db.session.add(user)
        return True, initial_password

    user.nombre = f"{student.primer_nombre} {student.primer_apellido}".strip()
    user.rol = 'estudiante'
    if reset_password:
        user.set_password(initial_password)
    return True, initial_password


@app.before_request
def force_student_password_change():
    if not getattr(current_user, 'is_authenticated', False):
        return None
    if not session.get('force_password_change'):
        return None
    allowed_endpoints = {'change_password', 'logout', 'static'}
    if request.endpoint in allowed_endpoints:
        return None
    return redirect(url_for('change_password'))


def notify_attendance(student, actividad):
    subject = f"Asistencia registrada: {actividad.nombre}"
    body = (
        f"Hola {student.primer_nombre},\n\n"
        f"Tu asistencia fue registrada en la actividad '{actividad.nombre}'.\n"
        f"Horas asignadas: {actividad.horas or 0}\n"
        f"Fecha de registro (UTC): {datetime.now(timezone.utc).isoformat()}\n"
    )

    email_dest = student.correo_institucional or student.correo_personal
    sms_dest = student.celular

    email_ok, email_msg = send_email(app.config, email_dest, subject, body)
    sms_ok, sms_msg = send_sms(app.config, sms_dest, f"Asistencia registrada: {actividad.nombre}. Horas: {actividad.horas or 0}")

    logging.info('Notificación asistencia email_ok=%s sms_ok=%s email_msg=%s sms_msg=%s', email_ok, sms_ok, email_msg, sms_msg)
    return {
        'email_ok': email_ok,
        'email_msg': email_msg,
        'sms_ok': sms_ok,
        'sms_msg': sms_msg
    }


def ensure_default_admin():
    correo = app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@campusucc.edu.co')
    password = app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin')
    nombre = app.config.get('DEFAULT_ADMIN_NAME', 'admin')

    if not is_institutional_email(correo):
        raise ValueError(f'El correo admin debe terminar en {INSTITUTIONAL_DOMAIN}')

    admin = User.query.filter_by(correo=correo).first()
    if admin:
        changed = False
        if not (admin.nombre or '').strip():
            admin.nombre = nombre
            changed = True
        if admin.rol != 'admin':
            admin.rol = 'admin'
            changed = True
        return ('updated' if changed else 'exists'), correo, None

    admin = User(nombre=nombre, correo=correo, rol='admin')
    admin.set_password(password)
    db.session.add(admin)
    return 'created', correo, password


def bootstrap_persistent_data():
    db.create_all()
    state, _, _ = ensure_default_admin()
    if state in ('created', 'updated'):
        db.session.commit()


with app.app_context():
    bootstrap_persistent_data()

@app.cli.command('init-db')
def init_db():
    with app.app_context():
        db.create_all()
        state, correo, password = ensure_default_admin()
        if state in ('created', 'updated'):
            db.session.commit()
        print('DB creada')
        if password:
            print(f'Admin por defecto {state}: {correo} / {password}')
        else:
            print(f'Admin por defecto {state}: {correo}')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if _is_login_temporarily_blocked():
            write_audit('login_blocked_rate_limit', 'user', None, {'reason': 'too_many_attempts'})
            db.session.commit()
            flash('Demasiados intentos fallidos. Espera 5 minutos e intenta de nuevo.', 'danger')
            return render_template('login.html')

        correo = request.form.get('correo')
        # Requerir dominio institucional (se omite en modo TESTING)
        if not app.config.get('TESTING', False):
            if correo and not is_institutional_email(correo):
                write_audit('login_failed_domain', 'user', None, {'correo': correo})
                flash(f'El correo debe ser una cuenta institucional {INSTITUTIONAL_DOMAIN}', 'danger')
                return render_template('login.html')
        password = request.form.get('password')
        usuario = User.query.filter_by(correo=correo).first()
        if usuario and usuario.check_password(password):
            login_user(usuario)
            _clear_login_attempt_tracking()
            if usuario.rol == 'estudiante':
                student = Student.query.filter_by(correo_institucional=usuario.correo).first()
                student_initial = get_last4_digits(student.numero_documento) if student else None
                if student_initial and password == student_initial:
                    session['force_password_change'] = True
                    write_audit('login_success', 'user', usuario.id, {'correo': correo, 'force_password_change': True})
                    db.session.commit()
                    flash('Por seguridad, debes cambiar tu contraseña para continuar', 'warning')
                    return redirect(url_for('change_password'))
                session.pop('force_password_change', None)
            write_audit('login_success', 'user', usuario.id, {'correo': correo})
            db.session.commit()
            flash('Ingresó correctamente', 'success')
            if usuario.rol == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif usuario.rol == 'docente':
                return redirect(url_for('docente_dashboard'))
            else:
                return redirect(url_for('estudiante_dashboard'))
        write_audit('login_failed', 'user', None, {'correo': correo})
        _register_failed_login_attempt()
        db.session.commit()
        flash('Credenciales inválidas', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('force_password_change', None)
    write_audit('logout', 'user', current_user.id, {'correo': current_user.correo})
    db.session.commit()
    logout_user()
    # Después de cerrar sesión redirigimos al login
    flash('Sesión cerrada', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    cedula_query = (request.args.get('cedula') or '').strip()
    students_query = Student.query
    if cedula_query:
        students_query = students_query.filter(Student.numero_documento.contains(cedula_query))
    students = students_query.order_by(Student.id.desc()).all()
    docentes = User.query.filter_by(rol='docente').order_by(User.id.desc()).all()
    return render_template('admin_dashboard.html', students=students, docentes=docentes, cedula_query=cedula_query)


@app.route('/admin/multimedia-demo')
@login_required
def admin_multimedia_demo():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    return render_template('admin_multimedia_demo.html')


@app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))

    student = db.session.get(Student, student_id)
    if not student:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        data = request.form
        numero_documento = (data.get('numero_documento') or '').strip()
        correo_institucional = (data.get('correo_institucional') or '').strip().lower()

        if not numero_documento:
            flash('Número documento es obligatorio', 'danger')
            return render_template('admin_edit_student.html', student=student)

        if not (data.get('primer_nombre') or '').strip() or not (data.get('primer_apellido') or '').strip():
            flash('Primer nombre y primer apellido son obligatorios', 'danger')
            return render_template('admin_edit_student.html', student=student)

        if not is_institutional_email(correo_institucional):
            flash(f'El correo institucional debe terminar en {INSTITUTIONAL_DOMAIN}', 'danger')
            return render_template('admin_edit_student.html', student=student)

        doc_duplicate = Student.query.filter(
            Student.numero_documento == numero_documento,
            Student.id != student.id
        ).first()
        if doc_duplicate:
            flash('Ya existe un estudiante con ese número de documento', 'danger')
            return render_template('admin_edit_student.html', student=student)

        old_correo = student.correo_institucional
        student.tipo_documento = (data.get('tipo_documento') or '').strip()
        student.numero_documento = numero_documento
        student.primer_nombre = (data.get('primer_nombre') or '').strip()
        student.segundo_nombre = (data.get('segundo_nombre') or '').strip() or None
        student.primer_apellido = (data.get('primer_apellido') or '').strip()
        student.segundo_apellido = (data.get('segundo_apellido') or '').strip() or None
        student.correo_institucional = correo_institucional
        student.correo_personal = (data.get('correo_personal') or '').strip() or None
        student.celular = (data.get('celular') or '').strip() or None
        student.direccion = (data.get('direccion') or '').strip() or None
        student.programa = (data.get('programa') or '').strip() or None

        ok, result = ensure_student_login(student, reset_password=False)
        if not ok:
            db.session.rollback()
            flash(result, 'danger')
            return render_template('admin_edit_student.html', student=student)

        write_audit('student_updated', 'student', student.id, {
            'source': 'manual_admin_edit',
            'old_correo_institucional': old_correo,
            'new_correo_institucional': correo_institucional
        })
        db.session.commit()
        flash('Estudiante actualizado correctamente', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_edit_student.html', student=student)


@app.route('/admin/students/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))

    student = db.session.get(Student, student_id)
    if not student:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('admin_dashboard'))

    linked_user = User.query.filter_by(correo=(student.correo_institucional or '').strip().lower(), rol='estudiante').first()
    deleted_attendance = Attendance.query.filter_by(estudiante_id=student.id).delete(synchronize_session=False)
    student_id_value = student.id
    student_doc = student.numero_documento
    student_mail = student.correo_institucional
    db.session.delete(student)
    linked_user_id = None
    if linked_user:
        linked_user_id = linked_user.id
        db.session.delete(linked_user)

    write_audit('student_deleted', 'student', student_id_value, {
        'numero_documento': student_doc,
        'correo_institucional': student_mail,
        'deleted_attendance_rows': deleted_attendance,
        'deleted_user_id': linked_user_id
    })
    db.session.commit()
    flash('Estudiante eliminado correctamente', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/audit_logs')
@login_required
def admin_audit_logs():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template('admin_audit_logs.html', logs=logs)


@app.route('/admin/export_students')
@login_required
def export_students():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    students = Student.query.all()
    write_audit('students_export', 'student', None, {'count': len(students)})
    db.session.commit()
    buf = export_students_to_excel(students)
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='students.xlsx')


@app.route('/admin/import_students', methods=['GET', 'POST'])
@login_required
def import_students():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            flash('No se subió archivo', 'danger')
            return redirect(url_for('import_students'))
        # ejecutar validación y mostrar vista previa editable
        rows, header_errors, row_errors = import_students_from_excel(f)
        if header_errors:
            for e in header_errors:
                flash(e, 'danger')
            write_audit('students_import_validation_failed', 'student', None, {'errors': header_errors})
            db.session.commit()
            return render_template('admin_import.html')
        write_audit('students_import_preview', 'student', None, {'rows': len(rows), 'row_errors': len(row_errors)})
        db.session.commit()
        # rows: lista de dicts, row_errors: lista de errores por fila
        return render_template('admin_import_preview.html', rows=rows, row_errors=row_errors, headers=EXCEL_HEADERS)
    return render_template('admin_import.html')


@app.route('/admin/import_confirm', methods=['POST'])
@login_required
def import_confirm():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    try:
        count = int(request.form.get('rows_count', '0'))
    except ValueError:
        count = 0
    created = 0
    updated = 0
    row_errors = []
    for i in range(count):
        rdata = {}
        for h in EXCEL_HEADERS:
            key = f'rows-{i}-{h}'
            rdata[h] = request.form.get(key, '').strip()
        numero = rdata.get('numero_documento', '').strip()
        if not numero:
            row_errors.append({'row': i+2, 'messages': ['Falta numero_documento'], 'data': rdata})
            continue
        if not rdata.get('primer_nombre') or not rdata.get('primer_apellido'):
            row_errors.append({'row': i+2, 'messages': ['Faltan nombres/apellidos obligatorios'], 'data': rdata})
            continue
        student = Student.query.filter_by(numero_documento=numero).first()
        if student:
            student.tipo_documento = rdata.get('tipo_documento') or student.tipo_documento
            student.primer_nombre = rdata.get('primer_nombre') or student.primer_nombre
            student.segundo_nombre = rdata.get('segundo_nombre') or student.segundo_nombre
            student.primer_apellido = rdata.get('primer_apellido') or student.primer_apellido
            student.segundo_apellido = rdata.get('segundo_apellido') or student.segundo_apellido
            student.correo_institucional = rdata.get('correo_institucional') or student.correo_institucional
            student.correo_personal = rdata.get('correo_personal') or student.correo_personal
            student.celular = rdata.get('celular') or student.celular
            student.direccion = rdata.get('direccion') or student.direccion
            student.programa = rdata.get('programa') or student.programa
            ok, msg = ensure_student_login(student, reset_password=False)
            if not ok:
                row_errors.append({'row': i+2, 'messages': [msg], 'data': rdata})
                continue
            updated += 1
            write_audit('student_updated', 'student', student.id, {'source': 'excel_import'})
        else:
            student = Student(
                tipo_documento=rdata.get('tipo_documento') or '',
                numero_documento=numero,
                primer_nombre=rdata.get('primer_nombre') or '',
                segundo_nombre=rdata.get('segundo_nombre'),
                primer_apellido=rdata.get('primer_apellido') or '',
                segundo_apellido=rdata.get('segundo_apellido'),
                correo_institucional=rdata.get('correo_institucional'),
                correo_personal=rdata.get('correo_personal'),
                celular=rdata.get('celular'),
                direccion=rdata.get('direccion'),
                programa=rdata.get('programa')
            )
            db.session.add(student)
            db.session.flush()
            ok, msg = ensure_student_login(student, reset_password=True)
            if not ok:
                db.session.delete(student)
                db.session.flush()
                row_errors.append({'row': i+2, 'messages': [msg], 'data': rdata})
                continue
            created += 1
            write_audit('student_created', 'student', student.id, {'source': 'excel_import'})
    db.session.commit()
    logging.info('Importación Excel finalizada created=%s updated=%s row_errors=%s', created, updated, len(row_errors))
    write_audit('students_import_confirmed', 'student', None, {'created': created, 'updated': updated, 'row_errors': len(row_errors)})
    db.session.commit()
    return render_template('admin_import_result.html', created=created, updated=updated, row_errors=row_errors)


@app.route('/admin/download_template')
@login_required
def download_template():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    write_audit('students_template_download', 'student', None, {})
    db.session.commit()
    buf = generate_template()
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='students_template.xlsx')


@app.route('/admin/create_activity', methods=['GET', 'POST'])
@login_required
def create_activity():
    if current_user.rol not in ('admin', 'docente'):
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        fecha = request.form.get('fecha')
        horas = request.form.get('horas')
        # Server-side validation
        if not nombre or not nombre.strip():
            flash('El nombre de la actividad es obligatorio', 'danger')
            return render_template('admin_create_activity.html')
        try:
            horas_val = float(horas) if horas else 0.0
            if horas_val < 0:
                raise ValueError()
        except ValueError:
            flash('Horas debe ser un número positivo', 'danger')
            return render_template('admin_create_activity.html')
        actividad = Activity(nombre=nombre.strip(), horas=horas_val)
        db.session.add(actividad)
        db.session.flush()
        write_audit('activity_created', 'activity', actividad.id, {'nombre': nombre, 'horas': horas_val, 'created_by_role': current_user.rol})
        db.session.commit()
        flash('Actividad creada', 'success')
        if current_user.rol == 'docente':
            return redirect(url_for('docente_dashboard'))
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_create_activity.html')


@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    # sumar horas por estudiante
    rows = db.session.query(
        Student,
        func.coalesce(func.sum(Attendance.horas), 0).label('total_horas')
    ).outerjoin(Attendance, Attendance.estudiante_id == Student.id).group_by(Student.id).all()
    required_hours = float(app.config.get('REQUIRED_WELLBEING_HOURS', 40))
    report = []
    for student, total in rows:
        horas_faltantes = max(0, required_hours - (total or 0))
        report.append({'student': student, 'total_horas': float(total or 0), 'horas_faltantes': horas_faltantes})
    return render_template('admin_report.html', report=report)

@app.route('/admin/register_student', methods=['GET', 'POST'])
@login_required
def register_student():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = request.form
        correo_institucional = (data.get('correo_institucional') or '').strip().lower()
        if not is_institutional_email(correo_institucional):
            flash(f'El correo institucional debe terminar en {INSTITUTIONAL_DOMAIN}', 'danger')
            return render_template('admin_register.html')

        initial_password = get_last4_digits(data.get('numero_documento'))
        if not initial_password:
            flash('El número de documento debe tener al menos 4 dígitos', 'danger')
            return render_template('admin_register.html')

        student = Student(
            tipo_documento=data.get('tipo_documento'),
            numero_documento=data.get('numero_documento'),
            primer_nombre=data.get('primer_nombre'),
            segundo_nombre=data.get('segundo_nombre'),
            primer_apellido=data.get('primer_apellido'),
            segundo_apellido=data.get('segundo_apellido'),
            correo_institucional=correo_institucional,
            correo_personal=data.get('correo_personal'),
            celular=data.get('celular'),
            direccion=data.get('direccion'),
            programa=data.get('programa')
        )
        db.session.add(student)
        db.session.flush()
        ok, result = ensure_student_login(student, reset_password=True)
        if not ok:
            db.session.rollback()
            flash(result, 'danger')
            return render_template('admin_register.html')
        write_audit('student_created', 'student', student.id, {'source': 'manual_admin'})
        db.session.commit()
        flash('Estudiante registrado. Contraseña inicial: últimos 4 dígitos del documento.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_register.html')


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password') or ''
        new_password = request.form.get('new_password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not current_user.check_password(current_password):
            flash('La contraseña actual no es correcta', 'danger')
            return render_template('change_password.html')

        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('change_password.html')

        student = Student.query.filter_by(correo_institucional=current_user.correo).first()
        student_initial = get_last4_digits(student.numero_documento) if student else None
        if student_initial and new_password == student_initial:
            flash('La nueva contraseña no puede ser los últimos 4 dígitos del documento', 'danger')
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash('La confirmación de contraseña no coincide', 'danger')
            return render_template('change_password.html')

        current_user.set_password(new_password)
        write_audit('password_changed', 'user', current_user.id, {'correo': current_user.correo})
        db.session.commit()
        session.pop('force_password_change', None)
        flash('Contraseña actualizada correctamente', 'success')

        if current_user.rol == 'admin':
            return redirect(url_for('admin_dashboard'))
        if current_user.rol == 'docente':
            return redirect(url_for('docente_dashboard'))
        return redirect(url_for('estudiante_dashboard'))
    return render_template('change_password.html')


@app.route('/admin/register_docente', methods=['GET', 'POST'])
@login_required
def register_docente():
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        correo = (request.form.get('correo') or '').strip().lower()
        password = request.form.get('password') or ''

        if not nombre or not correo or not password:
            flash('Nombre, correo y contraseña son obligatorios', 'danger')
            return render_template('admin_register_docente.html')

        if not is_institutional_email(correo):
            flash(f'El correo debe terminar en {INSTITUTIONAL_DOMAIN}', 'danger')
            return render_template('admin_register_docente.html')

        existing = User.query.filter_by(correo=correo).first()
        if existing:
            flash('Ya existe un usuario con ese correo', 'danger')
            return render_template('admin_register_docente.html')

        docente = User(nombre=nombre, correo=correo, rol='docente')
        docente.set_password(password)
        db.session.add(docente)
        db.session.flush()
        write_audit('docente_created', 'user', docente.id, {'correo': correo, 'rol': 'docente'})
        db.session.commit()
        flash('Docente creado correctamente', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_register_docente.html')


@app.route('/admin/docentes/<int:docente_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_docente(docente_id):
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))

    docente = db.session.get(User, docente_id)
    if not docente or docente.rol != 'docente':
        flash('Docente no encontrado', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        correo = (request.form.get('correo') or '').strip().lower()
        password = request.form.get('password') or ''

        if not nombre or not correo:
            flash('Nombre y correo son obligatorios', 'danger')
            return render_template('admin_edit_docente.html', docente=docente)

        if not is_institutional_email(correo):
            flash(f'El correo debe terminar en {INSTITUTIONAL_DOMAIN}', 'danger')
            return render_template('admin_edit_docente.html', docente=docente)

        duplicate = User.query.filter(User.correo == correo, User.id != docente.id).first()
        if duplicate:
            flash('Ya existe un usuario con ese correo', 'danger')
            return render_template('admin_edit_docente.html', docente=docente)

        docente.nombre = nombre
        docente.correo = correo
        docente.rol = 'docente'
        if password.strip():
            docente.set_password(password)

        write_audit('docente_updated', 'user', docente.id, {'correo': correo, 'password_changed': bool(password.strip())})
        db.session.commit()
        flash('Docente actualizado correctamente', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_edit_docente.html', docente=docente)


@app.route('/admin/docentes/<int:docente_id>/delete', methods=['POST'])
@login_required
def delete_docente(docente_id):
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))

    docente = db.session.get(User, docente_id)
    if not docente or docente.rol != 'docente':
        flash('Docente no encontrado', 'danger')
        return redirect(url_for('admin_dashboard'))

    if docente.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin_dashboard'))

    docente_id_value = docente.id
    docente_email = docente.correo
    db.session.delete(docente)
    write_audit('docente_deleted', 'user', docente_id_value, {'correo': docente_email, 'rol': 'docente'})
    db.session.commit()
    flash('Docente eliminado correctamente', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reset_student_password/<int:student_id>', methods=['POST'])
@login_required
def reset_student_password(student_id):
    if current_user.rol != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))

    student = db.session.get(Student, student_id)
    if not student:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('admin_dashboard'))

    ok, result = ensure_student_login(student, reset_password=True)
    if not ok:
        flash(result, 'danger')
        return redirect(url_for('admin_dashboard'))

    write_audit('student_password_reset', 'user', None, {
        'student_id': student.id,
        'correo': student.correo_institucional
    })
    db.session.commit()
    flash(f'Contraseña reseteada para {student.correo_institucional}. Temporal: últimos 4 dígitos del documento.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/docente')
@login_required
def docente_dashboard():
    if current_user.rol != 'docente':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    activities = Activity.query.all()
    return render_template('docente_dashboard.html', activities=activities)


@app.route('/docente/generate_qr/<int:actividad_id>')
@login_required
def docente_generate_qr(actividad_id):
    if current_user.rol != 'docente':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    token = generate_token(app.config['SECRET_KEY'], actividad_id)
    write_audit('qr_generated', 'activity', actividad_id, {'expires_seconds': 1800})
    db.session.commit()
    try:
        url = url_for('attendance_scan', token=token, _external=True)
    except BuildError:
        # Fallback: construct URL manually if the endpoint isn't registered for some reason
        url = request.host_url.rstrip('/') + f'/asistencia/{token}'
    img_buf = generate_qr_image(url)
    return send_file(img_buf, mimetype='image/png', download_name='qr.png')

@app.route('/estudiante')
@login_required
def estudiante_dashboard():
    if current_user.rol != 'estudiante':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('index'))
    student = Student.query.filter_by(correo_institucional=current_user.correo).first()
    total_horas = 0.0
    if student:
        total_horas = float(db.session.query(func.coalesce(func.sum(Attendance.horas), 0)).filter(Attendance.estudiante_id == student.id).scalar() or 0.0)
    required_hours = float(app.config.get('REQUIRED_WELLBEING_HOURS', 40))
    horas_faltantes = max(0, required_hours - total_horas)
    if required_hours > 0:
        progress_percent = min(100.0, max(0.0, (total_horas / required_hours) * 100.0))
    else:
        progress_percent = 100.0 if total_horas > 0 else 0.0
    return render_template(
        'estudiante_dashboard.html',
        total_horas=total_horas,
        horas_faltantes=horas_faltantes,
        required_hours=required_hours,
        progress_percent=progress_percent,
        student=student
    )

if __name__ == '__main__':
    debug_mode = bool(app.config.get('DEBUG', False))
    app.run(debug=debug_mode)


@app.route('/asistencia/<token>', endpoint='attendance_scan')
def attendance_scan(token):
    data = verify_token(app.config['SECRET_KEY'], token, max_age=1800)
    if not data:
        return render_template('qr_invalid.html')
    actividad_id = data.get('actividad_id')
    actividad = db.session.get(Activity, actividad_id)
    if not actividad:
        return render_template('qr_invalid.html')
    write_audit('qr_scanned', 'activity', actividad_id, {'token_valid': True})
    db.session.commit()
    # Para simplificar: mostrar página que permite registrar asistencia con documento
    return render_template('attendance_register.html', actividad=actividad, token=token)


@app.route('/asistencia/submit/<token>', methods=['POST'])
def attendance_submit(token):
    data = verify_token(app.config['SECRET_KEY'], token, max_age=1800)
    if not data:
        return render_template('qr_invalid.html')
    actividad_id = data.get('actividad_id')
    actividad = db.session.get(Activity, actividad_id)
    if not actividad:
        return render_template('qr_invalid.html')

    tipo = request.form.get('tipo_documento')
    numero = request.form.get('numero_documento')
    student = Student.query.filter_by(numero_documento=numero).first()
    if not student:
        # crear estudiante mínimo o pedir registro
        student = Student(tipo_documento=tipo, numero_documento=numero, primer_nombre='Desconocido', primer_apellido='')
        db.session.add(student)
        db.session.flush()
        write_audit('student_created', 'student', student.id, {'source': 'qr_scan_minimal'})
        db.session.commit()

    # evitar registro duplicado para la misma actividad
    existing = Attendance.query.filter_by(estudiante_id=student.id, actividad_id=actividad.id).first()
    if existing:
        write_audit('attendance_duplicate_attempt', 'attendance', existing.id, {'estudiante_id': student.id, 'actividad_id': actividad.id})
        db.session.commit()
        return render_template('attendance_already.html', student=student, actividad=actividad)

    attend = Attendance(estudiante_id=student.id, actividad_id=actividad.id, fecha_registro=datetime.now(timezone.utc), horas=actividad.horas or 0.0)
    db.session.add(attend)
    try:
        db.session.flush()
        write_audit('attendance_registered', 'attendance', attend.id, {'estudiante_id': student.id, 'actividad_id': actividad.id, 'horas': attend.horas})
        db.session.commit()
    except Exception:
        db.session.rollback()
        return render_template('attendance_already.html', student=student, actividad=actividad)

    notify_result = notify_attendance(student, actividad)
    write_audit('attendance_notification', 'attendance', attend.id, notify_result)
    db.session.commit()

    return render_template('attendance_success.html', student=student, actividad=actividad, notify_result=notify_result)
