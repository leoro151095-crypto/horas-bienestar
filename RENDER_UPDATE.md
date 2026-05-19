# 🚀 Actualización de Render - Recuperación de Contraseña

## ¿Qué cambios se han subido?

Se han subido cambios al repositorio que incluyen:

✅ **Nuevas páginas:**
- Página "¿Olvidó su contraseña?" (forgot_password.html)
- Página de "Restablecer contraseña" (reset_password.html)

✅ **Nueva funcionalidad:**
- Envío de códigos de recuperación por **email**
- Envío de códigos de recuperación por **SMS** (celular)
- Migración automática de columnas de base de datos

---

## 🔧 Pasos para actualizar Render

### 1️⃣ Render debería auto-actualizar

Si tienes habilitado el **Auto-Deploy** en Render, la aplicación se actualizará automáticamente cuando detecte los cambios en GitHub.

Puedes verificar el estado en:
👉 https://dashboard.render.com

### 2️⃣ Configurar Variables de Entorno (IMPORTANTE ⚠️)

Para que el email y SMS funcionen en Render, necesitas agregar estas variables de entorno en el dashboard de Render:

#### **Para Email:**
```
MAIL_FROM = tu-correo@example.com
SMTP_HOST = smtp.gmail.com (o tu proveedor)
SMTP_PORT = 587
SMTP_USER = tu-correo@gmail.com
SMTP_PASSWORD = tu-contraseña-o-app-password
SMTP_USE_TLS = true
```

#### **Para SMS (Twilio):**
```
TWILIO_ACCOUNT_SID = tu_account_sid
TWILIO_AUTH_TOKEN = tu_auth_token
TWILIO_FROM_NUMBER = +1234567890 (tu número Twilio)
```

---

## 📋 Pasos detallados para configurar en Render:

### Para Email (Gmail como ejemplo):

1. Ve a **Environment** en tu servicio de Render
2. Agrega estas variables:
   - `MAIL_FROM` = tu-correo@gmail.com
   - `SMTP_HOST` = smtp.gmail.com
   - `SMTP_PORT` = 587
   - `SMTP_USER` = tu-correo@gmail.com
   - `SMTP_PASSWORD` = tu **App Password** (no contraseña normal)
   
   **Para obtener App Password de Gmail:**
   - Ve a https://myaccount.google.com/
   - Seguridad → Contraseñas de aplicaciones
   - Selecciona "Correo" y "Windows"
   - Copia la contraseña generada

### Para SMS (Twilio):

1. Crea una cuenta en https://www.twilio.com
2. Obtén tu:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_FROM_NUMBER` (número Twilio)
3. Agrega estas variables en Render → Environment

---

## ✅ Verificación

Después de actualizar las variables de entorno:

1. Render volverá a hacer deploy automáticamente
2. Intenta usar "¿Olvidó su contraseña?" en tu aplicación desplegada
3. Deberías recibir un código por email o SMS

---

## 🔍 Solución de problemas

Si no recibes códigos de recuperación:

1. **Verifica las variables de entorno** están correctas en Render
2. **Revisa los logs** en Render → Logs
3. **Verifica que el email/SMS es válido** en la base de datos
4. **Para Gmail:** Asegúrate de usar **App Password**, no contraseña normal

---

## 📝 Notas importantes

- La BD en Render es temporal (SQLite en /tmp)
- Se recrea cada vez que haces deploy
- Los datos de prueba se pierden con cada deploy (considera usar PostgreSQL para producción)
- Las migraciones se ejecutan automáticamente al iniciar la aplicación

