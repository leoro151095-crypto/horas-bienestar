# Sistema de Asistencia (Flask)

Proyecto con roles (`admin`, `docente`, `estudiante`), QR temporal para asistencia, importación/exportación Excel, auditoría de eventos y notificaciones por correo/SMS.

## 1) Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Configuración

Puedes usar variables de entorno del sistema o crear un `.env` basado en `.env.example`.

### Variables mínimas
- `SECRET_KEY`
- `DATABASE_URL` (opcional; por defecto se usa una única DB en `instance/app.db`)

Si usas SQLite y defines `DATABASE_URL` como ruta relativa (por ejemplo `sqlite:///app.db`),
la app la normaliza automáticamente a una ruta absoluta del proyecto para evitar cambios de
base de datos por ejecutar comandos desde otra carpeta.

### Variables opcionales
- Logging: `LOG_FILE`, `LOG_LEVEL`
- Meta horas bienestar: `REQUIRED_WELLBEING_HOURS` (por defecto `40`)
- SMTP: `MAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`
- Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`

## 3) Inicializar base de datos

```bash
flask init-db
```

Al ejecutar `init-db`, el sistema deja listo un admin por defecto (si no existe lo crea; si existe,
solo garantiza que tenga rol admin sin resetear su contraseña):

- Correo: `admin@campusucc.edu.co`
- Contraseña: `admin`

Además, al iniciar la aplicación se asegura automáticamente la creación de tablas y la existencia
de un admin por defecto, para que no se pierda el acceso admin tras recargas o cambios de diseño.

## 4) Crear usuario admin (ejemplo)

```bash
python -c "from app import app; from models import db, User; app.app_context().push(); db.create_all(); u=User(nombre='admin', correo='admin@example.com', rol='admin'); u.set_password('pass'); db.session.add(u); db.session.commit(); print('admin creado')"
```

## 5) Ejecutar

```bash
flask run
```

En Windows, para evitar cambios accidentales de base de datos entre reinicios,
usa `iniciar.bat`; ese script fija `DATABASE_URL` a la DB del proyecto:
`instance/app.db`.

## Funcionalidades implementadas

### Roles y acceso
- Redirección por rol al iniciar sesión.
- Rutas protegidas para `admin`, `docente`, `estudiante`.
- El admin puede crear cuentas de docente desde el panel (`/admin/register_docente`).
- Los correos de usuarios del sistema deben terminar en `@campusucc.edu.co`.
- Al registrar estudiante, su acceso inicial es con el correo institucional y los últimos 4 dígitos del documento.
- En el primer ingreso del estudiante, el sistema exige cambio de contraseña antes de continuar.
- El admin puede resetear la clave del estudiante a los últimos 4 dígitos del documento desde el panel.

### Asistencia por QR temporal
- Docente genera QR para actividad (`/docente/generate_qr/<actividad_id>`).
- Token temporal validado con expiración de 30 min.
- Registro de asistencia con prevención de duplicados por estudiante/actividad.

### Excel (admin)
- Exportar estudiantes a `.xlsx`.
- Importar estudiantes desde `.xlsx`.
- Descarga de plantilla oficial (`/admin/download_template`).
- Vista previa editable antes de confirmar importación.
- Validación de columnas requeridas y formatos básicos (email/celular).

### Auditoría y logging
- Tabla `audit_logs` para eventos críticos.
- Vista admin: `/admin/audit_logs`.
- Log de aplicación en archivo (por defecto `app.log`).

### Notificaciones al registrar asistencia
- Envío de correo (si SMTP está configurado).
- Envío de SMS (si Twilio está configurado).
- Si no hay configuración, no bloquea el registro y se audita el resultado.
- En la pantalla de éxito se muestra estado de correo/SMS.

## Pruebas

```bash
python -m pytest -q
```

Incluye prueba de flujo de importación/exportación de estudiantes en `tests/test_excel_import.py`.
