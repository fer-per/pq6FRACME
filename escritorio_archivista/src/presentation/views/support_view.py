"""
Vista de Soporte — información de la aplicación, atajos y diagnóstico.

Contenido exclusivamente de texto (sin formularios ni botones), renderizado
como Markdown con el tema activo.
"""
import logging
import platform
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QTextBrowser,
    QApplication,
)
from PySide6.QtCore import Qt

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.constants import (
    APP_ROOT_DIR, DOCS_DIR, SESIONES_DIR, ModuleIcon,
)
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class SupportView(QWidget):
    """Vista de Soporte — solo texto."""

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._state = state
        self._container = container
        self._palette = get_palette()
        self._setup_ui()
        self._render()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading_icon = QLabel(ModuleIcon.SUPPORT)
        heading_icon.setFont(get_font("icon_lg"))
        heading_icon.setStyleSheet("background: transparent;")
        header.addWidget(heading_icon)

        title = QLabel("Soporte")
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        scroll.setWidget(self._browser)
        layout.addWidget(scroll, stretch=1)

    def _texto_soporte(self) -> str:
        estado = self._state
        return f"""# Soporte

## Información de la aplicación

- **Nombre**: Escritorio Archivista
- **Versión**: {self._version()}
- **Plataforma**: {platform.system()} {platform.release()}
- **Python**: {platform.python_version()}
- **PySide6**: {self._pyside_version()}
- **Proyecto**: Sistema de Gestión y Fragmentación Documental (SGFD)

## Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+S` | Guardar configuración |
| `Ctrl+L` | Cargar configuración |
| `Ctrl+N` | Nueva configuración |
| `Ctrl+1` | Espacio de Trabajo |
| `Ctrl+2` | Analizador |
| `Ctrl+3` | Fragmentar |

## Diagnóstico

- **Inventario**: {estado.excel_path or "— (sin cargar)"}
- **PDF**: {estado.pdf_path or "— (sin cargar)"}
- **Directorio de la aplicación**: `{APP_ROOT_DIR}`
- **Documentación**: `{DOCS_DIR}`
- **Sesiones**: `{SESIONES_DIR}`

## Contacto

Para consultas técnicas sobre este software, comunicate con el equipo de
desarrollo del proyecto.
"""

    def _version(self) -> str:
        app = QApplication.instance()
        if app and app.applicationVersion():
            return app.applicationVersion()
        return "2.0"

    def _pyside_version(self) -> str:
        try:
            from PySide6 import __version__
            return __version__
        except Exception:
            return "desconocida"

    def _render(self):
        self._browser.document().setDefaultStyleSheet(self._doc_css())
        self._browser.setMarkdown(self._texto_soporte())
        self._browser.verticalScrollBar().setValue(0)
        self._apply_widget_styles()

    def _doc_css(self) -> str:
        p = self._palette
        return f"""
            body {{ color: {p['text_primary']}; }}
            h1, h2, h3, h4 {{ color: {p['primary']}; }}
            code, pre {{ color: {p['text_primary']}; }}
            table, th, td {{ border: 1px solid {p['outline_variant']}; }}
            th {{ background-color: {p['surface_container']}; }}
        """

    def _apply_widget_styles(self):
        self._browser.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"color: {self._palette['text_primary']};"
        )

    def apply_theme(self, dark: bool):
        """Reaplica el tema al visor y al texto renderizado."""
        self._palette = get_palette(dark)
        self._render()