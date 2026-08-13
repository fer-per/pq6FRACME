"""
Modal de edición por registro en los analizadores.

Permite editar el campo relevante del analizador (folios, data tópica o
fecha de inicio) y configurar la paginación PDF del registro:
- compartir la última hoja del registro anterior, o
- indicar manualmente el rango de páginas PDF del fragmento.
"""
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QGridLayout, QCheckBox,
)
from PySide6.QtCore import Signal

from src.domain.entities import InventoryRecord
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class FieldCorrectionModal(QDialog):
    """
    Modal de edición para un registro seleccionado en un analizador.

    Incluye la edición del campo propio del analizador (si aplica) y la
    paginación PDF del registro: compartir la última hoja del anterior o
    fijar manualmente el rango de páginas.
    """

    correction_accepted = Signal(str, dict)  # (record_id, cambios)

    def __init__(self, record: InventoryRecord, field: str,
                 field_label: str, parent=None, dark: bool = False):
        super().__init__(parent)
        self._record = record
        self._field = field
        self._field_label = field_label
        self._palette = get_palette(dark)
        self.setWindowTitle(f"Corrección — {record.id}")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel(f"Corrección — {self._record.id}")
        title.setFont(get_font("title_md"))
        title.setStyleSheet(f"color: {self._palette['primary']};")
        layout.addWidget(title)

        info_grid = QGridLayout()
        info_grid.addWidget(QLabel("Registro:"), 0, 0)
        info_grid.addWidget(QLabel(self._record.registro), 0, 1)
        info_grid.addWidget(QLabel("Escribano:"), 1, 0)
        info_grid.addWidget(QLabel(self._record.escribano), 1, 1)
        info_grid.addWidget(QLabel("Pág. PDF:"), 2, 0)
        info_grid.addWidget(QLabel(self._record.pg_pdf), 2, 1)
        layout.addLayout(info_grid)

# Sección: edición del campo del analizador
        if self._field:
            layout.addWidget(self._build_field_group())

        # Sección: paginación (compartir hoja / rango manual)
        self._build_pagination_group(layout)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("Limpiar manual")
        reset_btn.setProperty("flat", True)
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Aplicar")
        apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)

    def _build_field_group(self):
        group = QGroupBox(f"Editar {self._field_label}")
        group_layout = QVBoxLayout(group)

        group_layout.addWidget(QLabel("Valor Actual:"))
        actual_label = QLabel(self._current_value())
        actual_label.setFont(get_font("mono_bold"))
        actual_label.setStyleSheet(
            f"background-color: {self._palette['error_bg']}; "
            f"color: {self._palette['error']}; "
            f"padding: 8px; border-radius: 6px;"
        )
        group_layout.addWidget(actual_label)

        group_layout.addSpacing(8)
        group_layout.addWidget(QLabel("Nuevo valor:"))
        self._input = QLineEdit(self._current_value())
        self._input.setFont(get_font("mono_bold"))
        self._input.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"color: {self._palette['text_primary']}; "
            f"padding: 8px; border-radius: 6px;"
        )
        group_layout.addWidget(self._input)
        return group

    def _build_pagination_group(self, layout):
        group = QGroupBox("Paginación del fragmento (PDF)")
        group_layout = QVBoxLayout(group)

        self._share_check = QCheckBox(
            "Comparte la última hoja del registro anterior "
            "(arranca en la misma página PDF donde terminó el anterior)"
        )
        self._share_check.setChecked(bool(self._record.comparte_hoja))
        group_layout.addWidget(self._share_check)

        group_layout.addSpacing(8)
        group_layout.addWidget(QLabel("Pág. PDF actual:"))
        actual_label = QLabel(self._record.pg_pdf or "—")
        actual_label.setFont(get_font("mono_bold"))
        actual_label.setStyleSheet(
            f"background-color: {self._palette['error_bg']}; "
            f"color: {self._palette['error']}; "
            f"padding: 8px; border-radius: 6px;"
        )
        group_layout.addWidget(actual_label)

        group_layout.addSpacing(8)
        group_layout.addWidget(QLabel("Nuevo valor (vacío = automático):"))
        self._manual_input = QLineEdit(self._record.pg_pdf_manual)
        self._manual_input.setPlaceholderText("ej. 140-149")
        self._manual_input.setFont(get_font("mono_bold"))
        self._manual_input.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"color: {self._palette['text_primary']}; "
            f"padding: 8px; border-radius: 6px;"
        )
        group_layout.addWidget(self._manual_input)

        hint = QLabel(
            "Si el escrito termina a mitad de una hoja y el siguiente "
            "continúa en la misma, marca la casilla para que esa hoja "
            "quede incluida en ambos fragmentos."
        )
        hint.setWordWrap(True)
        hint.setFont(get_font("body_xs"))
        hint.setStyleSheet(f"color: {self._palette['text_secondary']};")
        group_layout.addWidget(hint)

        layout.addWidget(group)

    def _current_value(self) -> str:
        return getattr(self._record, self._field, "")

    def _on_reset(self):
        """Limpia la paginación manual y desactiva compartir hoja."""
        self._share_check.setChecked(False)
        self._manual_input.setText("")

    def _on_apply(self):
        cambios = {
            "comparte_hoja": self._share_check.isChecked(),
            "pg_pdf_manual": self._manual_input.text().strip(),
        }
        if self._field:
            new_value = self._input.text().strip()
            if new_value:
                cambios["field"] = self._field
                cambios["value"] = new_value
        self.correction_accepted.emit(self._record.id, cambios)
        self.accept()