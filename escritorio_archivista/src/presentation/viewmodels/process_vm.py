"""ViewModel de Procesamiento y Fragmentación."""
import logging
import os
from typing import Optional

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot
from src.application.container import Container
from src.presentation.constants import DEFAULT_OUTPUT_DIR
from src.presentation.viewmodels.app_state import AppStateVM

logger = logging.getLogger(__name__)


def resolver_directorio_salida(base_dir: str) -> str:
    """
    Devuelve la primera ruta disponible para una corrida de fragmentación.

    Si la carpeta base ya existe (p. ej. una fragmentación previa), se
    numera con sufijo de Windows: ``base``, ``base (1)``, ``base (2)``, ...
    """
    if not os.path.exists(base_dir):
        return base_dir
    counter = 1
    while os.path.exists(f"{base_dir} ({counter})"):
        counter += 1
    return f"{base_dir} ({counter})"


def resolver_directorio_corrida(
    base_dir: str, default_dir: str = DEFAULT_OUTPUT_DIR
) -> str:
    """
    Devuelve el directorio que usará una corrida de fragmentación.

    Solo el directorio predeterminado se numera si ya existe
    (``output``, ``output (1)``, ``output (2)``, ...). Una carpeta
    elegida por el usuario se usa tal cual, sin numerarla.
    """
    if os.path.normpath(base_dir) == os.path.normpath(default_dir):
        return resolver_directorio_salida(base_dir)
    return base_dir


class FragmentWorker(QRunnable):
    class Signals(QObject):
        progress = Signal(int, int, str)  # current, total, record_id
        finished = Signal(object)
        error = Signal(str)

    def __init__(self, container, state, output_dir: str):
        super().__init__()
        self.signals = self.Signals()
        self._container = container
        self._state = state
        self._output_dir = output_dir

    @Slot()
    def run(self):
        try:
            os.makedirs(self._output_dir, exist_ok=True)
            result = self._container.fragmentar_pdf.ejecutar(
                records=list(self._state.records),
                pdf_path=self._state.pdf_path,
                output_dir=self._output_dir,
                acervo_num=self._state.acervo_num,
                pag_pdf_inicio=self._state.pag_pdf_inicio,
                segmentos=self._state.segmentos or None,
                exclusiones=self._state.exclusions or None,
                page_map=self._state.page_map or None,
                active_pages=self._state.active_pages or None,
                total_pdf_pages=self._state.pdf_total_pages,
                on_progress=lambda c, t, r: self.signals.progress.emit(c, t, r),
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class ProcessVM(QObject):
    """ViewModel para fragmentación."""
    fragment_started = Signal()
    fragment_progress = Signal(int, int, str)
    fragment_finished = Signal(object)
    fragment_error = Signal(str)

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._container = container
        self._state = state
        self._thread_pool = QThreadPool()

    def start_fragmentation(self):
        if not self._state.pdf_path:
            self._state.add_log("ERR", "No hay PDF cargado.")
            return
        if not self._state.records:
            self._state.add_log("ERR", "No hay registros cargados.")
            return

        base_dir = self._state.output_dir or DEFAULT_OUTPUT_DIR
        output_dir = resolver_directorio_corrida(base_dir)
        self._state.add_log(
            "INFO", f"Directorio de salida de esta corrida: {output_dir}"
        )

        self.fragment_started.emit()
        self._state.add_log("INFO", "Iniciando fragmentación...")

        worker = FragmentWorker(self._container, self._state, output_dir)
        worker.signals.progress.connect(
            lambda c, t, r: self.fragment_progress.emit(c, t, r)
        )
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)
        self._thread_pool.start(worker)

    def _on_finished(self, result):
        self._state.records = result.archivos_creados and self._state.records or self._state.records
        self._state.add_log(
            "SUCCESS",
            f"Fragmentación completada: {result.total_exitos} éxitos, "
            f"{result.total_fallos} fallos."
        )
        self.fragment_finished.emit(result)

    def _on_error(self, error_msg):
        self._state.add_log("ERR", f"Error en fragmentación: {error_msg}")
        self.fragment_error.emit(error_msg)

    def set_output_dir(self, path: str):
        self._state.output_dir = path
        self._state.add_log("INFO", f"Directorio de salida: {path}")
