"""
Funciones de base de datos para el módulo de ventas - PostgreSQL
"""
import logging
import pandas as pd
from decimal import Decimal
from datetime import datetime
from database import execute_query, get_db_connection, decimal_to_float
import psycopg2
from config import Config
from io import StringIO

logger = logging.getLogger(__name__)


def distribuir_cantidad_entre_dias(cantidad_total, dia_actual, total_dias):
    """
    Distribuye cantidades enteras uniformemente entre días, preservando el total exacto.

    Los primeros N días reciben cantidad_base + 1, donde N es el residuo.
    Los demás días reciben solo cantidad_base.

    Args:
        cantidad_total: Cantidad total a distribuir (int)
        dia_actual: Día actual (1 a total_dias)
        total_dias: Total de días en el mes (28, 29, 30 o 31)

    Returns:
        int: Cantidad para este día específico

    Ejemplo:
        cantidad_total = 277, total_dias = 31
        cantidad_base = 277 // 31 = 8
        residuo = 277 % 31 = 29
        Días 1-29: reciben 9 unidades
        Días 30-31: reciben 8 unidades
        Total: (29 × 9) + (2 × 8) = 277 ✅
    """
    if cantidad_total <= 0:
        return 0

    cantidad_base = cantidad_total // total_dias  # División entera
    residuo = cantidad_total % total_dias         # Residuo

    # Los primeros "residuo" días reciben +1 unidad extra
    if dia_actual <= residuo:
        return cantidad_base + 1
    else:
        return cantidad_base


def bulk_insert_copy(cursor, table, columns, registros):
    """
    Inserción masiva usando PostgreSQL COPY (10-100x más rápido que INSERT)

    Args:
        cursor: Cursor de psycopg2
        table: Nombre de la tabla con schema (ej: LealSilver.ventas_por_hora)
        columns: Lista de nombres de columnas
        registros: Lista de tuplas con los datos
    """
    if not registros:
        return

    buffer = StringIO()
    for registro in registros:
        # Convertir cada valor a string, usar \N para NULL
        row = []
        for val in registro:
            if val is None:
                row.append('\\N')
            elif isinstance(val, Decimal):
                row.append(str(val))
            elif isinstance(val, (int, float)):
                row.append(str(val))
            else:
                # Escapar caracteres especiales en strings
                row.append(str(val).replace('\t', ' ').replace('\n', ' '))
        buffer.write('\t'.join(row) + '\n')

    buffer.seek(0)

    # Usar copy_expert para manejar nombres con mayúsculas correctamente
    # Separar schema y tabla para agregar comillas
    if '.' in table:
        schema, tabla = table.split('.', 1)
        table_with_quotes = f'"{schema}".{tabla}'
    else:
        table_with_quotes = table

    columns_str = ', '.join(columns)
    copy_sql = f'COPY {table_with_quotes} ({columns_str}) FROM STDIN WITH (FORMAT TEXT, DELIMITER E\'\\t\', NULL \'\\N\')'
    cursor.copy_expert(copy_sql, buffer)


def obtener_ventas(limit=100, fecha_inicio=None, fecha_fin=None):
    """Obtener ventas con filtros opcionales"""
    try:
        query = """
            SELECT id, fecha, producto, cantidad, precio_unitario, total, usuario_id, fecha_carga
            FROM ventas
        """

        conditions = []
        params = []

        if fecha_inicio:
            conditions.append("fecha >= %s")
            params.append(fecha_inicio)

        if fecha_fin:
            conditions.append("fecha <= %s")
            params.append(fecha_fin)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY fecha DESC, id DESC LIMIT %s"
        params.append(limit)

        results = execute_query(query, tuple(params))
        return [dict(row) for row in results]

    except Exception as e:
        logger.error(f"Error obteniendo ventas: {str(e)}")
        raise


