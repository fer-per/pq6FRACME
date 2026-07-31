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
        total = len(reader.pages)
        logger.info("Total de páginas: %d", total)
        return total

    def extraer_paginas(
        self,
        ruta_origen: str,
        paginas: List[int],
        ruta_destino: str,
    ) -> None:
        """Extrae páginas específicas del PDF usando pypdf."""
        from pypdf import PdfReader, PdfWriter

        logger.info(
            "Extrayendo páginas %s de %s → %s",
            paginas, ruta_origen, ruta_destino,
        )

        reader = PdfReader(ruta_origen)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        for num_pag in paginas:
            if 1 <= num_pag <= total_pages:
                writer.add_page(reader.pages[num_pag - 1])  # 1-based → 0-based
            else:
                logger.warning(
                    "Página %d fuera de rango (1-%d), omitiendo.",
                    num_pag, total_pages,
                )

        if len(writer.pages) > 0:
            with open(ruta_destino, 'wb') as f:
                writer.write(f)
            logger.info("Archivo creado: %s (%d páginas)", ruta_destino, len(writer.pages))
        else:
            logger.warning("No se extrajeron páginas para %s.", ruta_destino)

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
