"""
Widget de header (barra superior).

Muestra el título de la aplicación, toggle de vista dual, y controles globales.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon

from src.presentation.constants import (
    ICON_MOON, ICON_SUN, ICON_SAVE, ICON_LOAD, ICON_VIEW_FULL, ICON_VIEW_SPLIT,
    TOOLBAR_ICON_SIZE,
)
from src.presentation.theme.icons import theme_icon
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class Header(QWidget):
    """Barra superior con título, toggle dual view, y botón de tema."""

    dual_view_toggled = Signal(bool)
    theme_toggled = Signal(bool)
    save_requested = Signal()
    load_requested = Signal()

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
        self._title_label = title
        layout.addWidget(title)

        sep = QLabel("\u2502")
        sep.setStyleSheet(f"color: {self._palette['outline_variant']}; background: transparent;")
        self._sep_label = sep
        layout.addWidget(sep)

        subtitle = QLabel("Sistema de Gestión y Fragmentación Documental")
        subtitle.setFont(get_font("body_sm"))
        subtitle.setStyleSheet(
            f"color: {self._palette['text_secondary']}; background: transparent;"
        )
        self._subtitle_label = subtitle
        layout.addWidget(subtitle)

        layout.addStretch()

        # Botón cargar configuración
        self._load_btn = QPushButton(" Cargar")
        self._load_btn.setProperty("flat", True)
        self._load_btn.setIcon(theme_icon(ICON_LOAD, self._dark_mode))
        self._load_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._load_btn.setToolTip("Cargar configuración guardada")
        self._load_btn.clicked.connect(self.load_requested.emit)
        layout.addWidget(self._load_btn)

        # Botón guardar
        self._save_btn = QPushButton(" Guardar")
        self._save_btn.setProperty("flat", True)
        self._save_btn.setIcon(theme_icon(ICON_SAVE, self._dark_mode))
        self._save_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._save_btn.setToolTip("Guardar sesión (Ctrl+S)")
        self._save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(self._save_btn)

        # Toggle dual view
        self._dual_btn = QPushButton()
        self._dual_btn.setProperty("flat", True)
        self._dual_btn.setFixedHeight(30)
        self._dual_btn.setCheckable(True)
        self._dual_btn.setChecked(True)
        self._dual_btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._dual_btn.setToolTip("Mostrar/ocultar vista previa del PDF")
        self._dual_btn.clicked.connect(self._on_dual_toggle)
        layout.addWidget(self._dual_btn)
        self._update_dual_button()

        # Toggle tema
        self._theme_btn = QPushButton()
        self._theme_btn.setProperty("flat", True)
        self._theme_btn.setFixedSize(25, 25)
        self._theme_btn.setToolTip("Cambiar tema claro/oscuro")
        self._theme_btn.clicked.connect(self._on_theme_toggle)
        self._theme_btn.setIconSize(self._theme_btn.size())
        layout.addWidget(self._theme_btn)
        self._update_theme_icon()

    def _on_dual_toggle(self):
        self._dual_view = self._dual_btn.isChecked()
        self._update_dual_button()
        self.dual_view_toggled.emit(self._dual_view)

    def _update_dual_button(self):
        """Vista partida (prevía visible) o completa (prevía oculta)."""
        if self._dual_view:
            self._dual_btn.setText(" Vista Partida")
            self._dual_btn.setIcon(theme_icon(ICON_VIEW_SPLIT, self._dark_mode))
        else:
            self._dual_btn.setText(" Vista Completa")
            self._dual_btn.setIcon(theme_icon(ICON_VIEW_FULL, self._dark_mode))

    def _on_theme_toggle(self):
        self._dark_mode = not self._dark_mode
        self._update_theme_icon()
        self.theme_toggled.emit(self._dark_mode)

    def _update_theme_icon(self):
        """Muestra la luna en modo oscuro y el sol en modo claro."""
        icon = ICON_MOON if self._dark_mode else ICON_SUN
        self._theme_btn.setIcon(QIcon(icon))

    def apply_theme(self, dark: bool):
        """Reaplica los estilos dependientes del tema."""
        self._dark_mode = dark
        self._update_theme_icon()
        self._save_btn.setIcon(theme_icon(ICON_SAVE, dark))
        self._load_btn.setIcon(theme_icon(ICON_LOAD, dark))
        self._update_dual_button()
        self._palette = get_palette(dark)
        self.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"border-bottom: 1px solid {self._palette['outline_variant']};"
        )
        self._title_label.setStyleSheet(
            f"color: {self._palette['primary']}; background: transparent;"
        )
        self._sep_label.setStyleSheet(
            f"color: {self._palette['outline_variant']}; background: transparent;"
        )
        self._subtitle_label.setStyleSheet(
            f"color: {self._palette['text_secondary']}; background: transparent;"
        )
