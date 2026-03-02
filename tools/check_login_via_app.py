from app import app
from models import db, User

with app.app_context():
    correo = 'docente@campusucc.edu.co'
    u = User.query.filter_by(correo=correo).first()
    if not u:
        print('APP_NO_USER')
    else:
        print('APP_FOUND', u.id, u.correo, u.rol)
        print('CHECK_PASSWORD(docente)=', u.check_password('docente'))
