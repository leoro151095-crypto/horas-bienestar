import requests

LOGIN_URL = 'http://127.0.0.1:5000/login'
CRED = {'correo': 'docente@campusucc.edu.co', 'password': 'docente'}

s = requests.Session()
try:
    r = s.get(LOGIN_URL, timeout=5)
except Exception as e:
    print('ERROR_CONNECT', e)
    raise SystemExit(1)

r = s.post(LOGIN_URL, data=CRED, allow_redirects=True, timeout=10)
print('HTTP_STATUS', r.status_code)
print('FINAL_URL', r.url)
if '/docente' in r.url:
    print('LOGIN_OK')
else:
    print('LOGIN_FAIL')
    if 'Credenciales inválidas' in r.text:
        print('MESSAGE: Credenciales inválidas')
    else:
        # show a short snippet for debugging
        snippet = r.text.replace('\n', ' ')[:800]
        print('PAGE_SNIPPET:', snippet)
