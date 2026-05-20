# 📧 Configuración de SendGrid en Render

## Problema Resuelto ✓

Antes el código de recuperación se mostraba en pantalla en lugar de ser enviado al correo. Ahora usa la **API de SendGrid directamente** (más confiable en producción).

---

## ⚙️ Configuración en Render

### Paso 1: Agregar Variables de Entorno en Render

En tu [dashboard de Render](https://dashboard.render.com), ve a tu servicio y configura estas variables:

```
MAIL_FROM = leo.ro151095@gmail.com
SENDGRID_API_KEY = SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**⚠️ IMPORTANTE:**
- La API Key comienza con `SG.`
- Reemplaza `SG.xxxx...` con tu API Key real (la que obtuviste de SendGrid)
- No compartas ni commits la API Key en Git
- Debe estar exactamente como aparece (sin espacios)
- Cambia `leo.ro151095@gmail.com` al correo que desees usar

### Paso 2: Redeploy

En Render, haz clic en el botón **"Manual Deploy"** para reiniciar con las nuevas variables.

---

## 🧪 Verificar Configuración

### Opción A: En Local (para pruebas rápidas)

```bash
# 1. Asegúrate de que requirements.txt esté actualizado
pip install -r requirements.txt

# 2. Ejecuta el test
python test_sendgrid.py tu_email@ejemplo.com
```

**Ejemplo:**
```bash
python test_sendgrid.py leo.ro151095@gmail.com
```

**Resultado esperado:**
```
✓ SendGrid está correctamente configurado
```

### Opción B: Usar el formulario de recuperación

1. Ve a la página de login: `https://tu-app.onrender.com/forgot-password`
2. Ingresa tu correo
3. Selecciona "Enviar por correo"
4. Haz clic en "Enviar"
5. Espera el email en tu bandeja de entrada

---

## 📋 Cómo obtener tu API Key de SendGrid

Si aún no tienes una:

1. Ve a [SendGrid](https://sendgrid.com/)
2. Crea una cuenta gratuita o inicia sesión
3. Ve a **Settings → API Keys**
4. Haz clic en **"Create API Key"**
5. Dale un nombre (ej: "Horas Bienestar Render")
6. Selecciona **"Full Access"** o permisos de email
7. Copia la key (aparecerá una sola vez)

---

## 🔍 Solución de Problemas

### "No recibo emails"

**Posible causa 1: Revisa la carpeta de Spam**
- Gmail, Outlook, etc. a veces filtran emails automatizados

**Posible causa 2: Variables de entorno no actualizadas**
```bash
# En Render, verifica que las variables estén en Environment
# (no en .env local)

# Las variables locales en .env SOLO funcionan en tu PC
# En Render necesitas configurarlas en el dashboard
```

**Posible causa 3: API Key inválida o expirada**
```bash
# Ejecuta nuevamente
python test_sendgrid.py tu_email@ejemplo.com

# Verifica el mensaje de error exacto
```

### "Error: SENDGRID_API_KEY no configurado"

Solución:
1. Ve a Render Dashboard
2. Abre tu servicio
3. Va a **Environment**
4. Agrega/actualiza: `SENDGRID_API_KEY`
5. Haz clic en **"Manual Deploy"**

### "Error: 403 Forbidden en SendGrid"

Significa que la API Key es inválida o no tiene permisos. Obtén una nueva:

1. Ve a [SendGrid API Keys](https://app.sendgrid.com/settings/api_keys)
2. Elimina la key antigua
3. Crea una nueva
4. Cópiala exactamente
5. Actualiza en Render

---

## 📊 Flujo de Recuperación de Contraseña

```
Usuario solicita recuperación
    ↓
Se genera código seguro (token)
    ↓
Se intenta enviar por SendGrid API
    ↓
✓ Si éxito: Usuario ve confirmación, recibe email
✗ Si fallo: Usuario ve error, NO se muestra código
```

**Seguridad:** El código NUNCA se muestra en pantalla, solo en el email.

---

## 📝 Logs de Debug

Si algo no funciona, revisa los logs en Render:

1. Ve a tu servicio en Render
2. Abre **Logs**
3. Busca por "SendGrid" o "email"

Ejemplo de log exitoso:
```
INFO - Intentando enviar email de recuperación a usuario@ejemplo.com
INFO - Email de recuperación enviado exitosamente a usuario@ejemplo.com
```

Ejemplo de log fallido:
```
ERROR - Error enviando email via SendGrid API: SendGrid API error 403
```

---

## ✅ Checklist de Verificación

- [ ] `MAIL_FROM` está configurado en Render
- [ ] `SENDGRID_API_KEY` está configurado en Render (con formato `SG....`)
- [ ] Se ejecutó **Manual Deploy** después de cambiar variables
- [ ] Ejecutaste `python test_sendgrid.py` y pasó
- [ ] Pruebas a recuperar contraseña y recibes el email

---

## 📞 Soporte SendGrid

Si la API Key sigue sin funcionar:

1. Verifica que tu cuenta de SendGrid está **activada**
2. Verifica que **no has superado límites** (free tier = 100 emails/día)
3. Ve a [SendGrid Status](https://status.sendgrid.com/) para verificar si hay apagones

---

## 🎯 Siguiente: SMS (Opcional)

Para agregar envío de código por SMS también:

1. Configura **Twilio** (similar a SendGrid)
2. Agrega variables de entorno:
   ```
   TWILIO_ACCOUNT_SID = xxx
   TWILIO_AUTH_TOKEN = xxx
   TWILIO_FROM_NUMBER = +1234567890
   ```
3. Los usuarios podrán elegir entre Email o SMS

---

**Última actualización:** 19 de mayo de 2026
