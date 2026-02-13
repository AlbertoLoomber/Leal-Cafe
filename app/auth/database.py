"""
Funciones de base de datos para el módulo de autenticación
"""
import logging
from database import execute_query

logger = logging.getLogger(__name__)


def obtener_usuario_por_email(email):
    """
    Buscar usuario por email

    Args:
        email (str): Email del usuario

    Returns:
        dict: Datos del usuario o None si no existe
    """
    try:
        query = """
            SELECT id, nombre, apellido, email, password, rol, activo, fecha_creacion
            FROM usuarios
            WHERE email = %s
            LIMIT 1
        """

        results = execute_query(query, (email,))

        if results:
            return dict(results[0])

        return None

    except Exception as e:
        logger.error(f"Error obteniendo usuario por email: {str(e)}")
        raise


def obtener_usuario_por_id(user_id):
    """
    Buscar usuario por ID

    Args:
        user_id (int): ID del usuario

    Returns:
        dict: Datos del usuario o None si no existe
    """
    try:
        query = """
            SELECT id, nombre, apellido, email, rol, activo, fecha_creacion
            FROM usuarios
            WHERE id = %s
            LIMIT 1
        """

        results = execute_query(query, (user_id,))

        if results:
            return dict(results[0])

        return None

    except Exception as e:
        logger.error(f"Error obteniendo usuario por ID: {str(e)}")
        raise


def crear_usuario(nombre, apellido, email, password_hash, rol='usuario'):
    """
    Crear nuevo usuario

    Args:
        nombre (str): Nombre del usuario
        apellido (str): Apellido del usuario
        email (str): Email del usuario
        password_hash (str): Contraseña hasheada
        rol (str): Rol del usuario ('admin' o 'usuario')

    Returns:
        int: ID del usuario creado o None si falla
    """
    try:
        # En PostgreSQL con SERIAL, el ID se genera automáticamente
        query = """
            INSERT INTO usuarios (nombre, apellido, email, password, rol, activo)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        import psycopg2
        from database import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(query, (nombre, apellido, email, password_hash, rol, True))
        user_id = cursor.fetchone()['id']

        connection.commit()
        connection.close()

        logger.info(f"Usuario creado exitosamente: {email} (ID: {user_id})")
        return user_id

    except Exception as e:
        logger.error(f"Error creando usuario: {str(e)}")
        raise


def actualizar_usuario(user_id, datos):
    """
    Actualizar datos de un usuario

    Args:
        user_id (int): ID del usuario
        datos (dict): Diccionario con los campos a actualizar

    Returns:
        bool: True si fue exitoso
    """
    try:
        # Construir query dinámica según los campos a actualizar
        set_clauses = []
        params = []

        campos_permitidos = ['nombre', 'apellido', 'email', 'rol', 'activo']

        for campo, valor in datos.items():
            if campo in campos_permitidos:
                set_clauses.append(f"{campo} = %s")
                params.append(valor)

        if not set_clauses:
            logger.warning("No hay campos válidos para actualizar")
            return False

        params.append(user_id)

        query = f"""
            UPDATE usuarios
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """

        execute_query(query, tuple(params))
        logger.info(f"Usuario {user_id} actualizado exitosamente")
        return True

    except Exception as e:
        logger.error(f"Error actualizando usuario: {str(e)}")
        raise


def desactivar_usuario(user_id):
    """
    Desactivar usuario (soft delete)

    Args:
        user_id (int): ID del usuario

    Returns:
        bool: True si fue exitoso
    """
    return actualizar_usuario(user_id, {'activo': False})


def listar_usuarios(activos_solo=True):
    """
    Listar todos los usuarios

    Args:
        activos_solo (bool): Si True, solo retorna usuarios activos

    Returns:
        list: Lista de usuarios
    """
    try:
        query = """
            SELECT id, nombre, apellido, email, rol, activo, fecha_creacion
            FROM usuarios
        """

        if activos_solo:
            query += " WHERE activo = TRUE"

        query += " ORDER BY fecha_creacion DESC"

        results = execute_query(query)

        usuarios = [dict(row) for row in results]
        return usuarios

    except Exception as e:
        logger.error(f"Error listando usuarios: {str(e)}")
        raise
