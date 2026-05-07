from itsdangerous import URLSafeTimedSerializer
from io import BytesIO
from flask import url_for


def make_serializer(secret_key):
    return URLSafeTimedSerializer(secret_key)

def generate_token(secret_key, actividad_id):
    s = make_serializer(secret_key)
    return s.dumps({"actividad_id": actividad_id})

def verify_token(secret_key, token, max_age=1800):
    s = make_serializer(secret_key)
    try:
        data = s.loads(token, max_age=max_age)
        return data
    except Exception:
        return None

def generate_qr_image(url):
    try:
        import qrcode
    except Exception as exc:
        raise RuntimeError('qrcode no está instalado en este entorno') from exc
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf
