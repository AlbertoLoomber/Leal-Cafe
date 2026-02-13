# Guía de Deployment en Render

## Preparación previa

1. **Crear cuenta en Render**: Ve a [render.com](https://render.com) y crea una cuenta
2. **Crear repositorio en GitHub**: Sube tu código a GitHub
3. **Configurar variables de entorno**: Prepara las variables necesarias

## Pasos para Deploy

### 1. Crear Base de Datos PostgreSQL en Render

1. En el dashboard de Render, click en "New +" → "PostgreSQL"
2. Configura:
   - **Name**: `leal-cafe-db`
   - **Database**: `lealdb`
   - **User**: `lealcafe`
   - **Region**: Elige la más cercana
   - **Plan**: Free (o el que prefieras)
3. Click en "Create Database"
4. Espera a que se cree (toma unos minutos)
5. **Guarda la "Internal Database URL"** - la necesitarás

### 2. Crear Web Service

1. En el dashboard, click en "New +" → "Web Service"
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Name**: `leal-cafe`
   - **Region**: La misma que la base de datos
   - **Branch**: `main` (o tu rama principal)
   - **Root Directory**: (dejar vacío)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Plan**: Free (o el que prefieras)

### 3. Configurar Variables de Entorno

En la sección "Environment Variables" del web service, agrega:

```
SECRET_KEY=<genera-una-clave-secreta-aleatoria>
FLASK_ENV=production
DATABASE_URL=<pega-aqui-la-internal-database-url>
```

**Importante**:
- Genera un `SECRET_KEY` aleatorio y seguro (puedes usar: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Usa la "Internal Database URL" de tu base de datos PostgreSQL

### 4. Deploy

1. Click en "Create Web Service"
2. Render automáticamente:
   - Clonará tu repositorio
   - Instalará las dependencias
   - Iniciará la aplicación
3. Espera a que termine el deploy (puede tardar varios minutos la primera vez)

### 5. Verificar

1. Una vez completado, Render te dará una URL como: `https://leal-cafe.onrender.com`
2. Abre esa URL en tu navegador
3. Deberías ver tu aplicación funcionando

## Problemas Comunes

### La app no inicia
- Revisa los logs en Render Dashboard → Tu servicio → "Logs"
- Verifica que todas las variables de entorno estén configuradas
- Asegúrate de que el `DATABASE_URL` sea el correcto

### Error de base de datos
- Verifica que la base de datos esté activa
- Asegúrate de usar la "Internal Database URL" (no la External)
- Verifica que las tablas se hayan creado correctamente

### La app es lenta
- En el plan Free, Render "duerme" tu app después de 15 minutos de inactividad
- La primera petición después de estar dormida puede tardar 30-60 segundos
- Considera upgradar a un plan pagado para evitar esto

## Actualizaciones

Para actualizar tu aplicación:

1. Haz push de tus cambios a GitHub:
   ```bash
   git add .
   git commit -m "Descripción de cambios"
   git push origin main
   ```

2. Render automáticamente detectará los cambios y re-desplegará tu app

## Monitoreo

- **Logs**: Ve a tu servicio → "Logs" para ver logs en tiempo real
- **Métricas**: Ve a tu servicio → "Metrics" para ver uso de CPU/memoria
- **Events**: Ve a tu servicio → "Events" para ver historial de deploys

## Base de Datos

### Backup
- Render hace backups automáticos en planes pagados
- Para el plan Free, considera hacer backups manuales usando `pg_dump`

### Acceso directo
- Puedes conectarte directamente usando la "External Database URL"
- Usa herramientas como pgAdmin, DBeaver, o psql

## Seguridad

✅ **Ya implementado:**
- Variables de entorno para credenciales sensibles
- `.gitignore` para excluir archivos sensibles
- Cookies seguras en producción
- SECRET_KEY desde variables de entorno

⚠️ **Recomendaciones adicionales:**
- Configura un dominio personalizado con HTTPS
- Implementa rate limiting para prevenir abusos
- Considera usar Redis para sesiones en producción
- Monitorea logs regularmente

## Costos

**Plan Free incluye:**
- 750 horas de ejecución al mes
- Base de datos PostgreSQL con 1GB de almacenamiento
- La app se "duerme" tras 15 min de inactividad

**Para producción seria, considera:**
- Plan Starter ($7/mes por servicio)
- Base de datos con backups automáticos
- Sin suspensión automática
