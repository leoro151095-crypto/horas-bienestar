import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = os.path.join('instance','app.db')
if not os.path.exists(db_path):
    print('NO_DB', db_path)
    raise SystemExit(1)

correo = 'docente@campusucc.edu.co'
password = 'docente'
nombre = 'docente'
rol = 'docente'

pwd_hash = generate_password_hash(password)
conn = sqlite3.connect(db_path)
cur = conn.cursor()
# Check if user exists with correo
cur.execute('SELECT id FROM users WHERE correo = ?', (correo,))
row = cur.fetchone()
if row:
    uid = row[0]
    cur.execute('UPDATE users SET password_hash = ?, nombre = ?, rol = ? WHERE id = ?', (pwd_hash, nombre, rol, uid))
    print('UPDATED existing user', correo)
else:
    # insert new user
    cur.execute('INSERT INTO users (nombre, correo, password_hash, rol) VALUES (?, ?, ?, ?)', (nombre, correo, pwd_hash, rol))
    print('INSERTED user', correo)
conn.commit()
conn.close()
