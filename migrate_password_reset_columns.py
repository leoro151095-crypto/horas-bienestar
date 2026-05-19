#!/usr/bin/env python
"""
Script para migrar la tabla users y agregar columnas de password reset.
Maneja correctamente PostgreSQL en Render.
"""
import logging
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, inspect
from app import app, db
from models import User

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_database():
    """Verificar el estado de la base de datos."""
    engine = db.get_engine()
    inspector = inspect(engine)
    
    logger.info(f"Tipo de base de datos: {engine.dialect.name}")
    logger.info(f"Tablas disponibles: {inspector.get_table_names()}")
    
    if 'users' in inspector.get_table_names():
        columns = inspector.get_columns('users')
        logger.info(f"Columnas en users:")
        for col in columns:
            logger.info(f"  - {col['name']}: {col['type']}")
    
    return inspector


def migrate_password_reset():
    """Realizar la migración de columnas de password reset."""
    with app.app_context():
        engine = db.get_engine()
        inspector = check_database()
        
        if 'users' not in inspector.get_table_names():
            logger.error("La tabla 'users' no existe. Ejecute db.create_all() primero.")
            return False
        
        dialect_name = engine.dialect.name.lower()
        is_postgres = 'postgres' in dialect_name
        
        existing_columns = {col['name'] for col in inspector.get_columns('users')}
        logger.info(f"Columnas existentes: {existing_columns}")
        
        # Definir las columnas a agregar
        columns_to_add = [
            {
                'name': 'password_reset_token',
                'type': 'VARCHAR(256)',
                'nullable': True
            },
            {
                'name': 'password_reset_expires',
                'type': 'TIMESTAMP' if is_postgres else 'DATETIME',
                'nullable': True
            }
        ]
        
        with engine.begin() as connection:
            for col_spec in columns_to_add:
                col_name = col_spec['name']
                col_type = col_spec['type']
                nullable = 'NULL' if col_spec['nullable'] else 'NOT NULL'
                
                if col_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type} {nullable}"
                        logger.info(f"Ejecutando: {sql}")
                        connection.execute(text(sql))
                        logger.info(f"✓ Columna {col_name} agregada exitosamente")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if 'already exists' in error_msg or 'duplicate' in error_msg:
                            logger.warning(f"⚠ Columna {col_name} ya existe")
                        else:
                            logger.error(f"✗ Error al agregar {col_name}: {e}")
                            return False
                else:
                    logger.info(f"✓ Columna {col_name} ya existe")
        
        # Verificar que la migración fue exitosa
        logger.info("\nVerificando columnas después de la migración...")
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('users')}
        
        for col_spec in columns_to_add:
            if col_spec['name'] not in columns:
                logger.error(f"✗ Columna {col_spec['name']} no se creó correctamente")
                return False
            logger.info(f"✓ Columna {col_spec['name']} confirmada")
        
        logger.info("\n✓ Migración completada exitosamente")
        return True


def main():
    """Ejecutar la migración."""
    try:
        success = migrate_password_reset()
        if success:
            logger.info("\n" + "="*60)
            logger.info("MIGRACIÓN EXITOSA")
            logger.info("La base de datos está lista para usar.")
            logger.info("="*60)
            return 0
        else:
            logger.error("\n" + "="*60)
            logger.error("MIGRACIÓN FALLIDA")
            logger.error("Por favor revisa los errores arriba.")
            logger.error("="*60)
            return 1
    except Exception as e:
        logger.error(f"Error durante la migración: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
