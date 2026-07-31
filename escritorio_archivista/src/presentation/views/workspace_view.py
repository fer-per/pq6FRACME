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
from PySide6.QtCore import Qt

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.workspace_vm import WorkspaceVM
from src.presentation.widgets.data_table import DataTable
from src.presentation.widgets.search_bar import SearchBar
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class DropZone(QWidget):
    """Zona de arrastrar y soltar / clic para seleccionar archivo."""

    def __init__(self, icon: str, label: str, extensions: str, parent=None):
        super().__init__(parent)
        self._extensions = extensions
        self._file_path = None
        self._palette = get_palette()

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel(icon)
        self._icon_label.setFont(get_font("icon_lg"))
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self._icon_label)

        self._text_label = QLabel(label)
        self._text_label.setFont(get_font("body"))
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setStyleSheet(
            f"color: {self._palette['text_secondary']}; background: transparent;"
        )
        layout.addWidget(self._text_label)

        self._hint_label = QLabel(f"Arrastra o haz clic ({extensions})")
        self._hint_label.setFont(get_font("body_xs"))
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_label.setStyleSheet(
            f"color: {self._palette['text_disabled']}; background: transparent;"
        )
        layout.addWidget(self._hint_label)

        self._update_style(False)

    def _update_style(self, hover: bool):
        p = self._palette
        border_color = p['primary'] if hover else p['outline_variant']
        bg = p['selected_bg'] if hover else p['surface']
        self.setStyleSheet(
            f"DropZone {{ background-color: {bg}; "
            f"border: 2px dashed {border_color}; border-radius: 10px; }}"
        )

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
        filename = os.path.basename(path)
        self._text_label.setText(f"\u2713 {filename}")
        self._hint_label.setText(path)
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

        self._excel_drop = DropZone("\u25A3", "Inventario Excel", "*.xlsx")
        step1_layout.addWidget(self._excel_drop)

        self._pdf_drop = DropZone("\u25A1", "PDF Original", "*.pdf")
        step1_layout.addWidget(self._pdf_drop)

        layout.addWidget(step1)

        # ─── PASO 2: Parámetros de Mapeo ────────────────────
        step2 = QGroupBox("PASO 2 \u2014 Parámetros de Mapeo")
        step2_grid = QGridLayout(step2)
        step2_grid.setSpacing(12)

        step2_grid.addWidget(QLabel("Inicia desde fila:"), 0, 0)
        self._fila_inicio_spin = QSpinBox()
        self._fila_inicio_spin.setRange(2, 99999)
        self._fila_inicio_spin.setValue(self._state.fila_inicio)
        self._fila_inicio_spin.setFixedWidth(80)
        step2_grid.addWidget(self._fila_inicio_spin, 0, 1)

        step2_grid.addWidget(QLabel("Termina en fila:"), 0, 2)
        self._fila_fin_spin = QSpinBox()
        self._fila_fin_spin.setRange(2, 99999)
        self._fila_fin_spin.setValue(self._state.fila_fin)
        self._fila_fin_spin.setFixedWidth(80)
        step2_grid.addWidget(self._fila_fin_spin, 0, 3)

        step2_grid.addWidget(QLabel("Folio Inicio Protocolo:"), 0, 4)
        self._folio_inicio_input = QLineEdit(self._state.folio_inicio)
        self._folio_inicio_input.setFixedWidth(80)
        step2_grid.addWidget(self._folio_inicio_input, 0, 5)

        step2_grid.addWidget(QLabel("Pág. PDF Inicio:"), 0, 6)
        self._pag_pdf_spin = QSpinBox()
        self._pag_pdf_spin.setRange(1, 99999)
        self._pag_pdf_spin.setValue(self._state.pag_pdf_inicio)
        self._pag_pdf_spin.setFixedWidth(80)
        step2_grid.addWidget(self._pag_pdf_spin, 0, 7)

        self._save_config_btn = QPushButton("\u2B07 Guardar Cambios")
        self._save_config_btn.setFixedHeight(32)
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
        top_bar.addWidget(self._expand_btn)
        step3_layout.addLayout(top_bar)

        # Tabla de datos — sin columna ID, usa Fila Excel
        self._table = DataTable(
            columns=["Fila", "Registro", "Escribano", "Protocolo",
                      "Folios", "Pág. PDF", "Título", "Estado"],
            field_map=["fila", "registro", "escribano", "protocolo",
                        "folios", "pg_pdf", "titulo", "estado"],
        )
        step3_layout.addWidget(self._table)

        # Tip
        tip = QLabel("\u2139  Haz clic en una fila para navegar a la página PDF correspondiente")
        tip.setFont(get_font("body_xs"))
        tip.setStyleSheet(f"color: {self._palette['text_disabled']};")
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
        self._refresh_table()

    def _on_loading_error(self, error_msg: str):
        pass

    def _refresh_table(self):
        records = self._state.records
        self._table.load_data(records)
        self._count_label.setText(f"{len(records)} registros")
