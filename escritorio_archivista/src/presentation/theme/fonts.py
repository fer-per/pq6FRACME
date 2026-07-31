"""
Tipografía del sistema de diseño.

Define fuentes, tamaños y pesos para toda la aplicación.
"""
from PySide6.QtGui import QFont


FONTS = {
    "title_lg":     ("Segoe UI", 18, QFont.Weight.Bold),
    "title_md":     ("Segoe UI", 13, QFont.Weight.Bold),
    "title_xl":     ("Segoe UI", 16, QFont.Weight.Bold),
    "subtitle":     ("Segoe UI", 10, QFont.Weight.Bold),
    "body":         ("Segoe UI", 9,  QFont.Weight.Normal),
    "body_sm":      ("Segoe UI", 8,  QFont.Weight.Normal),
    "body_sm_bold": ("Segoe UI", 8,  QFont.Weight.Bold),
    "body_xs":      ("Segoe UI", 7,  QFont.Weight.Normal),
    "body_lg":      ("Segoe UI", 10, QFont.Weight.Normal),
    "mono":         ("Courier New", 8, QFont.Weight.Normal),
    "mono_bold":    ("Courier New", 10, QFont.Weight.Bold),
    "mono_body":    ("Courier New", 9, QFont.Weight.Normal),
    "button":       ("Segoe UI", 9,  QFont.Weight.Bold),
    "button_lg":    ("Segoe UI", 11, QFont.Weight.Bold),
    "icon":         ("Segoe UI", 14, QFont.Weight.Normal),
    "icon_lg":      ("Segoe UI", 22, QFont.Weight.Normal),
}


def get_font(name: str) -> QFont:
    """Crea y retorna un QFont según el nombre del estilo."""
    if name not in FONTS:
        name = "body"
    family, size, weight = FONTS[name]
    font = QFont(family, size)
    font.setWeight(weight)
    return font
