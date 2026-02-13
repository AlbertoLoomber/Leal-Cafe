"""
Funciones de base de datos para gestión de metas - PostgreSQL
"""
import logging
from decimal import Decimal
from database import execute_query, get_db_connection, decimal_to_float

logger = logging.getLogger(__name__)


def obtener_metas_mes(mes, anio, sucursal=None):
    """
    Obtener metas de un mes específico con el cumplimiento actual

    Args:
        mes (int): Mes (1-12)
        anio (int): Año
        sucursal (str, optional): Filtrar por sucursal

    Returns:
        list: Lista de metas con información de cumplimiento
    """
    try:
        query = """
            WITH ventas_periodo AS (
                SELECT
                    sucursal,
                    COALESCE(SUM(total), 0) as ventas_reales
                FROM "LealSilver".ventas
                WHERE EXTRACT(MONTH FROM fecha) = %s
                AND EXTRACT(YEAR FROM fecha) = %s
                GROUP BY sucursal
            )
            SELECT
                m.id,
                m.sucursal,
                m.mes,
                m.anio,
                m.meta_monto,
                m.tipo_meta,
                m.activa,
                m.comentarios,
                m.usuario_id,
                m.fecha_creacion,
                m.fecha_modificacion,
                COALESCE(v.ventas_reales, 0) as ventas_reales,
                CASE
                    WHEN m.meta_monto > 0 THEN
                        ROUND((COALESCE(v.ventas_reales, 0) / m.meta_monto * 100)::numeric, 2)
                    ELSE 0
                END as porcentaje_cumplimiento,
                (COALESCE(v.ventas_reales, 0) - m.meta_monto) as diferencia
            FROM "LealSilver".metas_mensuales m
            LEFT JOIN ventas_periodo v ON m.sucursal = v.sucursal
            WHERE m.mes = %s
            AND m.anio = %s
            AND m.activa = TRUE
        """

        params = [mes, anio, mes, anio]

        if sucursal:
            query += " AND m.sucursal = %s"
            params.append(sucursal)

        query += " ORDER BY m.sucursal"

        results = execute_query(query, tuple(params))

        metas = []
        for row in results:
            meta = dict(row)
            meta['meta_monto'] = decimal_to_float(meta['meta_monto'])
            meta['ventas_reales'] = decimal_to_float(meta['ventas_reales'])
            meta['porcentaje_cumplimiento'] = decimal_to_float(meta['porcentaje_cumplimiento'])
            meta['diferencia'] = decimal_to_float(meta['diferencia'])

            # Determinar estado según cumplimiento
            cumplimiento = meta['porcentaje_cumplimiento']
            if cumplimiento >= 100:
                meta['estado'] = 'cumplido'
                meta['estado_texto'] = 'Cumplido'
                meta['color_estado'] = '#28a745'  # Verde
            elif cumplimiento >= 50:
                meta['estado'] = 'en_progreso'
                meta['estado_texto'] = 'En Progreso'
                meta['color_estado'] = '#ffc107'  # Amarillo
            else:
                meta['estado'] = 'requiere_accion'
                meta['estado_texto'] = 'Requiere Acción'
                meta['color_estado'] = '#dc3545'  # Rojo

            metas.append(meta)

        return metas

    except Exception as e:
        logger.error(f"Error obteniendo metas del mes {mes}/{anio}: {str(e)}")
        raise


