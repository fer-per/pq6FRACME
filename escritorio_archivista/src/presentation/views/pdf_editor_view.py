"""
Vista del Editor de PDF — grid de thumbnails con selección, exclusión y reordenamiento.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QSizePolicy, QToolBar,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QColor, QPainter

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.pdf_editor_vm import PDFEditorVM
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font
from src.presentation.constants import PDF_THUMBNAIL_WIDTH, PDF_THUMBNAIL_HEIGHT

logger = logging.getLogger(__name__)


class ThumbnailWidget(QWidget):
    """Widget individual de thumbnail de página PDF."""

    clicked = Signal(int)
    double_clicked = Signal(int)

    def __init__(self, page_num: int, active: bool = True, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self._active = active
        self._selected = False
        self._palette = get_palette()

        self.setFixedSize(PDF_THUMBNAIL_WIDTH + 10, PDF_THUMBNAIL_HEIGHT + 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._image_label = QLabel()
        self._image_label.setFixedSize(PDF_THUMBNAIL_WIDTH, PDF_THUMBNAIL_HEIGHT)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet(
            f"background-color: {self._palette['surface_high']}; "
            f"border: 1px solid {self._palette['outline_variant']}; "
            f"border-radius: 4px;"
        )
        layout.addWidget(self._image_label)

        info = QHBoxLayout()
        self._page_label = QLabel(f"Pág {page_num}")
        self._page_label.setFont(get_font("body_xs"))
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setStyleSheet("background: transparent;")
        info.addWidget(self._page_label)

        self._status_label = QLabel("\u2713" if active else "\u2717")
        self._status_label.setFont(get_font("body_xs"))
        self._status_label.setStyleSheet(
            f"color: {self._palette['success'] if active else self._palette['error']}; "
            "background: transparent;"
        )
        info.addWidget(self._status_label)
        layout.addLayout(info)

        self._update_style()

    def set_image(self, png_bytes: bytes):
        if png_bytes:
            image = QImage()
            image.loadFromData(png_bytes)
            pixmap = QPixmap.fromImage(image).scaled(
                PDF_THUMBNAIL_WIDTH, PDF_THUMBNAIL_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_label.setPixmap(pixmap)

            if not self._active:
                overlay = QPixmap(pixmap.size())
                overlay.fill(QColor(0, 0, 0, 120))
                painter = QPainter(pixmap)
                painter.drawPixmap(0, 0, overlay)
                painter.end()
                self._image_label.setPixmap(pixmap)

    def set_active(self, active: bool):
        self._active = active
        self._status_label.setText("\u2713 Activa" if active else "\u2717 Excluida")
        color = self._palette['success'] if active else self._palette['error']
        self._status_label.setStyleSheet(f"color: {color}; background: transparent;")
        self._update_style()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def _update_style(self):
        if self._selected:
            border = f"2px solid {self._palette['primary']}"
        elif not self._active:
            border = f"1px solid {self._palette['error']}"
        else:
            border = f"1px solid {self._palette['outline_variant']}"

        bg = self._palette['selected_bg'] if self._selected else self._palette['surface']
        self.setStyleSheet(
            f"ThumbnailWidget {{ background-color: {bg}; "
            f"border: {border}; border-radius: 6px; }}"
        )

    def mousePressEvent(self, event):
        self.clicked.emit(self.page_num)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.page_num)


class PDFEditorView(QWidget):
    """Vista del editor de PDF con grid de thumbnails."""

    def __init__(self, container: Container, state: AppStateVM, parent=None):
        super().__init__(parent)
        self._container = container
        self._state = state
        self._vm = PDFEditorVM(container, state)
        self._palette = get_palette()
        self._thumbnails: list[ThumbnailWidget] = []
        self._selected_page = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-bottom: 1px solid {self._palette['outline_variant']}; "
            f"padding: 4px;"
        )

        self._move_up_btn = QPushButton("\u25B2 Mover Arriba")
        self._move_up_btn.setProperty("flat", True)
        self._move_up_btn.clicked.connect(self._on_move_up)
        toolbar.addWidget(self._move_up_btn)

        self._move_down_btn = QPushButton("\u25BC Mover Abajo")
        self._move_down_btn.setProperty("flat", True)
        self._move_down_btn.clicked.connect(self._on_move_down)
        toolbar.addWidget(self._move_down_btn)

        toolbar.addSeparator()

        self._toggle_btn = QPushButton("\u25A1 Excluir/Incluir")
        self._toggle_btn.setProperty("flat", True)
        self._toggle_btn.clicked.connect(self._on_toggle)
        toolbar.addWidget(self._toggle_btn)

        toolbar.addSeparator()

        self._undo_btn = QPushButton("\u21B6 Deshacer")
        self._undo_btn.setProperty("flat", True)
        self._undo_btn.setEnabled(False)
        self._undo_btn.clicked.connect(self._vm.undo)
        toolbar.addWidget(self._undo_btn)

        self._redo_btn = QPushButton("\u21B7 Rehacer")
        self._redo_btn.setProperty("flat", True)
        self._redo_btn.setEnabled(False)
        self._redo_btn.clicked.connect(self._vm.redo)
        toolbar.addWidget(self._redo_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self._save_btn = QPushButton("\u2B07 Guardar Config")
        self._save_btn.clicked.connect(self._vm.save_config)
        toolbar.addWidget(self._save_btn)

        layout.addWidget(toolbar)

        # Grid de thumbnails con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {self._palette['surface_low']}; border: none;")

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(8)
        self._grid_layout.setContentsMargins(12, 12, 12, 12)
        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll)

    def _connect_signals(self):
        self._vm.pages_updated.connect(self._refresh_grid)
        self._vm.undo_available.connect(self._undo_btn.setEnabled)
        self._vm.redo_available.connect(self._redo_btn.setEnabled)
        self._state.pdf_changed.connect(self._on_pdf_changed)

    def _on_pdf_changed(self):
        if self._state.pdf_total_pages > 0:
            self._create_thumbnails()

    def _create_thumbnails(self):
        for thumb in self._thumbnails:
            thumb.deleteLater()
        self._thumbnails.clear()

        active_pages = self._vm.get_active_pages()
        total = self._state.pdf_total_pages
        cols = 4

        for i in range(total):
            page = i + 1
            is_active = page in active_pages
            thumb = ThumbnailWidget(page, is_active)
            thumb.clicked.connect(self._on_thumbnail_clicked)
            thumb.double_clicked.connect(self._on_thumbnail_double_clicked)

            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(thumb, row, col)
            self._thumbnails.append(thumb)

            if i < 20 and self._state.pdf_path:
                try:
                    png = self._container.pdf_service.renderizar_pagina(
                        self._state.pdf_path, page, zoom=30,
                    )
                    thumb.set_image(png)
                except Exception as e:
                    logger.debug("Error renderizando thumbnail pág %d: %s", page, e)

    def _on_thumbnail_clicked(self, page: int):
        self._selected_page = page
        for thumb in self._thumbnails:
            thumb.set_selected(thumb.page_num == page)

    def _on_thumbnail_double_clicked(self, page: int):
        self._state.pdf_current_page = page
        main_window = self.window()
        if hasattr(main_window, '_render_current_page'):
            main_window._render_current_page()

    def _on_toggle(self):
        if self._selected_page:
            self._vm.toggle_page(self._selected_page)

    def _on_move_up(self):
        if self._selected_page:
            pages = self._vm.get_active_pages()
            if self._selected_page in pages:
                idx = pages.index(self._selected_page)
                if idx > 0:
                    self._vm.move_page(idx, idx - 1)

    def _on_move_down(self):
        if self._selected_page:
            pages = self._vm.get_active_pages()
            if self._selected_page in pages:
                idx = pages.index(self._selected_page)
                if idx < len(pages) - 1:
                    self._vm.move_page(idx, idx + 1)

    def _refresh_grid(self):
        active_pages = self._vm.get_active_pages()
        for thumb in self._thumbnails:
            thumb.set_active(thumb.page_num in active_pages)
