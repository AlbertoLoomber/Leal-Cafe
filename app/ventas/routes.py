from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime

from . import ventas_bp
from auth import login_required
from .database import obtener_ventas, insertar_ventas, procesar_excel_ventas, insertar_ventas_leal_silver
from .excel_processor import ResumenVentasProcessor
from config import Config

logger = logging.getLogger(__name__)

# Configuración de uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

# Crear carpeta de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Valida que el archivo tenga una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@ventas_bp.route('/')
@login_required
def index():
    """Página principal de gestión de ventas"""
    try:
        # Obtener ventas recientes (últimas 100)
        ventas = obtener_ventas(limit=100)

        return render_template('ventas/index.html', ventas=ventas)

    except Exception as e:
        logger.error(f"Error en ventas index: {str(e)}")
        flash('Error al cargar las ventas', 'danger')
        return render_template('ventas/index.html', ventas=[])


@ventas_bp.route('/cargar', methods=['GET'])
@login_required
def cargar():
    """Página de carga de ventas desde archivo Excel"""
    return render_template('ventas/cargar.html')


@ventas_bp.route('/upload-preview', methods=['POST'])
@login_required
def upload_preview():
    """
    Endpoint para subir archivo Excel y mostrar preview de datos
    NO guarda en la base de datos, solo muestra lo que se extrajo
    Soporta dos modos: diario (día específico) y mensual (divide entre días del mes)
    """
    # Obtener modo de carga
    modo_carga = request.form.get('modo_carga', 'diario')

    # Validar metadatos requeridos
    sucursal = request.form.get('sucursal')
    anio = request.form.get('anio')
    mes = request.form.get('mes')
    dia = request.form.get('dia')  # Solo requerido en modo diario

    # Validación según modo
    if not sucursal or not anio or not mes:
        return jsonify({
            'success': False,
            'error': 'Faltan datos requeridos: sucursal, año y mes son obligatorios'
        }), 400

    if modo_carga == 'diario' and not dia:
        return jsonify({
            'success': False,
            'error': 'En modo diario, el día es obligatorio'
        }), 400

    # Validar que se envió un archivo
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se envió ningún archivo'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Formato de archivo no permitido. Solo .xlsx o .xls'}), 400

    filepath = None
    try:
        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        logger.info(f"Archivo guardado temporalmente en: {filepath}")

        # Log de metadatos según modo
        if modo_carga == 'diario':
            logger.info(f"Metadatos: Sucursal={sucursal}, Año={anio}, Mes={mes}, Día={dia}, Modo={modo_carga}")
        else:
            logger.info(f"Metadatos: Sucursal={sucursal}, Año={anio}, Mes={mes}, Modo={modo_carga}")

        # Procesar archivo con el procesador
        processor = ResumenVentasProcessor(filepath)
        data = processor.process_all()

        logger.info(f"Archivo procesado. Success: {data.get('success')}")

        # Eliminar archivo temporal
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info("Archivo temporal eliminado")

        if not data['success']:
            logger.error(f"Errores en procesamiento: {data.get('errors', [])}")
            return jsonify({
                'success': False,
                'error': 'Error procesando el archivo',
                'details': data.get('errors', [])
            }), 400

        # Calcular resumen de registros
        resumen = {
            'ventas_por_hora': len(data['ventas_por_hora']),
            'ventas_por_platillo': len(data['ventas_por_platillo']),
            'ventas_por_grupo': len(data['ventas_por_grupo']),
            'ventas_por_tipo_grupo': len(data['ventas_por_tipo_grupo']),
            'ventas_por_tipo_pago': len(data['ventas_por_tipo_pago']),
            'ventas_por_usuario': len(data['ventas_por_usuario']),
            'ventas_por_cajero': len(data['ventas_por_cajero']),
            'ventas_por_modificador': len(data['ventas_por_modificador'])
        }

        # Agregar metadatos de identificación al metadata
        metadata_completo = data['metadata'].copy()
        metadata_completo['modo_carga'] = modo_carga
        metadata_completo['sucursal'] = sucursal
        metadata_completo['anio'] = int(anio)
        metadata_completo['mes'] = int(mes)

        if modo_carga == 'diario':
            metadata_completo['dia'] = int(dia)
        else:
            # En modo mensual, calcular días del mes
            import calendar
            dias_en_mes = calendar.monthrange(int(anio), int(mes))[1]
            metadata_completo['dias_en_mes'] = dias_en_mes

        # Preparar respuesta con datos completos y preview
        response_data = {
            'success': True,
            'message': 'Archivo procesado correctamente',
            'metadata': metadata_completo,
            'resumen': resumen,
            'preview_data': {
                'ventas_por_hora': data['ventas_por_hora'][:5],  # Primeros 5
                'ventas_por_platillo': data['ventas_por_platillo'][:10],  # Primeros 10
                'ventas_por_grupo': data['ventas_por_grupo'][:5],
                'ventas_por_tipo_grupo': data['ventas_por_tipo_grupo'],  # Todos (son pocos)
                'ventas_por_tipo_pago': data['ventas_por_tipo_pago'],  # Todos (son pocos)
                'ventas_por_usuario': data['ventas_por_usuario'],  # Todos
                'ventas_por_cajero': data['ventas_por_cajero'],  # Todos
                'ventas_por_modificador': data['ventas_por_modificador'][:10]  # Primeros 10
            },
            'warnings': data.get('errors', []),
            # Incluir datos completos para el guardado posterior
            'ventas_por_hora': data['ventas_por_hora'],
            'ventas_por_platillo': data['ventas_por_platillo'],
            'ventas_por_grupo': data['ventas_por_grupo'],
            'ventas_por_tipo_grupo': data['ventas_por_tipo_grupo'],
            'ventas_por_tipo_pago': data['ventas_por_tipo_pago'],
            'ventas_por_usuario': data['ventas_por_usuario'],
            'ventas_por_cajero': data['ventas_por_cajero'],
            'ventas_por_modificador': data['ventas_por_modificador']
        }

        return jsonify(response_data), 200

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error procesando archivo: {str(e)}")
        logger.error(f"Traceback completo:\n{error_details}")

        # Limpiar archivo si existe
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info("Archivo temporal eliminado después de error")
            except Exception as cleanup_error:
                logger.error(f"Error limpiando archivo temporal: {str(cleanup_error)}")

        return jsonify({
            'success': False,
            'error': f'Error al procesar el archivo: {str(e)}',
            'details': error_details if logger.level == logging.DEBUG else None
        }), 500