def insertar_meta(sucursal, mes, anio, meta_monto, tipo_meta, comentarios, usuario_id):
    """
    Insertar nueva meta

    Args:
        sucursal (str): Sucursal
        mes (int): Mes (1-12)
        anio (int): Año
        meta_monto (float): Monto objetivo
        tipo_meta (str): Tipo de meta
        comentarios (str): Comentarios
        usuario_id (int): ID del usuario

    Returns:
        int: ID de la meta insertada
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO "LealSilver".metas_mensuales
            (sucursal, mes, anio, meta_monto, tipo_meta, comentarios, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        cursor.execute(query, (
            sucursal,
            mes,
            anio,
            Decimal(str(meta_monto)),
            tipo_meta,
            comentarios or '',
            usuario_id
        ))

        result = cursor.fetchone()
        meta_id = result['id'] if isinstance(result, dict) else result[0]

        connection.commit()
        connection.close()

        logger.info(f"Meta insertada con ID {meta_id}: {sucursal} - {mes}/{anio} - ${meta_monto}")
        return meta_id

    except Exception as e:
        logger.error(f"Error insertando meta: {str(e)}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            connection.close()
        raise


def actualizar_meta(meta_id, sucursal, mes, anio, meta_monto, tipo_meta, comentarios):
    """
    Actualizar una meta existente

    Args:
        meta_id (int): ID de la meta
        sucursal (str): Sucursal
        mes (int): Mes
        anio (int): Año
        meta_monto (float): Monto objetivo
        tipo_meta (str): Tipo de meta
        comentarios (str): Comentarios

    Returns:
        bool: True si se actualizó correctamente
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            UPDATE "LealSilver".metas_mensuales
            SET sucursal = %s,
                mes = %s,
                anio = %s,
                meta_monto = %s,
                tipo_meta = %s,
                comentarios = %s
            WHERE id = %s
        """

        cursor.execute(query, (
            sucursal,
            mes,
            anio,
            Decimal(str(meta_monto)),
            tipo_meta,
            comentarios or '',
            meta_id
        ))

        connection.commit()
        rows_affected = cursor.rowcount
        connection.close()

        logger.info(f"Meta {meta_id} actualizada exitosamente")
        return rows_affected > 0

    except Exception as e:
        logger.error(f"Error actualizando meta {meta_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            connection.close()
        raise


def eliminar_meta(meta_id):
    """
    Desactivar una meta (soft delete)

    Args:
        meta_id (int): ID de la meta

    Returns:
        bool: True si se desactivó correctamente
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = 'UPDATE "LealSilver".metas_mensuales SET activa = FALSE WHERE id = %s'
        cursor.execute(query, (meta_id,))

        connection.commit()
        rows_affected = cursor.rowcount
        connection.close()

        logger.info(f"Meta {meta_id} desactivada exitosamente")
        return rows_affected > 0

    except Exception as e:
        logger.error(f"Error desactivando meta {meta_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            connection.close()
        raise


def obtener_meta_por_id(meta_id):
    """
    Obtener una meta específica por ID

    Args:
        meta_id (int): ID de la meta

    Returns:
        dict: Datos de la meta
    """
    try:
        query = """
            SELECT
                id, sucursal, mes, anio, meta_monto, tipo_meta,
                activa, comentarios, usuario_id, fecha_creacion, fecha_modificacion
            FROM "LealSilver".metas_mensuales
            WHERE id = %s
        """

        results = execute_query(query, (meta_id,))

        if results:
            meta = dict(results[0])
            meta['meta_monto'] = decimal_to_float(meta['meta_monto'])
            return meta

        return None

    except Exception as e:
        logger.error(f"Error obteniendo meta {meta_id}: {str(e)}")
        raise


def obtener_resumen_metas_anual(anio, sucursal=None):
    """
    Obtener resumen de metas anuales

    Args:
        anio (int): Año
        sucursal (str, optional): Filtrar por sucursal

    Returns:
        dict: Resumen anual de metas
    """
    try:
        query = """
            WITH ventas_anuales AS (
                SELECT
                    sucursal,
                    EXTRACT(MONTH FROM fecha) as mes,
                    COALESCE(SUM(total), 0) as ventas_mes
                FROM "LealSilver".ventas
                WHERE EXTRACT(YEAR FROM fecha) = %s
                GROUP BY sucursal, EXTRACT(MONTH FROM fecha)
            ),
            metas_con_ventas AS (
                SELECT
                    m.sucursal,
                    m.mes,
                    m.meta_monto,
                    COALESCE(v.ventas_mes, 0) as ventas_reales,
                    CASE
                        WHEN m.meta_monto > 0 THEN
                            (COALESCE(v.ventas_mes, 0) / m.meta_monto * 100)
                        ELSE 0
                    END as cumplimiento
                FROM "LealSilver".metas_mensuales m
                LEFT JOIN ventas_anuales v ON m.sucursal = v.sucursal AND m.mes = v.mes
                WHERE m.anio = %s
                AND m.activa = TRUE
        """

        params = [anio, anio]

        if sucursal:
            query += " AND m.sucursal = %s"
            params.append(sucursal)

        query += """
            )
            SELECT
                sucursal,
                COUNT(*) as meses_con_meta,
                SUM(meta_monto) as meta_total,
                SUM(ventas_reales) as ventas_totales,
                ROUND(AVG(cumplimiento), 2) as cumplimiento_promedio,
                SUM(CASE WHEN cumplimiento >= 100 THEN 1 ELSE 0 END) as meses_cumplidos
            FROM metas_con_ventas
            GROUP BY sucursal
            ORDER BY sucursal
        """

        results = execute_query(query, tuple(params))

        resumen = {}
        for row in results:
            data = dict(row)
            resumen[data['sucursal']] = {
                'meses_con_meta': data['meses_con_meta'],
                'meta_total': decimal_to_float(data['meta_total']),
                'ventas_totales': decimal_to_float(data['ventas_totales']),
                'cumplimiento_promedio': decimal_to_float(data['cumplimiento_promedio']),
                'meses_cumplidos': data['meses_cumplidos']
            }

        return resumen

    except Exception as e:
        logger.error(f"Error obteniendo resumen anual {anio}: {str(e)}")
        raise
