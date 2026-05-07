from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120))
    cedula = db.Column(db.String(50), unique=True)
    celular = db.Column(db.String(40))
    correo_personal = db.Column(db.String(120))
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(30), nullable=False)
    area = db.Column(db.String(80))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(10), nullable=False)
    numero_documento = db.Column(db.String(50), unique=True, nullable=False)
    primer_nombre = db.Column(db.String(80), nullable=False)
    segundo_nombre = db.Column(db.String(80))
    primer_apellido = db.Column(db.String(80), nullable=False)
    segundo_apellido = db.Column(db.String(80))
    correo_institucional = db.Column(db.String(120))
    correo_personal = db.Column(db.String(120))
    celular = db.Column(db.String(40))
    direccion = db.Column(db.String(200))
    programa = db.Column(db.String(120))

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.DateTime)
    horas = db.Column(db.Float, default=0.0)

class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    __table_args__ = (db.UniqueConstraint('estudiante_id', 'actividad_id', name='uix_est_act'),)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    actividad_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    fecha_registro = db.Column(db.DateTime)
    horas = db.Column(db.Float, default=0.0)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    entity = db.Column(db.String(120), nullable=False)
    entity_id = db.Column(db.String(120), nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
