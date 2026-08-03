"""
Constantes de la capa de presentación.

IDs de vistas para navegación y valores fijos de UI.
"""


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
