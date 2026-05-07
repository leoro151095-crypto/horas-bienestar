from app import app
from models import db, User

with app.app_context():
    print('DB URI:', app.config.get('SQLALCHEMY_DATABASE_URI'))
    print('ENGINE URL:', db.engine.url)
    users = User.query.order_by(User.id.asc()).all()
    if not users:
        print('NO_USERS_IN_ACTIVE_DB')
    else:
        for user in users:
            print('USER:', (user.id, user.correo, user.rol))
