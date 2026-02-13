import os
from datetime import timedelta
from urllib.parse import urlparse

class Config:
    """Configuración base de la aplicación Leal Café"""

    # Secret key para sesiones (cambiar en producción)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'leal-cafe-secret-key-2024'

    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuración de PostgreSQL
    # Si existe DATABASE_URL (Render), úsala; si no, usa las variables individuales
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL:
        # Parse DATABASE_URL para extraer componentes
        url = urlparse(DATABASE_URL)
        POSTGRES_HOST = url.hostname
        POSTGRES_PORT = url.port or 5432
        POSTGRES_USER = url.username
        POSTGRES_PASSWORD = url.password
        POSTGRES_DATABASE = url.path[1:]  # Remover el '/' inicial
    else:
        # Usar variables individuales
        POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
        POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
        POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
        POSTGRES_DATABASE = os.environ.get('POSTGRES_DATABASE', 'leal_cafe')

    # Configuración de archivos
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

    # Configuración de la aplicación
    APP_NAME = 'Leal Café'
    APP_VERSION = '1.0.0'

    # Timezone
    TIMEZONE = 'America/Mexico_City'

    @staticmethod
    def init_app(app):
        """Inicializar configuraciones adicionales"""
        # Crear carpeta de uploads si no existe
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
