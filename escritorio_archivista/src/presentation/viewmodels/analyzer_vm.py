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
                active_pages=self._state.active_pages or None,
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

    def apply_correction(self, record_id: str, field: str, new_value: str):
        """Aplica una corrección de un campo específico a un registro."""
        for record in self._state.records:
            if record.id == record_id:
                setattr(record, field, new_value)
                record.estado = "VALIDADO"
                self._state.add_log(
                    "SUCCESS",
                    f"Corrección aplicada a {record_id} ({field}): {new_value}"
                )
                break
        # Recalcular pg_pdf de inmediato (respeta pg_pdf_manual) para que la
        # grilla muestre el rango aplicado sin esperar el análisis asíncrono.
        self._state.recalcular_pg_pdf()
        self._state.records_changed.emit()
        self.correction_applied.emit()
        self.guardar_en_excel()

    def apply_pagination(self, record_id: str, comparte_hoja: bool,
                         pg_pdf_manual: str):
        """Aplica la configuración de paginación PDF a un registro.

        ``comparte_hoja`` hace que el fragmento arranque en la misma página
        donde terminó el registro anterior. ``pg_pdf_manual`` fuerza un rango
        de páginas específico.
        """
        for record in self._state.records:
            if record.id == record_id:
                record.comparte_hoja = bool(comparte_hoja)
                record.pg_pdf_manual = pg_pdf_manual or ""
                record.estado = "VALIDADO"
                if record.pg_pdf_manual:
                    self._state.add_log(
                        "SUCCESS",
                        f"Paginación manual aplicada a {record_id}: "
                        f"{record.pg_pdf_manual}"
                    )
                else:
                    self._state.add_log(
                        "SUCCESS",
                        f"Compartir hoja {'activado' if comparte_hoja else 'desactivado'} "
                        f"en {record_id}"
                    )
                break
        # Recalcular pg_pdf de inmediato (respeta pg_pdf_manual) para que la
        # grilla muestre el rango aplicado sin esperar el análisis asíncrono.
        self._state.recalcular_pg_pdf()
        self._state.records_changed.emit()
        self.correction_applied.emit()
        self.guardar_en_excel()

    def guardar_en_excel(self) -> bool:
        """Escribe las correcciones de vuelta al Excel cargado."""
        ruta = self._state.excel_path
        if not ruta:
            logger.debug("Guardado automático omitido: no hay Excel cargado.")
            return False
        try:
            total = self._container.excel_repo.guardar_registros(
                ruta, self._state.fila_datos_inicio, list(self._state.records)
            )
            self._state.add_log(
                "SUCCESS", f"Guardado en Excel: {total} celda(s) actualizada(s)."
            )
            return True
        except Exception as e:
            logger.error("Error guardando en Excel: %s", e)
            self._state.add_log("ERR", f"No se pudo guardar en Excel: {e}")
            return False

    def apply_changes(self, record_id: str, cambios: dict):
        """Aplica los cambios combinados del modal de corrección.

        ``cambios`` incluye opcionalmente el campo editado (``field``/
        ``value``) y siempre la paginación (``comparte_hoja``,
        ``pg_pdf_manual``).
        """
        comparte_hoja = bool(cambios.get("comparte_hoja", False))
        pg_pdf_manual = cambios.get("pg_pdf_manual", "") or ""
        field = cambios.get("field")
        value = cambios.get("value")

        for record in self._state.records:
            if record.id == record_id:
                if field and value:
                    setattr(record, field, value)
                record.comparte_hoja = comparte_hoja
                record.pg_pdf_manual = pg_pdf_manual
                record.estado = "VALIDADO"
                partes = []
                if field and value:
                    partes.append(f"{field}: {value}")
                if pg_pdf_manual:
                    partes.append(f"Pág. PDF manual: {pg_pdf_manual}")
                if comparte_hoja:
                    partes.append("comparte hoja")
                detalle = "; ".join(partes) if partes else "sin cambios"
                self._state.add_log("SUCCESS", f"Corrección aplicada a {record_id}: {detalle}")
                break

        # Recalcular pg_pdf de inmediato (respeta pg_pdf_manual) para que la
        # grilla muestre el rango aplicado sin esperar el análisis asíncrono.
        self._state.recalcular_pg_pdf()
        self._state.records_changed.emit()
        self.correction_applied.emit()
        self.guardar_en_excel()