def insertar_ventas(ventas_data, usuario_id):
    """Insertar múltiples ventas"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO ventas (fecha, producto, cantidad, precio_unitario, total, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        data = [
            (
                venta['fecha'],
                venta['producto'],
                Decimal(str(venta['cantidad'])),
                Decimal(str(venta['precio_unitario'])),
                Decimal(str(venta['total'])),
                usuario_id
            )
            for venta in ventas_data
        ]

        cursor.executemany(query, data)
        connection.commit()
        connection.close()

        logger.info(f"Se insertaron {len(data)} ventas")
        return True

    except Exception as e:
        logger.error(f"Error insertando ventas: {str(e)}")
        raise


def procesar_excel_ventas(filepath):
    """Procesar archivo Excel de ventas"""
    try:
        df = pd.read_excel(filepath)

        if len(df.columns) < 4:
            raise ValueError("El archivo debe tener al menos 4 columnas")

        column_names = ['fecha', 'producto', 'cantidad', 'precio_unitario']
        if len(df.columns) >= 5:
            column_names.append('total')

        df.columns = column_names[:len(df.columns)]
        df = df.dropna(subset=['fecha', 'producto', 'cantidad', 'precio_unitario'])

        ventas = []

        for _, row in df.iterrows():
            try:
                if isinstance(row['fecha'], str):
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                        try:
                            fecha = datetime.strptime(row['fecha'], fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        logger.warning(f"Formato de fecha no reconocido: {row['fecha']}")
                        continue
                else:
                    fecha = row['fecha']

                fecha_str = fecha.strftime('%Y-%m-%d %H:%M:%S')
                cantidad = float(row['cantidad'])
                precio_unitario = float(row['precio_unitario'])

                if 'total' in row and pd.notna(row['total']):
                    total = float(row['total'])
                else:
                    total = cantidad * precio_unitario

                ventas.append({
                    'fecha': fecha_str,
                    'producto': str(row['producto']).strip(),
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'total': total
                })

            except Exception as e:
                logger.warning(f"Error procesando fila: {str(e)}")
                continue

        logger.info(f"Se procesaron {len(ventas)} ventas del Excel")
        return ventas

    except Exception as e:
        logger.error(f"Error procesando Excel: {str(e)}")
        raise


# ============================================================================
# FUNCIONES DE VALIDACIÓN DE DUPLICADOS
# ============================================================================

def verificar_existe_mes(sucursal, anio, mes):
    """
    Verifica si ya existen datos cargados para un mes específico de una sucursal.
    Usado en modo MENSUAL para evitar duplicados.

    Args:
        sucursal: Nombre de la sucursal
        anio: Año (2020-2100)
        mes: Número del mes (1-12)

    Returns:
        bool: True si ya existen datos para ese mes, False si no existen
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Verificar en ventas_por_hora (tabla representativa)
        query = """
            SELECT COUNT(*) as total
            FROM "LealSilver".ventas_por_hora
            WHERE sucursal = %s AND anio = %s AND mes = %s
        """

        cursor.execute(query, (sucursal, anio, mes))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        # Acceder por nombre de columna (cursor es RealDictCursor)
        total = result['total'] if result else 0
        existe = total > 0

        if existe:
            logger.info(f"Ya existen {total} registros para {sucursal} en {anio}-{mes}")

        return existe

    except Exception as e:
        logger.error(f"Error verificando existencia de mes: {str(e)}")
        if connection:
            connection.close()
        raise


def verificar_existe_dia(sucursal, anio, mes, dia):
    """
    Verifica si ya existen datos cargados para un día específico de una sucursal.
    Usado en modo DIARIO para evitar duplicados.

    Args:
        sucursal: Nombre de la sucursal
        anio: Año (2020-2100)
        mes: Número del mes (1-12)
        dia: Día del mes (1-31)

    Returns:
        bool: True si ya existen datos para ese día, False si no existen
    """
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Verificar en ventas_por_hora (tabla representativa)
        query = """
            SELECT COUNT(*) as total
            FROM "LealSilver".ventas_por_hora
            WHERE sucursal = %s AND anio = %s AND mes = %s AND dia = %s
        """

        cursor.execute(query, (sucursal, anio, mes, dia))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        # Acceder por nombre de columna (cursor es RealDictCursor)
        total = result['total'] if result else 0
        existe = total > 0

        if existe:
            logger.info(f"Ya existen {total} registros para {sucursal} en {anio}-{mes}-{dia}")

        return existe

    except Exception as e:
        logger.error(f"Error verificando existencia de día: {str(e)}")
        if connection:
            connection.close()
        raise


# ============================================================================
# FUNCIONES PARA INSERTAR DATOS EN ESQUEMA LealSilver
# ============================================================================

