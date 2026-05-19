#!/usr/bin/env python3
"""Mostrar usuarios y estudiantes en la BD."""
import sqlite3

conn = sqlite3.connect('instance/app.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('===== USUARIOS EN LA BD =====\n')

cursor.execute('SELECT id, nombre, apellido, correo, rol FROM users ORDER BY rol')
usuarios = cursor.fetchall()

for u in usuarios:
    print(f'Nombre: {u["nombre"]} {u["apellido"]}')
    print(f'Email: {u["correo"]}')
    print(f'Rol: {u["rol"]}')
    print()

print('\n===== ESTUDIANTES REGISTRADOS =====\n')
cursor.execute('SELECT primer_nombre, primer_apellido, numero_documento, correo_institucional FROM students')
estudiantes = cursor.fetchall()

if estudiantes:
    for i, e in enumerate(estudiantes, 1):
        print(f'{i}. {e[0]} {e[1]}')
        print(f'   Documento: {e[2]}')
        print(f'   Email: {e[3]}')
        print()
else:
    print('No hay estudiantes registrados')

conn.close()
