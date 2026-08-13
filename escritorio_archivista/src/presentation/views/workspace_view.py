"""
Vista de Workspace — Paso 1-2-3: carga de archivos, mapeo, previsualización.

Columnas muestran Fila Excel (no ID interno). Click en fila navega al PDF.
"""
import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QFileDialog, QGroupBox, QGridLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QSize

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.workspace_vm import WorkspaceVM
from src.presentation.widgets.data_table import DataTable
from src.presentation.widgets.search_bar import SearchBar
from src.presentation.constants import (
    ICON_EXCEL, ICON_PDF,
    ICON_SAVE, ICON_ANALYZER, TOOLBAR_ICON_SIZE,
)
from src.presentation.theme.icons import theme_icon, white_icon, tinted_pixmap
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class DropZone(QWidget):
    """Tarjeta de carga: cabecera con el módulo y zona de arrastrar/soltar.

    La cabecera identifica el tipo de archivo (Excel o PDF) y el cuerpo
    muestra el estado de carga; al cargarse un archivo se exhibe el nombre
    con elisión profesional y la ruta completa como tooltip.

    El ícono del documento (``icon_path``) es una silueta que se recoloriza
    según el tema activo de la aplicación.
    """

    ICON_DISPLAY_SIZE = QSize(35, 35)

    def __init__(self, icon_path: str, title: str,
                 extensions: str, parent=None):
        super().__init__(parent)
        self._extensions = extensions
        self._title = title
        self._icon_path = icon_path
        self._file_path = None
        self._filename = None
        self._hovered = False
        self._palette = get_palette()

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Cabecera con el nombre del módulo
        title_bar = QWidget()
        title_bar.setFixedHeight(34)
        self._title_bar = title_bar
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)

        self._title_label = QLabel(title)
        self._title_label.setFont(get_font("body_sm_bold"))
        title_layout.addWidget(self._title_label)
        title_layout.addStretch()
        outer.addWidget(title_bar)

        # Cuerpo: ícono grande + estado + pista
        self._body = QWidget()
        body_layout = QVBoxLayout(self._body)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.setContentsMargins(12, 18, 12, 18)
        body_layout.setSpacing(4)

        self._icon_label = QLabel()
        self._icon_label.setFixedHeight(self.ICON_DISPLAY_SIZE.height())
        self._icon_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent;")
        self._update_icon(False)
        body_layout.addWidget(self._icon_label)

        self._status_label = QLabel("Sin archivo cargado")
        self._status_label.setFont(get_font("body_sm_bold"))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(
            f"color: {self._palette['text_primary']}; background: transparent;"
        )
        body_layout.addWidget(self._status_label)

        self._hint_label = QLabel(f"Arrastra o haz clic aqu\u00ED ({extensions})")
        self._hint_label.setFont(get_font("body_xs"))
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_label.setStyleSheet(
            f"color: {self._palette['text_disabled']}; background: transparent;"
        )
        body_layout.addWidget(self._hint_label)

        outer.addWidget(self._body, stretch=1)

        self._update_style(False)

    def _update_style(self, hover: bool):
        self._hovered = hover
        p = self._palette
        self._title_bar.setStyleSheet(
            f"background-color: {p['primary']}; "
            f"border-top-left-radius: 8px; border-top-right-radius: 8px;"
        )
        self._title_label.setStyleSheet(
            f"color: {p['on_primary']}; background: transparent;"
        )
        border_color = p['primary'] if hover else p['outline_variant']
        bg = p['selected_bg'] if hover else p['surface']
        self._body.setStyleSheet(
            f"background-color: {bg}; "
            f"border: 2px dashed {border_color}; "
            f"border-top: none; "
            f"border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;"
        )

    def _update_icon(self, dark: bool):
        """Muestra el ícono del documento recolorizado según el tema."""
        pixmap = tinted_pixmap(self._icon_path, dark)
        if pixmap.isNull():
            return
        self._icon_label.setPixmap(
            pixmap.scaled(
                self.ICON_DISPLAY_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _elide(self, text: str, max_width: int) -> str:
        fm = self._status_label.fontMetrics()
        return fm.elidedText(text, Qt.TextElideMode.ElideMiddle, max_width)

    def _refresh_texts(self):
        if self._file_path:
            status_w = max(120, self._status_label.width() - 8)
            hint_w = max(120, self._hint_label.width() - 8)
            self._status_label.setText("\u2713 " + self._elide(self._filename, status_w))
            self._status_label.setToolTip(self._filename)
            self._hint_label.setText(self._elide(self._file_path, hint_w))
            self._hint_label.setToolTip(self._file_path)
        else:
            self._status_label.setText("Sin archivo cargado")
            self._status_label.setToolTip("")
            self._hint_label.setText(
                f"Arrastra o haz clic aqu\u00ED ({self._extensions})"
            )
            self._hint_label.setToolTip("")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_texts()

    def apply_theme(self, dark: bool):
        """Reaplica el estilo al cambiar el tema."""
        self._palette = get_palette(dark)
        self._update_icon(dark)
        self._status_label.setStyleSheet(
            f"color: {self._palette['text_primary']}; background: transparent;"
        )
        self._hint_label.setStyleSheet(
            f"color: {self._palette['text_disabled']}; background: transparent;"
        )
        self._update_style(self._hovered)

    def mousePressEvent(self, event):
        self._select_file()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._update_style(True)

    def dragLeaveEvent(self, event):
        self._update_style(False)

    def dropEvent(self, event):
        self._update_style(False)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.set_file(path)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo", "",
            f"Archivos ({self._extensions})"
        )
        if path:
            self.set_file(path)

    def set_file(self, path: str):
        self._file_path = path
        self._filename = os.path.basename(path)
        self._refresh_texts()
        self._update_style(False)

    @property
    def file_path(self):
        return self._file_path


class WorkspaceView(QWidget):
    """
    Vista de Workspace con los 3 pasos.
    Click en fila del inventario navega a la página PDF asignada.
    """

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._state = state
        self._container = container
        self._vm = WorkspaceVM(container, state)
        self._palette = get_palette()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # ─── PASO 1: Carga de Archivos ──────────────────────
        step1 = QGroupBox("PASO 1 \u2014 Carga de Archivos")
        step1_layout = QHBoxLayout(step1)
        step1_layout.setSpacing(16)

        self._excel_drop = DropZone(
            ICON_EXCEL, "INVENTARIO EXCEL", "*.xlsx"
        )
        step1_layout.addWidget(self._excel_drop, stretch=1)

        self._pdf_drop = DropZone(
            ICON_PDF, "PDF ORIGINAL", "*.pdf"
        )
        step1_layout.addWidget(self._pdf_drop, stretch=1)

        layout.addWidget(step1)

        # ─── PASO 2: Parámetros de Mapeo ────────────────────
        step2 = QGroupBox("PASO 2 \u2014 Parámetros de Mapeo")
        step2_grid = QGridLayout(step2)
        step2_grid.setSpacing(12)

        step2_grid.addWidget(QLabel("Fila inicio de datos:"), 0, 0)
        self._fila_datos_inicio_spin = QSpinBox()
        self._fila_datos_inicio_spin.setRange(0, 99999)
        self._fila_datos_inicio_spin.setValue(self._state.fila_datos_inicio)
        self._fila_datos_inicio_spin.setFixedWidth(80)
        step2_grid.addWidget(self._fila_datos_inicio_spin, 0, 1)

        step2_grid.addWidget(QLabel("Inicia desde fila:"), 0, 2)
        self._fila_inicio_spin = QSpinBox()
        self._fila_inicio_spin.setRange(0, 99999)
        self._fila_inicio_spin.setValue(self._state.fila_inicio)
        self._fila_inicio_spin.setFixedWidth(80)
        step2_grid.addWidget(self._fila_inicio_spin, 0, 3)

        step2_grid.addWidget(QLabel("Termina en fila:"), 0, 4)
        self._fila_fin_spin = QSpinBox()
        self._fila_fin_spin.setRange(0, 99999)
        self._fila_fin_spin.setValue(self._state.fila_fin)
        self._fila_fin_spin.setFixedWidth(80)
        step2_grid.addWidget(self._fila_fin_spin, 0, 5)

        step2_grid.addWidget(QLabel("Folio Inicio Protocolo:"), 0, 6)
        self._folio_inicio_input = QLineEdit(self._state.folio_inicio)
        self._folio_inicio_input.setFixedWidth(80)
        step2_grid.addWidget(self._folio_inicio_input, 0, 7)

        step2_grid.addWidget(QLabel("Pág. PDF Inicio:"), 1, 0)
        self._pag_pdf_spin = QSpinBox()
        self._pag_pdf_spin.setRange(0, 99999)
        self._pag_pdf_spin.setValue(self._state.pag_pdf_inicio)
        self._pag_pdf_spin.setFixedWidth(80)
        step2_grid.addWidget(self._pag_pdf_spin, 1, 1)

        self._save_config_btn = QPushButton(" Guardar Cambios")
        self._save_config_btn.setFixedHeight(32)
        self._save_config_btn.setIcon(white_icon(ICON_SAVE))
        self._save_config_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        step2_grid.addWidget(self._save_config_btn, 1, 6, 1, 2)

        layout.addWidget(step2)

        # ─── PASO 3: Previsualización ───────────────────────
        step3 = QGroupBox("PASO 3 \u2014 Previsualización del Inventario")
        step3_layout = QVBoxLayout(step3)

        # Barra de búsqueda + info + botón expandir
        top_bar = QHBoxLayout()
        self._search = SearchBar(placeholder="Buscar en inventario...")
        top_bar.addWidget(self._search, stretch=1)

        self._count_label = QLabel("0 registros")
        self._count_label.setFont(get_font("body_sm"))
        self._count_label.setStyleSheet(f"color: {self._palette['text_secondary']};")
        top_bar.addWidget(self._count_label)

        self._expand_btn = QPushButton("Analizador \u2192")
        self._expand_btn.setProperty("flat", True)
        self._expand_btn.setFixedHeight(32)
        self._expand_btn.setIcon(theme_icon(ICON_ANALYZER, False))
        self._expand_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        top_bar.addWidget(self._expand_btn)
        step3_layout.addLayout(top_bar)

        # Tabla de datos — sin columna ID, usa Fila Excel
        self._table = DataTable(
            columns=["Fila", "Registro", "Escribano", "Protocolo",
                      "Folios", "Pág. PDF", "Fecha Inicio", "Título",
                      "Interesado 1", "Interesado 2", "Estado"],
            field_map=["fila", "registro", "escribano", "protocolo",
                        "folios", "pg_pdf", "fecha_inicio", "titulo",
                        "interesado1", "interesado2", "estado"],
        )
        step3_layout.addWidget(self._table)

        # Tip
        tip = QLabel("\u2139  Haz clic en una fila para navegar a la página PDF correspondiente")
        tip.setFont(get_font("body_xs"))
        tip.setStyleSheet(f"color: {self._palette['text_disabled']};")
        self._tip_label = tip
        step3_layout.addWidget(tip)

        layout.addWidget(step3, stretch=1)

    def _connect_signals(self):
        # Drop zones
        self._excel_drop.mousePressEvent = self._on_excel_click
        self._pdf_drop.mousePressEvent = self._on_pdf_click

        # Config
        self._save_config_btn.clicked.connect(self._on_save_config)

        # Búsqueda
        self._search.search_changed.connect(self._table.filter_rows)
        self._search.search_cleared.connect(self._table.clear_filter)

        # Expand → navegar a analyzer
        self._expand_btn.clicked.connect(self._on_expand)

        # Table row click → navegar PDF
        self._table.row_clicked.connect(self._on_row_clicked)

        # ViewModel signals
        self._vm.loading_finished.connect(self._on_loading_finished)
        self._vm.loading_error.connect(self._on_loading_error)

        # State signals → actualizar tabla
        self._state.records_changed.connect(self._refresh_table)

    def _on_excel_click(self, event):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar inventario Excel", "", "Excel (*.xlsx *.xls)"
        )
        if path:
            self._excel_drop.set_file(path)
            self._vm.set_excel_path(path)

    def _on_pdf_click(self, event):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "PDF (*.pdf)"
        )
        if path:
            self._pdf_drop.set_file(path)
            self._vm.set_pdf_path(path)

    def _on_save_config(self):
        self._vm.update_config(
            fila_datos_inicio=self._fila_datos_inicio_spin.value(),
            fila_inicio=self._fila_inicio_spin.value(),
            fila_fin=self._fila_fin_spin.value(),
            folio_inicio=self._folio_inicio_input.text(),
            pag_pdf_inicio=self._pag_pdf_spin.value(),
        )

    def _on_expand(self):
        from src.presentation.constants import ViewId
        main_window = self.window()
        if hasattr(main_window, 'navigate_to'):
            main_window.navigate_to(ViewId.ANALYZER)

    def _on_row_clicked(self, row: int, record):
        """Al hacer clic en una fila, navegar a la página PDF asignada."""
        if not hasattr(record, 'pg_pdf') or not record.pg_pdf:
            return
        try:
            first_page = int(record.pg_pdf.split('-')[0])
            self._state.pdf_current_page = first_page
            # Renderizar la página inmediatamente
            main_window = self.window()
            if hasattr(main_window, '_render_current_page'):
                main_window._render_current_page()
        except (ValueError, IndexError):
            pass

    def _on_loading_finished(self, result):
        self._fila_datos_inicio_spin.setValue(self._state.fila_datos_inicio)
        self._fila_inicio_spin.setValue(self._state.fila_inicio)
        self._fila_fin_spin.setValue(self._state.fila_fin)
        self._pag_pdf_spin.setValue(self._state.pag_pdf_inicio)
        self._folio_inicio_input.setText(self._state.folio_inicio)
        self._refresh_table()

    def _on_loading_error(self, error_msg: str):
        pass

    def _refresh_table(self):
        records = self._state.records
        self._table.load_data(records)
        self._count_label.setText(f"{len(records)} registros")

    def refresh_from_state(self):
        """Refleja el estado cargado (p. ej. una configuración) en Paso 1 y 2
        y recarga el Excel y PDF con esos parámetros de mapeo."""
        if self._state.excel_path and os.path.isfile(self._state.excel_path):
            self._excel_drop.set_file(self._state.excel_path)
        if self._state.pdf_path and os.path.isfile(self._state.pdf_path):
            self._pdf_drop.set_file(self._state.pdf_path)

        self._fila_datos_inicio_spin.setValue(self._state.fila_datos_inicio)
        self._fila_inicio_spin.setValue(self._state.fila_inicio)
        self._fila_fin_spin.setValue(self._state.fila_fin)
        self._pag_pdf_spin.setValue(self._state.pag_pdf_inicio)
        self._folio_inicio_input.setText(self._state.folio_inicio)
        self._refresh_table()

        # Recargar el inventario desde el Excel solo si no hay registros
        # restaurados de la sesión guardada. Cargar de nuevo crearía
        # registros SIN las correcciones manuales (pg_pdf_manual,
        # comparte_hoja, estados) y la fragmentación generaría páginas viejas.
        if (
            self._state.excel_path
            and os.path.isfile(self._state.excel_path)
            and not self._state.records
        ):
            self._vm.load_inventory()
        if self._state.pdf_path and os.path.isfile(self._state.pdf_path):
            self._vm.set_pdf_path(self._state.pdf_path)

    def apply_theme(self, dark: bool):
        """Reaplica los estilos dependientes del tema."""
        self._palette = get_palette(dark)
        self._excel_drop.apply_theme(dark)
        self._pdf_drop.apply_theme(dark)
        self._save_config_btn.setIcon(white_icon(ICON_SAVE))
        self._search.apply_theme(dark)
        self._count_label.setStyleSheet(
            f"color: {self._palette['text_secondary']};"
        )
        self._tip_label.setStyleSheet(
            f"color: {self._palette['text_disabled']};"
        )
        self._table.apply_theme(dark)
