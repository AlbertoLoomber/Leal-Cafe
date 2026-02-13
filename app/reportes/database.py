"""
Funciones de base de datos para reportes - PostgreSQL
"""
import logging
from database import execute_query, decimal_to_float

logger = logging.getLogger(__name__)


def obtener_reporte_ventas_mes(mes=None, anio=None):
    """Obtener reporte de ventas agrupado por día"""
    try:
        query = """
            SELECT
                DATE(fecha) as dia,
                COUNT(*) as transacciones,
                SUM(cantidad) as productos_vendidos,
                SUM(total) as total_ventas
            FROM ventas
        """

        conditions = []
        params = []

        if mes and anio:
            conditions.append("EXTRACT(MONTH FROM fecha) = %s")
            conditions.append("EXTRACT(YEAR FROM fecha) = %s")
            params.extend([int(mes), int(anio)])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY DATE(fecha) ORDER BY dia DESC"

        results = execute_query(query, tuple(params) if params else None)

        return [dict(row) for row in results]

    except Exception as e:
        logger.error(f"Error obteniendo reporte ventas mes: {str(e)}")
        raise


def obtener_productos_mas_vendidos(limit=20):
    """Obtener productos más vendidos"""
    try:
        query = """
            SELECT
                producto,
                SUM(cantidad) as total_cantidad,
                SUM(total) as total_ventas,
                COUNT(*) as num_transacciones,
                AVG(precio_unitario) as precio_promedio
            FROM ventas
            GROUP BY producto
            ORDER BY total_ventas DESC
            LIMIT %s
        """

        results = execute_query(query, (limit,))
        return [dict(row) for row in results]

    except Exception as e:
        logger.error(f"Error obteniendo productos más vendidos: {str(e)}")
        raise


def obtener_catalogo_recetas():
    """Obtener catálogo de recetas con costo total calculado"""
    try:
        query = """
            SELECT
                r.codigo_platillo,
                r.platillo,
                COUNT(*) AS num_ingredientes,
                ROUND(SUM(r.cantidad * COALESCE(cp.costo_presupuestado, 0)), 2) AS costo_total
            FROM "LealSilver".recetas r
            LEFT JOIN "LealSilver".costo_producto cp ON r.producto = cp.nombre
            GROUP BY r.codigo_platillo, r.platillo
            ORDER BY costo_total DESC
        """

        results = execute_query(query)
        return [decimal_to_float(dict(row)) for row in results]

    except Exception as e:
        logger.error(f"Error obteniendo catálogo de recetas: {str(e)}")
        raise


def obtener_componentes_receta(codigo_platillo):
    """Obtener componentes/ingredientes de una receta específica con sus costos"""
    try:
        query = """
            SELECT
                r.producto,
                r.cantidad,
                r.unidad_medida,
                COALESCE(cp.costo_presupuestado, 0) as costo_unitario,
                COALESCE(cp.departamento, 'Sin clasificar') as departamento,
                ROUND(r.cantidad * COALESCE(cp.costo_presupuestado, 0), 4) as costo_ingrediente
            FROM "LealSilver".recetas r
            LEFT JOIN "LealSilver".costo_producto cp ON r.producto = cp.nombre
            WHERE r.codigo_platillo = %s
            ORDER BY
                CASE WHEN cp.costo_presupuestado IS NULL THEN 1 ELSE 0 END,
                costo_ingrediente DESC
        """

        results = execute_query(query, (codigo_platillo,))
        return [decimal_to_float(dict(row)) for row in results]

    except Exception as e:
        logger.error(f"Error obteniendo componentes de receta {codigo_platillo}: {str(e)}")
        raise


