import logging
import smtplib
import requests
from email.mime.text import MIMEText

try:
    from twilio.rest import Client
except Exception:
    Client = None


def send_email_sendgrid(config, to_email, subject, body):
    """Envía email usando la API de SendGrid (más confiable en producción)"""
    if not to_email:
        return False, 'Sin correo destino'
    
    api_key = config.get('SENDGRID_API_KEY')
    from_email = config.get('MAIL_FROM')
    
    if not api_key or not from_email:
        return False, 'SendGrid API Key o MAIL_FROM no configurado'
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'personalizations': [
                {
                    'to': [{'email': to_email}],
                    'subject': subject
                }
            ],
            'from': {'email': from_email},
            'content': [
                {
                    'type': 'text/plain',
                    'value': body
                }
            ]
        }
        
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in (200, 201, 202):
            logging.info(f'Email enviado exitosamente a {to_email} via SendGrid API')
            return True, 'Email enviado'
        else:
            error_msg = f'SendGrid API error {response.status_code}: {response.text}'
            logging.error(error_msg)
            return False, error_msg
            
    except Exception as exc:
        logging.exception('Error enviando email via SendGrid API')
        return False, f'Error email: {exc}'


def send_email_smtp(config, to_email, subject, body):
    """Envía email usando SMTP (fallback)"""
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
        logging.info(f'Email enviado exitosamente a {to_email} via SMTP')
        return True, 'Email enviado'
    except Exception as exc:
        logging.exception('Error enviando email via SMTP')
        return False, f'Error email: {exc}'


def send_email(config, to_email, subject, body):
    """Envía email usando SendGrid API si está disponible, sino usa SMTP"""
    # Intentar con SendGrid API primero (más confiable en producción)
    if config.get('SENDGRID_API_KEY'):
        success, message = send_email_sendgrid(config, to_email, subject, body)
        if success:
            return True, message
        # Si falla, loguear pero continuar con SMTP como fallback
        logging.warning(f'SendGrid API falló, intentando con SMTP: {message}')
    
    # Fallback a SMTP
    return send_email_smtp(config, to_email, subject, body)


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
