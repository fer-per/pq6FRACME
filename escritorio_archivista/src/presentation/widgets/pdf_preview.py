"""
Widget de vista previa del PDF.

Panel lateral con renderizado de página, navegación con scroll fluido y zoom.
Sin consola de logs integrada — la consola se maneja desde MainWindow.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class PDFPreview(QWidget):
    """
    Vista previa del PDF con navegación y zoom.

    Sin consola — solo renderizado, navegación y zoom.
    """

    page_changed = Signal(int)
    zoom_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        self._current_page = 1
        self._total_pages = 0
        self._zoom = 100
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Título
        title_bar = QWidget()
        title_bar.setFixedHeight(32)
        title_bar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-bottom: 1px solid {self._palette['outline_variant']};"
        )
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_label = QLabel("\u25A1 Vista Previa del PDF")
        title_label.setFont(get_font("body_sm_bold"))
        title_label.setStyleSheet(f"color: {self._palette['text_primary']}; background: transparent;")
        title_layout.addWidget(title_label)
        layout.addWidget(title_bar)

        # Área de renderizado con scroll fluido
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {self._palette['surface_high']}; border: none; }}"
        )

        # Container para la imagen dentro del scroll
        self._page_container = QWidget()
        self._page_container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(self._page_container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._page_label = QLabel("Cargue un PDF para visualizar")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setStyleSheet(
            f"color: {self._palette['text_secondary']}; background: transparent;"
        )
        self._page_label.setFont(get_font("body"))
        self._page_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        container_layout.addWidget(self._page_label)

        self._scroll.setWidget(self._page_container)
        layout.addWidget(self._scroll, stretch=1)

        # Barra de navegación
        nav_bar = QWidget()
        nav_bar.setFixedHeight(40)
        nav_bar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-top: 1px solid {self._palette['outline_variant']};"
        )
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(4)

        # Botones de navegación con estilo uniforme
        btn_style = f"""
            QPushButton {{
                background-color: {self._palette['surface']};
                color: {self._palette['text_primary']};
                border: 1px solid {self._palette['outline_variant']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9pt;
                font-weight: bold;
                min-width: 28px;
            }}
            QPushButton:hover {{
                background-color: {self._palette['selected_bg']};
                border-color: {self._palette['primary']};
            }}
            QPushButton:pressed {{
                background-color: {self._palette['primary']};
                color: {self._palette['surface']};
            }}
            QPushButton:disabled {{
                color: {self._palette['text_disabled']};
                background-color: {self._palette['surface_container']};
            }}
        """

        self._prev_btn = QPushButton("\u25C0")
        self._prev_btn.setFixedSize(32, 28)
        self._prev_btn.setStyleSheet(btn_style)
        self._prev_btn.setToolTip("Página anterior")
        self._prev_btn.clicked.connect(self._prev_page)
        nav_layout.addWidget(self._prev_btn)

        # Indicador de página
        self._page_spin = QSpinBox()
        self._page_spin.setMinimum(1)
        self._page_spin.setMaximum(1)
        self._page_spin.setFixedWidth(65)
        self._page_spin.setFixedHeight(28)
        self._page_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_spin.valueChanged.connect(self._on_page_spin_changed)
        nav_layout.addWidget(self._page_spin)

        self._total_label = QLabel("/ 0")
        self._total_label.setFont(get_font("body_sm"))
        self._total_label.setStyleSheet(f"color: {self._palette['text_secondary']}; background: transparent;")
        nav_layout.addWidget(self._total_label)

        self._next_btn = QPushButton("\u25B6")
        self._next_btn.setFixedSize(32, 28)
        self._next_btn.setStyleSheet(btn_style)
        self._next_btn.setToolTip("Página siguiente")
        self._next_btn.clicked.connect(self._next_page)
        nav_layout.addWidget(self._next_btn)

        nav_layout.addStretch()

        # Zoom
        zoom_label = QLabel("Zoom:")
        zoom_label.setFont(get_font("body_sm"))
        zoom_label.setStyleSheet(f"color: {self._palette['text_secondary']}; background: transparent;")
        nav_layout.addWidget(zoom_label)

        self._zoom_out_btn = QPushButton("\u2212")
        self._zoom_out_btn.setFixedSize(28, 28)
        self._zoom_out_btn.setStyleSheet(btn_style)
        self._zoom_out_btn.clicked.connect(lambda: self._adjust_zoom(-25))
        nav_layout.addWidget(self._zoom_out_btn)

        self._zoom_spin = QSpinBox()
        self._zoom_spin.setMinimum(25)
        self._zoom_spin.setMaximum(400)
        self._zoom_spin.setValue(100)
        self._zoom_spin.setSuffix("%")
        self._zoom_spin.setSingleStep(25)
        self._zoom_spin.setFixedWidth(75)
        self._zoom_spin.setFixedHeight(28)
        self._zoom_spin.valueChanged.connect(self._on_zoom_changed)
        nav_layout.addWidget(self._zoom_spin)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedSize(28, 28)
        self._zoom_in_btn.setStyleSheet(btn_style)
        self._zoom_in_btn.clicked.connect(lambda: self._adjust_zoom(25))
        nav_layout.addWidget(self._zoom_in_btn)

        layout.addWidget(nav_bar)

    def set_page_image(self, png_bytes: bytes):
        """Establece la imagen de la página desde bytes PNG."""
        if png_bytes is None:
            self._page_label.setText("No se pudo renderizar la página")
            return

        image = QImage()
        image.loadFromData(png_bytes)
        pixmap = QPixmap.fromImage(image)
        self._page_label.setPixmap(pixmap)
        self._page_label.adjustSize()

    def set_total_pages(self, total: int):
        self._total_pages = total
        self._page_spin.setMaximum(max(1, total))
        self._total_label.setText(f"/ {total}")

    def set_current_page(self, page: int):
        self._current_page = page
        self._page_spin.blockSignals(True)
        self._page_spin.setValue(page)
        self._page_spin.blockSignals(False)

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._page_spin.setValue(self._current_page)

    def _next_page(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._page_spin.setValue(self._current_page)

    def _on_page_spin_changed(self, value: int):
        self._current_page = value
        self.page_changed.emit(value)

    def _on_zoom_changed(self, value: int):
        self._zoom = value
        self.zoom_changed.emit(value)

    def _adjust_zoom(self, delta: int):
        new_val = max(25, min(400, self._zoom_spin.value() + delta))
        self._zoom_spin.setValue(new_val)
