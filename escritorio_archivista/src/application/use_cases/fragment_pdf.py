"""
Caso de uso: Fragmentar PDF.

Orquesta la fragmentación del PDF maestro en documentos individuales,
organizados en la jerarquía de 11 niveles de carpetas.
"""
import csv
import logging
import os
from typing import List, Optional

from src.domain.entities import InventoryRecord, ExclusionRule
from src.domain.ports.pdf_port import PDFServicePort
from src.domain.ports.hierarchy_port import HierarchyBuilderPort
from src.domain.services.folio_mapper import mapper_from_config
from src.domain.services.folio_parser import es_sin_folio
from src.application.dto import ResultadoFragmentacion, InfoArchivo

logger = logging.getLogger(__name__)


class FragmentarPDFUseCase:
    """Caso de uso para fragmentar el PDF maestro."""

    def __init__(
        self,
        pdf_service: PDFServicePort,
        hierarchy_builder: HierarchyBuilderPort,
    ):
        self._pdf_service = pdf_service
        self._hierarchy_builder = hierarchy_builder

    def ejecutar(
        self,
        records: List[InventoryRecord],
        pdf_path: str,
        output_dir: str,
        acervo_num: str = "",
        escribano: str = "",
        siglo: str = "",
        pag_pdf_inicio: int = 1,
        segmentos: Optional[list] = None,
        exclusiones: Optional[List[ExclusionRule]] = None,
        page_map: Optional[dict] = None,
        active_pages: Optional[list] = None,
        total_pdf_pages: int = 0,
        incidencias_validadas: Optional[set] = None,
        on_progress: Optional[callable] = None,
    ) -> ResultadoFragmentacion:
        """
        Ejecuta la fragmentación del PDF maestro.

        1. Crea FolioMapper
        2. Para cada registro:
           a. Si estado == REVISAR y su incidencia no fue validada → omitir
           b. Construir ruta jerárquica
           c. Calcular páginas PDF
           d. Extraer páginas
           e. Registrar resultado
        3. Generar CSV de pendientes
        """
        logger.info("Iniciando fragmentación de: %s", pdf_path)

        # Crear mapper
        mapper = mapper_from_config(
            pag_pdf_inicio=pag_pdf_inicio,
            segmentos=segmentos,
            exclusiones=exclusiones,
            page_map=page_map,
            active_pages=active_pages,
            total_pdf_pages=total_pdf_pages,
        )
        mapper.start_sequence()

        archivos_creados: List[InfoArchivo] = []
        errores: List[str] = []
        pendientes: List[dict] = []
        total = len(records)

        # Abrir el PDF maestro una sola vez para evitar re-cargarlo
        # completo en memoria por cada registro (causa de consumos elevados).
        lector = self._pdf_service.abrir(pdf_path)
        try:
            for i, record in enumerate(records):
                # Notificar progreso
                if on_progress:
                    on_progress(i + 1, total, record.id)

                # Omitir registros marcados como REVISAR cuya incidencia no
                # fue validada (validados = revisado pero aceptado).
                if (
                    record.estado == "REVISAR"
                    and record.id not in (incidencias_validadas or set())
                ):
                    pendientes.append({
                        "ID": record.id,
                        "Fila": record.fila,
                        "Registro": record.registro,
                        "Escribano": record.escribano,
                        "Folios": record.folios,
                        "Motivo": "Estado REVISAR — errores sin corregir",
                    })
                    logger.warning("Omitido %s: estado REVISAR.", record.id)
                    # Avanzar el contador del mapper para que los registros
                    # siguientes conserven su mapeo folio → página (la grilla
                    # recorre TODOS los registros en orden).
                    if record.pg_pdf_manual.strip():
                        mapper.folio_str_to_pdf_pages(
                            record.folios, override=record.pg_pdf_manual
                        )
                    else:
                        mapper.folio_str_to_pdf_pages(
                            record.folios, share_last=record.comparte_hoja
                        )
                    continue

                # Registros sin foliación (S/F): requieren rango manual,
                # no resuelven a páginas por sí mismos.
                if (
                    not record.pg_pdf_manual.strip()
                    and es_sin_folio(record.folios)
                ):
                    pendientes.append({
                        "ID": record.id,
                        "Fila": record.fila,
                        "Registro": record.registro,
                        "Escribano": record.escribano,
                        "Folios": record.folios,
                        "Motivo": "Sin foliación (S/F) — asignar rango de páginas PDF manualmente",
                    })
                    logger.warning(
                        "Omitido %s: sin foliación (S/F), sin rango manual.",
                        record.id,
                    )
                    # El registro no ocupa páginas del PDF: los siguientes
                    # conservan su mapeo folio → página.
                    continue

                # Calcular páginas (respetando comparte_hoja o rango manual)
                if record.pg_pdf_manual.strip():
                    pages = mapper.folio_str_to_pdf_pages(
                        record.folios, override=record.pg_pdf_manual
                    )
                else:
                    pages = mapper.folio_str_to_pdf_pages(
                        record.folios, share_last=record.comparte_hoja
                    )
                if not pages:
                    pendientes.append({
                        "ID": record.id,
                        "Fila": record.fila,
                        "Registro": record.registro,
                        "Escribano": record.escribano,
                        "Folios": record.folios,
                        "Motivo": "Folios no resuelven a páginas PDF",
                    })
                    errores.append(
                        f"Error en {record.id}: folios '{record.folios}' "
                        "no resuelven a páginas PDF."
                    )
                    continue

                # Construir ruta de destino
                try:
                    dest_path = self._hierarchy_builder.construir_ruta(
                        record, output_dir, acervo_num, escribano, siglo,
                    )

                    # Crear directorio padre
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                    # Extraer páginas (reutilizando el lector abierto)
                    self._pdf_service.extraer_paginas(lector, pages, dest_path)

                    archivos_creados.append(InfoArchivo(
                        path=dest_path,
                        filename=os.path.basename(dest_path),
                    ))

                    # Marcar como fragmentado
                    record.estado = "FRAGMENTADO"

                    logger.info(
                        "Extraído %s → %s (%d págs)",
                        record.id, os.path.basename(dest_path), len(pages),
                    )

                except Exception as e:
                    error_msg = f"Error en {record.id}: {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
        finally:
            self._pdf_service.cerrar(lector)

        # Generar CSV de pendientes
        if pendientes:
            self._generar_csv_pendientes(output_dir, pendientes)

        resultado = ResultadoFragmentacion(
            archivos_creados=archivos_creados,
            errores=errores,
            total_exitos=len(archivos_creados),
            total_fallos=len(errores),
            metadata={
                "total_registros": total,
                "pendientes": len(pendientes),
            },
        )

        logger.info(
            "Fragmentación completada: %d éxitos, %d fallos, %d pendientes.",
            resultado.total_exitos, resultado.total_fallos, len(pendientes),
        )

        return resultado

    @staticmethod
    def _generar_csv_pendientes(output_dir: str, pendientes: List[dict]):
        """Genera archivo CSV con registros pendientes/omitidos."""
        logs_dir = os.path.join(output_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        csv_path = os.path.join(logs_dir, "pendientes.csv")

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f, fieldnames=["ID", "Fila", "Registro", "Escribano", "Folios", "Motivo"]
            )
            writer.writeheader()
            writer.writerows(pendientes)

        logger.info("CSV de pendientes generado: %s", csv_path)
