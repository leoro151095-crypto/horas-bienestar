"""
Test simple para validar el sistema de recuperación de contraseña.
Ejecución: pytest test_password_recovery.py -v
"""
import pytest
from datetime import datetime, timezone, timedelta
from app import app
from models import User, db

class TestPasswordRecovery:
    """Suite de tests para recuperación de contraseña"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        with self.app.app_context():
            # Limpiar cualquier sesión anterior
            db.session.remove()
            db.drop_all()
        
    def test_routes_exist(self):
        """Test que las rutas existen"""
        with self.app.app_context():
            db.create_all()
            response = self.client.get('/forgot-password')
            assert response.status_code == 200
            print("✓ Ruta /forgot-password cargada correctamente")
    
    def test_db_columns_exist(self):
        """Test que los campos existen en la BD"""
        from sqlalchemy import inspect
        with self.app.app_context():
            db.create_all()
            inspector = inspect(db.engine)
            columns = {col['name'] for col in inspector.get_columns('users')}
            assert 'password_reset_token' in columns
            assert 'password_reset_expires' in columns
            print("✓ Columnas password_reset_* existen en la BD")
    
    def test_create_user_with_reset_fields(self):
        """Test que podemos crear usuario con campos de reset"""
        with self.app.app_context():
            db.create_all()
            user = User(
                nombre='Test',
                apellido='User',
                correo='test3@campusucc.edu.co',
                rol='estudiante'
            )
            user.set_password('password123')
            user.password_reset_token = 'test-token-123'
            user.password_reset_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
            db.session.add(user)
            db.session.commit()
            
            # Recuperar y verificar
            stored_user = User.query.filter_by(correo='test3@campusucc.edu.co').first()
            assert stored_user is not None
            assert stored_user.password_reset_token == 'test-token-123'
            print("✓ Usuario creado y guardado con campos de reset")
    
    def test_token_cleanup_after_reset(self):
        """Test que el token se limpia después del reset"""
        with self.app.app_context():
            db.create_all()
            user = User(
                nombre='Test',
                apellido='User',
                correo='test4@campusucc.edu.co',
                rol='estudiante'
            )
            user.set_password('password123')
            user.password_reset_token = 'token-to-clean'
            db.session.add(user)
            db.session.commit()
            
            # Simular reset
            user_to_reset = User.query.filter_by(password_reset_token='token-to-clean').first()
            user_to_reset.set_password('newpass456')
            user_to_reset.password_reset_token = None
            user_to_reset.password_reset_expires = None
            db.session.commit()
            
            # Verificar
            reset_user = User.query.filter_by(correo='test4@campusucc.edu.co').first()
            assert reset_user.password_reset_token is None
            assert reset_user.password_reset_expires is None
            assert reset_user.check_password('newpass456')
            print("✓ Token limpiado y nueva contraseña funciona")
