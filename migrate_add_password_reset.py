#!/usr/bin/env python3
"""
Script seguro para migrar la base de datos y agregar campos de recuperación de contraseña.
No daña datos existentes - solo agrega campos nuevos si no existen.

Uso:
    python migrate_add_password_reset.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar la ruta del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar configuración sin cargar app completamente
from config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

def get_engine():
    """Crea un engine de SQLAlchemy usando la configuración."""
    db_url = Config.SQLALCHEMY_DATABASE_URI
    print(f"📁 Base de datos: {db_url}")
    
    # Para SQLite, usar StaticPool para evitar problemas de conexión
    if db_url.startswith('sqlite'):
        engine = create_engine(db_url, poolclass=StaticPool, echo=False)
    else:
        engine = create_engine(db_url, echo=False)
    
    return engine

def migrate_database():
    """Agrega los campos password_reset_token y password_reset_expires a la tabla users."""
    
    print("🔍 Iniciando migración de base de datos...")
    
    engine = get_engine()
    
    try:
        # Verificar si las columnas ya existen
        inspector = inspect(engine)
        users_columns = {col['name'] for col in inspector.get_columns('users')}
        
        columns_to_add = {
            'password_reset_token': 'password_reset_token' not in users_columns,
            'password_reset_expires': 'password_reset_expires' not in users_columns,
        }
        
        if not any(columns_to_add.values()):
            print("✅ Los campos de recuperación de contraseña ya existen. No hay nada que hacer.")
            return True
        
        print("\n📝 Campos a agregar:")
        for col, need_add in columns_to_add.items():
            status = "✏️  Agregando" if need_add else "✔️  Ya existe"
            print(f"   {status}: {col}")
        
        with engine.connect() as conn:
            if columns_to_add['password_reset_token']:
                print("\n🔧 Agregando columna password_reset_token...")
                conn.execute(text(
                    'ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(256) DEFAULT NULL'
                ))
                print("   ✅ Columna password_reset_token agregada")
            
            if columns_to_add['password_reset_expires']:
                print("🔧 Agregando columna password_reset_expires...")
                conn.execute(text(
                    'ALTER TABLE users ADD COLUMN password_reset_expires DATETIME DEFAULT NULL'
                ))
                print("   ✅ Columna password_reset_expires agregada")
            
            conn.commit()
        
        print("\n✅ Migración completada exitosamente")
        print("\n💡 Tip: Los usuarios existentes pueden ahora usar 'Olvidó su contraseña'")
        return True
            
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        print("\n⚠️  Verifica que la BD no esté en uso y que las columnas no existan ya.")
        return False
    finally:
        engine.dispose()

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