def obtener_metricas_dashboard(anio=2026, mes=1, sucursal=None):
    """
    Obtener métricas financieras del negocio desde la vista vw_ventas_diarias_por_platillo

    Args:
        anio: Año a filtrar (default: 2026)
        mes: Mes a filtrar (default: 1 = Enero)
        sucursal: Sucursal específica (opcional, default: todas)

    Returns:
        dict: Métricas generales, por sucursal y por producto
    """
    try:
        # Construir filtro de sucursal si aplica
        filtro_sucursal = ""
        params_general = (anio, mes)
        if sucursal:
            filtro_sucursal = "AND sucursal = %s"
            params_general = (anio, mes, sucursal)

        # 1. MÉTRICAS GENERALES (todas las sucursales o una específica)
        query_general = f"""
            SELECT
                SUM(venta) as ventas_totales,
                SUM(costo_venta) as costo_venta_total,
                SUM(ingreso_real) as ingreso_real,
                ROUND(SUM(costo_venta) / NULLIF(SUM(venta), 0) * 100, 2) as porcentaje_costo,
                ROUND(SUM(ingreso_real) / NULLIF(SUM(venta), 0) * 100, 2) as porcentaje_ingreso,
                ROUND(SUM(ingreso_real) / NULLIF(SUM(costo_venta), 0) * 100, 2) as roi
            FROM "LealSilver".vw_ventas_diarias_por_platillo
            WHERE anio = %s AND mes = %s {filtro_sucursal}
        """

        result_general = execute_query(query_general, params_general)
        general = decimal_to_float(dict(result_general[0])) if result_general else {
            'ventas_totales': 0,
            'costo_venta_total': 0,
            'ingreso_real': 0,
            'porcentaje_costo': 0,
            'porcentaje_ingreso': 0,
            'roi': 0
        }

        # 2. DESGLOSE POR SUCURSAL
        query_sucursal = """
            SELECT
                sucursal,
                SUM(venta) as ventas_totales,
                SUM(costo_venta) as costo_venta_total,
                SUM(ingreso_real) as ingreso_real,
                ROUND(SUM(costo_venta) / NULLIF(SUM(venta), 0) * 100, 2) as porcentaje_costo,
                ROUND(SUM(ingreso_real) / NULLIF(SUM(venta), 0) * 100, 2) as porcentaje_ingreso,
                ROUND(SUM(ingreso_real) / NULLIF(SUM(costo_venta), 0) * 100, 2) as roi
            FROM "LealSilver".vw_ventas_diarias_por_platillo
            WHERE anio = %s AND mes = %s
            GROUP BY sucursal
            ORDER BY ventas_totales DESC
        """

        results_sucursal = execute_query(query_sucursal, (anio, mes))
        sucursales = [decimal_to_float(dict(row)) for row in results_sucursal]

        # Asegurar que todas las sucursales esperadas estén presentes
        sucursales_esperadas = ['Centro', 'LM', 'Auditorio', 'Ahumada']
        sucursales_dict = {s['sucursal']: s for s in sucursales}

        sucursales_completas = []
        for suc_nombre in sucursales_esperadas:
            if suc_nombre in sucursales_dict:
                sucursales_completas.append(sucursales_dict[suc_nombre])
            else:
                sucursales_completas.append({
                    'sucursal': suc_nombre,
                    'ventas_totales': 0,
                    'costo_venta_total': 0,
                    'ingreso_real': 0,
                    'porcentaje_costo': 0,
                    'porcentaje_ingreso': 0,
                    'roi': 0
                })

        # Ordenar por ventas_totales de mayor a menor
        sucursales_completas.sort(key=lambda x: x['ventas_totales'], reverse=True)

        # 3. DESGLOSE POR PRODUCTO (top 20)
        params_producto = (anio, mes)
        filtro_sucursal_producto = filtro_sucursal if sucursal else ""
        if sucursal:
            params_producto = (anio, mes, sucursal)

        query_producto = f"""
            SELECT
                clave_platillo,
                nombre_platillo,
                grupo,
                SUM(cantidad) as cantidad_total,
                SUM(venta) as ventas_totales,
                SUM(costo_venta) as costo_venta_total,
                SUM(ingreso_real) as ingreso_real,
                ROUND(SUM(costo_venta) / NULLIF(SUM(venta), 0) * 100, 2) as porcentaje_costo,
                ROUND(SUM(ingreso_real) / NULLIF(SUM(venta), 0) * 100, 2) as porcentaje_ingreso,
                ROUND(SUM(ingreso_real) / NULLIF(SUM(costo_venta), 0) * 100, 2) as roi
            FROM "LealSilver".vw_ventas_diarias_por_platillo
            WHERE anio = %s AND mes = %s {filtro_sucursal_producto}
            GROUP BY clave_platillo, nombre_platillo, grupo
            ORDER BY ventas_totales DESC
            LIMIT 20
        """

        results_producto = execute_query(query_producto, params_producto)
        productos = [decimal_to_float(dict(row)) for row in results_producto]

        return {
            'general': general,
            'sucursales': sucursales_completas,
            'productos': productos
        }

    except Exception as e:
        logger.error(f"Error obteniendo métricas dashboard: {str(e)}")
        # Retornar datos vacíos en caso de error
        return {
            'general': {
                'ventas_totales': 0,
                'costo_venta_total': 0,
                'ingreso_real': 0,
                'porcentaje_costo': 0,
                'porcentaje_ingreso': 0,
                'roi': 0
            },
            'sucursales': [
                {'sucursal': 'Centro', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0},
                {'sucursal': 'LM', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0},
                {'sucursal': 'Auditorio', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0},
                {'sucursal': 'Ahumada', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0}
            ],
            'productos': []
        }
