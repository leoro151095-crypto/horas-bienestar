import logging
import smtplib
from email.mime.text import MIMEText

try:
    from twilio.rest import Client
except Exception:
    Client = None


def send_email(config, to_email, subject, body):
    if not to_email:
        return False, 'Sin correo destino'
    if not config.get('SMTP_HOST') or not config.get('MAIL_FROM'):
        return False, 'SMTP no configurado'
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = config.get('MAIL_FROM')
    msg['To'] = to_email
    try:
        with smtplib.SMTP(config.get('SMTP_HOST'), config.get('SMTP_PORT', 587), timeout=10) as server:
            if config.get('SMTP_USE_TLS', True):
                server.starttls()
            if config.get('SMTP_USER'):
                server.login(config.get('SMTP_USER'), config.get('SMTP_PASSWORD'))
            server.send_message(msg)
        return True, 'Email enviado'
    except Exception as exc:
        logging.exception('Error enviando email')
        return False, f'Error email: {exc}'


def send_sms(config, to_number, body):
    if not to_number:
        return False, 'Sin número destino'
    sid = config.get('TWILIO_ACCOUNT_SID')
    token = config.get('TWILIO_AUTH_TOKEN')
    from_number = config.get('TWILIO_FROM_NUMBER')
    if not sid or not token or not from_number:
        return False, 'Twilio no configurado'
    if Client is None:
        return False, 'Librería Twilio no disponible'
    try:
        client = Client(sid, token)
        client.messages.create(
            body=body,
            from_=from_number,
            to=str(to_number)
        )
        return True, 'SMS enviado'
    except Exception as exc:
        logging.exception('Error enviando SMS')
        return False, f'Error sms: {exc}'
