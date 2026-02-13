"""
Funciones de base de datos para contabilidad - PostgreSQL
"""
import logging
from decimal import Decimal
from database import execute_query, get_db_connection, decimal_to_float

logger = logging.getLogger(__name__)


def obtener_gastos_mes(mes, anio, sucursal=None):
    """
    Obtener todos los gastos de un mes específico con cálculo de porcentaje

    Args:
        mes (int): Mes (1-12)
        anio (int): Año
        sucursal (str, optional): Filtrar por sucursal

    Returns:
        dict: {
            'gastos': [...],
            'total_mes': float,
            'total_facturado': float,
            'total_no_facturado': float
        }
    """
    try:
        # Query base
        query = """
            SELECT
                id,
                fecha,
                sucursal,
                tipo_gasto,
                categoria,
                descripcion,
                forma_pago,
                monto,
                facturado,
                comentarios,
                usuario_id,
                fecha_registro
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
        """

        params = [mes, anio]

        # Filtro opcional por sucursal
        if sucursal:
            query += " AND sucursal = %s"
            params.append(sucursal)

        query += " ORDER BY fecha DESC, id DESC"

        # Ejecutar query
        results = execute_query(query, tuple(params))
        gastos = [dict(row) for row in results]

        # Calcular total del mes
        total_mes = sum(decimal_to_float(g['monto']) for g in gastos)

        # Calcular porcentaje para cada gasto
        for gasto in gastos:
            gasto['monto'] = decimal_to_float(gasto['monto'])
            if total_mes > 0:
                gasto['porcentaje'] = round((gasto['monto'] / total_mes) * 100, 2)
            else:
                gasto['porcentaje'] = 0

        # Calcular totales
        total_facturado = sum(g['monto'] for g in gastos if g['facturado'])
        total_no_facturado = sum(g['monto'] for g in gastos if not g['facturado'])

        return {
            'gastos': gastos,
            'total_mes': round(total_mes, 2),
            'total_facturado': round(total_facturado, 2),
            'total_no_facturado': round(total_no_facturado, 2),
            'cantidad_gastos': len(gastos)
        }

    except Exception as e:
        logger.error(f"Error obteniendo gastos del mes {mes}/{anio}: {str(e)}")
        raise


