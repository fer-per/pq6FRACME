"""
Vista del Analizador Expandido.

Pestañas por analizador, tabla de errores filtrable, total de filas,
click en fila navega al PDF. Cada pestaña muestra solo sus errores.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTabWidget, QSplitter,
)
from PySide6.QtCore import Qt

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.analyzer_vm import AnalyzerVM
from src.presentation.widgets.data_table import DataTable
from src.presentation.widgets.search_bar import SearchBar
from src.presentation.widgets.correction_modal import CorrectionModal
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class AnalyzerPanel(QWidget):
    """Panel de resumen de un analizador individual."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self._icon = QLabel("\u23F3")
        self._icon.setFont(get_font("icon"))
        self._icon.setFixedWidth(30)
        self._icon.setStyleSheet("background: transparent;")
        layout.addWidget(self._icon)

        info = QVBoxLayout()
        self._name_label = QLabel(name)
        self._name_label.setFont(get_font("body_sm_bold"))
        self._name_label.setStyleSheet("background: transparent;")
        info.addWidget(self._name_label)

        self._detail_label = QLabel("Sin ejecutar")
        self._detail_label.setFont(get_font("body_xs"))
        self._detail_label.setStyleSheet(
            f"color: {self._palette['text_secondary']}; background: transparent;"
        )
        info.addWidget(self._detail_label)
        layout.addLayout(info, stretch=1)

        self._count_label = QLabel("")
        self._count_label.setFont(get_font("body_sm_bold"))
        self._count_label.setStyleSheet("background: transparent;")
        layout.addWidget(self._count_label)

        self.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"border: 1px solid {self._palette['outline_variant']}; "
            f"border-radius: 8px;"
        )

    def set_result(self, result):
        if result is None:
            return

        self._detail_label.setText(result.resumen)
        errors = len(result.errores)
        warnings = len(result.advertencias)

        if result.ok:
            self._icon.setText("\u2713")
            self._count_label.setText(f"{result.total_revisados} OK")
            self._count_label.setStyleSheet(
                f"color: {self._palette['success']}; background: transparent;"
            )
        else:
            self._icon.setText("\u26A0")
            total = errors + warnings
            self._count_label.setText(f"{total} incidencia(s)")
            color = self._palette['error'] if errors > 0 else self._palette['warning']
            self._count_label.setStyleSheet(
                f"color: {color}; background: transparent;"
            )


