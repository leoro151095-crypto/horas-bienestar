from app import app
from models import db, User

correo = 'docente@campusucc.edu.co'
password = 'docente'
nombre = 'docente'
rol = 'docente'

with app.app_context():
    print('DB URI:', app.config.get('SQLALCHEMY_DATABASE_URI'))
    print('ENGINE URL:', db.engine.url)
    user = User.query.filter_by(correo=correo).first()
    if user:
        user.nombre = nombre
        user.rol = rol
        user.set_password(password)
        print('UPDATED existing user', correo)
    else:
        user = User(nombre=nombre, correo=correo, rol=rol)
        user.set_password(password)
        db.session.add(user)
        print('INSERTED user', correo)
    db.session.commit()
