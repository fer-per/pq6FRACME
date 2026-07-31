"""
Generador de sugerencias de corrección.

Transforma errores de análisis en sugerencias editables
para que el usuario pueda corregir los registros del inventario.
"""
import logging
from typing import List, Optional

from src.domain.entities import (
    AnalysisError,
    InventoryRecord,
    SugerenciaCorreccion,
)
from src.domain.services.folio_parser import calculate_suggested_range
from src.domain.services.folio_mapper import FolioMapper

logger = logging.getLogger(__name__)


def generar_sugerencias(
    errors: List[AnalysisError],
    records: List[InventoryRecord],
    mapper: Optional[FolioMapper] = None,
) -> List[SugerenciaCorreccion]:
    """
    Genera sugerencias de corrección a partir de errores de análisis.

    Para cada error:
    1. Busca el InventoryRecord correspondiente.
    2. Si es tipo SALTO, calcula el rango sugerido basándose en el registro anterior.
    3. Crea una SugerenciaCorreccion con valores actuales y sugeridos.

    Args:
        errors: Lista de errores detectados.
        records: Lista de registros del inventario.
        mapper: FolioMapper para calcular páginas PDF sugeridas (opcional).

    Returns:
        Lista de SugerenciaCorreccion.
    """
    records_by_id = {r.id: r for r in records}
    records_list = list(records)  # Para acceder por índice
    sugerencias: List[SugerenciaCorreccion] = []
    sug_counter = 0

    for error in errors:
        record = records_by_id.get(error.record_id)
        if record is None:
            continue

        sug_counter += 1
        sug_id = f"SUG_{sug_counter:03d}"

        # Calcular rango sugerido para errores de tipo SALTO
        rango_sugerido = ""
        paginas_sugeridas = ""

        if error.tipo == "SALTO":
            # Buscar registro anterior
            prev_record = _find_previous_record(record, records_list)
            if prev_record is not None:
                suggested = calculate_suggested_range(prev_record, record)
                if suggested:
                    rango_sugerido = suggested
                    # Calcular páginas PDF del rango sugerido
                    if mapper is not None:
                        mapper.start_sequence()
                        # Procesar todos los registros hasta el actual
                        # para que el contador esté en posición correcta
                        for r in records_list:
                            if r.id == record.id:
                                break
                            mapper.folio_str_to_pdf_pages(r.folios)
                        pdf_range = mapper.folio_str_to_pdf_range(rango_sugerido)
                        paginas_sugeridas = pdf_range or ""

        valor_sugerido = rango_sugerido or error.valor_esperado

        sugerencias.append(SugerenciaCorreccion(
            id=sug_id,
            registro_id=record.id,
            tipo_error=error.tipo,
            descripcion=error.descripcion,
            valor_actual=record.folios,
            valor_sugerido=valor_sugerido,
            escribano=record.escribano,
            folios_original=record.folios,
            rango_sugerido=rango_sugerido,
            paginas_pdf=record.pg_pdf,
            paginas_sugeridas=paginas_sugeridas,
            fecha_original=record.fecha_inicio,
        ))

    return sugerencias


def _find_previous_record(
    current: InventoryRecord,
    records: List[InventoryRecord],
) -> Optional[InventoryRecord]:
    """Busca el registro inmediatamente anterior al actual en la lista."""
    for i, r in enumerate(records):
        if r.id == current.id and i > 0:
            return records[i - 1]
    return None
