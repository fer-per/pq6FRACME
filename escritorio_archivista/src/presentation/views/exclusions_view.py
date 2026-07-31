"""
Vista de Exclusiones — gestión de saltos, páginas ignoradas y segmentos.

Incluye la vista de referencia del inventario Excel al lado (con QSplitter)
y navegación al PDF al hacer clic en las filas.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QGroupBox, QComboBox, QSplitter,
)
from PySide6.QtCore import Qt

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.exclusions_vm import ExclusionsVM
from src.presentation.widgets.data_table import DataTable
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class ExclusionsView(QWidget):
    """Vista de gestión de exclusiones con referencia visual al Excel."""

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._state = state
        self._vm = ExclusionsVM(container, state)
        self._palette = get_palette()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Título
        title = QLabel("\u2691  Saltos, Exclusiones y Segmentos")
        title.setProperty("heading", True)
        layout.addWidget(title)

        # Splitter principal: Izquierda = Formularios y Exclusiones; Derecha = Vista del Excel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ─── PANEL IZQUIERDO: FORMULARIOS Y EXCLUSIONES ───────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Formulario Salto
        salto_group = QGroupBox("Agregar Salto de Folio")
        salto_layout = QHBoxLayout(salto_group)

        salto_layout.addWidget(QLabel("Desde folio:"))
        self._salto_desde = QSpinBox()
        self._salto_desde.setRange(1, 99999)
        salto_layout.addWidget(self._salto_desde)

        salto_layout.addWidget(QLabel("Hasta folio:"))
        self._salto_hasta = QSpinBox()
        self._salto_hasta.setRange(1, 99999)
        salto_layout.addWidget(self._salto_hasta)

        salto_layout.addWidget(QLabel("Motivo:"))
        self._salto_motivo = QLineEdit()
        self._salto_motivo.setPlaceholderText("Justificación del salto")
        salto_layout.addWidget(self._salto_motivo, stretch=1)

        self._salto_btn = QPushButton("+ Agregar Salto")
        self._salto_btn.clicked.connect(self._on_add_salto)
        salto_layout.addWidget(self._salto_btn)

        left_layout.addWidget(salto_group)

        # Formulario Ignorar
        ignorar_group = QGroupBox("Agregar Páginas a Ignorar (PDF)")
        ignorar_layout = QHBoxLayout(ignorar_group)

        ignorar_layout.addWidget(QLabel("Desde pág:"))
        self._ign_desde = QSpinBox()
        self._ign_desde.setRange(1, 99999)
        ignorar_layout.addWidget(self._ign_desde)

        ignorar_layout.addWidget(QLabel("Hasta pág:"))
        self._ign_hasta = QSpinBox()
        self._ign_hasta.setRange(1, 99999)
        ignorar_layout.addWidget(self._ign_hasta)

        ignorar_layout.addWidget(QLabel("Motivo:"))
        self._ign_motivo = QLineEdit()
        self._ign_motivo.setPlaceholderText("Razón")
        ignorar_layout.addWidget(self._ign_motivo, stretch=1)

        ignorar_layout.addWidget(QLabel("Tipo:"))
        self._ign_tipo = QComboBox()
        self._ign_tipo.addItems(["Hoja en Blanco", "Portada", "Separador", "Dañada"])
        ignorar_layout.addWidget(self._ign_tipo)

        self._ign_btn = QPushButton("+ Agregar Exclusión")
        self._ign_btn.clicked.connect(self._on_add_ignorar)
        ignorar_layout.addWidget(self._ign_btn)

        left_layout.addWidget(ignorar_group)

        # Formulario Segmento
        seg_group = QGroupBox("Agregar Segmento (Punto de Quiebre)")
        seg_layout = QHBoxLayout(seg_group)

        seg_layout.addWidget(QLabel("Folio inicio:"))
        self._seg_folio = QLineEdit()
        self._seg_folio.setPlaceholderText("001r")
        self._seg_folio.setFixedWidth(80)
        seg_layout.addWidget(self._seg_folio)

        seg_layout.addWidget(QLabel("Pág PDF inicio:"))
        self._seg_pag = QSpinBox()
        self._seg_pag.setRange(1, 99999)
        seg_layout.addWidget(self._seg_pag)

        seg_layout.addStretch()

        self._seg_btn = QPushButton("+ Agregar Segmento")
        self._seg_btn.clicked.connect(self._on_add_segmento)
        seg_layout.addWidget(self._seg_btn)

        left_layout.addWidget(seg_group)

        # Tabla de exclusiones activas
        excl_group = QGroupBox("Exclusiones Activas")
        excl_layout = QVBoxLayout(excl_group)

        self._excl_table = DataTable(
            columns=["Tipo", "Desde", "Hasta", "Motivo", "Detalle"],
            field_map=["tipo", "desde", "hasta", "motivo", "tipo_contenido"],
        )
        excl_layout.addWidget(self._excl_table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._delete_btn = QPushButton("\u2717 Eliminar Seleccionada")
        self._delete_btn.setProperty("flat", True)
        self._delete_btn.clicked.connect(self._on_delete_exclusion)
        btn_layout.addWidget(self._delete_btn)
        excl_layout.addLayout(btn_layout)

        left_layout.addWidget(excl_group, stretch=1)
        splitter.addWidget(left_widget)

        # ─── PANEL DERECHO: REFERENCIA DEL EXCEL ───────────────
        right_group = QGroupBox("Referencia del Inventario Excel")
        right_layout = QVBoxLayout(right_group)

        tip_label = QLabel("\u2139 Haz clic en cualquier fila para previsualizar su página PDF")
        tip_label.setFont(get_font("body_xs"))
        tip_label.setStyleSheet(f"color: {self._palette['text_secondary']};")
        right_layout.addWidget(tip_label)

        self._excel_table = DataTable(
            columns=["Fila", "Registro", "Folios", "Pág. PDF", "Escribano"],
            field_map=["fila", "registro", "folios", "pg_pdf", "escribano"],
        )
        right_layout.addWidget(self._excel_table)
        splitter.addWidget(right_group)

        # Proporciones 55% / 45%
        splitter.setSizes([550, 450])
        layout.addWidget(splitter, stretch=1)

    def _connect_signals(self):
        self._vm.exclusions_updated.connect(self._refresh_tables)
        self._state.exclusions_changed.connect(self._refresh_tables)
        self._state.records_changed.connect(self._refresh_excel_table)

        # Click en la tabla de referencia del Excel -> navegar al PDF
        self._excel_table.row_clicked.connect(self._on_excel_row_clicked)

    def _on_excel_row_clicked(self, row: int, record):
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

    def _on_add_salto(self):
        self._vm.add_salto(
            self._salto_desde.value(),
            self._salto_hasta.value(),
            self._salto_motivo.text(),
        )
        self._salto_motivo.clear()

    def _on_add_ignorar(self):
        self._vm.add_ignorar(
            self._ign_desde.value(),
            self._ign_hasta.value(),
            self._ign_motivo.text(),
            self._ign_tipo.currentText(),
        )
        self._ign_motivo.clear()

    def _on_add_segmento(self):
        self._vm.add_segmento(
            self._seg_folio.text(),
            self._seg_pag.value(),
        )
        self._seg_folio.clear()

    def _on_delete_exclusion(self):
        row = self._excl_table.currentRow()
        data = self._excl_table.get_data_at_row(row)
        if data and hasattr(data, 'id'):
            self._vm.remove_exclusion(data.id)

    def _refresh_tables(self):
        self._excl_table.load_data(self._state.exclusions)
        self._refresh_excel_table()

    def _refresh_excel_table(self):
        self._excel_table.load_data(self._state.records)