class AnalyzerErrorTab(QWidget):
    """Pestaña individual de errores de un analizador."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        self._name = name
        self._all_errors = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Info bar
        info_bar = QHBoxLayout()
        self._info_label = QLabel(f"{name}: sin ejecutar")
        self._info_label.setFont(get_font("body_sm_bold"))
        info_bar.addWidget(self._info_label)
        info_bar.addStretch()

        self._filter_btn = QPushButton("Solo Errores Fatales")
        self._filter_btn.setProperty("flat", True)
        self._filter_btn.setFixedHeight(28)
        self._filter_btn.setCheckable(True)
        self._filter_btn.clicked.connect(self._on_filter_toggled)
        info_bar.addWidget(self._filter_btn)
        layout.addLayout(info_bar)

        # Tabla de errores
        self._table = DataTable(
            columns=["Fila", "Tipo", "Descripción", "Valor Actual", "Esperado", "Fatal"],
            field_map=["fila", "tipo", "descripcion", "valor_actual", "valor_esperado", "fatal"],
        )
        layout.addWidget(self._table)

    def set_errors(self, errors: list, total_revisados: int = 0):
        self._all_errors = errors
        total = len(errors)
        fatales = sum(1 for e in errors if e.fatal)
        warnings = total - fatales
        self._info_label.setText(
            f"{self._name}: {total_revisados} revisados \u2502 "
            f"{fatales} errores fatales \u2502 {warnings} advertencias"
        )
        self._table.load_data(errors)

    def get_table(self) -> DataTable:
        return self._table

    def _on_filter_toggled(self):
        if self._filter_btn.isChecked():
            self._filter_btn.setText("Mostrar Todos")
            fatal_only = [e for e in self._all_errors if e.fatal]
            self._table.load_data(fatal_only)
        else:
            self._filter_btn.setText("Solo Errores Fatales")
            self._table.load_data(self._all_errors)


class AnalyzerView(QWidget):
    """Vista del analizador con pestañas por analizador, total filas, click→PDF."""

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._state = state
        self._container = container
        self._vm = AnalyzerVM(container, state)
        self._palette = get_palette()
        self._last_result = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("\u2637  Analizador de Inventario")
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()

        self._total_label = QLabel("0 filas totales")
        self._total_label.setFont(get_font("body"))
        self._total_label.setStyleSheet(f"color: {self._palette['text_secondary']};")
        header.addWidget(self._total_label)

        self._analyze_btn = QPushButton("\u27F3  Ejecutar Análisis")
        self._analyze_btn.setFixedHeight(34)
        self._analyze_btn.clicked.connect(self._vm.run_analysis)
        header.addWidget(self._analyze_btn)
        layout.addLayout(header)

        # Paneles de resumen
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(10)

        self._panel_folios = AnalyzerPanel("Folios")
        self._panel_topica = AnalyzerPanel("Data Tópica")
        self._panel_cronica = AnalyzerPanel("Data Crónica")
        self._panel_coverage = AnalyzerPanel("Cobertura PDF")

        panels_layout.addWidget(self._panel_folios)
        panels_layout.addWidget(self._panel_topica)
        panels_layout.addWidget(self._panel_cronica)
        panels_layout.addWidget(self._panel_coverage)
        layout.addLayout(panels_layout)

        # Pestañas por analizador
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._tab_all = AnalyzerErrorTab("Todos")
        self._tab_folios = AnalyzerErrorTab("Analizador de Folios")
        self._tab_topica = AnalyzerErrorTab("Data Tópica")
        self._tab_cronica = AnalyzerErrorTab("Data Crónica")
        self._tab_coverage = AnalyzerErrorTab("Cobertura PDF")

        self._tabs.addTab(self._tab_all, "Todas las Incidencias")
        self._tabs.addTab(self._tab_folios, "Folios")
        self._tabs.addTab(self._tab_topica, "Data Tópica")
        self._tabs.addTab(self._tab_cronica, "Data Crónica")
        self._tabs.addTab(self._tab_coverage, "Cobertura PDF")

        layout.addWidget(self._tabs, stretch=1)

        # Botón corregir
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        tip = QLabel("\u2139  Haz clic en un error para navegar a la página PDF correspondiente")
        tip.setFont(get_font("body_xs"))
        tip.setStyleSheet(f"color: {self._palette['text_disabled']};")
        btn_layout.addWidget(tip)
        btn_layout.addStretch()

        self._correct_btn = QPushButton("\u270E  Corregir Seleccionado")
        self._correct_btn.setEnabled(False)
        self._correct_btn.clicked.connect(self._on_correct)
        btn_layout.addWidget(self._correct_btn)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self._vm.analysis_finished.connect(self._on_analysis_finished)
        self._vm.analysis_started.connect(
            lambda: self._analyze_btn.setEnabled(False)
        )
        self._vm.correction_applied.connect(self._vm.run_analysis)

        # Conectar click en cada tabla de error → habilitar corrección + navegar PDF
        for tab in [self._tab_all, self._tab_folios, self._tab_topica,
                     self._tab_cronica, self._tab_coverage]:
            tab.get_table().row_clicked.connect(self._on_error_row_clicked)

    def _on_error_row_clicked(self, row: int, error):
        """Habilita corrección y navega a la página PDF del error."""
        self._correct_btn.setEnabled(True)
        self._current_error = error

        # Buscar el registro correspondiente para navegar al PDF
        if hasattr(error, 'record_id'):
            for record in self._state.records:
                if record.id == error.record_id and record.pg_pdf:
                    try:
                        first_page = int(record.pg_pdf.split('-')[0])
                        self._state.pdf_current_page = first_page
                        main_window = self.window()
                        if hasattr(main_window, '_render_current_page'):
                            main_window._render_current_page()
                    except (ValueError, IndexError):
                        pass
                    break

    def _on_analysis_finished(self, result):
        self._last_result = result
        self._analyze_btn.setEnabled(True)

        # Total de filas
        total = len(self._state.records)
        self._total_label.setText(f"{total} filas totales en el Excel")

        # Actualizar paneles
        self._panel_folios.set_result(result.folios_result)
        self._panel_topica.set_result(result.topica_result)
        self._panel_cronica.set_result(result.cronica_result)
        self._panel_coverage.set_result(result.coverage_result)

        # Combinar todos los errores
        all_errors = []
        folios_errors = []
        topica_errors = []
        cronica_errors = []
        coverage_errors = []

        if result.folios_result:
            folios_errors = result.folios_result.errores + result.folios_result.advertencias
            all_errors.extend(folios_errors)

        if result.topica_result:
            topica_errors = result.topica_result.advertencias
            all_errors.extend(topica_errors)

        if result.cronica_result:
            cronica_errors = result.cronica_result.errores + result.cronica_result.advertencias
            all_errors.extend(cronica_errors)

        if result.coverage_result:
            coverage_errors = result.coverage_result.errores
            all_errors.extend(coverage_errors)

        # Llenar pestañas
        self._tab_all.set_errors(all_errors, total)
        self._tab_folios.set_errors(
            folios_errors,
            result.folios_result.total_revisados if result.folios_result else 0,
        )
        self._tab_topica.set_errors(
            topica_errors,
            result.topica_result.total_revisados if result.topica_result else 0,
        )
        self._tab_cronica.set_errors(
            cronica_errors,
            result.cronica_result.total_revisados if result.cronica_result else 0,
        )
        self._tab_coverage.set_errors(
            coverage_errors,
            result.coverage_result.total_revisados if result.coverage_result else 0,
        )

        self._correct_btn.setEnabled(False)

    def _on_correct(self):
        """Abre el modal de corrección para el error seleccionado."""
        error = getattr(self, '_current_error', None)
        if error is None:
            return

        suggestion = None
        for s in self._state.suggestions:
            if s.registro_id == error.record_id:
                suggestion = s
                break

        if suggestion is None:
            from src.domain.entities import SugerenciaCorreccion
            suggestion = SugerenciaCorreccion(
                id="TEMP", registro_id=error.record_id,
                tipo_error=error.tipo, descripcion=error.descripcion,
                valor_actual=error.valor_actual,
                valor_sugerido=error.valor_esperado,
                escribano="", folios_original=error.valor_actual,
                rango_sugerido="", paginas_pdf="", paginas_sugeridas="",
            )

        modal = CorrectionModal(suggestion, self)
        modal.correction_accepted.connect(self._vm.apply_correction)
        modal.exec()
