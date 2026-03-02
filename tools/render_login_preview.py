import os
import importlib.util
import sys
from flask import render_template

os.makedirs('preview', exist_ok=True)

# Cargar app.py dinámicamente desde la ruta del proyecto
app_path = os.path.join(os.getcwd(), 'app.py')
# Asegurar que el directorio del proyecto esté en sys.path para resolver imports locales
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
spec = importlib.util.spec_from_file_location('app_module', app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = getattr(app_module, 'app')

with app.app_context():
    with app.test_request_context('/login'):
        html = render_template('login.html')

out_path = os.path.join('preview', 'preview_login.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(out_path)
