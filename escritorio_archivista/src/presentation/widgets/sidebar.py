"""
Sidebar de navegación vertical.

Barra lateral con botones de navegación, collapse/expand,
y botón activo resaltado. Inspiración: Obsidian/VSCode.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font
from src.presentation.constants import (
    ViewId, MODULE_ICONS, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED,
    ANIMATION_DURATION_MS,
)

logger = logging.getLogger(__name__)

# Ícono del botón de colapso (menú)
MENU_ICON = "\u2630"  # ☰


class SidebarButton(QPushButton):
    """Botón individual del sidebar con ícono y texto.

    El estilo visual se delega a la hoja de estilo global mediante la
    propiedad ``sidebar="true"``, de modo que sigue el tema activo.
    """

    def __init__(self, icon_text: str, label: str, view_id: int, parent=None):
        super().__init__(parent)
        self.view_id = view_id
        self._icon_text = icon_text
        self._label = label

        self.setProperty("sidebar", True)
        self.setText(f"  {icon_text}   {label}")
        self.setFont(get_font("body"))
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)

    def set_collapsed(self, collapsed: bool):
        if collapsed:
            self.setText(f"  {self._icon_text}")
            self.setToolTip(self._label)
        else:
            self.setText(f"  {self._icon_text}   {self._label}")
            self.setToolTip("")

    def set_active(self, active: bool):
        self.setChecked(active)


class Sidebar(QWidget):
    """Sidebar de navegación vertical con collapse/expand."""

    navigation_requested = Signal(int)

    NAV_ITEMS = [
        (MODULE_ICONS["workspace"],  "Espacio de Trabajo",  ViewId.WORKSPACE),
        (MODULE_ICONS["analyzer"],   "Analizador",          ViewId.ANALYZER),
        (MODULE_ICONS["exclusions"], "Exclusiones",          ViewId.EXCLUSIONS),
        (MODULE_ICONS["process"],    "Fragmentar",           ViewId.PROCESS),
        (MODULE_ICONS["pdf_editor"], "Editor PDF",           ViewId.PDF_EDITOR),
    ]

    BOTTOM_ITEMS = [
        (MODULE_ICONS["docs"],    "Documentación", ViewId.DOCS),
        (MODULE_ICONS["support"], "Soporte",       ViewId.SUPPORT),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._buttons: list[SidebarButton] = []
        self._active_id = ViewId.WORKSPACE
        self._palette = get_palette()

        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH_EXPANDED)
        self._setup_ui()

    def _setup_ui(self):
        self._apply_background()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)

        self._toggle_btn = QPushButton(f"  {MENU_ICON}   Menú")
        self._toggle_btn.setProperty("sidebar", True)
        self._toggle_btn.setFixedHeight(36)
        self._toggle_btn.setFont(get_font("body_sm_bold"))
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self._toggle_btn)

        layout.addSpacing(8)

        for icon, label, view_id in self.NAV_ITEMS:
            btn = SidebarButton(icon, label, view_id)
            btn.clicked.connect(lambda checked, vid=view_id: self._on_nav_click(vid))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        for icon, label, view_id in self.BOTTOM_ITEMS:
            btn = SidebarButton(icon, label, view_id)
            btn.clicked.connect(lambda checked, vid=view_id: self._on_nav_click(vid))
            self._buttons.append(btn)
            layout.addWidget(btn)

        self._update_active(ViewId.WORKSPACE)

    def _apply_background(self):
        """Aplica el fondo del sidebar con selector por objectName."""
        self.setStyleSheet(
            f"#sidebar {{ background-color: {self._palette['surface_low']}; "
            f"border-right: 1px solid {self._palette['outline_variant']}; }}"
        )

    def _on_nav_click(self, view_id: int):
        self._update_active(view_id)
        self.navigation_requested.emit(view_id)

    def _update_active(self, view_id: int):
        self._active_id = view_id
        for btn in self._buttons:
            btn.set_active(btn.view_id == view_id)

    def toggle_collapse(self):
        self._collapsed = not self._collapsed
        target_width = SIDEBAR_WIDTH_COLLAPSED if self._collapsed else SIDEBAR_WIDTH_EXPANDED

        anim = QPropertyAnimation(self, b"minimumWidth")
        anim.setDuration(ANIMATION_DURATION_MS)
        anim.setStartValue(self.width())
        anim.setEndValue(target_width)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()
        self._anim = anim

        anim2 = QPropertyAnimation(self, b"maximumWidth")
        anim2.setDuration(ANIMATION_DURATION_MS)
        anim2.setStartValue(self.width())
        anim2.setEndValue(target_width)
        anim2.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim2.start()
        self._anim2 = anim2

        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)

        if self._collapsed:
            self._toggle_btn.setText(f"  {MENU_ICON}")
        else:
            self._toggle_btn.setText(f"  {MENU_ICON}   Menú")

    def set_active_view(self, view_id: int):
        self._update_active(view_id)

    def apply_theme(self, dark: bool):
        """Reaplica los estilos dependientes del tema."""
        self._palette = get_palette(dark)
        self._apply_background()
