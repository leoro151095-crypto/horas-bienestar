import re

# Leer el archivo
with open('templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la imagen en base64 con la referencia a logoucc.jpeg
content = re.sub(
    r'src="data:image/jpeg;base64,[^"]*"',
    'src="{{ url_for(\'static\', filename=\'logoucc.jpeg\') }}"',
    content
)

# Escribir el archivo
with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Logo reemplazado exitosamente')
