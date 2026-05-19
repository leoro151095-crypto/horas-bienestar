#!/usr/bin/env python3
"""Extraer y restaurar BD de git."""
import subprocess
import os

print("Extrayendo BD válida del commit 74f9646...")

# Obtener el blob de forma binaria correcta
result = subprocess.run(
    ['git', 'cat-file', 'blob', '74f9646:instance/app.db'],
    capture_output=True,
    text=False  # ¡IMPORTANTE! Obtener bytes sin procesar
)

blob_data = result.stdout

# Guardar como app.db.valid
output_file = 'instance/app.db.valid'
with open(output_file, 'wb') as f:
    f.write(blob_data)

print(f"✅ Archivo guardado: {output_file}")
print(f"   Tamaño: {len(blob_data)} bytes")
print(f"   Header: {blob_data[:16]}")

# Verificar que es válido
import sqlite3
try:
    conn = sqlite3.connect(output_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    estudiantes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE rol='docente'")
    docentes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE rol='admin'")
    admins = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n📊 Datos en la BD:")
    print(f"   ✓ Estudiantes: {estudiantes}")
    print(f"   ✓ Docentes: {docentes}")
    print(f"   ✓ Administradores: {admins}")
    
    if estudiantes > 0 or docentes > 0:
        print(f"\n✅ ¡BD válida con datos!")
        
        # Ahora reemplazar la BD actual
        import shutil
        print("\nRestaurando BD...")
        shutil.copy(output_file, 'instance/app.db')
        print("✅ BD restaurada en instance/app.db")
    else:
        print("\n⚠️  BD válida pero sin datos")
        
except Exception as e:
    print(f"\n❌ Error al verificar BD: {e}")
    import traceback
    traceback.print_exc()