@ventas_bp.route('/confirmar-guardado', methods=['POST'])
@login_required
def confirmar_guardado():
    """
    Endpoint para confirmar y guardar datos en la base de datos
    Recibe los datos procesados y los metadatos, y los inserta en las 8 tablas
    """
    try:
        # Obtener datos del request
        request_data = request.get_json()

        if not request_data:
            return jsonify({
                'success': False,
                'error': 'No se recibieron datos'
            }), 400

        # Validar estructura de datos
        required_keys = ['metadata', 'ventas_por_hora', 'ventas_por_platillo',
                        'ventas_por_grupo', 'ventas_por_tipo_grupo', 'ventas_por_tipo_pago',
                        'ventas_por_usuario', 'ventas_por_cajero', 'ventas_por_modificador']

        for key in required_keys:
            if key not in request_data:
                return jsonify({
                    'success': False,
                    'error': f'Falta el campo requerido: {key}'
                }), 400

        # Extraer metadatos
        metadata = request_data['metadata']
        modo_carga = metadata.get('modo_carga', 'diario')
        sucursal = metadata.get('sucursal')
        anio = metadata.get('anio')
        mes = metadata.get('mes')
        dia = metadata.get('dia')
        dias_en_mes = metadata.get('dias_en_mes')

        if not sucursal or not anio or not mes:
            return jsonify({
                'success': False,
                'error': 'Faltan metadatos: sucursal, año y mes son obligatorios'
            }), 400

        if modo_carga == 'diario' and not dia:
            return jsonify({
                'success': False,
                'error': 'En modo diario, el día es obligatorio'
            }), 400

        # Obtener usuario actual de la sesión
        created_by = f"{session['user']['nombre']} {session['user']['apellido']}"

        # ========================================================================
        # VALIDACIÓN DE DUPLICADOS
        # ========================================================================
        from .database import verificar_existe_dia, verificar_existe_mes

        if modo_carga == 'diario':
            # Validar que no exista ese día específico
            if verificar_existe_dia(sucursal, int(anio), int(mes), int(dia)):
                # Crear nombre del mes en español
                meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                nombre_mes = meses[int(mes)]

                return jsonify({
                    'success': False,
                    'error': f'Ya existen datos para {sucursal} en {dia} de {nombre_mes} {anio}. No se puede volver a cargar el mismo día.'
                }), 400

        else:  # modo_carga == 'mensual'
            # Validar que no exista ningún día de ese mes
            if verificar_existe_mes(sucursal, int(anio), int(mes)):
                # Crear nombre del mes en español
                meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                nombre_mes = meses[int(mes)]

                return jsonify({
                    'success': False,
                    'error': f'Ya existen datos para algunos días de {nombre_mes} {anio} en {sucursal}. No se puede cargar el mes completo.'
                }), 400

        # ========================================================================
        # INSERTAR DATOS
        # ========================================================================

        if modo_carga == 'diario':
            logger.info(f"Iniciando guardado DIARIO: Sucursal={sucursal}, Fecha={anio}-{mes}-{dia}, Usuario={created_by}")

            # Insertar datos en la base de datos (modo diario)
            resumen = insertar_ventas_leal_silver(
                data=request_data,
                sucursal=sucursal,
                anio=int(anio),
                mes=int(mes),
                dia=int(dia),
                created_by=created_by
            )
        else:  # modo_carga == 'mensual'
            logger.info(f"Iniciando guardado MENSUAL: Sucursal={sucursal}, Año-Mes={anio}-{mes}, Días={dias_en_mes}, Usuario={created_by}")

            # Importar función para dividir ventas mensuales
            from .database import insertar_ventas_mensual_dividido

            # Insertar datos divididos por cada día del mes
            resumen = insertar_ventas_mensual_dividido(
                data=request_data,
                sucursal=sucursal,
                anio=int(anio),
                mes=int(mes),
                dias_en_mes=int(dias_en_mes),
                created_by=created_by
            )

        logger.info(f"Guardado exitoso. Resumen: {resumen}")

        return jsonify({
            'success': True,
            'message': 'Datos guardados exitosamente',
            'resumen': resumen
        }), 200

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error guardando datos: {str(e)}")
        logger.error(f"Traceback completo:\n{error_details}")

        return jsonify({
            'success': False,
            'error': f'Error al guardar los datos: {str(e)}',
            'details': error_details if logger.level == logging.DEBUG else None
        }), 500


