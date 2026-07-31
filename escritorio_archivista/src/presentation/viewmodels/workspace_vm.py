"""
ViewModel del Workspace.

Orquesta la carga de archivos Excel y PDF,
la configuración de mapeo y la previsualización.
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM

logger = logging.getLogger(__name__)


class LoadInventoryWorker(QRunnable):
    """Worker para cargar inventario en segundo plano."""

    class Signals(QObject):
        finished = Signal(object)  # ResultadoCarga
        error = Signal(str)

    def __init__(self, container, state):
        super().__init__()
        self.signals = self.Signals()
        self._container = container
        self._state = state

    @Slot()
    def run(self):
        try:
            result = self._container.cargar_inventario.ejecutar(
                ruta_excel=self._state.excel_path,
                fila_inicio=self._state.fila_inicio,
                fila_fin=self._state.fila_fin,
                folio_inicio=self._state.folio_inicio,
                pag_pdf_inicio=self._state.pag_pdf_inicio,
                segmentos=self._state.segmentos or None,
                exclusiones=self._state.exclusions or None,
                page_map=self._state.page_map or None,
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class WorkspaceVM(QObject):
    """ViewModel para la vista de Workspace."""

    loading_started = Signal()
    loading_finished = Signal(object)
    loading_error = Signal(str)
    pdf_loaded = Signal(int)  # total pages

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._container = container
        self._state = state
        self._thread_pool = QThreadPool()

    def set_excel_path(self, path: str):
        """Establece la ruta del Excel y carga el inventario."""
        self._state.excel_path = path
        self._state.add_log("INFO", f"Excel seleccionado: {path}")
        self.load_inventory()

    def set_pdf_path(self, path: str):
        """Establece la ruta del PDF."""
        self._state.pdf_path = path
        self._state.add_log("INFO", f"PDF seleccionado: {path}")

        try:
            total = self._container.pdf_service.obtener_total_paginas(path)
            self._state.pdf_total_pages = total
            self._state.add_log("SUCCESS", f"PDF cargado: {total} páginas.")
            self.pdf_loaded.emit(total)
        except Exception as e:
            self._state.add_log("ERR", f"Error al cargar PDF: {e}")

    def load_inventory(self):
        """Carga el inventario en segundo plano."""
        if not self._state.excel_path:
            return

        self.loading_started.emit()
        self._state.add_log("INFO", "Cargando inventario...")

        worker = LoadInventoryWorker(self._container, self._state)
        worker.signals.finished.connect(self._on_load_finished)
        worker.signals.error.connect(self._on_load_error)
        self._thread_pool.start(worker)

    def _on_load_finished(self, result):
        """Callback cuando el inventario termina de cargarse."""
        self._state.records = result.records
        self._state.suggestions = result.suggestions

        if result.metadata.get("acervo_detectado"):
            self._state.acervo_num = result.metadata["acervo_detectado"]

        self._state.add_log(
            "SUCCESS",
            f"Inventario cargado: {len(result.records)} registros, "
            f"{result.metadata.get('errores_count', 0)} errores."
        )
        self.loading_finished.emit(result)

    def _on_load_error(self, error_msg: str):
        """Callback cuando hay error en la carga."""
        self._state.add_log("ERR", f"Error cargando inventario: {error_msg}")
        self.loading_error.emit(error_msg)

    def update_config(self, fila_inicio: int, fila_fin: int,
                      folio_inicio: str, pag_pdf_inicio: int):
        """Actualiza la configuración de mapeo y recarga."""
        self._state.fila_inicio = fila_inicio
        self._state.fila_fin = fila_fin
        self._state.folio_inicio = folio_inicio
        self._state.pag_pdf_inicio = pag_pdf_inicio
        self._state.add_log("INFO", "Configuración actualizada.")

        if self._state.excel_path:
            self.load_inventory()
