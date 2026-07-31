"""
Analizador de data tópica — valida el campo data_topica de los registros.

Detecta:
1. Campo vacío (warning)
2. Solo dígitos — posible confusión de columna (warning)
3. Caracteres inválidos para nombres de archivos (warning)
"""
import logging
import re
from typing import List

from src.domain.entities import AnalysisResult, AnalysisError, InventoryRecord

logger = logging.getLogger(__name__)

# Caracteres inválidos para nombres de archivo/carpeta en Windows
INVALID_CHARS_PATTERN = re.compile(r'[<>{}[\]\\|^`~]')


def analizar_topica(records: List[InventoryRecord]) -> AnalysisResult:
    """
    Evalúa el campo data_topica de cada registro.

    Args:
        records: Lista de registros del inventario.

    Returns:
        AnalysisResult con errores encontrados.
    """
    errores: List[AnalysisError] = []
    campos_validados = 0

    for record in records:
        topica = record.data_topica.strip() if record.data_topica else ""

        # 1. Vacío
        if not topica:
            errores.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="TOPICA",
                descripcion="El campo 'Data Tópica (Lugar)' está vacío.",
                valor_actual="(vacío)",
                fatal=False,
            ))
            continue

        # 2. Solo dígitos
        if topica.isdigit():
            errores.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="TOPICA",
                descripcion=(
                    f"La Data Tópica '{topica}' contiene solo dígitos. "
                    "Posible confusión de columna."
                ),
                valor_actual=topica,
                fatal=False,
            ))
            continue

        # 3. Caracteres inválidos
        if INVALID_CHARS_PATTERN.search(topica):
            errores.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="TOPICA",
                descripcion=(
                    f"La Data Tópica '{topica}' contiene caracteres inválidos "
                    "para nombres de archivos/carpetas."
                ),
                valor_actual=topica,
                fatal=False,
            ))
            continue

        campos_validados += 1

    return AnalysisResult(
        nombre="Analizador de Data Tópica",
        total_revisados=len(records),
        errores=[],
        advertencias=errores,  # Todos son warnings, no fatales
        info_extra={"campos_validados": campos_validados},
    )
