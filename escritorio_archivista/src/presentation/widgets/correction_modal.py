"""
Modal de corrección inteligente.

Permite al usuario ver el error, comparar valor actual vs sugerido,
editar el valor sugerido y aplicar la corrección.
"""
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QGridLayout,
)
from PySide6.QtCore import Qt, Signal

from src.domain.entities import SugerenciaCorreccion
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class CorrectionModal(QDialog):
    """
    Modal de corrección inteligente.

    Muestra contexto del error, comparación actual vs sugerido,
    y permite editar el valor sugerido antes de aplicar.
    """

    correction_accepted = Signal(str, str)  # (record_id, new_folios)

    def __init__(self, suggestion: SugerenciaCorreccion, parent=None,
                 dark: bool = False):
        super().__init__(parent)
        self._suggestion = suggestion
        self._palette = get_palette(dark)
        self.setWindowTitle(f"⚠️ Corrección — {suggestion.registro_id}")
        self.setMinimumWidth(600)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Título
        title = QLabel(f"⚠️ Corrección Inteligente — {self._suggestion.registro_id}")
        title.setFont(get_font("title_md"))
        title.setStyleSheet(f"color: {self._palette['primary']};")
        layout.addWidget(title)

        # Tipo de error
        tipo_label = QLabel(f"[{self._suggestion.tipo_error}]")
        tipo_label.setFont(get_font("body_sm_bold"))
        tipo_label.setStyleSheet(f"color: {self._palette['warning']};")
        layout.addWidget(tipo_label)

        # Cuerpo: contexto + comparación
        body = QHBoxLayout()

        # Contexto
        ctx_group = QGroupBox("Contexto del Error")
        ctx_layout = QVBoxLayout(ctx_group)

        ctx_layout.addWidget(QLabel(self._suggestion.descripcion))
        ctx_layout.addSpacing(8)

        info_grid = QGridLayout()
        info_grid.addWidget(QLabel("ID:"), 0, 0)
        info_grid.addWidget(QLabel(self._suggestion.registro_id), 0, 1)
        info_grid.addWidget(QLabel("Escribano:"), 1, 0)
        info_grid.addWidget(QLabel(self._suggestion.escribano), 1, 1)
        info_grid.addWidget(QLabel("Folio Original:"), 2, 0)
        info_grid.addWidget(QLabel(self._suggestion.folios_original), 2, 1)
        info_grid.addWidget(QLabel("Páginas PDF:"), 3, 0)
        info_grid.addWidget(QLabel(self._suggestion.paginas_pdf), 3, 1)
        ctx_layout.addLayout(info_grid)
        ctx_layout.addStretch()

        body.addWidget(ctx_group)

        # Comparación
        cmp_group = QGroupBox("Comparación Detallada")
        cmp_layout = QVBoxLayout(cmp_group)

        # Valor actual
        cmp_layout.addWidget(QLabel("Valor Actual (ERROR):"))
        actual_label = QLabel(self._suggestion.valor_actual)
        actual_label.setFont(get_font("mono_bold"))
        actual_label.setStyleSheet(
            f"background-color: {self._palette['error_bg']}; "
            f"color: {self._palette['error']}; "
            f"padding: 8px; border-radius: 6px;"
        )
        cmp_layout.addWidget(actual_label)

        cmp_layout.addSpacing(8)

        # Valor sugerido (editable)
        cmp_layout.addWidget(QLabel("Valor Sugerido (editable):"))
        self._suggested_input = QLineEdit(self._suggestion.valor_sugerido)
        self._suggested_input.setFont(get_font("mono_bold"))
        self._suggested_input.setStyleSheet(
            f"background-color: {self._palette['success_bg']}; "
            f"color: {self._palette['success']}; "
            f"padding: 8px; border-radius: 6px;"
        )
        cmp_layout.addWidget(self._suggested_input)

        if self._suggestion.paginas_sugeridas:
            cmp_layout.addSpacing(4)
            cmp_layout.addWidget(
                QLabel(f"Páginas PDF sugeridas: {self._suggestion.paginas_sugeridas}")
            )

        cmp_layout.addStretch()

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("✅ Aplicar Corrección")
        apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(apply_btn)

        cmp_layout.addLayout(btn_layout)

        body.addWidget(cmp_group)
        layout.addLayout(body)

    def _on_apply(self):
        new_value = self._suggested_input.text().strip()
        if new_value:
            self.correction_accepted.emit(
                self._suggestion.registro_id, new_value
            )
            self.accept()
