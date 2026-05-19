#!/usr/bin/env python3
"""Simular inicio de Render - gunicorn app:app"""
import sys
import os

print("=" * 60)
print("Simulando: gunicorn app:app")
print("=" * 60)
print()

try:
    print("1. Cargando configuración...")
    from config import Config
    print("   ✅ Config cargada")
    
    print("\n2. Importando app...")
    from app import app, db
    print("   ✅ App importada")
    
    print("\n3. Verificando context de app...")
    with app.app_context():
        print("   ✅ App context activo")
        
        print("\n4. Verificando base de datos...")
        inspector = __import__('sqlalchemy').inspect(db.get_engine())
        tables = inspector.get_table_names()
        print(f"   ✅ Tablas en BD: {tables}")
        
        print("\n5. Verificando usuarios...")
        from models import User
        admin_count = User.query.filter_by(rol='admin').count()
        print(f"   ✅ Admins: {admin_count}")
        
        print("\n6. Verificando columnas de usuarios...")
        users_columns = {col['name'] for col in inspector.get_columns('users')}
        required_columns = {'password_reset_token', 'password_reset_expires'}
        missing = required_columns - users_columns
        if missing:
            print(f"   ⚠️  Columnas faltantes: {missing}")
        else:
            print(f"   ✅ Todas las columnas presentes")
        
    print("\n" + "=" * 60)
    print("✅ LA APLICACION INICIA CORRECTAMENTE EN RENDER")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
