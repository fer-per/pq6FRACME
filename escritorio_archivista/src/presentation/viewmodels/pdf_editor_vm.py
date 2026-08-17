"""ViewModel del Editor de PDF."""
import logging
from PySide6.QtCore import QObject, Signal
from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM

logger = logging.getLogger(__name__)


class PDFEditorVM(QObject):
    pages_updated = Signal()
    undo_available = Signal(bool)
    redo_available = Signal(bool)

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._container = container
        self._state = state
        self._undo_stack: list = []
        self._redo_stack: list = []

    def get_active_pages(self) -> list:
        """Retorna la lista de páginas activas."""
        if self._state.active_pages:
            return list(self._state.active_pages)
        return list(range(1, self._state.pdf_total_pages + 1))

    def toggle_page(self, page: int):
        """Incluye/excluye una página."""
        self._save_undo()
        pages = self.get_active_pages()
        if page in pages:
            pages.remove(page)
        else:
            pages.append(page)
            pages.sort()
        self._state.active_pages = pages
        self._update_page_map()
        self.pages_updated.emit()

    def move_page(self, from_idx: int, to_idx: int):
        """Mueve una página de posición."""
        self._save_undo()
        pages = self.get_active_pages()
        if 0 <= from_idx < len(pages) and 0 <= to_idx < len(pages):
            page = pages.pop(from_idx)
            pages.insert(to_idx, page)
            self._state.active_pages = pages
            self._update_page_map()
            self.pages_updated.emit()

    def undo(self):
        if self._undo_stack:
            self._redo_stack.append(list(self._state.active_pages))
            self._state.active_pages = self._undo_stack.pop()
            self._update_page_map()
            self.pages_updated.emit()
            self.undo_available.emit(bool(self._undo_stack))
            self.redo_available.emit(True)

    def redo(self):
        if self._redo_stack:
            self._undo_stack.append(list(self._state.active_pages))
            self._state.active_pages = self._redo_stack.pop()
            self._update_page_map()
            self.pages_updated.emit()
            self.undo_available.emit(True)
            self.redo_available.emit(bool(self._redo_stack))

    def save_config(self):
        """Genera el page_map desde las páginas activas y lo guarda en el estado."""
        self._update_page_map()
        n = len(self.get_active_pages())
        self._state.add_log(
            "SUCCESS", f"Configuración de PDF guardada: {n} páginas activas."
        )

    def get_page_map(self) -> dict:
        """Retorna el mapeo página física -> nueva numeración (posiciones activas)."""
        return dict(self._state.page_map)

    def _update_page_map(self):
        """Reconstruye page_map según el orden actual de páginas activas.

        page_map[física] = nueva posición (1-based), de modo que mover una
        hoja arriba/abajo renumerirá el mapeo de manera consistente.
        """
        pages = self.get_active_pages()
        page_map = {}
        for new_idx, original_page in enumerate(pages, start=1):
            page_map[original_page] = new_idx
        self._state.page_map = page_map
        self._state.recalcular_pg_pdf()
        # Las tablas muestran el mapeo folio → página (pg_pdf) y deben
        # reflejar de inmediato las exclusiones/reordenamientos del editor.
        self._state.records_changed.emit()

    def _save_undo(self):
        self._undo_stack.append(self.get_active_pages())
        self._redo_stack.clear()
        self.undo_available.emit(True)
        self.redo_available.emit(False)
