import io
from app import app, db
from models import User, Student
from excel_utils import EXCEL_HEADERS
from openpyxl import Workbook
import pytest


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        # crear admin
        u = User.query.filter_by(correo='admin@test').first()
        if not u:
            u = User(nombre='admin', correo='admin@test', rol='admin')
            u.set_password('pass')
            db.session.add(u)
        db.session.commit()
    with app.test_client() as client:
        yield client


def make_excel_bytes(rows):
    wb = Workbook()
    ws = wb.active
    ws.append(EXCEL_HEADERS)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def login_admin(client):
    return client.post('/login', data={'correo':'admin@test', 'password':'pass'}, follow_redirects=True)


def test_import_and_export(client):
    # login
    rv = login_admin(client)
    assert b'Ingres' in rv.data or b'Ingres' in rv.data
    # preparar excel con un estudiante
    rows = [['CC', '12345', 'Juan', 'Carlos', 'Perez', 'Lopez', 'juan@uni.edu', 'juan@gmail.com', '3001112222', 'Calle 1', 'Ingenieria']]
    buf = make_excel_bytes(rows)
    data = {'file': (buf, 'students.xlsx')}
    rv = client.post('/admin/import_students', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b'Vista previa de importaci' in rv.data

    # confirmar importación (1 fila)
    confirm_data = {
        'rows_count': '1',
        'rows-0-tipo_documento': 'CC',
        'rows-0-numero_documento': '12345',
        'rows-0-primer_nombre': 'Juan',
        'rows-0-segundo_nombre': 'Carlos',
        'rows-0-primer_apellido': 'Perez',
        'rows-0-segundo_apellido': 'Lopez',
        'rows-0-correo_institucional': 'juan@uni.edu',
        'rows-0-correo_personal': 'juan@gmail.com',
        'rows-0-celular': '3001112222',
        'rows-0-direccion': 'Calle 1',
        'rows-0-programa': 'Ingenieria'
    }
    rv = client.post('/admin/import_confirm', data=confirm_data, follow_redirects=True)
    assert b'Resultado de importaci' in rv.data
    with app.app_context():
        s = Student.query.filter_by(numero_documento='12345').first()
        assert s is not None
        assert s.primer_nombre == 'Juan'
    # probar export
    rv = client.get('/admin/export_students')
    assert rv.status_code == 200
    assert rv.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
