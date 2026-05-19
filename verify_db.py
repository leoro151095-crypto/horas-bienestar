#!/usr/bin/env python3
"""Verificar datos en la base de datos restaurada."""
import sqlite3

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

# Contar estudiantes
cursor.execute('SELECT COUNT(*) FROM students')
estudiantes = cursor.fetchone()[0]

# Contar docentes
cursor.execute("SELECT COUNT(*) FROM users WHERE rol='docente'")
docentes = cursor.fetchone()[0]

# Contar admins
cursor.execute("SELECT COUNT(*) FROM users WHERE rol='admin'")
admins = cursor.fetchone()[0]

print(f"📊 Datos en la BD restaurada:")
print(f"  - Estudiantes: {estudiantes}")
print(f"  - Docentes: {docentes}")
print(f"  - Administradores: {admins}")

if estudiantes > 0 or docentes > 0:
    print("\n✅ ¡Los datos fueron recuperados exitosamente!")
else:
    print("\n❌ La BD parece estar vacía")

conn.close()
