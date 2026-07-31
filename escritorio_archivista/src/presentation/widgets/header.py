"""
Widget de header (barra superior).

Muestra el título de la aplicación, toggle de vista dual, y controles globales.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Signal, Qt

from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class Header(QWidget):
    """Barra superior con título, toggle dual view, y botón de tema."""

    dual_view_toggled = Signal(bool)
    theme_toggled = Signal(bool)
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        self._dark_mode = False
        self._dual_view = True
        self.setFixedHeight(44)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"border-bottom: 1px solid {self._palette['outline_variant']};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Título
        title = QLabel("Escritorio Archivista")
        title.setFont(get_font("title_md"))
        title.setStyleSheet(f"color: {self._palette['primary']}; background: transparent;")
        layout.addWidget(title)

        sep = QLabel("\u2502")
        sep.setStyleSheet(f"color: {self._palette['outline_variant']}; background: transparent;")
        layout.addWidget(sep)

        subtitle = QLabel("Sistema de Gestión y Fragmentación Documental")
        subtitle.setFont(get_font("body_sm"))
        subtitle.setStyleSheet(
            f"color: {self._palette['text_secondary']}; background: transparent;"
        )
        layout.addWidget(subtitle)

        layout.addStretch()

        # Botón guardar
        self._save_btn = QPushButton("\u2B07 Guardar")
        self._save_btn.setProperty("flat", True)
        self._save_btn.setFixedHeight(30)
        self._save_btn.setToolTip("Guardar sesión (Ctrl+S)")
        self._save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(self._save_btn)

        # Toggle dual view
        self._dual_btn = QPushButton("\u25A8 Vista Dual")
        self._dual_btn.setProperty("flat", True)
        self._dual_btn.setFixedHeight(30)
        self._dual_btn.setCheckable(True)
        self._dual_btn.setChecked(True)
        self._dual_btn.setToolTip("Mostrar/ocultar vista previa del PDF")
        self._dual_btn.clicked.connect(self._on_dual_toggle)
        layout.addWidget(self._dual_btn)

        # Toggle tema
        self._theme_btn = QPushButton("\u263D")
        self._theme_btn.setProperty("flat", True)
        self._theme_btn.setFixedSize(30, 30)
        self._theme_btn.setToolTip("Cambiar tema claro/oscuro")
        self._theme_btn.clicked.connect(self._on_theme_toggle)
        layout.addWidget(self._theme_btn)

    def _on_dual_toggle(self):
        self._dual_view = self._dual_btn.isChecked()
        self._dual_btn.setText(
            "\u25A8 Vista Dual" if self._dual_view else "\u25A1 Vista Simple"
        )
        self.dual_view_toggled.emit(self._dual_view)

    def _on_theme_toggle(self):
        self._dark_mode = not self._dark_mode
        self._theme_btn.setText("\u2600" if self._dark_mode else "\u263D")
        self.theme_toggled.emit(self._dark_mode)
