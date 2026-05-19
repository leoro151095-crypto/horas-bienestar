# Solución: Recuperación de Contraseña - Render Deployment

## Problema Identificado

En Render, la base de datos PostgreSQL tenía un estado inconsistente:
- Las columnas `password_reset_token` y `password_reset_expires` no existían en la tabla `users`
- El tipo de dato `DATETIME` (SQLite) no es válido en PostgreSQL - debe ser `TIMESTAMP`

## Solución Implementada

Se han realizado las siguientes mejoras:

### 1. **Función `ensure_user_columns()` Mejorada**
   - Ahora detecta correctamente entre `DATETIME` (SQLite) y `TIMESTAMP` (PostgreSQL)
   - Usa `engine.begin()` para mejor manejo de transacciones
   - Mejor logging para debugging
   - No bloquea el startup incluso si hay errores

### 2. **Función `ensure_default_admin()` Robusta**
   - Si la query normal de SQLAlchemy falla por columnas faltantes, intenta una query SQL cruda
   - Permite que el admin se cree incluso en estado de BD inconsistente

### 3. **Columnas Agregadas al Modelo User**
   ```python
   password_reset_token = db.Column(db.String(256), nullable=True)
   password_reset_expires = db.Column(db.DateTime, nullable=True)
   ```

## Rutas de Recuperación de Contraseña Implementadas

### Solicitar Recuperación (Estudiante o Personal)
- **Ruta**: `POST /forgot-password`
- **Métodos de entrega**:
  - **Email**: Envía código al `correo_personal` (si existe) o `correo` institucional
  - **SMS**: Envía código al `celular`
- **Código**: Válido por 30 minutos

### Restablecer Contraseña
- **Ruta**: `GET/POST /reset-password/<token>`
- **Validaciones**:
  - Token válido y no expirado
  - Contraseña mínimo 6 caracteres
  - Contraseñas coinciden
  - Para estudiantes: no puede ser los últimos 4 dígitos del documento

## Deployment en Render

### Pasos para Actualizar Render:

1. **Los cambios están en GitHub** (`main` branch)
   - Render debería detectar el push automáticamente
   - Iniciará un nuevo deploy

2. **Si Render aún tiene errores de "columna no existe"**:
   - El script `migrate_password_reset_columns.py` se ejecutará automáticamente en Render
   - Pero también puedes ejecutarlo manualmente:
   ```bash
   # Localmente para probar
   python migrate_password_reset_columns.py
   
   # En Render (via console)
   python migrate_password_reset_columns.py
   ```

### Orden de Inicialización en la App

1. `db.create_all()` - Crea todas las tablas/columnas definidas en modelos
2. `ensure_user_columns()` - Agrega columnas faltantes si es necesario
3. `ensure_default_admin()` - Crea/actualiza el admin por defecto

## Verificación de la Solución

Para verificar que todo funciona:

### Localmente:
```bash
# 1. Ejecutar la migración
python migrate_password_reset_columns.py

# 2. Iniciar la app
python app.py

# 3. Probar flujo de recuperación
curl -X POST http://localhost:5000/forgot-password \
  -d "correo=student@campusucc.edu.co&delivery_method=email"
```

### En Render:
1. Ir a https://www.uccbienestarmonteria.site/login
2. Hacer clic en "¿Olvidaste tu contraseña?"
3. Ingresar email de estudiante
4. Seleccionar método (Email o SMS)
5. Verificar que se recibe el código

## Características Implementadas

✅ **Recuperación por Email**: Estudiantes reciben código en correo personal  
✅ **Recuperación por SMS**: Estudiantes reciben código en celular  
✅ **Token con Expiración**: Válido por 30 minutos  
✅ **Auditoría Completa**: Todos los intentos se registran en `audit_logs`  
✅ **Validaciones**: Contraseña fuerte, no reutilización  
✅ **PostgreSQL Compatible**: Usa `TIMESTAMP` en lugar de `DATETIME`  

## Archivos Modificados

- `app.py` - Funciones de recuperación y mejoras a inicialización
- `models.py` - Columnas de password reset en modelo User
- `migrate_password_reset_columns.py` - Script de migración seguro
- `templates/forgot_password.html` - Formulario de solicitud
- `templates/reset_password.html` - Formulario de restablecimiento

## Próximos Pasos (Si Aún Hay Errores)

Si después del redeploy en Render aún hay errores:

1. **Verificar logs de Render**:
   - Ir a Dashboard de Render
   - Revisar "Logs"
   - Buscar errores de PostgreSQL

2. **Ejecutar migración manual**:
   - Usar Render Shell (si está disponible)
   - O conectar con herramientas como DBeaver/pgAdmin

3. **Como último recurso**:
   - Hacer backup de datos
   - Destruir y recrear la BD en Render
   - El app creará todas las tablas correctamente

## Contacto/Debugging

Para debuggear:
```bash
# Ver qué columnas existen
psql $DATABASE_URL -c "\\d users"

# Ver si las columnas están creadas
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
```
