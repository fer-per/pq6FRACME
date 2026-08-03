"""
Estado global observable de la aplicación (ViewModel principal).

Centraliza todo el estado reactivo usando señales Qt.
Las vistas se suscriben a las señales para actualizarse automáticamente.
"""
import logging
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from src.domain.entities import (
    InventoryRecord,
    ExclusionRule,
    SugerenciaCorreccion,
    SystemLog,
)

logger = logging.getLogger(__name__)


class AppStateVM(QObject):
    """
    Estado global de la aplicación como ViewModel observable.

    Emite señales Qt cuando cambian los datos para que las vistas
    se actualicen de forma reactiva.
    """

    # ─── Señales ─────────────────────────────────────────────
    records_changed = Signal()
    exclusions_changed = Signal()
    suggestions_changed = Signal()
    logs_changed = Signal()
    pdf_changed = Signal()
    config_changed = Signal()
    session_changed = Signal()
    theme_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ─── Rutas de archivos ───────────────────────────────
        self._excel_path: Optional[str] = None
        self._pdf_path: Optional[str] = None
        self._output_dir: Optional[str] = None

        # ─── Datos del inventario ────────────────────────────
        self._records: List[InventoryRecord] = []
        self._exclusions: List[ExclusionRule] = []
        self._suggestions: List[SugerenciaCorreccion] = []
        self._logs: List[SystemLog] = []

        # ─── Configuración de mapeo ──────────────────────────
        self._fila_datos_inicio: int = 0
        self._fila_datos_auto: bool = True
        self._fila_inicio: int = 0
        self._fila_fin: int = 0
        self._folio_inicio: str = ""
        self._pag_pdf_inicio: int = 0
        self._segmentos: list = []
        self._overrides: dict = {}
        self._page_map: dict = {}
        self._active_pages: list = []

        # ─── Estado del PDF ──────────────────────────────────
        self._pdf_current_page: int = 1
        self._pdf_total_pages: int = 0
        self._pdf_zoom: int = 100
        self._dual_view_active: bool = True

        # ─── Metadatos ───────────────────────────────────────
        self._acervo_num: str = "7"
        self._siglo: str = ""

        # ─── Tema ────────────────────────────────────────────
        self._dark_mode: bool = False

    # ═══ PROPIEDADES CON SEÑALES ═══════════════════════════════

    @property
    def excel_path(self) -> Optional[str]:
        return self._excel_path

    @excel_path.setter
    def excel_path(self, value: Optional[str]):
        self._excel_path = value
        self.session_changed.emit()

    @property
    def pdf_path(self) -> Optional[str]:
        return self._pdf_path

    @pdf_path.setter
    def pdf_path(self, value: Optional[str]):
        self._pdf_path = value
        self.pdf_changed.emit()

    @property
    def output_dir(self) -> Optional[str]:
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value: Optional[str]):
        self._output_dir = value

    @property
    def records(self) -> List[InventoryRecord]:
        return self._records

    @records.setter
    def records(self, value: List[InventoryRecord]):
        self._records = value
        self.records_changed.emit()

    @property
    def exclusions(self) -> List[ExclusionRule]:
        return self._exclusions

    @exclusions.setter
    def exclusions(self, value: List[ExclusionRule]):
        self._exclusions = value
        self.exclusions_changed.emit()

    @property
    def suggestions(self) -> List[SugerenciaCorreccion]:
        return self._suggestions

    @suggestions.setter
    def suggestions(self, value: List[SugerenciaCorreccion]):
        self._suggestions = value
        self.suggestions_changed.emit()

    @property
    def logs(self) -> List[SystemLog]:
        return self._logs

    @property
    def pdf_current_page(self) -> int:
        return self._pdf_current_page

    @pdf_current_page.setter
    def pdf_current_page(self, value: int):
        self._pdf_current_page = max(1, min(value, self._pdf_total_pages or 1))
        self.pdf_changed.emit()

    @property
    def pdf_total_pages(self) -> int:
        return self._pdf_total_pages

    @pdf_total_pages.setter
    def pdf_total_pages(self, value: int):
        self._pdf_total_pages = value
        self.pdf_changed.emit()

    @property
    def pdf_zoom(self) -> int:
        return self._pdf_zoom

    @pdf_zoom.setter
    def pdf_zoom(self, value: int):
        self._pdf_zoom = max(25, min(value, 400))
        self.pdf_changed.emit()

    @property
    def dual_view_active(self) -> bool:
        return self._dual_view_active

    @dual_view_active.setter
    def dual_view_active(self, value: bool):
        self._dual_view_active = value

    @property
    def fila_datos_inicio(self) -> int:
        return self._fila_datos_inicio

    @fila_datos_inicio.setter
    def fila_datos_inicio(self, value: int):
        self._fila_datos_inicio = max(0, value)
        self.config_changed.emit()

    @property
    def fila_datos_auto(self) -> bool:
        return self._fila_datos_auto

    @fila_datos_auto.setter
    def fila_datos_auto(self, value: bool):
        self._fila_datos_auto = value

    @property
    def fila_inicio(self) -> int:
        return self._fila_inicio

    @fila_inicio.setter
    def fila_inicio(self, value: int):
        self._fila_inicio = max(0, value)
        self.config_changed.emit()

    @property
    def fila_fin(self) -> int:
        return self._fila_fin

    @fila_fin.setter
    def fila_fin(self, value: int):
        self._fila_fin = value
        self.config_changed.emit()

    @property
    def pag_pdf_inicio(self) -> int:
        return self._pag_pdf_inicio

    @pag_pdf_inicio.setter
    def pag_pdf_inicio(self, value: int):
        self._pag_pdf_inicio = max(0, value)
        self.config_changed.emit()

    @property
    def folio_inicio(self) -> str:
        return self._folio_inicio

    @folio_inicio.setter
    def folio_inicio(self, value: str):
        self._folio_inicio = value
        self.config_changed.emit()

    @property
    def segmentos(self) -> list:
        return self._segmentos

    @segmentos.setter
    def segmentos(self, value: list):
        self._segmentos = value
        self.config_changed.emit()

    @property
    def page_map(self) -> dict:
        return self._page_map

    @page_map.setter
    def page_map(self, value: dict):
        self._page_map = value
        self.config_changed.emit()

    @property
    def active_pages(self) -> list:
        return self._active_pages

    @active_pages.setter
    def active_pages(self, value: list):
        self._active_pages = value

    @property
    def acervo_num(self) -> str:
        return self._acervo_num

    @acervo_num.setter
    def acervo_num(self, value: str):
        self._acervo_num = value

    @property
    def dark_mode(self) -> bool:
        return self._dark_mode

    @dark_mode.setter
    def dark_mode(self, value: bool):
        self._dark_mode = bool(value)
        self.theme_changed.emit(self._dark_mode)

    # ═══ MÉTODOS ═══════════════════════════════════════════════

    def add_log(self, tipo: str, mensaje: str):
        """Agrega una entrada de log y emite señal."""
        log = SystemLog.now(tipo, mensaje)
        self._logs.append(log)
        self.logs_changed.emit()
        logger.info("[%s] %s", tipo, mensaje)

    def clear_logs(self):
        """Limpia todos los logs."""
        self._logs.clear()
        self.logs_changed.emit()

    def to_dict(self) -> dict:
        """Serializa el estado completo para guardado de sesión."""
        return {
            "excel_path": self._excel_path,
            "pdf_path": self._pdf_path,
            "output_dir": self._output_dir,
            "fila_datos_inicio": self._fila_datos_inicio,
            "fila_inicio": self._fila_inicio,
            "fila_fin": self._fila_fin,
            "folio_inicio": self._folio_inicio,
            "pag_pdf_inicio": self._pag_pdf_inicio,
            "pdf_total_pages": self._pdf_total_pages,
            "acervo_num": self._acervo_num,
            "segmentos": self._segmentos,
            "overrides": self._overrides,
            "page_map": self._page_map,
            "active_pages": self._active_pages,
            "records": self._records,
            "exclusions": self._exclusions,
            "suggestions": self._suggestions,
        }

    def from_dict(self, data: dict):
        """Restaura el estado desde un diccionario de sesión."""
        self._excel_path = data.get("excel_path")
        self._pdf_path = data.get("pdf_path")
        self._output_dir = data.get("output_dir")
        self._fila_datos_inicio = data.get("fila_datos_inicio", 0)
        self._fila_inicio = data.get("fila_inicio", 0)
        self._fila_fin = data.get("fila_fin", 0)
        self._folio_inicio = data.get("folio_inicio", "")
        self._pag_pdf_inicio = data.get("pag_pdf_inicio", 0)
        self._pdf_total_pages = data.get("pdf_total_pages", 0)
        self._acervo_num = data.get("acervo_num", "7")
        self._segmentos = data.get("segmentos", [])
        self._overrides = data.get("overrides", {})
        self._page_map = data.get("page_map", {})
        self._active_pages = data.get("active_pages", [])
        self._records = data.get("records", [])
        self._exclusions = data.get("exclusions", [])
        self._suggestions = data.get("suggestions", [])

        # Emitir todas las señales
        self.records_changed.emit()
        self.exclusions_changed.emit()
        self.suggestions_changed.emit()
        self.pdf_changed.emit()
        self.config_changed.emit()
        self.session_changed.emit()
