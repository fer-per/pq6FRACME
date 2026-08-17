"""
Motor de mapeo folio → página PDF.

Convierte folios notariales (ej: "001r-002v") a páginas PDF reales,
considerando offsets, segmentos, páginas ignoradas y reordenamiento.

Este módulo depende SOLO de folio_parser (mismo paquete de dominio).
"""
import logging
import re
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
        active_pages: Optional[list] = None,
        total_pdf_pages: Optional[int] = None,
    ):
        self.page_map = page_map or {}
        self.pag_pdf_inicio = pag_pdf_inicio
        # El editor PDF define las páginas activas EN ORDEN (reordenamiento).
        # Cuando están presentes, el mapeo trabaja con POSICIONES renumeradas
        # (1,2,3,...): la columna pg_pdf coincide con el editor y la vista
        # previa. Sin páginas activas se mantiene el mapeo físico clásico.
        self._active_sequence = [int(p) for p in (active_pages or [])]
        self._sequence_len = len(self._active_sequence)
        self._position_mode = self._sequence_len > 0
        self.total_pdf_pages = total_pdf_pages

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
        self.folio_page_counter = 1 if self._position_mode else self.pag_pdf_inicio
        self._last_segment: Optional[Segmento] = None
        self._last_used_page: Optional[int] = None

    def start_sequence(self):
        """Reinicia el contador interno. LLAMAR antes de procesar registros."""
        self.folio_page_counter = 1 if self._position_mode else self.pag_pdf_inicio
        self._last_segment = None
        self._last_used_page = None

    def folio_str_to_pdf_pages(
        self,
        folio_str: str,
        share_last: bool = False,
        override: Optional[str] = None,
    ) -> Optional[List[int]]:
        """
        Convierte un string de folio a lista de páginas PDF reales.

        Parámetros opcionales (usados en la fragmentación):
        - ``override``: rango en **posición renumerada** (la misma numeración
          que muestra la columna ``pg_pdf`` de la grilla, resultante de
          descartar las hojas excluidas). Se traduce internamente a páginas
          físicas usando ``_active_sequence``. Sin exclusiones activas, el
          rango se usa literalmente como páginas físicas directas.
        - ``share_last``: si es True, el registro arranca en la misma página
          donde terminó el registro anterior (comparte la hoja PDF).

        Algoritmo normal:
        1. Parsear el folio a rango (desde_int, hasta_int)
        2. Para cada folio_int en el rango:
           a. Buscar si hay un Segmento activo
           b. Si hay nuevo segmento, resetear el contador
           c. La página es el valor actual del contador
           d. Incrementar contador
           e. Saltar páginas en ignoradas_set
           f. Si hay page_map, traducir la página
           g. Si hay total_pdf_pages, descartar páginas más allá del PDF
        3. Retornar lista de páginas
        """
        # Sin PDF cargado no hay mapeo a páginas.
        if self.total_pdf_pages is not None and self.total_pdf_pages <= 0:
            return None

        if override:
            return self._map_manual_override(override)

        if self._position_mode:
            return self._map_positions(folio_str, share_last)

        return self._map_physical(folio_str, share_last)

    def _map_manual_override(self, override: str) -> Optional[List[int]]:
        """Resuelve un rango manual (override) de pg_pdf.

        En modo posición el usuario ingresa posiciones renumeradas (las que
        muestra la columna pg_pdf tras descartar hojas). En modo físico, las
        páginas físicas validadas contra las activas. El contador continúa
        después de la última página del rango.
        """
        pages = self._parse_manual_pages(override)
        if not pages:
            return None
        if self._position_mode:
            pages = [p for p in pages if 1 <= p <= self._sequence_len]
            if not pages:
                return None
        else:
            pages = self._translate_manual_pages(pages)
            if not pages:
                return None
        if self.total_pdf_pages is not None:
            pages = [p for p in pages if p <= self.total_pdf_pages]
            if not pages:
                return None
        # El contador avanza al siguiente número; el algoritmo normal se
        # encargará de saltar las ignoradas si las hubiera.
        self.folio_page_counter = pages[-1] + 1
        self._last_used_page = pages[-1]
        return pages

    def _map_positions(self, folio_str: str, share_last: bool) -> Optional[List[int]]:
        """Mapeo folio → posición renumerada (editor PDF con páginas activas).

        La secuencia es la lista ordenada de páginas físicas activas (la
        que reordena el editor con Mover ↑/↓). El folio consume la siguiente
        posición (1-based) de esa secuencia.
        """
        if share_last and self._last_used_page is not None:
            self.folio_page_counter = self._last_used_page

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
                self.folio_page_counter = self._seg_to_position(seg)
                self._last_segment = seg

            page = self.folio_page_counter
            self.folio_page_counter += 1

            # No hay más posiciones activas que asignar.
            if page > self._sequence_len:
                continue
            pages.append(page)

        if pages:
            self._last_used_page = pages[-1]
        return pages

    def _seg_to_position(self, seg: Segmento) -> int:
        """Convierte la página física de un segmento a su posición activa."""
        try:
            return self._active_sequence.index(seg.pag_pdf_inicio) + 1
        except ValueError:
            return 1

    def _map_physical(self, folio_str: str, share_last: bool) -> Optional[List[int]]:
        """Mapeo clásico folio → página física (sin editor PDF activo)."""
        if share_last and self._last_used_page is not None:
            self.folio_page_counter = self._last_used_page

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

            # No mapear más allá del total de hojas del PDF cargado.
            if self.total_pdf_pages is not None and page > self.total_pdf_pages:
                continue

            pages.append(page)

        if pages:
            self._last_used_page = pages[-1]
        return pages

    @staticmethod
    def _parse_manual_pages(override: str) -> Optional[List[int]]:
        """Convierte un rango manual '140-149' o '1,5-7' a lista de páginas."""
        override = override.strip()
        if not override:
            return None
        pages: List[int] = []
        try:
            for part in re.split(r'[;,]', override):
                part = part.strip()
                if not part:
                    continue
                if '-' in part:
                    start_str, end_str = part.split('-', 1)
                    start, end = int(start_str), int(end_str)
                    step = 1 if start <= end else -1
                    pages.extend(range(start, end + step, step))
                else:
                    pages.append(int(part))
        except ValueError:
            return None
        return pages

    def _translate_manual_pages(self, pages: List[int]) -> Optional[List[int]]:
        """Valida páginas manuales (físicas) contra las páginas activas del editor PDF.

        El usuario ingresa el rango como **páginas físicas** del PDF: el mismo
        número que aparece en la columna ``pg_pdf`` de la grilla y en lectores
        externos (Adobe Reader, etc.). Esta función filtra las páginas que hayan
        sido excluidas en el editor, para que no se reintroduzcan hojas
        descartadas accidentalmente.

        Si no hay ``active_sequence`` (el editor PDF no está activo), el rango
        se trata como literal para compatibilidad con el flujo sin exclusiones.
        """
        if not self._active_sequence:
            if self.page_map:
                inverse = {np: op for op, np in self.page_map.items() if np is not None}
                return [inverse.get(p, p) for p in pages]
            return pages
        active_set = set(self._active_sequence)
        result = [p for p in pages if p in active_set]
        return result if result else None

    def folio_str_to_pdf_range(
        self,
        folio_str: str,
        share_last: bool = False,
        override: Optional[str] = None,
    ) -> Optional[str]:
        """Retorna '1-4' o '7' o None."""
        pages = self.folio_str_to_pdf_pages(
            folio_str, share_last=share_last, override=override
        )
        return self.format_pages(pages)

    @staticmethod
    def format_pages(pages: Optional[List[int]]) -> Optional[str]:
        """Formatea una lista de páginas a string compacto preservando huecos.

        [373,374,375] -> "373-375"; [1,5,6,7] -> "1,5-7"; [] -> None.
        """
        if not pages:
            return None
        if len(pages) == 1:
            return str(pages[0])
        partes = []
        inicio = prev = pages[0]
        for p in pages[1:]:
            if p == prev + 1:
                prev = p
                continue
            if inicio == prev:
                partes.append(str(inicio))
            else:
                partes.append(f"{inicio}-{prev}")
            inicio = prev = p
        if inicio == prev:
            partes.append(str(inicio))
        else:
            partes.append(f"{inicio}-{prev}")
        return ",".join(partes)

    def to_physical_pages(self, pages: Optional[List[int]]) -> Optional[List[int]]:
        """Convierte posiciones renumeradas a páginas físicas del PDF.

        En modo posición (editor PDF activo), la posición 1,2,3... corresponde
        a ``_active_sequence[pos-1]`` (la página física en ese lugar del
        orden). Sin modo posición, posición y página física coinciden
        (identidad). Usar antes de extraer páginas del PDF maestro.
        """
        if not pages or not self._position_mode:
            return pages
        result = []
        for p in pages:
            if 1 <= p <= self._sequence_len:
                result.append(self._active_sequence[p - 1])
        return result if result else None

    def max_pdf_page(self, records: list) -> int:
        """Calcula la página PDF máxima requerida.

        Respeta ``pg_pdf_manual`` (rango literal) y ``comparte_hoja``
        (arranca en la última hoja del registro anterior), igual que el
        cálculo de ``pg_pdf`` por registro, para que la cobertura siempre
        coincida con el mapeo mostrado en la grilla.
        """
        self.start_sequence()
        max_p = 0
        for r in records:
            manual = getattr(r, "pg_pdf_manual", "") or ""
            share_last = bool(getattr(r, "comparte_hoja", False))
            if manual.strip():
                pages = self.folio_str_to_pdf_pages(
                    r.folios, override=manual
                )
            else:
                pages = self.folio_str_to_pdf_pages(
                    r.folios, share_last=share_last
                )
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
    active_pages: Optional[list] = None,
    total_pdf_pages: Optional[int] = None,
) -> FolioMapper:
    """
    Factory que crea un FolioMapper desde parámetros de configuración.

    Args:
        pag_pdf_inicio: Página PDF de inicio.
        segmentos: Lista de dicts con {"folio_inicio": "001r", "pag_pdf_inicio": 1}.
        exclusiones: Lista de ExclusionRule — las de tipo "IGNORAR" generan páginas a saltar.
        page_map: Dict {página_original: página_nueva} o {página: None}.
        active_pages: Páginas activas seleccionadas en el editor PDF. Las
            páginas ausentes (descartadas) se tratan como ignoradas y no
            cuentan en el mapeo folio → página.
        total_pdf_pages: Cantidad total de páginas físicas del PDF.

    Returns:
        FolioMapper configurado.
    """
    ignoradas = []
    for excl in (exclusiones or []):
        if excl.tipo == 'IGNORAR':
            for p in range(int(excl.desde), int(excl.hasta) + 1):
                ignoradas.append(p)

    # Las páginas descartadas en el editor PDF también se ignoran.
    # Cuando se definen páginas activas, estas gobiernan el mapeo y el
    # page_map (reindexado antiguo) se descarta para no extraer páginas
    # físicas incorrectas tras eliminar una hoja.
    if active_pages and total_pdf_pages:
        activas = set(active_pages)
        for p in range(1, int(total_pdf_pages) + 1):
            if p not in activas:
                ignoradas.append(p)
        page_map = None

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
        active_pages=active_pages,
        total_pdf_pages=total_pdf_pages,
    )
