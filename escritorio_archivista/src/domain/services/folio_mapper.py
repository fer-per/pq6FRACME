"""
Motor de mapeo folio → página PDF.

Convierte folios notariales (ej: "001r-002v") a páginas PDF reales,
considerando offsets, segmentos, páginas ignoradas y reordenamiento.

Este módulo depende SOLO de folio_parser (mismo paquete de dominio).
"""
import logging
from typing import List, Optional

from src.domain.services.folio_parser import parse_folios, folio_to_int
from src.domain.value_objects import MAX_IGNORED_ITERATIONS

logger = logging.getLogger(__name__)


class Segmento:
    """Punto de quiebre: a partir de este folio, el PDF salta a otra página."""

    def __init__(self, folio_inicio_str: str, pag_pdf_inicio: int):
        parsed = parse_folios(folio_inicio_str)
        if parsed:
            self.folio_int = folio_to_int(parsed[0], parsed[1])
        else:
            self.folio_int = 1
        self.pag_pdf_inicio = pag_pdf_inicio


class FolioMapper:
    """
    Motor de mapeo completo: convierte folios notariales a páginas PDF reales.

    Soporta:
    - Offset base (folio 1r = página X del PDF)
    - Segmentos (puntos donde el offset cambia)
    - Páginas ignoradas (exclusiones tipo IGNORAR)
    - Page map (reordenamiento manual de páginas)

    IMPORTANTE: Este mapper usa un CONTADOR SECUENCIAL interno.
    Se debe llamar start_sequence() antes de procesar una lista de registros,
    y los registros deben procesarse EN ORDEN.
    """

    def __init__(
        self,
        pag_pdf_inicio: int = 1,
        segmentos: Optional[List[Segmento]] = None,
        ignoradas: Optional[List[int]] = None,
        page_map: Optional[dict] = None,
    ):
        self.page_map = page_map or {}
        self.pag_pdf_inicio = pag_pdf_inicio

        # Si hay page_map, traducir pag_pdf_inicio al espacio original
        if page_map:
            for op, np in page_map.items():
                if np == pag_pdf_inicio:
                    self.pag_pdf_inicio = op
                    break

        self.segmentos = sorted(segmentos or [], key=lambda s: s.folio_int)

        # Traducir segmentos al espacio original si hay page_map
        if page_map:
            for seg in self.segmentos:
                for op, np in page_map.items():
                    if np == seg.pag_pdf_inicio:
                        seg.pag_pdf_inicio = op
                        break

        self.ignoradas_set = set(ignoradas or [])
        self.folio_page_counter = self.pag_pdf_inicio
        self._last_segment: Optional[Segmento] = None

    def start_sequence(self):
        """Reinicia el contador interno. LLAMAR antes de procesar registros."""
        self.folio_page_counter = self.pag_pdf_inicio
        self._last_segment = None

    def folio_str_to_pdf_pages(self, folio_str: str) -> Optional[List[int]]:
        """
        Convierte un string de folio a lista de páginas PDF reales.

        Algoritmo:
        1. Parsear el folio a rango (desde_int, hasta_int)
        2. Para cada folio_int en el rango:
           a. Buscar si hay un Segmento activo
           b. Si hay nuevo segmento, resetear el contador
           c. La página es el valor actual del contador
           d. Incrementar contador
           e. Saltar páginas en ignoradas_set
           f. Si hay page_map, traducir la página
        3. Retornar lista de páginas
        """
        parsed = parse_folios(folio_str)
        if parsed is None:
            return None
        desde_num, desde_cara, hasta_num, hasta_cara = parsed
        desde_int = folio_to_int(desde_num, desde_cara)
        hasta_int = folio_to_int(hasta_num, hasta_cara)

        pages = []
        for folio_int in range(desde_int, hasta_int + 1):
            seg = self._find_segment(folio_int)
            if seg is not None and seg != self._last_segment:
                self.folio_page_counter = seg.pag_pdf_inicio
                self._last_segment = seg

            page = self.folio_page_counter
            self.folio_page_counter += 1

            # Saltar páginas ignoradas con límite de seguridad
            iterations = 0
            while page in self.ignoradas_set and iterations < MAX_IGNORED_ITERATIONS:
                page = self.folio_page_counter
                self.folio_page_counter += 1
                iterations += 1

            if self.page_map:
                if page in self.page_map:
                    page = self.page_map[page]
                    if page is None:
                        continue
                else:
                    continue

            pages.append(page)
        return pages

    def folio_str_to_pdf_range(self, folio_str: str) -> Optional[str]:
        """Retorna '1-4' o '7' o None."""
        pages = self.folio_str_to_pdf_pages(folio_str)
        if not pages:
            return None
        if len(pages) == 1:
            return str(pages[0])
        return f"{pages[0]}-{pages[-1]}"

    def max_pdf_page(self, records: list) -> int:
        """Calcula la página PDF máxima requerida."""
        self.start_sequence()
        max_p = 0
        for r in records:
            pages = self.folio_str_to_pdf_pages(r.folios)
            if pages:
                max_p = max(max_p, pages[-1])
        return max_p

    def _find_segment(self, folio_int: int) -> Optional[Segmento]:
        """Busca el segmento activo más grande cuyo folio_int <= folio_int."""
        for seg in reversed(self.segmentos):
            if folio_int >= seg.folio_int:
                return seg
        return None


def mapper_from_config(
    pag_pdf_inicio: int = 1,
    segmentos: Optional[list] = None,
    exclusiones: Optional[list] = None,
    page_map: Optional[dict] = None,
) -> FolioMapper:
    """
    Factory que crea un FolioMapper desde parámetros de configuración.

    Args:
        pag_pdf_inicio: Página PDF de inicio.
        segmentos: Lista de dicts con {"folio_inicio": "001r", "pag_pdf_inicio": 1}.
        exclusiones: Lista de ExclusionRule — las de tipo "IGNORAR" generan páginas a saltar.
        page_map: Dict {página_original: página_nueva} o {página: None}.

    Returns:
        FolioMapper configurado.
    """
    ignoradas = []
    for excl in (exclusiones or []):
        if excl.tipo == 'IGNORAR':
            for p in range(int(excl.desde), int(excl.hasta) + 1):
                ignoradas.append(p)

    segmentos_objs = []
    for seg_data in (segmentos or []):
        segmentos_objs.append(Segmento(
            folio_inicio_str=seg_data.get('folio_inicio', '1r'),
            pag_pdf_inicio=int(seg_data.get('pag_pdf_inicio', 1)),
        ))

    return FolioMapper(
        pag_pdf_inicio=pag_pdf_inicio,
        segmentos=segmentos_objs,
        ignoradas=ignoradas,
        page_map=page_map,
    )
