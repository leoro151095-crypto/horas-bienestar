import sqlite3
import os
p = os.path.join('instance','app.db')
if not os.path.exists(p):
    print('NO_DB', p)
else:
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, correo, rol FROM users")
        rows = cur.fetchall()
        if not rows:
            print('NO_USERS_IN_INSTANCE_DB')
        else:
            for r in rows:
                print('USER:', r)
    except Exception as e:
        print('ERROR', e)
    finally:
        conn.close()
