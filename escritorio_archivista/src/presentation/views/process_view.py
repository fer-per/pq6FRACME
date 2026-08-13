"""
Vista de Procesamiento y Fragmentación.

Botón de fragmentar, barra de progreso, consola dedicada
y tabla de foliación mapeada.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QGroupBox, QFileDialog, QHeaderView,
)
from PySide6.QtCore import Qt, QSize, QTimer, QUrl
from PySide6.QtGui import QIcon, QDesktopServices

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.process_vm import ProcessVM
from src.presentation.widgets.data_table import DataTable
from src.presentation.constants import (
    ICON_FOLDER, ICON_SELECT, ICON_PROCESS, TOOLBAR_ICON_SIZE,
)
from src.presentation.theme.icons import theme_icon, white_icon
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class ProcessView(QWidget):
    """Vista de fragmentación del PDF maestro."""

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._state = state
        self._vm = ProcessVM(container, state)
        self._palette = get_palette()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        self._heading_icon = QLabel()
        self._heading_icon.setPixmap(
            theme_icon(ICON_PROCESS, False).pixmap(
                QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE)
            )
        )
        self._heading_icon.setStyleSheet("background: transparent;")
        header_layout.addWidget(self._heading_icon)

        title = QLabel("Fragmentar PDF Maestro")
        title.setProperty("heading", True)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Directorio de salida
        output_layout = QHBoxLayout()
        folder_icon = QLabel()
        folder_pixmap = QIcon(ICON_FOLDER).pixmap(QSize(24, 24))
        folder_icon.setPixmap(folder_pixmap)
        folder_icon.setFixedSize(28, 28)
        folder_icon.setStyleSheet("background: transparent;")
        folder_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        output_layout.addWidget(folder_icon)

        output_layout.addWidget(QLabel("Directorio de salida:"))
        self._output_label = QLineEdit(self._state.output_dir or "No seleccionado")
        self._output_label.setReadOnly(True)
        self._output_label.setFont(get_font("body_sm"))
        self._output_label.setToolTip(self._state.output_dir or "")
        output_layout.addWidget(self._output_label, stretch=1)

        self._select_dir_btn = QPushButton(" Seleccionar")
        self._select_dir_btn.setProperty("flat", True)
        self._select_dir_btn.setIcon(theme_icon(ICON_SELECT, False))
        self._select_dir_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._select_dir_btn.clicked.connect(self._on_select_dir)
        output_layout.addWidget(self._select_dir_btn)

        self._open_dir_btn = QPushButton(" Abrir carpeta")
        self._open_dir_btn.setProperty("flat", True)
        self._open_dir_btn.setIcon(theme_icon(ICON_FOLDER, False))
        self._open_dir_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._open_dir_btn.clicked.connect(self._on_open_dir)
        self._open_dir_btn.setEnabled(bool(self._state.output_dir))
        output_layout.addWidget(self._open_dir_btn)
        layout.addLayout(output_layout)

        # Botón fragmentar + progreso
        action_group = QGroupBox()
        action_layout = QVBoxLayout(action_group)

        btn_row = QHBoxLayout()
        self._fragment_btn = QPushButton("  FRAGMENTAR PDF")
        self._fragment_btn.setFont(get_font("button_lg"))
        self._fragment_btn.setFixedHeight(44)
        self._fragment_btn.setIcon(white_icon(ICON_PROCESS))
        self._fragment_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._fragment_btn.clicked.connect(self._vm.start_fragmentation)
        btn_row.addWidget(self._fragment_btn)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        btn_row.addWidget(self._progress, stretch=1)
        action_layout.addLayout(btn_row)

        self._status_label = QLabel("")
        self._status_label.setFont(get_font("body_sm"))
        self._status_label.setStyleSheet(
            f"color: {self._palette['text_secondary']};"
        )
        action_layout.addWidget(self._status_label)

        layout.addWidget(action_group)

        # Tabla de foliación mapeada
        table_group = QGroupBox("Detalle de Foliación Mapeada (Excel vs PDF)")
        table_layout = QVBoxLayout(table_group)
        self._table = DataTable(
            columns=["Fila", "Registro", "Folios", "Rango PDF", "Estado", "Escribano"],
            field_map=["fila", "registro", "folios", "pg_pdf", "estado", "escribano"],
        )
        # Solo esta tabla se adapta al espacio disponible: las columnas se
        # estiran para llenar el ancho de la vista.
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table_layout.addWidget(self._table)
        layout.addWidget(table_group, stretch=1)

    def _connect_signals(self):
        self._vm.fragment_started.connect(self._on_started)
        self._vm.fragment_progress.connect(self._on_progress)
        self._vm.fragment_finished.connect(self._on_finished)
        self._vm.fragment_error.connect(self._on_error)
        self._state.records_changed.connect(self._refresh_table)

        # Row click -> navigate PDF page
        self._table.row_clicked.connect(self._on_row_clicked)

    def _on_row_clicked(self, row: int, record):
        if not hasattr(record, 'pg_pdf') or not record.pg_pdf:
            return
        try:
            first_page = int(record.pg_pdf.split('-')[0])
            self._state.pdf_current_page = first_page
            main_window = self.window()
            if hasattr(main_window, '_render_current_page'):
                main_window._render_current_page()
        except (ValueError, IndexError):
            pass

    def _on_select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Directorio de salida")
        if path:
            self._vm.set_output_dir(path)
            self._set_output_text(path)
            self._open_dir_btn.setEnabled(True)

    def _set_output_text(self, path: str):
        """Muestra la ruta completa y la lleva al final para ver el nombre."""
        self._output_label.setText(path)
        self._output_label.setToolTip(path)
        self._output_label.setCursorPosition(len(path))

    def _on_open_dir(self):
        path = self._state.output_dir
        if not path:
            self._open_dir_btn.setEnabled(False)
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
            self._status_label.setText(f"No se pudo abrir: {path}")

    def _on_started(self):
        self._fragment_btn.setEnabled(False)
        self._fragment_btn.setText("\u23F3 Procesando...")
        self._progress.setVisible(True)
        self._progress.setValue(0)

    def _on_progress(self, current: int, total: int, record_id: str):
        pct = int((current / total) * 100) if total > 0 else 0
        self._progress.setValue(pct)
        self._status_label.setText(
            f"Procesando registro {current}/{total} ({record_id})..."
        )

    def _on_finished(self, result):
        self._fragment_btn.setText("\u2713 Completado")
        self._progress.setValue(100)
        self._status_label.setText(
            f"\u2713 {result.total_exitos} fragmentos creados, "
            f"{result.total_fallos} errores."
        )

        QTimer.singleShot(3000, self._reset_button)
        self._refresh_table()

    def _on_error(self, error_msg: str):
        self._fragment_btn.setText("\u2717 Error")
        self._fragment_btn.setEnabled(True)
        self._progress.setVisible(False)

        QTimer.singleShot(3000, self._reset_button)

    def _reset_button(self):
        self._fragment_btn.setText("  FRAGMENTAR PDF")
        self._fragment_btn.setEnabled(True)
        self._progress.setVisible(False)

    def _refresh_table(self):
        self._table.load_data(self._state.records)

    def apply_theme(self, dark: bool):
        """Reaplica el tema a etiquetas y tabla de la vista."""
        self._palette = get_palette(dark)
        self._heading_icon.setPixmap(
            theme_icon(ICON_PROCESS, dark).pixmap(
                QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE)
            )
        )
        self._select_dir_btn.setIcon(theme_icon(ICON_SELECT, dark))
        self._open_dir_btn.setIcon(theme_icon(ICON_FOLDER, dark))
        self._fragment_btn.setIcon(white_icon(ICON_PROCESS))
        self._status_label.setStyleSheet(
            f"color: {self._palette['text_secondary']};"
        )
        self._table.apply_theme(dark)
