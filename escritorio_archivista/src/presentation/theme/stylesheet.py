"""
Generador de hojas de estilo QSS dinámicas.

Genera QSS a partir de la paleta de colores activa,
permitiendo cambiar entre tema claro y oscuro en tiempo de ejecución.
"""
from src.presentation.theme.colors import get_palette


def generate_stylesheet(dark: bool = False) -> str:
    """Genera la hoja de estilo QSS completa para la aplicación."""
    p = get_palette(dark)
    return f"""
    /* ═══ GLOBAL ═══ */
    QMainWindow {{
        background-color: {p['background']};
    }}

    QWidget {{
        color: {p['text_primary']};
        font-family: "Segoe UI";
        font-size: 9pt;
    }}

    /* ═══ SCROLL BARS ═══ */
    QScrollBar:vertical {{
        background: {p['surface']};
        width: 8px;
        margin: 0;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {p['outline_variant']};
        min-height: 30px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p['outline']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {p['surface']};
        height: 8px;
        margin: 0;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {p['outline_variant']};
        min-width: 30px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {p['outline']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ═══ BUTTONS ═══ */
    QPushButton {{
        background-color: {p['primary']};
        color: {p['on_primary']};
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: bold;
        font-size: 9pt;
    }}
    QPushButton:hover {{
        background-color: {p['primary_hover']};
        color: {p['on_primary']};
    }}
    QPushButton:pressed {{
        background-color: {p['primary_pressed']};
        color: {p['on_primary']};
        padding-top: 9px;
    }}
    QPushButton:disabled {{
        background-color: {p['surface_high']};
        color: {p['text_disabled']};
        border: 1px solid {p['outline_variant']};
    }}
    QPushButton[flat="true"] {{
        background-color: {p['surface']};
        color: {p['text_primary']};
        border: 1px solid {p['outline_variant']};
    }}
    QPushButton[flat="true"]:hover {{
        background-color: {p['selected_bg']};
        border-color: {p['primary']};
        color: {p['primary']};
    }}
    QPushButton[flat="true"]:pressed {{
        background-color: {p['primary']};
        color: {p['on_primary']};
    }}

    /* Sidebar */
    QPushButton[sidebar="true"] {{
        background-color: transparent;
        color: {p['text_secondary']};
        border: none;
        border-left: 3px solid transparent;
        border-radius: 0;
        text-align: left;
        padding-left: 10px;
        padding-top: 8px;
        padding-bottom: 8px;
        font-weight: normal;
    }}
    QPushButton[sidebar="true"]:hover {{
        background-color: {p['surface_high']};
        color: {p['text_primary']};
    }}
    QPushButton[sidebar="true"]:checked {{
        background-color: {p['selected_bg']};
        color: {p['primary']};
        border-left: 3px solid {p['primary']};
        font-weight: bold;
    }}

    /* ═══ INPUTS ═══ */
    QLineEdit, QSpinBox {{
        background-color: {p['surface']};
        border: 1px solid {p['outline_variant']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {p['text_primary']};
        font-size: 9pt;
    }}
    QLineEdit:focus, QSpinBox:focus {{
        border: 2px solid {p['primary']};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 20px;
        border: none;
        background: {p['surface_container']};
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background: {p['surface_high']};
    }}

    /* ═══ COMBO BOX ═══ */
    QComboBox {{
        background-color: {p['surface']};
        border: 1px solid {p['outline_variant']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {p['text_primary']};
    }}
    QComboBox:hover {{
        border: 1px solid {p['outline']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p['surface']};
        border: 1px solid {p['outline_variant']};
        selection-background-color: {p['selected_bg']};
        selection-color: {p['text_primary']};
    }}

    /* ═══ TABLE ═══ */
    QTableWidget, QTableView {{
        background-color: {p['surface']};
        alternate-background-color: {p['surface_low']};
        border: 1px solid {p['outline_variant']};
        border-radius: 8px;
        gridline-color: {p['outline_variant']};
        selection-background-color: {p['selected_bg']};
        selection-color: {p['text_primary']};
    }}
    QHeaderView::section {{
        background-color: {p['surface_container']};
        color: {p['text_primary']};
        padding: 6px 8px;
        border: none;
        border-bottom: 2px solid {p['primary']};
        font-weight: bold;
        font-size: 8pt;
    }}

    /* ═══ TABS ═══ */
    QTabWidget::pane {{
        border: 1px solid {p['outline_variant']};
        border-radius: 8px;
        background: {p['surface']};
    }}
    QTabBar::tab {{
        background: {p['surface_container']};
        color: {p['text_secondary']};
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 9pt;
    }}
    QTabBar::tab:selected {{
        color: {p['primary']};
        border-bottom: 2px solid {p['primary']};
        background: {p['surface']};
    }}
    QTabBar::tab:hover:!selected {{
        background: {p['surface_high']};
    }}

    /* ═══ GROUP BOX ═══ */
    QGroupBox {{
        font-weight: bold;
        font-size: 9pt;
        border: 1px solid {p['outline_variant']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        color: {p['primary']};
    }}

    /* ═══ PROGRESS BAR ═══ */
    QProgressBar {{
        background-color: {p['surface_container']};
        border: none;
        border-radius: 6px;
        height: 12px;
        text-align: center;
        font-size: 7pt;
        color: {p['text_secondary']};
    }}
    QProgressBar::chunk {{
        background-color: {p['primary']};
        border-radius: 6px;
    }}

    /* ═══ TOOLTIPS ═══ */
    QToolTip {{
        background-color: {p['surface_highest']};
        color: {p['text_primary']};
        border: 1px solid {p['outline_variant']};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 8pt;
    }}

    /* ═══ LABELS ═══ */
    QLabel {{
        color: {p['text_primary']};
        background: transparent;
    }}
    QLabel[heading="true"] {{
        font-size: 16pt;
        font-weight: bold;
        color: {p['primary']};
    }}
    QLabel[subtitle="true"] {{
        font-size: 10pt;
        font-weight: bold;
    }}
    QLabel[caption="true"] {{
        font-size: 8pt;
        color: {p['text_secondary']};
    }}
    QLabel[hint="true"] {{
        font-size: 7pt;
        color: {p['text_disabled']};
    }}

    /* ═══ TOOLBAR ═══ */
    QToolBar {{
        background-color: {p['surface_container']};
        border: none;
        border-bottom: 1px solid {p['outline_variant']};
        padding: 4px;
        spacing: 4px;
    }}
    QToolBar::separator {{
        background-color: {p['outline_variant']};
        width: 1px;
        margin: 4px 6px;
    }}

    /* ═══ SPLITTER ═══ */
    QSplitter::handle {{
        background: {p['outline_variant']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* ═══ DOCK WIDGET ═══ */
    QDockWidget {{
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
        font-weight: bold;
        color: {p['text_primary']};
    }}
    QDockWidget::title {{
        background: {p['surface_container']};
        padding: 6px;
        border-bottom: 1px solid {p['outline_variant']};
    }}

    /* ═══ DIALOG ═══ */
    QDialog {{
        background-color: {p['surface']};
    }}

    /* ═══ MENU ═══ */
    QMenuBar {{
        background-color: {p['surface']};
        border-bottom: 1px solid {p['outline_variant']};
    }}
    QMenuBar::item:selected {{
        background-color: {p['selected_bg']};
    }}
    QMenu {{
        background-color: {p['surface']};
        border: 1px solid {p['outline_variant']};
        border-radius: 6px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {p['selected_bg']};
    }}
    """
