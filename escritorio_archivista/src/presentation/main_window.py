"""
Ventana principal de la aplicación.

Compone sidebar, header, área de contenido (QStackedWidget)
y panel lateral de PDF preview como dock widget.
"""
import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QSplitter, QDockWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from src.presentation.constants import ViewId, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
from src.presentation.theme.colors import get_palette
from src.presentation.theme.stylesheet import generate_stylesheet
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.widgets.sidebar import Sidebar
from src.presentation.widgets.header import Header
from src.presentation.widgets.pdf_preview import PDFPreview

from src.application.container import Container

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Ventana principal del Escritorio Archivista.

    Layout:
    ┌──────────────────────────────────────────────────┐
    │  HEADER                                          │
    ├──────┬───────────────────────┬───────────────────┤
    │      │                       │                   │
    │  S   │    CONTENT            │   PDF PREVIEW     │
    │  I   │    (QStackedWidget)   │   (DockWidget)    │
    │  D   │                       │                   │
    │  E   │                       │                   │
    │  B   │                       │                   │
    │  A   │                       │                   │
    │  R   │                       │                   │
    └──────┴───────────────────────┴───────────────────┘
    """

    def __init__(self, container: Container, state: AppStateVM):
        super().__init__()
        self._container = container
        self._state = state
        self._views = {}

        self.setWindowTitle("Escritorio Archivista — SGFD v2.0")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(1400, 850)

        self._preview_pdf_path = None

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()

        # Aplicar tema
        self.setStyleSheet(generate_stylesheet(self._state.dark_mode))

        logger.info("MainWindow inicializada.")

    def _setup_ui(self):
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._header = Header()
        main_layout.addWidget(self._header)

        # Cuerpo: sidebar + contenido
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        body_layout.addWidget(self._sidebar)

        # Contenido principal (QStackedWidget)
        self._stack = QStackedWidget()
        body_layout.addWidget(self._stack, stretch=1)

        main_layout.addWidget(body, stretch=1)

        # PDF Preview como DockWidget
        self._pdf_dock = QDockWidget("Vista Previa PDF", self)
        self._pdf_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self._pdf_preview = PDFPreview()
        self._pdf_preview.set_renderer(self._render_pdf_page)
        self._pdf_dock.setWidget(self._pdf_preview)
        self._pdf_dock.setMinimumWidth(320)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._pdf_dock)

        # Crear vistas placeholder (se reemplazan al registrar vistas reales)
        self._create_placeholder_views()

    def _create_placeholder_views(self):
        """Crea placeholders para las vistas que aún no están registradas."""
        from PySide6.QtWidgets import QLabel
        from src.presentation.theme.fonts import get_font

        placeholder_names = [
            ("📁 Workspace", ViewId.WORKSPACE),
            ("📊 Analizador", ViewId.ANALYZER),
            ("⚠️ Exclusiones", ViewId.EXCLUSIONS),
            ("✂️ Fragmentar", ViewId.PROCESS),
            ("📄 Editor PDF", ViewId.PDF_EDITOR),
            ("📖 Documentación", ViewId.DOCS),
            ("🛟 Soporte", ViewId.SUPPORT),
        ]
        for name, view_id in placeholder_names:
            placeholder = QLabel(f"{name}\n\nVista en construcción...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setFont(get_font("title_md"))
            idx = self._stack.addWidget(placeholder)
            self._views[view_id] = idx

    def register_view(self, view_id: int, widget: QWidget):
        """Registra una vista real reemplazando el placeholder."""
        if view_id in self._views:
            old_idx = self._views[view_id]
            old_widget = self._stack.widget(old_idx)
            self._stack.removeWidget(old_widget)
            old_widget.deleteLater()

        idx = self._stack.insertWidget(view_id, widget)
        self._views[view_id] = idx

    def navigate_to(self, view_id: int):
        """Navega a una vista por su ID."""
        if view_id in self._views:
            self._stack.setCurrentIndex(self._views[view_id])
            self._sidebar.set_active_view(view_id)
            logger.info("Navegación a vista: %d", view_id)

    def _setup_shortcuts(self):
        """Configura atajos de teclado."""
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_save)
        QShortcut(QKeySequence("Ctrl+N"), self, lambda: self.navigate_to(ViewId.WORKSPACE))
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.navigate_to(ViewId.WORKSPACE))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.navigate_to(ViewId.ANALYZER))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.navigate_to(ViewId.EXCLUSIONS))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.navigate_to(ViewId.PROCESS))

    def _connect_signals(self):
        """Conecta señales entre componentes."""
        self._sidebar.navigation_requested.connect(self.navigate_to)
        self._header.dual_view_toggled.connect(self._on_dual_view_toggled)
        self._header.theme_toggled.connect(self._on_theme_toggled)
        self._header.save_requested.connect(self._on_save)

        # PDF preview signals
        self._pdf_preview.page_changed.connect(self._on_page_changed)
        self._pdf_preview.zoom_changed.connect(self._on_zoom_changed)

        # State signals
        self._state.logs_changed.connect(self._on_logs_changed)
        self._state.pdf_changed.connect(self._on_pdf_state_changed)
        self._state.theme_changed.connect(self._on_theme_changed)

    def _on_dual_view_toggled(self, visible: bool):
        """Muestra/oculta la vista previa del PDF."""
        self._pdf_dock.setVisible(visible)
        self._state.dual_view_active = visible

    def _on_theme_toggled(self, dark: bool):
        """Cambia el tema de la aplicación."""
        self._state.dark_mode = dark
        self.setStyleSheet(generate_stylesheet(dark))
        self._state.add_log("INFO", f"Tema cambiado a {'oscuro' if dark else 'claro'}.")

    def _on_theme_changed(self, dark: bool):
        """Propaga el cambio de tema a vistas y widgets con estilos inline."""
        self._apply_theme(self._sidebar, dark)
        self._apply_theme(self._header, dark)
        self._apply_theme(self._pdf_preview, dark)
        for idx in self._views.values():
            self._apply_theme(self._stack.widget(idx), dark)

    @staticmethod
    def _apply_theme(widget: QWidget, dark: bool):
        """Invoca ``apply_theme`` en un widget si lo implementa."""
        apply = getattr(widget, 'apply_theme', None)
        if apply is not None:
            apply(dark)

    def _on_save(self):
        """Guarda la sesión actual."""
        try:
            session_path = "session.json"
            self._container.gestionar_sesion.guardar(
                session_path, self._state.to_dict()
            )
            self._state.add_log("SUCCESS", "Sesión guardada exitosamente.")
        except Exception as e:
            self._state.add_log("ERR", f"Error al guardar sesión: {e}")

    def _on_page_changed(self, page: int):
        """Actualiza la página del PDF en el estado (el preview maneja el render)."""
        self._syncing_from_preview = True
        try:
            self._state.pdf_current_page = page
        finally:
            self._syncing_from_preview = False

    def _on_zoom_changed(self, zoom: int):
        """Actualiza el zoom del PDF (el preview maneja el render)."""
        self._state.pdf_zoom = zoom

    def _on_logs_changed(self):
        """Los logs se manejan en Python logging, no en UI."""
        pass

    def _on_pdf_state_changed(self):
        """Actualiza la vista previa cuando cambia el estado del PDF."""
        if self._state.pdf_path != self._preview_pdf_path:
            self._preview_pdf_path = self._state.pdf_path
            self._pdf_preview.reset_document()
        self._pdf_preview.set_total_pages(self._state.pdf_total_pages)
        if not getattr(self, '_syncing_from_preview', False):
            self._pdf_preview.set_current_page(self._state.pdf_current_page)

    def _render_pdf_page(self, page: int, zoom: int):
        """Renderer para el preview continuo: devuelve PNG o None."""
        if not self._state.pdf_path:
            return None
        try:
            return self._container.pdf_service.renderizar_pagina(
                self._state.pdf_path, page, zoom,
            )
        except Exception as e:
            logger.error("Error renderizando PDF: %s", e)
            return None

    def _render_current_page(self):
        """Compat: desplaza la vista previa a la página actual del estado."""
        self._pdf_preview.set_current_page(self._state.pdf_current_page)

    @property
    def pdf_preview(self) -> PDFPreview:
        return self._pdf_preview

    @property
    def state(self) -> AppStateVM:
        return self._state

    @property
    def container(self) -> Container:
        return self._container
