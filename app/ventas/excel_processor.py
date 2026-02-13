"""
Procesador de archivos Excel de Resumen de Ventas
Extrae las 8 secciones importantes del archivo
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional


class ResumenVentasProcessor:
    """
    Procesa archivo Excel de Resumen de Ventas.
    Extrae solo las 8 secciones importantes.
    """

    def __init__(self, filepath: str):
        """Inicializa el procesador con la ruta del archivo"""
        self.filepath = filepath
        self.df = None
        self.total_ventas = None
        self.fecha_carga = datetime.now()
        self.errors = []

    def load_file(self) -> bool:
        """Carga el archivo Excel"""
        try:
            self.df = pd.read_excel(
                self.filepath,
                sheet_name='Resumen de Ventas',
                header=None
            )
            return True
        except Exception as e:
            self.errors.append(f"Error al cargar archivo: {str(e)}")
            return False

    def validate_structure(self) -> bool:
        """Valida la estructura básica del archivo"""
        # Validar número de columnas (debe estar cerca de 95, permitir variación)
        if self.df.shape[1] < 90 or self.df.shape[1] > 100:
            self.errors.append(f"Columnas incorrectas: esperadas ~95, encontradas {self.df.shape[1]}")
            return False

        # Validar encabezados en fila 8 (índice 7)
        try:
            # Buscar "Hora" y "Monto" en las primeras columnas de la fila 8
            hora_found = False
            monto_found = False

            for col in range(0, 5):
                cell_value = str(self.df.iloc[7, col]).strip().lower() if pd.notna(self.df.iloc[7, col]) else ""
                if 'hora' in cell_value:
                    hora_found = True
                if 'monto' in cell_value:
                    monto_found = True

            if not hora_found:
                self.errors.append("No se encontró el encabezado 'Hora' en las primeras columnas")
                return False

            if not monto_found:
                self.errors.append("No se encontró el encabezado 'Monto' en las primeras columnas")
                return False

        except Exception as e:
            self.errors.append(f"Error validando encabezados: {str(e)}")
            return False

        return True

    def get_total_ventas(self) -> Optional[float]:
        """
        Extrae el total de ventas del archivo.
        Busca el texto 'Ventas' y el valor numérico asociado.
        """
        try:
            # Buscar en las primeras 5 filas
            for i in range(0, 5):
                for j in range(0, 10):
                    cell = self.df.iloc[i, j]
                    if pd.notna(cell) and str(cell).strip().lower() == 'ventas':
                        # Buscar valor numérico en área cercana
                        for k in range(i, min(i+3, len(self.df))):
                            for m in range(max(0, j-2), min(j+5, self.df.shape[1])):
                                val = self.df.iloc[k, m]
                                if pd.notna(val) and isinstance(val, (int, float)) and val > 1000:
                                    self.total_ventas = float(val)
                                    return self.total_ventas

            self.errors.append("No se encontró el total de ventas en el archivo")
            return None
        except Exception as e:
            self.errors.append(f"Error extrayendo total de ventas: {str(e)}")
            return None

    # ========================================================================
    # SECCIONES IMPORTANTES - EXTRAER
    # ========================================================================

    def extract_ventas_por_hora(self) -> List[Dict]:
        """1. Ventas por hora - Columnas 2-3"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):  # Datos desde fila 9 (índice 8)
                hora = self.df.iloc[idx, 2]
                monto = self.df.iloc[idx, 3]

                if pd.notna(hora) and pd.notna(monto):
                    try:
                        ventas.append({
                            'hora': str(hora).strip(),
                            'monto': float(monto)
                        })
                    except (ValueError, TypeError):
                        continue  # Saltar filas con datos inválidos
        except Exception as e:
            self.errors.append(f"Error en ventas por hora: {str(e)}")

        return ventas

    def extract_ventas_por_platillo(self) -> List[Dict]:
        """2. Ventas por platillo/artículo - Columnas 6-11"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                clave = self.df.iloc[idx, 6]

                if pd.notna(clave):
                    try:
                        ventas.append({
                            'clave_platillo': str(clave).strip(),
                            'nombre_platillo': str(self.df.iloc[idx, 7]).strip(),
                            'grupo': str(self.df.iloc[idx, 8]).strip(),
                            'cantidad': int(self.df.iloc[idx, 9]),
                            'subtotal': float(self.df.iloc[idx, 10]),
                            'porcentaje': float(self.df.iloc[idx, 11])
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por platillo: {str(e)}")

        return ventas

    def extract_ventas_por_grupo(self) -> List[Dict]:
        """3. Ventas por grupo - Columnas 24-25"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                grupo = self.df.iloc[idx, 24]

                if pd.notna(grupo):
                    try:
                        ventas.append({
                            'grupo': str(grupo).strip(),
                            'subtotal': float(self.df.iloc[idx, 25])
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por grupo: {str(e)}")

        return ventas

    def extract_ventas_por_tipo_grupo(self) -> List[Dict]:
        """4. Ventas por tipo de grupo - Columnas 38-43"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                grupo = self.df.iloc[idx, 38]

                if pd.notna(grupo):
                    try:
                        ventas.append({
                            'grupo': str(grupo).strip(),
                            'cantidad': int(self.df.iloc[idx, 39]),
                            'subtotal': float(self.df.iloc[idx, 40]),
                            'iva': float(self.df.iloc[idx, 41]),
                            'total': float(self.df.iloc[idx, 42]),
                            'porcentaje': float(self.df.iloc[idx, 43])
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por tipo de grupo: {str(e)}")

        return ventas

    def extract_ventas_por_tipo_pago(self) -> List[Dict]:
        """5. Ventas por tipo de pago - Columnas 47-49"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                pago = self.df.iloc[idx, 47]

                if pd.notna(pago):
                    try:
                        ventas.append({
                            'tipo_pago': str(pago).strip(),
                            'total': float(self.df.iloc[idx, 48]),
                            'porcentaje': float(self.df.iloc[idx, 49]) if pd.notna(self.df.iloc[idx, 49]) else 0.0
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por tipo de pago: {str(e)}")

        return ventas

    def extract_ventas_por_usuario(self) -> List[Dict]:
        """6. Ventas por usuario - Columnas 53-61"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                usuario = self.df.iloc[idx, 53]

                if pd.notna(usuario):
                    try:
                        ventas.append({
                            'usuario': str(usuario).strip(),
                            'subtotal': float(self.df.iloc[idx, 54]),
                            'iva': float(self.df.iloc[idx, 55]),
                            'total': float(self.df.iloc[idx, 56]),
                            'num_cuentas': int(self.df.iloc[idx, 57]),
                            'ticket_promedio': float(self.df.iloc[idx, 58]),
                            'num_personas': int(self.df.iloc[idx, 59]),
                            'promedio_por_persona': float(self.df.iloc[idx, 60]),
                            'porcentaje': float(self.df.iloc[idx, 61])
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por usuario: {str(e)}")

        return ventas

    def extract_ventas_por_cajero(self) -> List[Dict]:
        """7. Ventas por cajero - Columnas 65-70"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                cajero = self.df.iloc[idx, 65]

                if pd.notna(cajero):
                    try:
                        ventas.append({
                            'cajero': str(cajero).strip(),
                            'subtotal': float(self.df.iloc[idx, 66]),
                            'iva': float(self.df.iloc[idx, 67]),
                            'total': float(self.df.iloc[idx, 68]),
                            'cantidad_transacciones': int(self.df.iloc[idx, 69]),
                            'porcentaje': float(self.df.iloc[idx, 70])
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por cajero: {str(e)}")

        return ventas

    def extract_ventas_por_modificador(self) -> List[Dict]:
        """8. Ventas por modificador - Columnas 74-79"""
        ventas = []
        try:
            for idx in range(8, len(self.df)):
                grupo = self.df.iloc[idx, 74]

                if pd.notna(grupo):
                    try:
                        ventas.append({
                            'grupo': str(grupo).strip(),
                            'clave_platillo': str(self.df.iloc[idx, 75]).strip(),
                            'nombre_platillo': str(self.df.iloc[idx, 76]).strip(),
                            'tamano': str(self.df.iloc[idx, 77]).strip() if pd.notna(self.df.iloc[idx, 77]) else None,
                            'cantidad': int(self.df.iloc[idx, 78]),
                            'subtotal': float(self.df.iloc[idx, 79])
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            self.errors.append(f"Error en ventas por modificador: {str(e)}")

        return ventas

    # ========================================================================
    # PROCESO COMPLETO
    # ========================================================================

    def process_all(self) -> Dict:
        """
        Procesa todas las secciones importantes y retorna un diccionario
        con todos los datos extraídos.
        """
        # Cargar archivo
        if not self.load_file():
            return {'success': False, 'errors': self.errors}

        # Validar estructura
        if not self.validate_structure():
            return {'success': False, 'errors': self.errors}

        # Obtener total
        total = self.get_total_ventas()
        if total is None:
            return {'success': False, 'errors': self.errors}

        # Extraer todas las secciones importantes
        data = {
            'success': True,
            'metadata': {
                'archivo': self.filepath.split('\\')[-1],  # Solo nombre del archivo
                'fecha_carga': self.fecha_carga.strftime('%Y-%m-%d %H:%M:%S'),
                'total_ventas': self.total_ventas,
                'filas': self.df.shape[0],
                'columnas': self.df.shape[1]
            },
            'ventas_por_hora': self.extract_ventas_por_hora(),
            'ventas_por_platillo': self.extract_ventas_por_platillo(),
            'ventas_por_grupo': self.extract_ventas_por_grupo(),
            'ventas_por_tipo_grupo': self.extract_ventas_por_tipo_grupo(),
            'ventas_por_tipo_pago': self.extract_ventas_por_tipo_pago(),
            'ventas_por_usuario': self.extract_ventas_por_usuario(),
            'ventas_por_cajero': self.extract_ventas_por_cajero(),
            'ventas_por_modificador': self.extract_ventas_por_modificador(),
            'errors': self.errors
        }

        return data
