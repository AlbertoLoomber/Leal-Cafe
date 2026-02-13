import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Crear conexión a PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DATABASE,
            cursor_factory=RealDictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {str(e)}")
        raise

def execute_query(query, params=None):
    """
    Ejecutar query y retornar resultados

    Args:
        query (str): Query SQL a ejecutar
        params (dict o tuple): Parámetros para query parametrizada

    Returns:
        list: Resultados de la query
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        try:
            results = cursor.fetchall()
            return results
        except psycopg2.ProgrammingError:
            # Query no retorna resultados (INSERT, UPDATE, etc)
            return []

    except Exception as e:
        logger.error(f"Error ejecutando query: {str(e)}")
        raise

    finally:
        if connection:
            connection.close()

def execute_insert(query, data):
    """
    Ejecutar INSERT múltiple

    Args:
        query (str): Query INSERT base (sin VALUES)
        data (list): Lista de tuplas con datos a insertar

    Returns:
        bool: True si fue exitoso
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Para PostgreSQL, usar executemany con placeholder %s
        cursor.executemany(query, data)
        connection.commit()
        return True

    except Exception as e:
        logger.error(f"Error en INSERT: {str(e)}")
        if connection:
            connection.rollback()
        raise

    finally:
        if connection:
            connection.close()

def init_database():
    """
    Inicializar base de datos con tablas necesarias
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                apellido VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                rol VARCHAR(20) DEFAULT 'usuario' CHECK (rol IN ('admin', 'usuario')),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT TRUE
            )
        """)

        # Tabla de ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                fecha TIMESTAMP NOT NULL,
                producto VARCHAR(255) NOT NULL,
                cantidad DECIMAL(10, 2) NOT NULL,
                precio_unitario DECIMAL(10, 2) NOT NULL,
                total DECIMAL(10, 2) NOT NULL,
                usuario_id INTEGER REFERENCES usuarios(id),
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índice para mejorar búsquedas por fecha
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha DESC)
        """)

        # Tabla de productos (catálogo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                categoria VARCHAR(100),
                precio DECIMAL(10, 2),
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de gastos (contabilidad)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY,
                fecha TIMESTAMP NOT NULL,
                concepto VARCHAR(255) NOT NULL,
                categoria VARCHAR(100) NOT NULL,
                monto DECIMAL(10, 2) NOT NULL,
                comprobante VARCHAR(100),
                usuario_id INTEGER REFERENCES usuarios(id),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índice para mejorar búsquedas por fecha en gastos
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha DESC)
        """)

        connection.commit()
        logger.info("Base de datos PostgreSQL inicializada correctamente")

    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        if connection:
            connection.rollback()
        raise

    finally:
        if connection:
            connection.close()

def decimal_to_float(value):
    """Convertir Decimal a float para JSON"""
    if isinstance(value, Decimal):
        return float(value)
    return value
