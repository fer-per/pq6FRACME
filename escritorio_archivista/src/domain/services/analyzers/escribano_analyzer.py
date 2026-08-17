"""
Analizador de escribano — valida la columna de escribano.

Detecta:
1. ESCRIBANO — escribano vacío (warning)
2. ESCRIBANO — nombre anormalmente corto (< 3 caracteres) (warning)
3. ESCRIBANO — nombre anormalmente largo (> 60 caracteres) (warning)
"""
import logging
from typing import List

from src.domain.entities import AnalysisResult, AnalysisError, InventoryRecord

logger = logging.getLogger(__name__)

MIN_LONGITUD = 3
MAX_LONGITUD = 60


def analizar_escribano(records: List[InventoryRecord]) -> AnalysisResult:
    """
    Evalúa la columna de escribano de cada registro.

    Args:
        records: Lista de registros del inventario.

    Returns:
        AnalysisResult con las advertencias encontradas.
    """
    advertencias: List[AnalysisError] = []

    for record in records:
        valor = (record.escribano or "").strip()

        if not valor:
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="ESCRIBANO",
                descripcion="El registro no indica escribano.",
                valor_actual="(vacío)",
                valor_esperado="Nombre del escribano",
                fatal=False,
            ))
        elif len(valor) < MIN_LONGITUD:
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="ESCRIBANO",
                descripcion=(
                    f"El nombre '{valor}' es demasiado corto para un "
                    f"escribano (mínimo {MIN_LONGITUD} caracteres)."
                ),
                valor_actual=valor,
                valor_esperado="Nombre completo",
                fatal=False,
            ))
        elif len(valor) > MAX_LONGITUD:
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="ESCRIBANO",
                descripcion=(
                    f"El nombre '{valor}' es anormalmente largo "
                    f"(más de {MAX_LONGITUD} caracteres)."
                ),
                valor_actual=valor,
                valor_esperado=f"Máx. {MAX_LONGITUD} caracteres",
                fatal=False,
            ))

    return AnalysisResult(
        nombre="Analizador de Escribano",
        total_revisados=len(records),
        errores=[],
        advertencias=advertencias,
    )