def insertar_gasto(fecha, sucursal, tipo_gasto, categoria, descripcion,
                   forma_pago, monto, facturado, comentarios, usuario_id):
    """
    Insertar nuevo gasto

    Args:
        fecha (str): Fecha en formato 'YYYY-MM-DD'
        sucursal (str): Sucursal
        tipo_gasto (str): Variable o Fijo
        categoria (str): Categoría del gasto
        descripcion (str): Descripción
        forma_pago (str): Forma de pago
        monto (float): Monto
        facturado (bool): Si está facturado
        comentarios (str): Comentarios
        usuario_id (int): ID del usuario

    Returns:
        int: ID del gasto insertado
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO "LealSilver".gastos
            (fecha, sucursal, tipo_gasto, categoria, descripcion,
             forma_pago, monto, facturado, comentarios, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        cursor.execute(query, (
            fecha,
            sucursal,
            tipo_gasto,
            categoria,
            descripcion or '',
            forma_pago,
            Decimal(str(monto)),
            facturado,
            comentarios or '',
            usuario_id
        ))

        result = cursor.fetchone()
        # RealDictCursor retorna un diccionario, no una tupla
        gasto_id = result['id'] if isinstance(result, dict) else result[0]

        connection.commit()
        connection.close()

        facturado_texto = 'Sí' if facturado else 'No'
        logger.info(f"Gasto insertado con ID {gasto_id}: {descripcion} - ${monto} - Facturado: {facturado_texto}")
        return gasto_id

    except Exception as e:
        logger.error(f"Error insertando gasto: {str(e)}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            connection.close()
        raise


def actualizar_gasto(gasto_id, fecha, sucursal, tipo_gasto, categoria, descripcion,
                     forma_pago, monto, facturado, comentarios):
    """
    Actualizar un gasto existente

    Args:
        gasto_id (int): ID del gasto a actualizar
        ... (resto de campos igual que insertar_gasto)

    Returns:
        bool: True si se actualizó correctamente
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            UPDATE "LealSilver".gastos
            SET fecha = %s,
                sucursal = %s,
                tipo_gasto = %s,
                categoria = %s,
                descripcion = %s,
                forma_pago = %s,
                monto = %s,
                facturado = %s,
                comentarios = %s
            WHERE id = %s
        """

        cursor.execute(query, (
            fecha,
            sucursal,
            tipo_gasto,
            categoria,
            descripcion or '',
            forma_pago,
            Decimal(str(monto)),
            facturado,
            comentarios or '',
            gasto_id
        ))

        connection.commit()
        rows_affected = cursor.rowcount
        connection.close()

        logger.info(f"Gasto {gasto_id} actualizado exitosamente")
        return rows_affected > 0

    except Exception as e:
        logger.error(f"Error actualizando gasto {gasto_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            connection.close()
        raise


def eliminar_gasto(gasto_id):
    """
    Eliminar un gasto

    Args:
        gasto_id (int): ID del gasto a eliminar

    Returns:
        bool: True si se eliminó correctamente
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = 'DELETE FROM "LealSilver".gastos WHERE id = %s'
        cursor.execute(query, (gasto_id,))

        connection.commit()
        rows_affected = cursor.rowcount
        connection.close()

        logger.info(f"Gasto {gasto_id} eliminado exitosamente")
        return rows_affected > 0

    except Exception as e:
        logger.error(f"Error eliminando gasto {gasto_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        if connection:
            connection.rollback()
            connection.close()
        raise


def obtener_gasto_por_id(gasto_id):
    """
    Obtener un gasto específico por ID

    Args:
        gasto_id (int): ID del gasto

    Returns:
        dict: Datos del gasto
    """
    try:
        query = """
            SELECT
                id, fecha, sucursal, tipo_gasto, categoria, descripcion,
                forma_pago, monto, facturado, comentarios, usuario_id, fecha_registro
            FROM "LealSilver".gastos
            WHERE id = %s
        """

        results = execute_query(query, (gasto_id,))

        if results:
            gasto = dict(results[0])
            gasto['monto'] = decimal_to_float(gasto['monto'])
            return gasto

        return None

    except Exception as e:
        logger.error(f"Error obteniendo gasto {gasto_id}: {str(e)}")
        raise


def obtener_metricas_gastos(mes, anio):
    """
    Obtener métricas generales de gastos para un mes

    Args:
        mes (int): Mes (1-12)
        anio (int): Año

    Returns:
        dict: Métricas por sucursal, tipo, categoría
    """
    try:
        # Por sucursal
        query_sucursal = """
            SELECT
                sucursal,
                SUM(monto) as total,
                COUNT(*) as cantidad
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY sucursal
            ORDER BY total DESC
        """

        # Por tipo
        query_tipo = """
            SELECT
                tipo_gasto,
                SUM(monto) as total,
                COUNT(*) as cantidad
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY tipo_gasto
            ORDER BY total DESC
        """

        # Por categoría
        query_categoria = """
            SELECT
                categoria,
                SUM(monto) as total,
                COUNT(*) as cantidad
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY categoria
            ORDER BY total DESC
        """

        params = (mes, anio)

        por_sucursal = execute_query(query_sucursal, params)
        por_tipo = execute_query(query_tipo, params)
        por_categoria = execute_query(query_categoria, params)

        return {
            'por_sucursal': [dict(row) for row in por_sucursal],
            'por_tipo': [dict(row) for row in por_tipo],
            'por_categoria': [dict(row) for row in por_categoria]
        }

    except Exception as e:
        logger.error(f"Error obteniendo métricas de gastos: {str(e)}")
        raise


def obtener_estado_resultados(mes, anio):
    """
    Obtener datos completos para Estado de Resultados

    Args:
        mes (int): Mes (1-12)
        anio (int): Año

    Returns:
        dict: {
            'ingresos': float,
            'costo_ventas': float,
            'utilidad_bruta': float,
            'gastos_fijos': {
                'total': float,
                'desglose': [{categoria, monto}, ...]
            },
            'gastos_variables': {
                'total': float,
                'desglose': [{categoria, monto}, ...]
            },
            'utilidad_neta': float,
            'margen_neto': float (porcentaje)
        }
    """
    try:
        # 1. Obtener solo ingresos (ventas totales) desde la vista
        query_ventas = """
            SELECT COALESCE(SUM(venta), 0) as ingresos
            FROM "LealSilver".vw_ventas_diarias_por_platillo
            WHERE anio = %s AND mes = %s
        """

        result_ventas = execute_query(query_ventas, (anio, mes))
        if result_ventas:
            ingresos = float(decimal_to_float(result_ventas[0]['ingresos']))
        else:
            ingresos = 0.0

        # 2. Obtener solo INSUMOS como Costo de Venta
        query_costo_venta = """
            SELECT SUM(monto) as monto
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            AND tipo_gasto = 'Variable'
            AND UPPER(categoria) = 'INSUMOS'
        """

        costo_venta_result = execute_query(query_costo_venta, (mes, anio))
        costo_ventas = float(decimal_to_float(costo_venta_result[0]['monto'])) if costo_venta_result and costo_venta_result[0]['monto'] else 0.0

        # 3. Calcular utilidad bruta
        utilidad_bruta = ingresos - costo_ventas

        # 4. Obtener otros gastos variables (NO insumos)
        query_gastos_variables = """
            SELECT
                categoria,
                SUM(monto) as monto
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            AND tipo_gasto = 'Variable'
            AND UPPER(categoria) != 'INSUMOS'
            GROUP BY categoria
            ORDER BY monto DESC
        """

        gastos_variables_result = execute_query(query_gastos_variables, (mes, anio))
        gastos_variables_desglose = [
            {'categoria': row['categoria'], 'monto': decimal_to_float(row['monto'])}
            for row in gastos_variables_result
        ]
        total_gastos_variables = sum(item['monto'] for item in gastos_variables_desglose)

        # 6. Obtener gastos fijos agrupados por categoría
        query_gastos_fijos = """
            SELECT
                categoria,
                SUM(monto) as monto
            FROM "LealSilver".gastos
            WHERE EXTRACT(MONTH FROM fecha) = %s
            AND EXTRACT(YEAR FROM fecha) = %s
            AND tipo_gasto = 'Fijo'
            GROUP BY categoria
            ORDER BY monto DESC
        """

        gastos_fijos_result = execute_query(query_gastos_fijos, (mes, anio))
        gastos_fijos_desglose = [
            {'categoria': row['categoria'], 'monto': decimal_to_float(row['monto'])}
            for row in gastos_fijos_result
        ]
        total_gastos_fijos = sum(item['monto'] for item in gastos_fijos_desglose)

        # 7. Calcular utilidad neta
        utilidad_neta = utilidad_bruta - total_gastos_fijos - total_gastos_variables

        # 8. Calcular margen neto (%)
        margen_neto = (utilidad_neta / ingresos * 100) if ingresos > 0 else 0

        return {
            'ingresos': round(ingresos, 2),
            'costo_ventas': round(costo_ventas, 2),
            'utilidad_bruta': round(utilidad_bruta, 2),
            'gastos_fijos': {
                'total': round(total_gastos_fijos, 2),
                'desglose': gastos_fijos_desglose
            },
            'gastos_variables': {
                'total': round(total_gastos_variables, 2),
                'desglose': gastos_variables_desglose
            },
            'utilidad_neta': round(utilidad_neta, 2),
            'margen_neto': round(margen_neto, 2),
            'margen_bruto': round((utilidad_bruta / ingresos * 100) if ingresos > 0 else 0, 2)
        }

    except Exception as e:
        logger.error(f"Error obteniendo estado de resultados {mes}/{anio}: {str(e)}")
        raise
