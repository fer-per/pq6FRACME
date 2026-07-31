"""
Analizador de cobertura — verifica que el PDF tenga páginas suficientes.

Detecta si el PDF tiene menos páginas que las requeridas por el inventario.
"""
import logging
from typing import List, Optional

from src.domain.entities import AnalysisResult, AnalysisError, InventoryRecord
from src.domain.services.folio_mapper import FolioMapper

logger = logging.getLogger(__name__)


def analizar_coverage(
    records: List[InventoryRecord],
    total_pdf_pages: int,
    mapper: Optional[FolioMapper] = None,
) -> AnalysisResult:
    """
    Verifica que el PDF tenga suficientes páginas para cubrir todos los folios.

    Args:
        records: Lista de registros del inventario.
        total_pdf_pages: Total de páginas del PDF maestro.
        mapper: FolioMapper para calcular páginas (opcional).

    Returns:
        AnalysisResult con errores si el PDF es insuficiente.
    """
    errores: List[AnalysisError] = []
    max_requerido = 0

    if mapper is not None:
        max_requerido = mapper.max_pdf_page(records)
    else:
        # Parsear pg_pdf directamente
        for record in records:
            if record.pg_pdf:
                try:
                    parts = record.pg_pdf.split('-')
                    for part in parts:
                        val = int(part.strip())
                        if val > max_requerido:
                            max_requerido = val
                except (ValueError, AttributeError):
                    continue

    diferencia = total_pdf_pages - max_requerido

    if diferencia < 0:
        errores.append(AnalysisError(
            record_id="GLOBAL",
            fila=0,
            tipo="COVERAGE",
            descripcion=(
                f"El PDF tiene {total_pdf_pages} páginas pero el "
                f"inventario requiere {max_requerido}."
            ),
            valor_actual=str(total_pdf_pages),
            valor_esperado=str(max_requerido),
            fatal=True,
        ))

    estado = "OK" if diferencia >= 0 else "INSUFICIENTE"

    return AnalysisResult(
        nombre="Analizador de Cobertura PDF",
        total_revisados=len(records),
        errores=errores,
        advertencias=[],
        info_extra={
            "pdf_total": total_pdf_pages,
            "max_requerido": max_requerido,
            "diferencia": diferencia,
            "estado": estado,
        },
    )
