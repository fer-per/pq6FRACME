"""ViewModel de Exclusiones."""
import logging
from PySide6.QtCore import QObject, Signal
from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM

logger = logging.getLogger(__name__)


class ExclusionsVM(QObject):
    exclusions_updated = Signal()

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._container = container
        self._state = state

    def add_salto(self, desde: int, hasta: int, motivo: str):
        result = self._container.gestionar_exclusiones.agregar_salto(
            self._state.exclusions, desde, hasta, motivo,
        )
        self._state.exclusions = result
        self._state.add_log("SUCCESS", f"Salto agregado: folios {desde}-{hasta}")
        self.exclusions_updated.emit()

    def add_ignorar(self, desde: int, hasta: int, motivo: str, tipo: str):
        result = self._container.gestionar_exclusiones.agregar_ignorar(
            self._state.exclusions, desde, hasta, motivo, tipo,
        )
        self._state.exclusions = result
        self._state.add_log("SUCCESS", f"Exclusión IGNORAR agregada: págs {desde}-{hasta}")
        self.exclusions_updated.emit()

    def remove_exclusion(self, excl_id: str):
        result = self._container.gestionar_exclusiones.eliminar_exclusion(
            self._state.exclusions, excl_id,
        )
        self._state.exclusions = result
        self._state.add_log("INFO", f"Exclusión {excl_id} eliminada.")
        self.exclusions_updated.emit()

    def add_segmento(self, folio_inicio: str, pag_pdf_inicio: int):
        seg = {"folio_inicio": folio_inicio, "pag_pdf_inicio": pag_pdf_inicio}
        self._state.segmentos = self._state.segmentos + [seg]
        self._state.add_log("SUCCESS", f"Segmento agregado: {folio_inicio} → pág {pag_pdf_inicio}")
        self.exclusions_updated.emit()
