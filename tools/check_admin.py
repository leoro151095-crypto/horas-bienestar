from app import app
from models import db, User

with app.app_context():
    u = User.query.filter_by(correo='admin@campusucc.edu.co').first()
    if not u:
        print('NO_USER')
    else:
        print('FOUND', u.id, u.correo, u.rol)
        ok = u.check_password('admin')
        print('PASSWORD_MATCH', ok)
