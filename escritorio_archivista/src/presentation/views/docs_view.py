"""
Vista de Documentación — consulta de la documentación del proyecto.

Muestra los archivos markdown de ``docs/`` en un visor con lista lateral
de documentos. Soporta navegación entre documentos mediante enlaces
relativos y reaplica el tema activo.
"""
import logging
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSplitter, QTextBrowser,
)

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.constants import DOCS_DIR, ModuleIcon
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class DocsView(QWidget):
    """Vista de documentación consultable desde la aplicación."""

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._state = state
        self._container = container
        self._palette = get_palette()
        self._docs_dir = DOCS_DIR
        self._current_doc = None
        self._setup_ui()
        self._load_documents()
        self._apply_widget_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        heading_icon = QLabel(ModuleIcon.DOCS)
        heading_icon.setFont(get_font("icon_lg"))
        heading_icon.setStyleSheet("background: transparent;")
        header.addWidget(heading_icon)

        title = QLabel("Documentación")
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Splitter: lista de documentos + visor
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list = QListWidget()
        self._list.setFixedWidth(210)
        self._list.setFont(get_font("body"))
        self._list.currentItemChanged.connect(self._on_doc_selected)
        self._splitter.addWidget(self._list)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setOpenLinks(False)
        self._browser.anchorClicked.connect(self._on_anchor_clicked)
        self._splitter.addWidget(self._browser)

        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        layout.addWidget(self._splitter, stretch=1)

    def _load_documents(self):
        """Carga la lista de documentos markdown de ``docs/``."""
        if not os.path.isdir(self._docs_dir):
            self._list.addItem("(sin documentación)")
            return
        names = [f for f in os.listdir(self._docs_dir) if f.endswith(".md")]
        # `index.md` primero y el resto alfabéticamente.
        names.sort(key=lambda n: (n != "index.md", n.lower()))
        for name in names:
            item = QListWidgetItem(name[:-3])
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _current_path(self):
        item = self._list.currentItem()
        if item is None:
            return None
        return os.path.join(self._docs_dir, item.data(Qt.ItemDataRole.UserRole))

    def _on_doc_selected(self, current, previous):
        if current is not None:
            self._render_document(self._current_path())

    def _on_anchor_clicked(self, url: QUrl):
        """Navega a otro documento cuando el enlace apunta a un .md local."""
        if url.isRelative():
            name = url.toString().split("#", 1)[0]
        else:
            name = os.path.basename(url.toLocalFile())
        if not name.endswith(".md"):
            return
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self._list.setCurrentItem(item)
                return
        self._render_document(os.path.join(self._docs_dir, name))

    def _render_document(self, path: str):
        if not path or not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as f:
                texto = f.read()
        except OSError as e:
            logger.error("No se pudo leer la documentación: %s", e)
            return
        self._current_doc = path
        self._browser.document().setDefaultStyleSheet(self._doc_css())
        self._browser.setMarkdown(texto)
        self._browser.verticalScrollBar().setValue(0)

    def _doc_css(self) -> str:
        """CSS del documento según el tema activo."""
        p = self._palette
        return f"""
            body {{ color: {p['text_primary']}; }}
            h1 {{ color: {p['primary']}; }}
            h2, h3, h4 {{ color: {p['secondary']}; }}
            a {{ color: {p['info']}; }}
            code, pre {{ color: {p['text_primary']}; }}
            table, th, td {{ border: 1px solid {p['outline_variant']}; }}
            th {{ background-color: {p['surface_container']}; }}
        """

    def _apply_widget_styles(self):
        """Aplica los colores de fondo/texto de la lista y el visor."""
        self._list.setStyleSheet(
            f"background-color: {self._palette['surface_low']}; "
            f"color: {self._palette['text_primary']};"
        )
        self._browser.setStyleSheet(
            f"background-color: {self._palette['surface']}; "
            f"color: {self._palette['text_primary']};"
        )

    def apply_theme(self, dark: bool):
        """Reaplica el tema a la lista, el visor y el documento actual."""
        self._palette = get_palette(dark)
        self._apply_widget_styles()
        if self._current_doc is not None:
            self._render_document(self._current_doc)
