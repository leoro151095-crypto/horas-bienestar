from app import app
print('SQLALCHEMY_DATABASE_URI=', app.config.get('SQLALCHEMY_DATABASE_URI'))
print('TESTING=', app.config.get('TESTING'))
