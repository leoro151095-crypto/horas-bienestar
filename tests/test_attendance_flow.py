from app import app, db
from models import User, Student, Activity, Attendance
from qr_utils import generate_token
import pytest


@pytest.fixture
def client_attendance():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret'

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

        admin = User(nombre='admin', correo='admin2@test', rol='admin')
        admin.set_password('pass')
        docente = User(nombre='doc', correo='doc@test', rol='docente')
        docente.set_password('pass')
        db.session.add(admin)
        db.session.add(docente)

        student = Student(
            tipo_documento='CC',
            numero_documento='999',
            primer_nombre='Ana',
            primer_apellido='Perez',
            correo_personal='ana@test.com',
            celular='3001112233'
        )
        activity = Activity(nombre='Actividad Test', horas=2.0)
        db.session.add(student)
        db.session.add(activity)
        db.session.commit()

    with app.test_client() as client:
        yield client


def test_attendance_register_and_no_duplicate(client_attendance):
    with app.app_context():
        activity = Activity.query.filter_by(nombre='Actividad Test').first()
        token = generate_token(app.config['SECRET_KEY'], activity.id)

    # primer registro exitoso
    rv = client_attendance.post(
        f'/asistencia/submit/{token}',
        data={'tipo_documento': 'CC', 'numero_documento': '999'},
        follow_redirects=True
    )
    assert rv.status_code == 200
    assert b'Asistencia registrada' in rv.data

    with app.app_context():
        count = Attendance.query.count()
        assert count == 1

    # segundo intento debe marcar duplicado
    rv = client_attendance.post(
        f'/asistencia/submit/{token}',
        data={'tipo_documento': 'CC', 'numero_documento': '999'},
        follow_redirects=True
    )
    assert rv.status_code == 200
    assert b'Asistencia ya registrada' in rv.data

    with app.app_context():
        count = Attendance.query.count()
        assert count == 1


def test_student_dashboard_shows_accumulated_and_missing_hours(client_attendance):
    with app.app_context():
        student = Student.query.filter_by(numero_documento='999').first()
        student.correo_institucional = 'ana@campusucc.edu.co'

        student_user = User(nombre='Ana Perez', correo='ana@campusucc.edu.co', rol='estudiante')
        student_user.set_password('pass')
        db.session.add(student_user)

        activity = Activity.query.filter_by(nombre='Actividad Test').first()
        db.session.add(Attendance(estudiante_id=student.id, actividad_id=activity.id, horas=2.0))
        db.session.commit()

    rv = client_attendance.post('/login', data={'correo': 'ana@campusucc.edu.co', 'password': 'pass'}, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Panel Estudiante' in rv.data
    assert b'Horas acumuladas: 2.00' in rv.data
    assert b'Horas faltantes: 38.00 de 40.00' in rv.data
    assert b'Progreso: 5.00%' in rv.data
