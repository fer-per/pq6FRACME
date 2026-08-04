"""
Constantes de la capa de presentación.

IDs de vistas para navegación y valores fijos de UI.
"""
from pathlib import Path


class ViewId:
    """Identificadores de vistas para navegación con sidebar."""
    WORKSPACE = 0
    ANALYZER = 1
    EXCLUSIONS = 2
    PROCESS = 3
    PDF_EDITOR = 4
    DOCS = 5
    SUPPORT = 6


# Dimensiones de UI
SIDEBAR_WIDTH_EXPANDED = 200
SIDEBAR_WIDTH_COLLAPSED = 52
SIDEBAR_ICON_SIZE = 20
PDF_THUMBNAIL_WIDTH = 130
PDF_THUMBNAIL_HEIGHT = 184
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 750

# Animación
ANIMATION_DURATION_MS = 200

# Recursos
RESOURCES_DIR = Path(__file__).resolve().parents[2] / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"

# Íconos del toggle de tema (botón del header)
THEME_ICONS_DIR = ICONS_DIR / "theme"
ICON_MOON = str(THEME_ICONS_DIR / "luna.ico")  # luna → modo oscuro
ICON_SUN = str(THEME_ICONS_DIR / "sol.ico")    # sol → modo claro

# Íconos de módulos (sidebar): una carpeta por módulo
MODULE_ICON_DIRS = {
    "workspace": ICONS_DIR / "espaciotrabajo",
    "analyzer": ICONS_DIR / "analizador",
    "exclusions": ICONS_DIR / "exclusiones",
    "process": ICONS_DIR / "fragmentar",
    "pdf_editor": ICONS_DIR / "editorpdf",
    "docs": ICONS_DIR / "docs",
    "support": ICONS_DIR / "support",
}

ICON_WORKSPACE = str(MODULE_ICON_DIRS["workspace"] / "espaciotrabajo.ico")
ICON_ANALYZER = str(MODULE_ICON_DIRS["analyzer"] / "analizador.ico")
ICON_EXCLUSIONS = str(MODULE_ICON_DIRS["exclusions"] / "exclusiones.ico")
ICON_PROCESS = str(MODULE_ICON_DIRS["process"] / "fragmentar.ico")
ICON_PDF_EDITOR = str(MODULE_ICON_DIRS["pdf_editor"] / "editorpdf.ico")

# Ícono de selección de carpeta (fragmentación)
ICON_FOLDER = str(MODULE_ICON_DIRS["process"] / "carpeta.webp")

# Animación del botón Menú (sidebar)
ICON_MENU = str(ICONS_DIR / "menu" / "menu.webp")

# Íconos de carga de documentos (DropZone del workspace): alternan según tema
# En tema claro (fondo claro) se usan íconos oscuros; en oscuro, íconos claros.
ICON_EXCEL_LIGHT = str(MODULE_ICON_DIRS["workspace"] / "excelnegro.ico")   # tema claro → ícono negro
ICON_EXCEL_DARK = str(MODULE_ICON_DIRS["workspace"] / "excelblanco.ico")   # tema oscuro → ícono blanco
ICON_PDF_LIGHT = str(MODULE_ICON_DIRS["workspace"] / "pdfnegro.ico")       # tema claro → ícono negro
ICON_PDF_DARK = str(MODULE_ICON_DIRS["workspace"] / "pdfblanco.ico")       # tema oscuro → ícono blanco


class ModuleIcon:
    """Íconos de cada módulo (caracteres Unicode formales).

    Cada ícono evoca la función de su módulo para facilitar la navegación.
    """
    WORKSPACE = "\u25A4"    # ▤ carpeta/documento → carga y gestión de archivos
    ANALYZER = "\u2611"     # ☑ casilla verificada → validación de datos
    EXCLUSIONS = "\u2691"   # ⚑ bandera → exclusiones/saltos
    PROCESS = "\u2702"      # ✂ tijeras → fragmentación del PDF
    PDF_EDITOR = "\u25AD"   # ▭ página → edición de páginas PDF
    DOCS = "\u2261"         # ≡ líneas → documentación
    SUPPORT = "\u2139"      # ℹ info → soporte


MODULE_ICONS = {
    "workspace": ModuleIcon.WORKSPACE,
    "analyzer": ModuleIcon.ANALYZER,
    "exclusions": ModuleIcon.EXCLUSIONS,
    "process": ModuleIcon.PROCESS,
    "pdf_editor": ModuleIcon.PDF_EDITOR,
    "docs": ModuleIcon.DOCS,
    "support": ModuleIcon.SUPPORT,
}
