"""
Factory de la aplicación PySide6.

Crea la instancia de QApplication, el Container DI, el AppState
y la MainWindow. Registra todas las vistas.
"""
import logging
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.main_window import MainWindow
from src.presentation.constants import ViewId

logger = logging.getLogger(__name__)


def create_app(argv: list) -> QApplication:
    """
    Crea y configura la aplicación completa.

    Returns:
        QApplication lista para ejecutar con app.exec().
    """
    app = QApplication(argv)
    app.setApplicationName("Escritorio Archivista")
    app.setOrganizationName("SGFD")
    app.setApplicationVersion("2.0")

    logger.info("Creando aplicación...")

    # Crear Container DI
    container = Container()

    # Crear estado global
    state = AppStateVM()

    # Crear ventana principal
    window = MainWindow(container, state)

    # Registrar vistas
    _register_views(window, container, state)

    # Arrancar con estado "sin cambios": no hay que guardar nada aún.
    state.mark_saved()

    # Log inicial
    state.add_log("INFO", "Sistema listo. Bienvenido al Escritorio Archivista.")

    # Iniciar en el Espacio de Trabajo, ocupando toda la pantalla
    # pero sin ocultar la barra de tareas de Windows.
    window.navigate_to(ViewId.WORKSPACE)
    window.showMaximized()
    logger.info("Aplicación iniciada.")

    return app


def _register_views(window: MainWindow, container: Container, state: AppStateVM):
    """Registra todas las vistas en la MainWindow."""
    try:
        from src.presentation.views.workspace_view import WorkspaceView
        workspace = WorkspaceView(container, state)
        window.register_view(ViewId.WORKSPACE, workspace)
    except ImportError as e:
        logger.warning("WorkspaceView no disponible: %s", e)

    try:
        from src.presentation.views.analyzer_view import AnalyzerView
        analyzer = AnalyzerView(container, state)
        window.register_view(ViewId.ANALYZER, analyzer)
    except ImportError as e:
        logger.warning("AnalyzerView no disponible: %s", e)

    try:
        from src.presentation.views.process_view import ProcessView
        process = ProcessView(container, state)
        window.register_view(ViewId.PROCESS, process)
    except ImportError as e:
        logger.warning("ProcessView no disponible: %s", e)

    try:
        from src.presentation.views.pdf_editor_view import PDFEditorView
        pdf_editor = PDFEditorView(container, state)
        window.register_view(ViewId.PDF_EDITOR, pdf_editor)
    except ImportError as e:
        logger.warning("PDFEditorView no disponible: %s", e)
