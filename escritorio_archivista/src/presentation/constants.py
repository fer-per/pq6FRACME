"""
Constantes de la capa de presentación.

IDs de vistas para navegación y valores fijos de UI.
"""
from pathlib import Path


class ViewId:
    """Identificadores de vistas para navegación con sidebar."""
    WORKSPACE = 0
    ANALYZER = 1
    PROCESS = 2
    PDF_EDITOR = 3
    DOCS = 4
    SUPPORT = 5


# Dimensiones de UI
SIDEBAR_WIDTH_EXPANDED = 200
SIDEBAR_WIDTH_COLLAPSED = 52
SIDEBAR_ICON_SIZE = 20
PDF_THUMBNAIL_WIDTH = 144
PDF_THUMBNAIL_HEIGHT = 184
TOOLBAR_ICON_SIZE = 18
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 750

# Animación
ANIMATION_DURATION_MS = 200

# Recursos
APP_ROOT_DIR = Path(__file__).resolve().parents[2]
RESOURCES_DIR = APP_ROOT_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"

# Directorio de salida predeterminado para los fragmentos PDF.
# Se muestra en el front y cada corrida de fragmentación crea un nombre
# numerado: output, output (1), output (2), ...
DEFAULT_OUTPUT_DIR = str(APP_ROOT_DIR / "output")

# Directorio donde se guardan las configuraciones (perfiles) con nombre.
SESIONES_DIR = str(APP_ROOT_DIR / "sesiones")

# Directorio de documentación (markdown) consultable desde la aplicación.
DOCS_DIR = str(APP_ROOT_DIR / "docs")

# Íconos del toggle de tema (botón del header)
THEME_ICONS_DIR = ICONS_DIR / "theme"
ICON_MOON = str(THEME_ICONS_DIR / "luna.ico")  # luna → modo oscuro
ICON_SUN = str(THEME_ICONS_DIR / "sol.ico")    # sol → modo claro

# Íconos de módulos (sidebar): una carpeta por módulo
MODULE_ICON_DIRS = {
    "workspace": ICONS_DIR / "espaciotrabajo",
    "analyzer": ICONS_DIR / "analizador",
    "process": ICONS_DIR / "fragmentar",
    "pdf_editor": ICONS_DIR / "editorpdf",
    "docs": ICONS_DIR / "docs",
    "support": ICONS_DIR / "support",
}

ICON_WORKSPACE = str(MODULE_ICON_DIRS["workspace"] / "espaciotrabajo.ico")
ICON_ANALYZER = str(MODULE_ICON_DIRS["analyzer"] / "analizador.ico")
ICON_ANALYZE_CAM = str(MODULE_ICON_DIRS["analyzer"] / "camanalizador.ico")
ICON_PROCESS = str(MODULE_ICON_DIRS["process"] / "fragmentar.ico")
ICON_PDF_EDITOR = str(MODULE_ICON_DIRS["pdf_editor"] / "editorpdf.ico")

# Íconos de acciones del analizador
ICON_ANALYZE = str(MODULE_ICON_DIRS["analyzer"] / "creeper.ico")
ICON_CORRECT = str(MODULE_ICON_DIRS["analyzer"] / "corregir.ico")

# Íconos de acciones del editor de PDF (toolbar)
ICON_MOVE_UP = str(MODULE_ICON_DIRS["pdf_editor"] / "arriba.ico")
ICON_MOVE_DOWN = str(MODULE_ICON_DIRS["pdf_editor"] / "abajo.ico")
ICON_EXCLUDE = str(MODULE_ICON_DIRS["pdf_editor"] / "excluir.ico")
ICON_UNDO = str(MODULE_ICON_DIRS["pdf_editor"] / "deshacer.ico")
ICON_REDO = str(MODULE_ICON_DIRS["pdf_editor"] / "rehacer.ico")

# Íconos de acciones compartidas (usados por varios módulos)
ACCIONES_ICONS_DIR = ICONS_DIR / "acciones"
ICON_SAVE = str(ACCIONES_ICONS_DIR / "guardar.ico")
ICON_LOAD = str(ICONS_DIR / "fragmentar" / "documento.ico")

# Íconos del toggle de vista del PDF (header)
HEADER_ICONS_DIR = ICONS_DIR / "header"
ICON_VIEW_FULL = str(HEADER_ICONS_DIR / "vistacompleta.ico")  # vista previa oculta
ICON_VIEW_SPLIT = str(HEADER_ICONS_DIR / "vistapartida.ico")  # vista previa visible

# Íconos de navegación y zoom de la vista previa del PDF
PDFPREVIEW_ICONS_DIR = ICONS_DIR / "pdfpreview"
ICON_PREV_PAGE = str(PDFPREVIEW_ICONS_DIR / "flecha-atras.ico")
ICON_NEXT_PAGE = str(PDFPREVIEW_ICONS_DIR / "flecha-siguiente.ico")
ICON_ZOOM_OUT = str(PDFPREVIEW_ICONS_DIR / "menos.ico")
ICON_ZOOM_IN = str(PDFPREVIEW_ICONS_DIR / "mas.ico")

# Ícono de búsqueda (SearchBar)
SEARCH_ICONS_DIR = ICONS_DIR / "search"
ICON_SEARCH = str(SEARCH_ICONS_DIR / "lupa.ico")

# Ícono de selección de carpeta (fragmentación)
ICON_FOLDER = str(MODULE_ICON_DIRS["process"] / "carpeta.webp")
ICON_SELECT = str(MODULE_ICON_DIRS["process"] / "documento.ico")

# Animación del botón Menú (sidebar)
ICON_MENU = str(ICONS_DIR / "menu" / "menu.webp")

# Íconos de carga de documentos (DropZone del workspace): siluetas negras
# que se recolorizan según el tema (negro en claro, blanco en oscuro).
ICON_EXCEL = str(MODULE_ICON_DIRS["workspace"] / "excelnegro.ico")
ICON_PDF = str(MODULE_ICON_DIRS["workspace"] / "pdfnegro.ico")


class ModuleIcon:
    """Íconos de cada módulo (caracteres Unicode formales).

    Cada ícono evoca la función de su módulo para facilitar la navegación.
    """
    WORKSPACE = "\u25A4"    # ▤ carpeta/documento → carga y gestión de archivos
    ANALYZER = "\u2611"     # ☑ casilla verificada → validación de datos
    PROCESS = "\u2702"      # ✂ tijeras → fragmentación del PDF
    PDF_EDITOR = "\u25AD"   # ▭ página → edición de páginas PDF
    DOCS = "\u2261"         # ≡ líneas → documentación
    SUPPORT = "\u2139"      # ℹ info → soporte


MODULE_ICONS = {
    "workspace": ModuleIcon.WORKSPACE,
    "analyzer": ModuleIcon.ANALYZER,
    "process": ModuleIcon.PROCESS,
    "pdf_editor": ModuleIcon.PDF_EDITOR,
    "docs": ModuleIcon.DOCS,
    "support": ModuleIcon.SUPPORT,
}
