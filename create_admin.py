from app import app
from models import db, User

correo = 'admin@campusucc.edu.co'
password = 'admin'

with app.app_context():
    u = User.query.filter_by(correo=correo).first()
    if u:
        u.set_password(password)
        u.nombre = getattr(u, 'nombre', 'admin') or 'admin'
        u.rol = 'admin'
        db.session.commit()
        print('Admin actualizado:', correo)
    else:
        u = User(nombre='admin', correo=correo, rol='admin')
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print('Admin creado:', correo)
