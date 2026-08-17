"""
Vista del Editor de PDF — grid de thumbnails con selección, exclusión y reordenamiento.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QSizePolicy, QToolBar,
)
from PySide6.QtCore import Qt, QSize, Signal, QObject, QRunnable, QThreadPool, Slot
from PySide6.QtGui import QPixmap, QImage, QColor, QPainter

from src.application.container import Container
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.pdf_editor_vm import PDFEditorVM
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font
from src.presentation.theme.icons import theme_icon
from src.presentation.constants import (
    PDF_THUMBNAIL_WIDTH, PDF_THUMBNAIL_HEIGHT, TOOLBAR_ICON_SIZE,
    ICON_MOVE_UP, ICON_MOVE_DOWN, ICON_EXCLUDE, ICON_UNDO, ICON_REDO,
    ICON_SAVE,
)

logger = logging.getLogger(__name__)


class _ThumbnailRenderTask(QRunnable):
    """Renderiza un thumbnail en segundo plano sin bloquear la UI."""

    class Signals(QObject):
        rendered = Signal(int, object, int)  # page, png_bytes, doc_id

    def __init__(self, renderer, page: int, doc_id: int):
        super().__init__()
        self.signals = self.Signals()
        self._renderer = renderer
        self._page = page
        self._doc_id = doc_id

    @Slot()
    def run(self):
        try:
            data = self._renderer(self._page)
            if data:
                self.signals.rendered.emit(self._page, data, self._doc_id)
        except Exception as e:
            logger.debug("Error renderizando thumbnail pág %d: %s", self._page, e)


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
        self._status_label.setText("\u2713" if active else "\u2717")
        color = self._palette['success'] if active else self._palette['error']
        self._status_label.setStyleSheet(f"color: {color}; background: transparent;")
        self._update_style()

    def set_number(self, n: int):
        """Renumera la hoja mostrada según su posición en la secuencia (1-based)."""
        self._page_label.setText(f"Pág {n}")

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def apply_theme(self, dark: bool):
        """Reaplica los colores del thumbnail al cambiar el tema."""
        self._palette = get_palette(dark)
        self._page_label.setStyleSheet(
            f"color: {self._palette['text_primary']}; background: transparent;"
        )
        color = self._palette['success'] if self._active else self._palette['error']
        self._status_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )
        self._update_style()

    def _update_style(self):
        """Aplica borde y fondo del widget y de la lámina según el estado."""
        if self._selected:
            border_widget = f"2px solid {self._palette['primary']}"
        elif not self._active:
            border_widget = f"1px solid {self._palette['error']}"
        else:
            border_widget = f"1px solid {self._palette['outline_variant']}"
        border_img = (
            f"2px solid {self._palette['primary']}"
            if self._selected else
            f"1px solid {self._palette['outline_variant']}"
        )

        bg = self._palette['selected_bg'] if self._selected else self._palette['surface']
        self.setStyleSheet(
            f"ThumbnailWidget {{ background-color: {bg}; "
            f"border: {border_widget}; border-radius: 6px; }}"
        )
        self._image_label.setStyleSheet(
            f"background-color: {self._palette['surface_high']}; "
            f"border: {border_img}; border-radius: 4px;"
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
        self._thumb_by_page: dict = {}
        self._selected_page = None
        self._doc_id = 0
        self._pending: set = set()
        self._rendered: set = set()
        self._thumb_tops: dict = {}
        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(2)
        self._last_total = 0
        self._last_path = None
        self._tool_icons = {}
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
        self._toolbar = toolbar

        self._move_up_btn = self._create_tool_button("Mover Arriba", ICON_MOVE_UP)
        self._move_up_btn.clicked.connect(self._on_move_up)
        toolbar.addWidget(self._move_up_btn)

        self._move_down_btn = self._create_tool_button("Mover Abajo", ICON_MOVE_DOWN)
        self._move_down_btn.clicked.connect(self._on_move_down)
        toolbar.addWidget(self._move_down_btn)

        toolbar.addSeparator()

        self._toggle_btn = self._create_tool_button("Excluir/Incluir", ICON_EXCLUDE)
        self._toggle_btn.clicked.connect(self._on_toggle)
        toolbar.addWidget(self._toggle_btn)

        toolbar.addSeparator()

        self._undo_btn = self._create_tool_button("Deshacer", ICON_UNDO)
        self._undo_btn.setEnabled(False)
        self._undo_btn.clicked.connect(self._vm.undo)
        toolbar.addWidget(self._undo_btn)

        self._redo_btn = self._create_tool_button("Rehacer", ICON_REDO)
        self._redo_btn.setEnabled(False)
        self._redo_btn.clicked.connect(self._vm.redo)
        toolbar.addWidget(self._redo_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self._save_btn = self._create_tool_button(" Guardar Config", ICON_SAVE)
        self._save_btn.clicked.connect(self._vm.save_config)
        toolbar.addWidget(self._save_btn)

        layout.addWidget(toolbar)

        # Grid de thumbnails con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {self._palette['surface_low']}; border: none;")
        self._scroll = scroll
        scroll.verticalScrollBar().valueChanged.connect(self._render_visible)

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(8)
        self._grid_layout.setContentsMargins(12, 12, 12, 12)
        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll)

    def _create_tool_button(self, text: str, icon_path: str) -> QPushButton:
        """Crea un botón plano del toolbar con ícono escalado."""
        btn = QPushButton(text)
        btn.setProperty("flat", True)
        btn.setIcon(theme_icon(icon_path, False))
        btn.setIconSize(QSize(TOOLBAR_ICON_SIZE, TOOLBAR_ICON_SIZE))
        self._tool_icons[btn] = icon_path
        return btn

    def _connect_signals(self):
        self._vm.pages_updated.connect(self._refresh_grid)
        self._vm.undo_available.connect(self._undo_btn.setEnabled)
        self._vm.redo_available.connect(self._redo_btn.setEnabled)
        self._state.pdf_changed.connect(self._on_pdf_changed)

    def _on_pdf_changed(self):
        # Reconstruye solo cuando cambia el documento (path o nº de páginas),
        # no en cada cambio de página, para no perder las miniaturas.
        total = self._state.pdf_total_pages
        path = self._state.pdf_path
        if total > 0 and (total != self._last_total or path != self._last_path):
            self._last_total = total
            self._last_path = path
            self._create_thumbnails()

    def _create_thumbnails(self):
        for thumb in self._thumbnails:
            thumb.deleteLater()
        self._thumbnails.clear()
        self._thumb_by_page.clear()
        self._doc_id += 1
        self._pending.clear()
        self._rendered.clear()
        self._thumb_tops.clear()
        self._sync_preview()

        active = self._vm.get_active_pages()
        active_set = set(active)
        total = self._state.pdf_total_pages
        excluded = [p for p in range(1, total + 1) if p not in active_set]
        ordered = list(active) + excluded
        cols = 4
        thumb_w = PDF_THUMBNAIL_WIDTH + 10
        thumb_h = PDF_THUMBNAIL_HEIGHT + 30
        spacing = 8

        for i, page in enumerate(ordered):
            is_active = page in active_set
            thumb = ThumbnailWidget(page, is_active)
            thumb.clicked.connect(self._on_thumbnail_clicked)
            thumb.double_clicked.connect(self._on_thumbnail_double_clicked)

            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(thumb, row, col)
            self._thumbnails.append(thumb)
            self._thumb_by_page[page] = thumb
            self._thumb_tops[page] = row * (thumb_h + spacing)
            thumb.set_number(i + 1)

        # El widget de contenido debe crecer por su contenido para que el
        # QScrollArea active la barra vertical (widgetResizable=True fuerza
        # el alto al viewport, por lo que la altura mínima marca el rango).
        rows = (len(ordered) + cols - 1) // cols
        content_h = rows * (thumb_h + spacing) - spacing + 24
        self._grid_widget.setMinimumSize(cols * thumb_w + (cols - 1) * spacing + 24, content_h)

        # Renderiza solo lo visible; el scroll completa el resto
        self._render_visible()

    def _render_visible(self):
        """Renderiza en segundo plano los thumbnails cercanos al viewport."""
        if not self._state.pdf_path or not self._thumbnails:
            return
        sb = self._scroll.verticalScrollBar()
        y0 = sb.value() - 300
        y1 = sb.value() + self._scroll.viewport().height() + 300

        for thumb in self._thumbnails:
            if thumb.page_num in self._pending or thumb.page_num in self._rendered:
                continue
            top = self._thumb_tops.get(thumb.page_num, 0)
            bottom = top + PDF_THUMBNAIL_HEIGHT + 30
            if bottom < y0 or top > y1:
                continue
            self._pending.add(thumb.page_num)
            page = thumb.page_num
            task = _ThumbnailRenderTask(
                lambda p=page: self._container.pdf_service.renderizar_pagina(
                    self._state.pdf_path, p, zoom=30,
                ),
                page,
                self._doc_id,
            )
            task.signals.rendered.connect(self._on_thumbnail_rendered)
            self._thread_pool.start(task)

    def _on_thumbnail_rendered(self, page: int, data: bytes, doc_id: int):
        if doc_id != self._doc_id:
            return
        self._pending.discard(page)
        self._rendered.add(page)
        # La imagen se asigna por página física (no por índice): los
        # thumbnails no están en orden físico cuando hay hojas excluidas.
        thumb = self._thumb_by_page.get(page)
        if thumb is not None:
            thumb.set_image(data)

    def _on_thumbnail_clicked(self, page: int):
        self._selected_page = page
        for thumb in self._thumbnails:
            thumb.set_selected(thumb.page_num == page)

        # Navega la vista previa a la posición (nuevo nº de hoja) del editor.
        active = self._vm.get_active_pages()
        if page in active:
            self._state.pdf_current_page = active.index(page) + 1
            main_window = self.window()
            if hasattr(main_window, '_render_current_page'):
                main_window._render_current_page()

    def _on_thumbnail_double_clicked(self, page: int):
        active = self._vm.get_active_pages()
        if page in active:
            self._state.pdf_current_page = active.index(page) + 1
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
        """Reordena el grid según el orden de las páginas activas (Mover ↑/↓).

        Reubica los thumbnails existentes sin volver a renderizarlos ni
        perder la selección actual.
        """
        active = self._vm.get_active_pages()
        active_set = set(active)
        total = self._state.pdf_total_pages
        excluded = [p for p in range(1, total + 1) if p not in active_set]
        ordered = list(active) + excluded

        thumb_by_page = {t.page_num: t for t in self._thumbnails}
        cols = 4
        thumb_w = PDF_THUMBNAIL_WIDTH + 10
        thumb_h = PDF_THUMBNAIL_HEIGHT + 30
        spacing = 8

        self._thumb_tops.clear()
        idx = 0
        for page in ordered:
            thumb = thumb_by_page.get(page)
            if thumb is None:
                continue
            row = idx // cols
            col = idx % cols
            self._grid_layout.addWidget(thumb, row, col)
            thumb.set_active(page in active_set)
            thumb.set_selected(page == self._selected_page)
            thumb.set_number(idx + 1)
            self._thumb_tops[page] = row * (thumb_h + spacing)
            idx += 1

        rows = (idx + cols - 1) // cols
        content_h = rows * (thumb_h + spacing) - spacing + 24
        self._grid_widget.setMinimumSize(
            cols * thumb_w + (cols - 1) * spacing + 24, content_h
        )
        self._sync_preview()

    def _sync_preview(self):
        """Sincroniza la vista previa con el orden y las páginas activas del editor."""
        active = self._vm.get_active_pages()
        main_window = self.window()
        if hasattr(main_window, 'pdf_preview'):
            main_window.pdf_preview.set_active_sequence(active)

    def apply_theme(self, dark: bool):
        """Reaplica el tema al toolbar y a los thumbnails."""
        self._palette = get_palette(dark)
        for btn, icon_path in self._tool_icons.items():
            btn.setIcon(theme_icon(icon_path, dark))
        self._toolbar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-bottom: 1px solid {self._palette['outline_variant']}; "
            f"padding: 4px;"
        )
        self._scroll.setStyleSheet(
            f"background-color: {self._palette['surface_low']}; border: none;"
        )
        for thumb in self._thumbnails:
            thumb.apply_theme(dark)
