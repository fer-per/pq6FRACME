"""
ViewModel del Analizador.
"""
import logging
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot
from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM

logger = logging.getLogger(__name__)


class AnalyzeWorker(QRunnable):
    class Signals(QObject):
        finished = Signal(object)
        error = Signal(str)

    def __init__(self, container, state):
        super().__init__()
        self.signals = self.Signals()
        self._container = container
        self._state = state

    @Slot()
    def run(self):
        try:
            result = self._container.analizar_datos.ejecutar(
                records=list(self._state.records),
                exclusions=self._state.exclusions or None,
                segmentos=self._state.segmentos or None,
                page_map=self._state.page_map or None,
                pag_pdf_inicio=self._state.pag_pdf_inicio,
                total_pdf_pages=self._state.pdf_total_pages,
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class AnalyzerVM(QObject):
    """ViewModel para la vista del analizador."""

    analysis_started = Signal()
    analysis_finished = Signal(object)
    analysis_error = Signal(str)
    correction_applied = Signal()

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._container = container
        self._state = state
        self._thread_pool = QThreadPool()

    def run_analysis(self):
        """Ejecuta el análisis completo en segundo plano."""
        if not self._state.records:
            self._state.add_log("WARN", "No hay registros para analizar.")
            return

        self.analysis_started.emit()
        self._state.add_log("INFO", "Ejecutando análisis...")

        worker = AnalyzeWorker(self._container, self._state)
        worker.signals.finished.connect(self._on_analysis_finished)
        worker.signals.error.connect(self._on_analysis_error)
        self._thread_pool.start(worker)

    def _on_analysis_finished(self, result):
        self._state.records = result.records
        self._state.suggestions = result.suggestions
        self._state.add_log(
            "SUCCESS",
            f"Análisis completado: {result.metadata.get('total_errores', 0)} incidencias."
        )
        self.analysis_finished.emit(result)

    def _on_analysis_error(self, error_msg):
        self._state.add_log("ERR", f"Error en análisis: {error_msg}")
        self.analysis_error.emit(error_msg)

    def apply_correction(self, record_id: str, new_folios: str):
        """Aplica una corrección de folios a un registro."""
        for record in self._state.records:
            if record.id == record_id:
                record.folios = new_folios
                record.estado = "VALIDADO"
                self._state.add_log(
                    "SUCCESS",
                    f"Corrección aplicada a {record_id}: {new_folios}"
                )
                break
        self._state.records_changed.emit()
        self.correction_applied.emit()