def insertar_ventas_leal_silver(data, sucursal, anio, mes, dia, created_by):
    """
    Inserta todas las ventas procesadas en las 8 tablas del esquema LealSilver

    Args:
        data: Diccionario con las 8 secciones de ventas
        sucursal: Nombre de la sucursal
        anio: Año (2020-2100)
        mes: Número del mes (1-12)
        dia: Día del mes (1-31)
        created_by: Usuario que carga los datos

    Returns:
        dict: Resumen de registros insertados
    """
    connection = None
    try:
        # Crear conexión DIRECTA sin RealDictCursor para máxima velocidad en inserts
        connection = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DATABASE
            # NO usar cursor_factory=RealDictCursor - es solo para SELECTs
        )
        cursor = connection.cursor()

        resumen = {}

        # 1. Ventas por hora
        if data.get('ventas_por_hora'):
            query = """
                INSERT INTO "LealSilver".ventas_por_hora
                (sucursal, anio, mes, dia, hora, monto, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['hora'], Decimal(str(v['monto'])), created_by)
                for v in data['ventas_por_hora']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_hora'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_hora")

        # 2. Ventas por platillo
        if data.get('ventas_por_platillo'):
            query = """
                INSERT INTO "LealSilver".ventas_por_platillo
                (sucursal, anio, mes, dia, clave_platillo, nombre_platillo, grupo,
                 cantidad, subtotal, porcentaje, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['clave_platillo'], v['nombre_platillo'],
                 v['grupo'], v['cantidad'], Decimal(str(v['subtotal'])),
                 Decimal(str(v['porcentaje'])), created_by)
                for v in data['ventas_por_platillo']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_platillo'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_platillo")

        # 3. Ventas por grupo
        if data.get('ventas_por_grupo'):
            query = """
                INSERT INTO "LealSilver".ventas_por_grupo
                (sucursal, anio, mes, dia, grupo, subtotal, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['grupo'], Decimal(str(v['subtotal'])), created_by)
                for v in data['ventas_por_grupo']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_grupo'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_grupo")

        # 4. Ventas por tipo de grupo
        if data.get('ventas_por_tipo_grupo'):
            query = """
                INSERT INTO "LealSilver".ventas_por_tipo_grupo
                (sucursal, anio, mes, dia, grupo, cantidad, subtotal, iva, total,
                 porcentaje, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['grupo'], v['cantidad'],
                 Decimal(str(v['subtotal'])), Decimal(str(v['iva'])),
                 Decimal(str(v['total'])), Decimal(str(v['porcentaje'])), created_by)
                for v in data['ventas_por_tipo_grupo']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_tipo_grupo'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_tipo_grupo")

        # 5. Ventas por tipo de pago
        if data.get('ventas_por_tipo_pago'):
            query = """
                INSERT INTO "LealSilver".ventas_por_tipo_pago
                (sucursal, anio, mes, dia, tipo_pago, total, porcentaje, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['tipo_pago'], Decimal(str(v['total'])),
                 Decimal(str(v['porcentaje'])), created_by)
                for v in data['ventas_por_tipo_pago']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_tipo_pago'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_tipo_pago")

        # 6. Ventas por usuario
        if data.get('ventas_por_usuario'):
            query = """
                INSERT INTO "LealSilver".ventas_por_usuario
                (sucursal, anio, mes, dia, usuario, subtotal, iva, total, num_cuentas,
                 ticket_promedio, num_personas, promedio_por_persona, porcentaje, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['usuario'], Decimal(str(v['subtotal'])),
                 Decimal(str(v['iva'])), Decimal(str(v['total'])), v['num_cuentas'],
                 Decimal(str(v['ticket_promedio'])), v['num_personas'],
                 Decimal(str(v['promedio_por_persona'])), Decimal(str(v['porcentaje'])), created_by)
                for v in data['ventas_por_usuario']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_usuario'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_usuario")

        # 7. Ventas por cajero
        if data.get('ventas_por_cajero'):
            query = """
                INSERT INTO "LealSilver".ventas_por_cajero
                (sucursal, anio, mes, dia, cajero, subtotal, iva, total,
                 cantidad_transacciones, porcentaje, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['cajero'], Decimal(str(v['subtotal'])),
                 Decimal(str(v['iva'])), Decimal(str(v['total'])),
                 v['cantidad_transacciones'], Decimal(str(v['porcentaje'])), created_by)
                for v in data['ventas_por_cajero']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_cajero'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_cajero")

        # 8. Ventas por modificador
        if data.get('ventas_por_modificador'):
            query = """
                INSERT INTO "LealSilver".ventas_por_modificador
                (sucursal, anio, mes, dia, grupo, clave_platillo, nombre_platillo,
                 tamano, cantidad, subtotal, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            registros = [
                (sucursal, anio, mes, dia, v['grupo'], v['clave_platillo'],
                 v['nombre_platillo'], v.get('tamano'), v['cantidad'],
                 Decimal(str(v['subtotal'])), created_by)
                for v in data['ventas_por_modificador']
            ]
            cursor.executemany(query, registros)
            resumen['ventas_por_modificador'] = len(registros)
            logger.info(f"Insertados {len(registros)} registros en ventas_por_modificador")

        # Commit de todas las inserciones
        connection.commit()
        cursor.close()

        logger.info(f"Transacción completada exitosamente. Resumen: {resumen}")
        return resumen

    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error insertando datos en LealSilver: {str(e)}")
        raise
    finally:
        if connection:
            connection.close()


def insertar_ventas_mensual_dividido(data, sucursal, anio, mes, dias_en_mes, created_by):
    """
    Inserta ventas MENSUALES divididas PROPORCIONALMENTE entre todos los días del mes.
    Usado para llenar información histórica de meses pasados.

    Args:
        data: Diccionario con las 8 secciones de ventas (datos agregados del mes completo)
        sucursal: Nombre de la sucursal
        anio: Año (2020-2100)
        mes: Número del mes (1-12)
        dias_en_mes: Número de días que tiene el mes (28, 29, 30 o 31)
        created_by: Usuario que carga los datos

    Returns:
        dict: Resumen de registros insertados (total en todas las tablas para todos los días)
    """
    connection = None
    try:
        # Crear conexión DIRECTA sin RealDictCursor para máxima velocidad en inserts
        connection = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DATABASE
            # NO usar cursor_factory=RealDictCursor - es solo para SELECTs
        )
        cursor = connection.cursor()

        resumen = {}

        logger.info(f"Iniciando inserción OPTIMIZADA mensual dividida: {dias_en_mes} días")
        logger.info(f"Construyendo registros para TODOS los días en memoria...")

        # OPTIMIZACIÓN: Construir TODOS los registros de TODOS los días para CADA tabla
        # Esto reduce de 248 operaciones (31 días × 8 tablas) a solo 8 operaciones (1 por tabla)

        # 1. Ventas por hora - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_hora'):
            logger.info("Insertando ventas_por_hora para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['hora'],
                 Decimal(str(v['monto'])) / Decimal(str(dias_en_mes)), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_hora']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_hora',
                           ['sucursal', 'anio', 'mes', 'dia', 'hora', 'monto', 'created_by'],
                           registros)
            resumen['ventas_por_hora'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_hora")

        # 2. Ventas por platillo - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_platillo'):
            logger.info("Insertando ventas_por_platillo para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['clave_platillo'], v['nombre_platillo'],
                 v['grupo'], distribuir_cantidad_entre_dias(v['cantidad'], dia, dias_en_mes),
                 Decimal(str(v['subtotal'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['porcentaje'])), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_platillo']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_platillo',
                           ['sucursal', 'anio', 'mes', 'dia', 'clave_platillo', 'nombre_platillo',
                            'grupo', 'cantidad', 'subtotal', 'porcentaje', 'created_by'],
                           registros)
            resumen['ventas_por_platillo'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_platillo")

        # 3. Ventas por grupo - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_grupo'):
            logger.info("Insertando ventas_por_grupo para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['grupo'],
                 Decimal(str(v['subtotal'])) / Decimal(str(dias_en_mes)), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_grupo']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_grupo',
                           ['sucursal', 'anio', 'mes', 'dia', 'grupo', 'subtotal', 'created_by'],
                           registros)
            resumen['ventas_por_grupo'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_grupo")

        # 4. Ventas por tipo de grupo - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_tipo_grupo'):
            logger.info("Insertando ventas_por_tipo_grupo para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['grupo'],
                 distribuir_cantidad_entre_dias(v['cantidad'], dia, dias_en_mes),
                 Decimal(str(v['subtotal'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['iva'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['total'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['porcentaje'])), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_tipo_grupo']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_tipo_grupo',
                           ['sucursal', 'anio', 'mes', 'dia', 'grupo', 'cantidad', 'subtotal',
                            'iva', 'total', 'porcentaje', 'created_by'],
                           registros)
            resumen['ventas_por_tipo_grupo'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_tipo_grupo")

        # 5. Ventas por tipo de pago - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_tipo_pago'):
            logger.info("Insertando ventas_por_tipo_pago para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['tipo_pago'],
                 Decimal(str(v['total'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['porcentaje'])), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_tipo_pago']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_tipo_pago',
                           ['sucursal', 'anio', 'mes', 'dia', 'tipo_pago', 'total', 'porcentaje', 'created_by'],
                           registros)
            resumen['ventas_por_tipo_pago'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_tipo_pago")

        # 6. Ventas por usuario - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_usuario'):
            logger.info("Insertando ventas_por_usuario para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['usuario'],
                 Decimal(str(v['subtotal'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['iva'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['total'])) / Decimal(str(dias_en_mes)),
                 distribuir_cantidad_entre_dias(v['num_cuentas'], dia, dias_en_mes),
                 Decimal(str(v['ticket_promedio'])) / Decimal(str(dias_en_mes)),
                 distribuir_cantidad_entre_dias(v['num_personas'], dia, dias_en_mes),
                 Decimal(str(v['promedio_por_persona'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['porcentaje'])), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_usuario']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_usuario',
                           ['sucursal', 'anio', 'mes', 'dia', 'usuario', 'subtotal', 'iva', 'total',
                            'num_cuentas', 'ticket_promedio', 'num_personas', 'promedio_por_persona',
                            'porcentaje', 'created_by'],
                           registros)
            resumen['ventas_por_usuario'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_usuario")

        # 7. Ventas por cajero - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_cajero'):
            logger.info("Insertando ventas_por_cajero para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['cajero'],
                 Decimal(str(v['subtotal'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['iva'])) / Decimal(str(dias_en_mes)),
                 Decimal(str(v['total'])) / Decimal(str(dias_en_mes)),
                 distribuir_cantidad_entre_dias(v['cantidad_transacciones'], dia, dias_en_mes),
                 Decimal(str(v['porcentaje'])), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_cajero']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_cajero',
                           ['sucursal', 'anio', 'mes', 'dia', 'cajero', 'subtotal', 'iva', 'total',
                            'cantidad_transacciones', 'porcentaje', 'created_by'],
                           registros)
            resumen['ventas_por_cajero'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_cajero")

        # 8. Ventas por modificador - TODOS los días a la vez (usando COPY - ultra rápido)
        if data.get('ventas_por_modificador'):
            logger.info("Insertando ventas_por_modificador para todos los días...")
            registros = [
                (sucursal, anio, mes, dia, v['grupo'], v['clave_platillo'],
                 v['nombre_platillo'], v.get('tamano'),
                 distribuir_cantidad_entre_dias(v['cantidad'], dia, dias_en_mes),
                 Decimal(str(v['subtotal'])) / Decimal(str(dias_en_mes)), created_by)
                for dia in range(1, dias_en_mes + 1)
                for v in data['ventas_por_modificador']
            ]
            bulk_insert_copy(cursor, 'LealSilver.ventas_por_modificador',
                           ['sucursal', 'anio', 'mes', 'dia', 'grupo', 'clave_platillo', 'nombre_platillo',
                            'tamano', 'cantidad', 'subtotal', 'created_by'],
                           registros)
            resumen['ventas_por_modificador'] = len(registros)
            logger.info(f"✓ Insertados {len(registros)} registros en ventas_por_modificador")

        # Commit único al final
        connection.commit()
        cursor.close()

        logger.info(f"Transacción mensual completada exitosamente. Resumen: {resumen}")
        return resumen

    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error insertando datos mensuales divididos en LealSilver: {str(e)}")
        raise
    finally:
        if connection:
            connection.close()
