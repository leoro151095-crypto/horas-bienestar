from app import app
from models import db, User

with app.app_context():
    print('APP DB URI =', app.config.get('SQLALCHEMY_DATABASE_URI'))
    correo = 'docente@campusucc.edu.co'
    try:
        print('SQLALCHEMY engine url:', db.engine.url)
    except Exception as e:
        print('ERROR getting engine url', e)
    u = User.query.filter_by(correo=correo).first()
    try:
        rows = db.session.execute('SELECT id, correo, rol FROM users').fetchall()
        print('RAW_USERS:', rows)
    except Exception as e:
        print('RAW_QUERY_ERROR', e)
    if not u:
        print('APP_NO_USER')
    else:
        print('APP_FOUND', u.id, u.correo, u.rol)
        print('CHECK_PASSWORD(docente)=', u.check_password('docente'))
