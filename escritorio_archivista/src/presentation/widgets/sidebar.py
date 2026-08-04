"""
Sidebar de navegación vertical.

Barra lateral con botones de navegación, collapse/expand,
y botón activo resaltado. Inspiración: Obsidian/VSCode.
"""
import logging
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QMovie

from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font
from src.presentation.constants import (
    ViewId, MODULE_ICONS, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED,
    SIDEBAR_ICON_SIZE, ANIMATION_DURATION_MS,
    ICON_WORKSPACE, ICON_ANALYZER, ICON_EXCLUSIONS, ICON_PROCESS, ICON_PDF_EDITOR,
    ICON_MENU,
)

logger = logging.getLogger(__name__)


class MenuToggleButton(QPushButton):
    """Botón de colapso del sidebar con animación al hacer hover.

    Reproduce el webp animado ``menu.webp`` mientras el cursor está sobre
    el botón; al salir, vuelve a su estado estático.
    """

    def __init__(self, text: str, movie_path: str, parent=None):
        super().__init__(text, parent)
        self._hovered = False
        self._movie = QMovie(movie_path)
        self._movie.setScaledSize(QSize(SIDEBAR_ICON_SIZE, SIDEBAR_ICON_SIZE))
        self._movie.frameChanged.connect(self._on_frame)
        self.setIconSize(QSize(SIDEBAR_ICON_SIZE, SIDEBAR_ICON_SIZE))

    def _on_frame(self, frame: int):
        if self._hovered:
            self.setIcon(QIcon(self._movie.currentPixmap()))

    def enterEvent(self, event):
        super().enterEvent(event)
        self._hovered = True
        if self._movie.isValid():
            self.setIcon(QIcon(self._movie.currentPixmap()))
            self._movie.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hovered = False
        self._movie.stop()
        self.setIcon(QIcon())


class SidebarButton(QPushButton):
    """Botón individual del sidebar con ícono y texto.

    El estilo visual se delega a la hoja de estilo global mediante la
    propiedad ``sidebar="true"``, de modo que sigue el tema activo.
    """

    def __init__(self, icon: str, label: str, view_id: int, parent=None):
        super().__init__(parent)
        self.view_id = view_id
        self._icon = icon
        self._label = label

        self.setProperty("sidebar", True)
        self.setFont(get_font("body"))
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)

        if os.path.exists(icon):
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(SIDEBAR_ICON_SIZE, SIDEBAR_ICON_SIZE))
        else:
            self._icon_text = icon
        self.set_collapsed(False)

    def set_collapsed(self, collapsed: bool):
        text_icon = getattr(self, "_icon_text", None)
        if collapsed:
            self.setText(f"  {text_icon}" if text_icon else "")
            self.setToolTip(self._label)
        else:
            if text_icon:
                self.setText(f"  {text_icon}   {self._label}")
            else:
                self.setText(f"  {self._label}")
            self.setToolTip("")

    def set_active(self, active: bool):
        self.setChecked(active)


class Sidebar(QWidget):
    """Sidebar de navegación vertical con collapse/expand."""

    navigation_requested = Signal(int)

    NAV_ITEMS = [
        (ICON_WORKSPACE, "Espacio de Trabajo", ViewId.WORKSPACE),
        (ICON_ANALYZER,  "Analizador",         ViewId.ANALYZER),
        (ICON_EXCLUSIONS,"Exclusiones",         ViewId.EXCLUSIONS),
        (ICON_PROCESS,   "Fragmentar",          ViewId.PROCESS),
        (ICON_PDF_EDITOR,"Editor PDF",          ViewId.PDF_EDITOR),
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

        self._toggle_btn = MenuToggleButton("  Menú", ICON_MENU)
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
            self._toggle_btn.setText("")
        else:
            self._toggle_btn.setText("  Menú")

    def set_active_view(self, view_id: int):
        self._update_active(view_id)

    def apply_theme(self, dark: bool):
        """Reaplica los estilos dependientes del tema."""
        self._palette = get_palette(dark)
        self._apply_background()