@ventas_bp.route('/api/ventas')
@login_required
def api_ventas():
    """API para obtener ventas (para DataTables, etc.)"""
    try:
        # Obtener parámetros de filtrado
        limit = request.args.get('limit', 100, type=int)
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        ventas = obtener_ventas(
            limit=limit,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        return jsonify({
            'success': True,
            'data': ventas
        })

    except Exception as e:
        logger.error(f"Error en API ventas: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ventas_bp.route('/metas')
@login_required
def metas():
    """Página de gestión de metas mensuales"""
    try:
        import math

        # TODO: Datos de prueba - reemplazar con datos reales de la BD
        metas_data = [
            {
                'sucursal': 'Centro',
                'meta_monto': 1500000,
                'ventas_reales': 1425000,
                'porcentaje_cumplimiento': 95,
                'diferencia': -75000,
                'estado': 'en_progreso',
                'mes': 2,
                'anio': 2026
            },
            {
                'sucursal': 'LM',
                'meta_monto': 2000000,
                'ventas_reales': 1018677,
                'porcentaje_cumplimiento': 51,
                'diferencia': -981323,
                'estado': 'en_progreso',
                'mes': 2,
                'anio': 2026
            },
            {
                'sucursal': 'Auditorio',
                'meta_monto': 1800000,
                'ventas_reales': 810000,
                'porcentaje_cumplimiento': 45,
                'diferencia': -990000,
                'estado': 'requiere_accion',
                'mes': 2,
                'anio': 2026
            },
            {
                'sucursal': 'Ahumada',
                'meta_monto': 1600000,
                'ventas_reales': 816000,
                'porcentaje_cumplimiento': 51,
                'diferencia': -784000,
                'estado': 'en_progreso',
                'mes': 2,
                'anio': 2026
            }
        ]

        # Calcular coordenadas del arco para cada meta
        for meta in metas_data:
            porcentaje = min(meta['porcentaje_cumplimiento'], 100)
            angle = (porcentaje / 100) * 180
            rad = math.radians(angle)

            # Coordenadas del punto final del arco (para SVG de 280x150)
            meta['arc_x'] = 140 + 120 * math.cos(math.pi - rad)
            meta['arc_y'] = 128 - 120 * math.sin(math.pi - rad)
            # Para un semicírculo, siempre usar arco corto (large-arc-flag = 0)
            meta['arc_large'] = 0

        return render_template('ventas/metas.html', metas=metas_data)

    except Exception as e:
        logger.error(f"Error en metas: {str(e)}")
        flash('Error al cargar las metas', 'danger')
        return render_template('ventas/metas.html', metas=[])
