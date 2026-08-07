"""
Caso de uso: Analizar Datos.

Ejecuta todos los analizadores sobre los registros del inventario
y genera sugerencias de corrección consolidadas.
"""
import logging
from typing import List, Optional

from src.domain.entities import InventoryRecord, ExclusionRule
from src.domain.services.folio_mapper import mapper_from_config
from src.domain.services.analyzers.folio_analyzer import analizar_folios
from src.domain.services.analyzers.topica_analyzer import analizar_topica
from src.domain.services.analyzers.cronica_analyzer import analizar_cronica
from src.domain.services.analyzers.coverage_analyzer import analizar_coverage
from src.domain.services.suggestion_generator import generar_sugerencias
from src.application.dto import ResultadoAnalisis

logger = logging.getLogger(__name__)


class AnalizarDatosUseCase:
    """Caso de uso para ejecutar todos los análisis de calidad."""

    def ejecutar(
        self,
        records: List[InventoryRecord],
        exclusions: Optional[List[ExclusionRule]] = None,
        segmentos: Optional[list] = None,
        page_map: Optional[dict] = None,
        pag_pdf_inicio: int = 1,
        total_pdf_pages: int = 0,
        active_pages: Optional[list] = None,
    ) -> ResultadoAnalisis:
        """
        Ejecuta análisis completo del inventario.

        1. Crea FolioMapper
        2. Resetea estados de registros
        3. Recalcula pg_pdf
        4. Ejecuta los 4 analizadores
        5. Combina errores y genera sugerencias
        """
        logger.info("Ejecutando AnalizarDatosUseCase con %d registros.", len(records))

        exclusions = exclusions or []

# 1. Crear mapper
        mapper = mapper_from_config(
            pag_pdf_inicio=pag_pdf_inicio,
            segmentos=segmentos,
            exclusiones=exclusions,
            page_map=page_map,
            active_pages=active_pages,
            total_pdf_pages=total_pdf_pages,
        )

        # 2. Resetear estados
        for record in records:
            if record.estado != "FRAGMENTADO":
                record.estado = ""

        # 3. Recalcular pg_pdf (respetando comparte_hoja y pg_pdf_manual)
        mapper.start_sequence()
        for record in records:
            if record.pg_pdf_manual.strip():
                pages = mapper.folio_str_to_pdf_pages(
                    record.folios, override=record.pg_pdf_manual
                )
                record.pg_pdf = record.pg_pdf_manual.strip() if pages else ""
            else:
                pdf_range = mapper.folio_str_to_pdf_range(
                    record.folios, share_last=record.comparte_hoja
                )
                record.pg_pdf = pdf_range or ""

        # 4. Ejecutar analizadores
        folios_result = analizar_folios(records, exclusions)
        topica_result = analizar_topica(records)
        cronica_result = analizar_cronica(records)
        coverage_result = None
        if total_pdf_pages > 0:
            coverage_result = analizar_coverage(
                records, total_pdf_pages, mapper
            )

        # 5. Combinar errores
        all_errors = (
            folios_result.errores + folios_result.advertencias
            + topica_result.advertencias
            + cronica_result.errores + cronica_result.advertencias
        )
        if coverage_result:
            all_errors += coverage_result.errores

        # Generar sugerencias
        suggestions = generar_sugerencias(all_errors, records, mapper)

        # Marcar registros con errores fatales como REVISAR
        fatal_ids = set()
        for result in [folios_result, cronica_result]:
            for error in result.errores:
                if error.fatal:
                    fatal_ids.add(error.record_id)
        if coverage_result:
            for error in coverage_result.errores:
                if error.fatal:
                    fatal_ids.add(error.record_id)

        for record in records:
            if record.id in fatal_ids:
                record.estado = "REVISAR"

        total_errors = sum(
            len(r.errores) + len(r.advertencias)
            for r in [folios_result, topica_result, cronica_result]
            if r is not None
        )
        if coverage_result:
            total_errors += len(coverage_result.errores)

        logger.info("Análisis completado: %d incidencias totales.", total_errors)

        return ResultadoAnalisis(
            folios_result=folios_result,
            topica_result=topica_result,
            cronica_result=cronica_result,
            coverage_result=coverage_result,
            suggestions=suggestions,
            records=records,
            metadata={
                "total_errores": total_errors,
                "registros_revisar": len(fatal_ids),
            },
        )
