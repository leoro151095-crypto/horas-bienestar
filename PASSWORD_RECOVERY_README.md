# 🔐 Sistema de Recuperación de Contraseña

## 📋 Descripción
Se ha agregado un sistema seguro de recuperación de contraseña al proyecto que permite a los usuarios resetear su contraseña sin intervención del administrador.

## ✨ Características
- ✅ **Token de recuperación**: Códigos seguros generados con `secrets` (32 caracteres aleatorios)
- ✅ **Expiración**: Los códigos expiran en 30 minutos
- ✅ **Múltiples canales**: Email o SMS
- ✅ **Auditoría completa**: Todos los intentos se registran en audit_logs
- ✅ **Sin daños**: Los cambios son totalmente reversibles
- ✅ **Retrocompatible**: Funciona con bases de datos existentes

## 🚀 Instalación

### 1. Migración de Base de Datos (Una sola vez)
```bash
python migrate_add_password_reset.py
```
Esto agregará 2 columnas a la tabla `users`:
- `password_reset_token` (VARCHAR 256)
- `password_reset_expires` (DATETIME)

### 2. Configuración de Notificaciones (Opcional pero recomendado)

#### Para Email (SMTP):
```env
# En tu .env o variables de entorno
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-o-app-password
MAIL_FROM=noreply@tuuniversidad.edu.co
SMTP_USE_TLS=true
```

#### Para SMS (Twilio):
```env
TWILIO_ACCOUNT_SID=tu-sid
TWILIO_AUTH_TOKEN=tu-token
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
```

## 🔄 Flujo de Usuario

### Para Estudiante que Olvidó su Contraseña:

1. **En login.html** → Click en "¿Olvidó su contraseña?"
2. **En /forgot-password** → Ingresa tu correo
3. **Selecciona canal**:
   - 📧 Email: Recibirás un enlace + código
   - 📱 SMS: Recibirás el código (primeros 8 caracteres)
4. **En /reset-password/<token>** → Ingresa nueva contraseña
5. **✅ Listo** → Puedes iniciar sesión con tu nueva contraseña

## 🔒 Seguridad

### Medidas Implementadas:
- **Tokens únicos y seguros**: Generados con `secrets.token_urlsafe(32)`
- **Expiración limitada**: 30 minutos
- **One-time use**: El token se elimina después de usarse
- **Auditoría**: Todos los eventos registrados en `audit_logs`:
  - `forgot_password_requested`
  - `forgot_password_email_sent`
  - `forgot_password_email_failed`
  - `forgot_password_sms_sent`
  - `forgot_password_sms_failed`
  - `forgot_password_nonexistent` (sin revelar si usuario existe)
  - `forgot_password_expired`
  - `password_reset`
  - `reset_password_invalid_token`

- **Rate limiting**: Ya existente en el login (5 minutos)
- **Validación de dominio**: Solo usuarios institucionales (si está habilitado)
- **Validación adicional**: Los estudiantes no pueden usar últimos 4 dígitos del documento

## 📁 Archivos Modificados/Creados

### Modificados:
- **models.py**: +2 columnas a la clase `User`
- **app.py**: +2 rutas nuevas (`forgot_password`, `reset_password`)
- **templates/login.html**: Enlace actualizado a `/forgot-password`

### Creados:
- **templates/forgot_password.html**: Formulario de solicitud
- **templates/reset_password.html**: Formulario de actualización
- **migrate_add_password_reset.py**: Script de migración

## 🧪 Pruebas

### En Desarrollo (DEBUG=true):
```bash
# Los emails se pueden probar con print en la consola
# Los SMS se pueden probar sin credenciales de Twilio
```

### En Producción:
```bash
# Verificar que SMTP_HOST y Twilio estén configurados
# Los logs estarán en app.log
```

## 🔄 Reversión (Si es necesario)

Si necesitas revertir los cambios:

```bash
# En desarrollo (DEBUG=true):
python migrate_add_password_reset.py --rollback

# En producción: Es más seguro hacer backup y eliminar las columnas manualmente
# O simplemente no usar la funcionalidad (los campos están ahí pero inactivos)
```

## 📊 Monitoreo

Puedes monitorear los intentos de recuperación en admin_audit_logs:

```python
# Ver intentos recientes
AuditLog.query.filter(
    AuditLog.action.in_([
        'forgot_password_requested',
        'forgot_password_email_sent',
        'password_reset'
    ])
).order_by(AuditLog.created_at.desc()).limit(10).all()
```

## ⚠️ Consideraciones

1. **Email sin configurar**: Los usuarios verán mensaje amigable pero no recibirán emails
2. **SMS sin Twilio**: Los usuarios verán opción de SMS pero fallará silenciosamente (registrado en logs)
3. **Tokens expirados**: Usuario debe solicitar código nuevo (se limpia la BD automáticamente)
4. **Múltiples solicitudes**: El token anterior se reemplaza por uno nuevo

## 🆘 Troubleshooting

### "Error enviando email":
- Verificar SMTP_HOST, SMTP_USER, SMTP_PASSWORD
- Si es Gmail, usar [App Password](https://myaccount.google.com/apppasswords)

### "Enlace inválido o expirado":
- Los enlaces duran 30 minutos
- El usuario debe solicitar uno nuevo

### "La migración no funcionó":
```bash
# Eliminar app.db y dejar que se recree:
del instance/app.db
python app.py  # Se creará nueva BD
python migrate_add_password_reset.py
```

## 📝 Ejemplo de Email Enviado

```
Asunto: Recuperar contraseña - Horas Bienestar

Hola [Nombre],

Recibimos una solicitud de recuperación de contraseña. 
Si no fuiste tú, ignora este mensaje.

Código de recuperación: [32-caracteres-token]

O haz clic en el siguiente enlace (válido por 30 minutos):
https://tuapp.com/reset-password/[token]

Si el enlace no funciona, copia el código anterior 
y pégalo en el formulario de recuperación.

Saludos,
Sistema de Horas de Bienestar
```

## 🎯 Próximas Mejoras (Opcionales)

- [ ] Confirmación por 2FA antes de resetear
- [ ] Historial de cambios de contraseña
- [ ] Notificación cuando se resetea contraseña
- [ ] Preguntas de seguridad
- [ ] Integración con Google/Microsoft

---

**Versión**: 1.0  
**Última actualización**: Mayo 2026  
**Estado**: ✅ Producción lista
