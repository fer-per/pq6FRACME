"""
Servicio PDF — implementación del PDFServicePort.

Usa pypdf para lectura/escritura y PyMuPDF (fitz) para renderizado.
"""
import logging
from typing import List, Any

from src.domain.ports.pdf_port import PDFServicePort

logger = logging.getLogger(__name__)


class PDFService(PDFServicePort):
    """Implementación concreta del servicio PDF."""

    def obtener_total_paginas(self, ruta: str) -> int:
        """Obtiene el total de páginas usando pypdf."""
        from pypdf import PdfReader

        logger.info("Obteniendo total de páginas de: %s", ruta)
        reader = PdfReader(ruta)
        try:
            total = len(reader.pages)
            logger.info("Total de páginas: %d", total)
            return total
        finally:
            reader.close()

    def abrir(self, ruta: str) -> Any:
        """Abre el PDF maestro una sola vez para reutilizarlo en la extracción."""
        from pypdf import PdfReader

        logger.info("Abriendo PDF maestro: %s", ruta)
        return PdfReader(ruta)

    def cerrar(self, lector: Any) -> None:
        """Cierra el lector abierto con ``abrir``."""
        if lector is None:
            return
        try:
            lector.close()
            logger.debug("PDF maestro cerrado.")
        except Exception as e:
            logger.warning("Error al cerrar PDF maestro: %s", e)

    def extraer_paginas(
        self,
        lector: Any,
        paginas: List[int],
        ruta_destino: str,
    ) -> None:
        """Extrae páginas de un lector ya abierto usando pypdf."""
        from pypdf import PdfWriter

        logger.info(
            "Extrayendo páginas %s → %s",
            paginas, ruta_destino,
        )

        total_pages = len(lector.pages)
        indices = [
            num - 1 for num in paginas if 1 <= num <= total_pages
        ]  # 1-based → 0-based

        for num_pag in paginas:
            if num_pag < 1 or num_pag > total_pages:
                logger.warning(
                    "Página %d fuera de rango (1-%d), omitiendo.",
                    num_pag, total_pages,
                )

        if not indices:
            logger.warning("No se extrajeron páginas para %s.", ruta_destino)
            return

        writer = PdfWriter()
        try:
            writer.append(lector, pages=indices)
            with open(ruta_destino, 'wb') as f:
                writer.write(f)
            logger.info(
                "Archivo creado: %s (%d páginas)",
                ruta_destino, len(indices),
            )
        finally:
            writer.close()

    def renderizar_pagina(
        self,
        ruta: str,
        num_pagina: int,
        zoom: int = 100,
    ) -> Any:
        """
        Renderiza una página del PDF como bytes de imagen PNG.

        Usa PyMuPDF (fitz) para renderizar a pixmap.
        Retorna bytes PNG que pueden convertirse a QPixmap en la capa de presentación.
        """
        import fitz  # PyMuPDF

        logger.debug("Renderizando página %d de %s (zoom=%d%%)", num_pagina, ruta, zoom)

        doc = fitz.open(ruta)
        try:
            if num_pagina < 1 or num_pagina > len(doc):
                logger.warning(
                    "Página %d fuera de rango (1-%d).", num_pagina, len(doc)
                )
                return None

            page = doc[num_pagina - 1]  # 0-based
            mat = fitz.Matrix(zoom / 100, zoom / 100)
            pix = page.get_pixmap(matrix=mat)
            return pix.tobytes("png")
        finally:
            doc.close()
