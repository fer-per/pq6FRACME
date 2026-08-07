"""
Analizador de data crónica — valida la secuencia cronológica de los registros.

Detecta:
0. Mes fuera de rango (fatal)
1. Año no extraíble (warning)
2. Año fuera de rango histórico [1500-2100] (fatal)
3. Regresión cronológica: año actual < año anterior (fatal)
4. Regresión de mes dentro del mismo año (warning)

La sucesión se valida por MES y no por día, ya que en los protocolos
históricos el día exacto no siempre es fiable ni relevante.

El analizador usa únicamente ``fecha_inicio``; ``fecha_fin`` no se
considera en las validaciones.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple

from src.domain.entities import AnalysisResult, AnalysisError, InventoryRecord
from src.domain.value_objects import YEAR_MIN, YEAR_MAX

logger = logging.getLogger(__name__)


def analizar_cronica(records: List[InventoryRecord]) -> AnalysisResult:
    """
    Evalúa la secuencia cronológica de los registros.

    Args:
        records: Lista de registros del inventario en orden.

    Returns:
        AnalysisResult con errores y advertencias.
    """
    errores: List[AnalysisError] = []
    advertencias: List[AnalysisError] = []
    prev_anio: Optional[int] = None
    prev_mes: Optional[int] = None
    anio_min: Optional[int] = None
    anio_max: Optional[int] = None

    for record in records:
        # 0. Verificar rango de mes antes de procesar
        mes_error = _verificar_rango_mes(record)
        if mes_error is not None:
            errores.append(mes_error)
            continue

        anio = _extraer_anio(record.fecha_inicio)

        # Fallback: intentar desde campo registro
        if anio is None:
            anio = _extraer_anio_de_texto(record.registro)

        # 1. Año no extraíble
        if anio is None:
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="CRONICA",
                descripcion="No se pudo extraer el año.",
                valor_actual=record.fecha_inicio or "(vacío)",
                fatal=False,
            ))
            continue

        # Actualizar rango
        if anio_min is None or anio < anio_min:
            anio_min = anio
        if anio_max is None or anio > anio_max:
            anio_max = anio

        # 2. Año fuera de rango
        if anio < YEAR_MIN or anio > YEAR_MAX:
            errores.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="CRONICA",
                descripcion=(
                    f"El año {anio} está fuera del rango histórico "
                    f"[{YEAR_MIN}-{YEAR_MAX}]."
                ),
                valor_actual=str(anio),
                valor_esperado=f"{YEAR_MIN}-{YEAR_MAX}",
                fatal=True,
            ))
            continue

        # 3. Regresión cronológica
        if prev_anio is not None and anio < prev_anio:
            errores.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="CRONICA",
                descripcion=(
                    f"REGRESIÓN CRONOLÓGICA FATAL: registro es de {anio} "
                    f"pero anterior era de {prev_anio}."
                ),
                valor_actual=str(anio),
                valor_esperado=f">= {prev_anio}",
                fatal=True,
            ))
            # No actualizar prev para no propagar cascada
            continue

        # 4. Mismo año — verificar sucesión por mes (no por día)
        if prev_anio is not None and anio == prev_anio:
            mes_actual = _extraer_mes(record.fecha_inicio)
            if mes_actual is not None and prev_mes is not None:
                if mes_actual < prev_mes:
                    advertencias.append(AnalysisError(
                        record_id=record.id,
                        fila=record.fila,
                        tipo="CRONICA",
                        descripcion=(
                            "ADVERTENCIA: el mes es anterior al del "
                            "registro previo."
                        ),
                        valor_actual=record.fecha_inicio,
                        fatal=False,
                    ))

        prev_anio = anio
        prev_mes = _extraer_mes(record.fecha_inicio)

    return AnalysisResult(
        nombre="Analizador de Data Crónica",
        total_revisados=len(records),
        errores=errores,
        advertencias=advertencias,
        info_extra={
            "anio_min": anio_min,
            "anio_max": anio_max,
        },
    )


def _verificar_rango_mes(record: InventoryRecord) -> Optional[AnalysisError]:
    """
    Verifica que el mes de ``fecha_inicio`` esté dentro del rango 1-12.

    Fechas con mes inválido (ej: "6/19/1586" interpretado como mes 19)
    son datos corruptos o en formato ambiguo, y harían que el registro
    caiga en la carpeta "SIN FECHA". Se reportan como error fatal.
    """
    campo = record.fecha_inicio
    if not campo:
        return None
    mes = _extraer_mes_bruto(campo)
    if mes is not None and not (1 <= mes <= 12):
        return AnalysisError(
            record_id=record.id,
            fila=record.fila,
            tipo="CRONICA",
            descripcion=(
                f"MES FUERA DE RANGO: la fecha '{campo}' tiene el mes "
                f"{mes}, pero el mes debe estar entre 1 y 12 (posible "
                "fecha en formato m/d/y ingresada como d/m/y)."
            ),
            valor_actual=str(mes),
            valor_esperado="1-12",
            fatal=True,
        )
    return None


def _extraer_mes_bruto(texto: str) -> Optional[int]:
    """
    Extrae el segundo campo numérico de una fecha d/m/yyyy (el mes).

    A diferencia de ``_extraer_mes`` (que solo devuelve None si el formato
    no es parseable), este devuelve el valor crudo aunque esté fuera de
    rango, para poder detectarlo como error.
    """
    if not texto or not isinstance(texto, str):
        return None
    texto = texto.strip()
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto)
    if match:
        return int(match.group(2))
    return None


def _extraer_anio(texto: str) -> Optional[int]:
    """
    Extrae el año de un string de fecha.

    Intenta formatos: d/m/yyyy, yyyy-mm-dd, o busca 4 dígitos.
    """
    if not texto or not isinstance(texto, str):
        return None
    texto = texto.strip()

    # Formato d/m/yyyy o dd/mm/yyyy
    match = re.match(r'\d{1,2}/\d{1,2}/(\d{4})', texto)
    if match:
        return int(match.group(1))

    # Formato yyyy-mm-dd
    match = re.match(r'(\d{4})-\d{1,2}-\d{1,2}', texto)
    if match:
        return int(match.group(1))

    # Buscar cualquier grupo de 4 dígitos
    match = re.search(r'(\d{4})', texto)
    if match:
        return int(match.group(1))

    return None


def _extraer_anio_de_texto(texto: str) -> Optional[int]:
    """Busca 4 dígitos consecutivos en un texto genérico."""
    if not texto or not isinstance(texto, str):
        return None
    match = re.search(r'(\d{4})', texto)
    if match:
        return int(match.group(1))
    return None


def _extraer_mes(texto: str) -> Optional[int]:
    """Extrae el mes (1-12) de un string de fecha, o None si no se puede."""
    fecha = _parsear_fecha(texto)
    if fecha is None:
        return None
    return fecha.month


def _parsear_fecha(texto: str) -> Optional[datetime]:
    """
    Parsea una fecha completa desde un string.

    Intenta: d/m/yyyy, yyyy-mm-dd, d-m-yyyy
    """
    if not texto or not isinstance(texto, str):
        return None
    texto = texto.strip()

    formatos = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue

    return None
