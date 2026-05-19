# Configuración de Recuperación de Contraseña

## El Problema

Para que funcione la recuperación de contraseña, necesitas configurar:
1. **Email (SMTP)** - OBLIGATORIO para enviar códigos por correo
2. **SMS (Twilio)** - OPCIONAL para enviar códigos por SMS

## Solución: Configurar Email (Gmail)

### Paso 1: Crear una Contraseña de Aplicación en Google

1. Ir a https://myaccount.google.com/security
2. En el lado izquierdo, hacer clic en "Seguridad"
3. Buscar "Contraseñas de aplicación" (si no ves esto, activa autenticación de 2 factores primero)
4. Seleccionar:
   - Aplicación: **Mail**
   - Dispositivo: **Windows, Mac o Linux**
5. Google te generará una contraseña de 16 caracteres

### Paso 2: Configurar las Variables de Entorno

En tu archivo `.env` (o en Render en Settings > Environment Variables):

```env
MAIL_FROM=tu-email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_USE_TLS=true
```

Ejemplo completo:
```env
MAIL_FROM=bienestar@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=bienestar@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
SMTP_USE_TLS=true
```

### Paso 3: Reiniciar la Aplicación

- **Localmente**: Reinicia `python app.py`
- **En Render**: Haz push a GitHub para triggear redeploy

### Paso 4: Probar

1. Ir a http://localhost:5000/forgot-password
2. Ingresar un email existente
3. Seleccionar "Por email"
4. Deberías recibir el código

## Alternativa: Usar Sendgrid (Recomendado para Producción)

### Paso 1: Crear Cuenta en Sendgrid

1. Ir a https://sendgrid.com/
2. Registrarse y crear cuenta
3. Ir a Settings > API Keys
4. Crear una nueva API Key

### Paso 2: Configurar Variables de Entorno

```env
MAIL_FROM=noreply@uccbienestarmonteria.site
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.tu-api-key-aqui
SMTP_USE_TLS=true
```

## Configurar SMS (Twilio) - OPCIONAL

Si quieres que los estudiantes reciban códigos por SMS:

### Paso 1: Crear Cuenta en Twilio

1. Ir a https://www.twilio.com
2. Registrarse y crear cuenta
3. Ir a Console > Account Info
4. Copiar:
   - Account SID
   - Auth Token
5. Ir a Phone Numbers > Manage Numbers
6. Comprar un número de teléfono (costo ~$1 USD/mes)

### Paso 2: Configurar Variables de Entorno

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1234567890
```

### Paso 3: Probar

1. Ir a http://localhost:5000/forgot-password
2. Ingresar un email con celular registrado
3. Seleccionar "Por SMS"
4. El código llegará al celular

## ¿Qué Pasa Si No Configuro Nada?

Si no configuras Email ni SMS:
- El código se mostrará en pantalla en la página de confirmación
- El usuario podrá copiar el código manualmente
- Es menos seguro pero funciona

## Troubleshooting

### "No llega el email"

1. **Revisa que las variables estén configuradas:**
   ```bash
   # En tu app, agrega esto temporalmente para debuggear
   echo $MAIL_FROM
   echo $SMTP_HOST
   ```

2. **Verifica credenciales de Gmail:**
   - Asegúrate de usar contraseña de aplicación (no la contraseña normal)
   - La contraseña tiene 16 caracteres sin espacios en el código

3. **Revisa spam/correo no deseado**

4. **En los logs, deberías ver:**
   ```
   Ejecutando: ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(256)
   Ejecutando: ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP
   ```

### "Error email: [Errno 11001]"

Significa que no puede conectar a smtp.gmail.com. Posibles causas:
- Firewall bloqueando puerto 587
- SMTP_HOST mal escrito
- Credenciales incorrectas

### "No llega SMS"

1. **Twilio no está configurado:**
   - Verifica que TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN tengan valores
   - Si están vacíos, el código se mostrará en pantalla

2. **Número de teléfono incorrecto:**
   - Debe incluir código de país (+57 para Colombia)
   - Formato: +57 3001234567

3. **Balance insuficiente:**
   - Twilio cobra por cada SMS (~$0.01 USD)
   - Asegúrate de tener crédito en la cuenta

## Configuración en Render

### Paso 1: Ir al Dashboard de Render

1. Ir a https://dashboard.render.com
2. Seleccionar tu servicio "horas-bienestar"
3. Ir a Settings

### Paso 2: Agregar Variables de Entorno

1. Hacer clic en "Environment"
2. Agregar variables:
   - MAIL_FROM=bienestar@gmail.com
   - SMTP_HOST=smtp.gmail.com
   - SMTP_PORT=587
   - SMTP_USER=bienestar@gmail.com
   - SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   - SMTP_USE_TLS=true

3. Hacer clic en "Save"

### Paso 3: Redeploy

Render debería redeploy automáticamente o hacer clic en "Deploy latest commit"

## Verificar que Está Funcionando

1. **Localmente:**
   ```bash
   python app.py
   ```
   Deberías ver en los logs:
   ```
   Agregando columna: ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(256)
   Columna password_reset_token agregada exitosamente
   Agregando columna: ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP
   Columna password_reset_expires agregada exitosamente
   ```

2. **Ir a login:**
   - Hacer clic en "¿Olvidaste tu contraseña?"
   - Ingresar email de estudiante
   - Seleccionar método (Email o SMS)
   - Si las variables están correctas, recibirás el código

## Resumen Quick Start

Para que funcione **hoy mismo**:

1. **Opción rápida (Gmail):**
   ```bash
   # En .env o Render settings
   MAIL_FROM=tu-email@gmail.com
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=tu-email@gmail.com
   SMTP_PASSWORD=contraseña-app-16-caracteres
   SMTP_USE_TLS=true
   ```

2. **Reiniciar app**

3. **Probar:** http://localhost:5000/forgot-password

¡Listo! Ya debería funcionar.
