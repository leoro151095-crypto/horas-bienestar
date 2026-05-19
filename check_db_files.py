#!/usr/bin/env python3
"""Verificar integridad de archivos de base de datos."""
import os

def check_db_file(filepath):
    """Verificar si un archivo es una DB SQLite válida."""
    if not os.path.exists(filepath):
        print(f"❌ Archivo no existe: {filepath}")
        return False
    
    size = os.path.getsize(filepath)
    print(f"📄 {filepath}")
    print(f"   Tamaño: {size} bytes")
    
    with open(filepath, 'rb') as f:
        header = f.read(16)
    
    # Verificar firma SQLite
    if header.startswith(b'SQLite format 3'):
        print(f"   ✅ Es una BD SQLite válida")
        return True
    else:
        print(f"   ❌ NO es una BD SQLite (header: {header[:16]})")
        return False

files = [
    'instance/app.db',
    'instance/app.db.backup',
    'instance/app.db.old'
]

print("=" * 50)
print("Verificando archivos de BD:")
print("=" * 50)

for f in files:
    if os.path.exists(f):
        check_db_file(f)
    print()
