"""
Caso de uso: Cargar Inventario.

Orquesta la carga del inventario Excel, el mapeo de folios
y el análisis inicial de la secuencia.
"""
import logging
from typing import List, Optional

from src.domain.ports.excel_port import ExcelRepositoryPort
from src.domain.services.folio_mapper import mapper_from_config
from src.domain.services.analyzers.folio_analyzer import analizar_folios
from src.domain.services.suggestion_generator import generar_sugerencias
from src.domain.value_objects import DEFAULT_DATA_START_ROW
from src.application.dto import ResultadoCarga

logger = logging.getLogger(__name__)


class CargarInventarioUseCase:
    """Caso de uso para cargar un inventario archivístico."""

    def __init__(self, excel_repo: ExcelRepositoryPort):
        self._excel_repo = excel_repo

    def ejecutar(
        self,
        ruta_excel: str,
        fila_datos_inicio: int = DEFAULT_DATA_START_ROW,
        fila_inicio: int = DEFAULT_DATA_START_ROW,
        fila_fin: int = 500,
        pag_pdf_inicio: int = 1,
        segmentos: Optional[list] = None,
        exclusiones: Optional[list] = None,
        page_map: Optional[dict] = None,
        active_pages: Optional[list] = None,
        total_pdf_pages: Optional[int] = None,
        auto_detect: bool = True,
    ) -> ResultadoCarga:
        """
        Ejecuta la carga completa del inventario.

        1. Extrae metadatos globales del Excel
        2. Carga registros con el repositorio
        3. Crea FolioMapper con la configuración
        4. Asigna pg_pdf a cada registro
        5. Ejecuta análisis de folios
        6. Genera sugerencias para errores
        """
        logger.info("Ejecutando CargarInventarioUseCase para: %s", ruta_excel)

        # 0. Detectar fila de inicio de datos si está habilitado
        if auto_detect:
            detected = self._excel_repo.detectar_fila_inicio_datos(ruta_excel)
            if detected:
                logger.info("Fila de inicio de datos detectada: %d", detected)
                fila_datos_inicio = detected

        # 1. Extraer metadatos
        metadata = self._excel_repo.extraer_metadatos(ruta_excel, fila_datos_inicio)

        # 2. Cargar registros
        records = self._excel_repo.cargar_registros(
            ruta_excel, fila_datos_inicio, fila_inicio, fila_fin,
        )

        # 3. Crear mapper
        mapper = mapper_from_config(
            pag_pdf_inicio=pag_pdf_inicio,
            segmentos=segmentos,
            exclusiones=exclusiones,
            page_map=page_map,
            active_pages=active_pages,
            total_pdf_pages=total_pdf_pages,
        )

        # 4. Asignar pg_pdf
        mapper.start_sequence()
        for record in records:
            if record.pg_pdf_manual.strip():
                pdf_range = mapper.folio_str_to_pdf_range(
                    record.folios, override=record.pg_pdf_manual
                )
                record.pg_pdf = pdf_range or ""
            else:
                pdf_range = mapper.folio_str_to_pdf_range(
                    record.folios, share_last=record.comparte_hoja
                )
                record.pg_pdf = pdf_range or ""

        # 5. Analizar folios
        analysis = analizar_folios(records, exclusiones)

        # 6. Generar sugerencias
        all_errors = analysis.errores + analysis.advertencias
        suggestions = generar_sugerencias(all_errors, records, mapper)

        # Marcar registros con errores como REVISAR
        error_ids = {e.record_id for e in analysis.errores}
        for record in records:
            if record.id in error_ids:
                record.estado = "REVISAR"

        metadata.update({
            "total_records": len(records),
            "errores_count": len(analysis.errores),
            "advertencias_count": len(analysis.advertencias),
            "acervo_detectado": metadata.get("acervo_num", ""),
            "escribano_detectado": metadata.get("escribano", ""),
            "siglo_detectado": metadata.get("siglo", ""),
            "fila_datos_inicio": fila_datos_inicio,
        })

        logger.info(
            "Carga completada: %d registros, %d errores, %d advertencias.",
            len(records), len(analysis.errores), len(analysis.advertencias),
        )

        return ResultadoCarga(
            records=records,
            suggestions=suggestions,
            errors=all_errors,
            metadata=metadata,
        )
