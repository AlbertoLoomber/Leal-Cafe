from flask import render_template, request, jsonify
import logging

from . import reportes_bp
from auth import login_required
from .database import (
    obtener_reporte_ventas_mes,
    obtener_productos_mas_vendidos,
    obtener_catalogo_recetas,
    obtener_componentes_receta,
    obtener_metricas_dashboard
)

logger = logging.getLogger(__name__)


@reportes_bp.route('/')
@login_required
def index():
    """Dashboard de reportes de ventas con filtros"""
    try:
        # Obtener parámetros de filtro (con valores por defecto)
        anio = request.args.get('anio', 2026, type=int)
        mes = request.args.get('mes', 1, type=int)
        sucursal = request.args.get('sucursal', None)

        # Obtener métricas con filtros
        metricas = obtener_metricas_dashboard(anio=anio, mes=mes, sucursal=sucursal)

        return render_template('reportes/index.html',
                             general=metricas['general'],
                             sucursales=metricas['sucursales'],
                             productos=metricas['productos'],
                             anio_seleccionado=anio,
                             mes_seleccionado=mes,
                             sucursal_seleccionada=sucursal)
    except Exception as e:
        logger.error(f"Error obteniendo métricas dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        # Retornar template con datos vacíos en caso de error
        return render_template('reportes/index.html',
                             general={
                                 'ventas_totales': 0,
                                 'costo_venta_total': 0,
                                 'ingreso_real': 0,
                                 'porcentaje_costo': 0,
                                 'porcentaje_ingreso': 0,
                                 'roi': 0
                             },
                             sucursales=[
                                 {'sucursal': 'Centro', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0},
                                 {'sucursal': 'LM', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0},
                                 {'sucursal': 'Auditorio', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0},
                                 {'sucursal': 'Ahumada', 'ventas_totales': 0, 'costo_venta_total': 0, 'ingreso_real': 0, 'porcentaje_costo': 0, 'porcentaje_ingreso': 0, 'roi': 0}
                             ],
                             productos=[],
                             anio_seleccionado=2026,
                             mes_seleccionado=1,
                             sucursal_seleccionada=None,
                             error=str(e))


@reportes_bp.route('/productos')
@login_required
def productos():
    """Reporte de productos más vendidos"""
    try:
        productos = obtener_productos_mas_vendidos(limit=50)
        return render_template('reportes/productos.html', productos=productos)

    except Exception as e:
        logger.error(f"Error en reportes productos: {str(e)}")
        return render_template('reportes/productos.html', productos=[])


@reportes_bp.route('/api/ventas-mes')
@login_required
def api_ventas_mes():
    """API para obtener ventas por mes"""
    try:
        mes = request.args.get('mes')
        anio = request.args.get('anio')

        datos = obtener_reporte_ventas_mes(mes, anio)

        return jsonify({
            'success': True,
            'data': datos
        })

    except Exception as e:
        logger.error(f"Error en API ventas mes: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reportes_bp.route('/catalogo-recetas')
@login_required
def catalogo_recetas():
    """Catálogo de recetas con costos"""
    try:
        recetas = obtener_catalogo_recetas()
        return render_template('reportes/catalogo_recetas.html', recetas=recetas)

    except Exception as e:
        logger.error(f"Error en catálogo de recetas: {str(e)}")
        return render_template('reportes/catalogo_recetas.html', recetas=[], error=str(e))


@reportes_bp.route('/api/componentes-receta/<codigo_platillo>')
@login_required
def api_componentes_receta(codigo_platillo):
    """API para obtener componentes de una receta"""
    try:
        componentes = obtener_componentes_receta(codigo_platillo)

        # Calcular costo total
        costo_total = sum(c.get('costo_ingrediente', 0) or 0 for c in componentes)

        return jsonify({
            'success': True,
            'componentes': componentes,
            'costo_total': round(costo_total, 2)
        })

    except Exception as e:
        logger.error(f"Error obteniendo componentes de {codigo_platillo}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
