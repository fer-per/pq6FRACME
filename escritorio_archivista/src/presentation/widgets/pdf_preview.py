"""
Widget de vista previa del PDF.

Panel lateral con scroll continuo: renderiza todas las páginas en una
columna vertical. Las páginas visibles se renderizan en segundo plano
(thread pool) para no bloquear la UI, con caché de pixmaps y zoom.
"""
import logging
import bisect

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize, Signal, QObject, QRunnable, QThreadPool, Slot
from PySide6.QtGui import QPixmap, QImage

from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font
from src.presentation.theme.icons import theme_icon
from src.presentation.constants import (
    MODULE_ICONS, TOOLBAR_ICON_SIZE,
    ICON_PREV_PAGE, ICON_NEXT_PAGE, ICON_ZOOM_OUT, ICON_ZOOM_IN,
)

logger = logging.getLogger(__name__)

_SPACING = 8
_BUFFER_PX = 700


class _PageRenderTask(QRunnable):
    """Renderiza una página en segundo plano y devuelve los bytes PNG."""

    class Signals(QObject):
        rendered = Signal(int, object, int)  # page, bytes_png, doc_id
        failed = Signal(int)

    def __init__(self, renderer, page, zoom, doc_id):
        super().__init__()
        self.signals = self.Signals()
        self._renderer = renderer
        self._page = page
        self._zoom = zoom
        self._doc_id = doc_id

    @Slot()
    def run(self):
        try:
            data = self._renderer(self._page, self._zoom)
            if data:
                self.signals.rendered.emit(self._page, data, self._doc_id)
            else:
                self.signals.failed.emit(self._page)
        except Exception:
            self.signals.failed.emit(self._page)


class PDFPreview(QWidget):
    """
    Vista previa del PDF con scroll continuo y zoom.

    Todas las páginas se apilan verticalmente; solo se renderizan las
    cercanas a la ventana visible (con caché). El scroll actualiza la
    página actual y la emite via ``page_changed``.
    """

    page_changed = Signal(int)
    zoom_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        self._current_page = 1
        self._total_pages = 0
        self._zoom = 100
        self._renderer = None

        self._doc_id = 0
        self._page_labels = []
        self._empty_label = None
        self._page_dims = []        # (ancho, alto) por página
        self._page_tops = []        # posiciones Y acumuladas por página
        self._pixmaps = {}          # page -> QPixmap
        self._pending = set()       # páginas en renderizado

        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(3)
        self._nav_icons = {}
        self._setup_ui()

    # ─── UI ────────────────────────────────────────────────

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
        self._title_bar = title_bar
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_label = QLabel(f"{MODULE_ICONS['pdf_editor']} Vista Previa del PDF")
        title_label.setFont(get_font("body_sm_bold"))
        title_label.setStyleSheet(f"color: {self._palette['text_primary']}; background: transparent;")
        self._title_label = title_label
        title_layout.addWidget(title_label)
        layout.addWidget(title_bar)

        # Área de scroll continuo
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {self._palette['surface_high']}; border: none; }}"
        )

        self._pages_container = QWidget()
        self._pages_container.setStyleSheet("background: transparent;")
        self._pages_layout = QVBoxLayout(self._pages_container)
        self._pages_layout.setContentsMargins(8, 8, 8, 8)
        self._pages_layout.setSpacing(_SPACING)
        self._pages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._pages_container)
        layout.addWidget(self._scroll, stretch=1)

        # Barra de navegación
        nav_bar = QWidget()
        nav_bar.setFixedHeight(40)
        nav_bar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-top: 1px solid {self._palette['outline_variant']};"
        )
        self._nav_bar = nav_bar
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(4)

        btn_style = self._build_btn_style()
        self._nav_buttons = []
        self._prev_btn = self._create_nav_button(ICON_PREV_PAGE, "Página anterior", (32, 28))
        self._prev_btn.clicked.connect(self._prev_page)
        nav_layout.addWidget(self._prev_btn)

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

        self._next_btn = self._create_nav_button(ICON_NEXT_PAGE, "Página siguiente", (32, 28))
        self._next_btn.clicked.connect(self._next_page)
        nav_layout.addWidget(self._next_btn)

        nav_layout.addStretch()

        zoom_label = QLabel("Zoom:")
        zoom_label.setFont(get_font("body_sm"))
        zoom_label.setStyleSheet(f"color: {self._palette['text_secondary']}; background: transparent;")
        self._zoom_label = zoom_label
        nav_layout.addWidget(zoom_label)

        self._zoom_out_btn = self._create_nav_button(ICON_ZOOM_OUT, "Alejar", (25, 25), icon_size=9)
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

        self._zoom_in_btn = self._create_nav_button(ICON_ZOOM_IN, "Acercar", (28, 28), icon_size=14)
        self._zoom_in_btn.clicked.connect(lambda: self._adjust_zoom(25))
        nav_layout.addWidget(self._zoom_in_btn)

        layout.addWidget(nav_bar)

        # Señales de scroll
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

    # ─── API pública ───────────────────────────────────────

    def set_renderer(self, renderer):
        """Establece el callable ``renderer(page:int, zoom:int) -> bytes``."""
        self._renderer = renderer
        if self._total_pages > 0:
            self._render_visible()

    def _build_btn_style(self) -> str:
        """Estilo de los botones de navegación, dependiente del tema."""
        return f"""
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
                color: {self._palette['on_primary']};
            }}
            QPushButton:disabled {{
                color: {self._palette['text_disabled']};
                background-color: {self._palette['surface_container']};
            }}
        """

    def _create_nav_button(self, icon_path: str, tooltip: str,
                           size: tuple[int, int],
                           icon_size: int = TOOLBAR_ICON_SIZE) -> QPushButton:
        """Crea un botón de navegación/zoom con ícono."""
        btn = QPushButton()
        btn.setFixedSize(*size)
        btn.setIcon(theme_icon(icon_path, False))
        btn.setIconSize(QSize(icon_size, icon_size))
        btn.setStyleSheet(self._build_btn_style())
        btn.setToolTip(tooltip)
        self._nav_icons[btn] = icon_path
        self._nav_buttons.append(btn)
        return btn

    def apply_theme(self, dark: bool):
        """Reaplica los estilos dependientes del tema."""
        self._palette = get_palette(dark)

        self._title_bar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-bottom: 1px solid {self._palette['outline_variant']};"
        )
        self._title_label.setStyleSheet(
            f"color: {self._palette['text_primary']}; background: transparent;"
        )
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {self._palette['surface_high']}; border: none; }}"
        )
        self._nav_bar.setStyleSheet(
            f"background-color: {self._palette['surface_container']}; "
            f"border-top: 1px solid {self._palette['outline_variant']};"
        )

        btn_style = self._build_btn_style()
        for btn in self._nav_buttons:
            btn.setStyleSheet(btn_style)
        for btn, icon_path in self._nav_icons.items():
            btn.setIcon(theme_icon(icon_path, dark))

        label_style = f"color: {self._palette['text_secondary']}; background: transparent;"
        self._total_label.setStyleSheet(label_style)
        self._zoom_label.setStyleSheet(label_style)

        page_style = (
            f"color: {self._palette['text_disabled']}; "
            f"background-color: {self._palette['surface']}; "
            f"border: 1px solid {self._palette['outline_variant']};"
        )
        for label in self._page_labels:
            label.setStyleSheet(page_style)
        if self._empty_label is not None:
            self._empty_label.setStyleSheet(
                f"color: {self._palette['text_secondary']}; background: transparent;"
            )

    def reset_document(self):
        """Limpia el documento cargado (se usa al cambiar de PDF)."""
        self._doc_id += 1
        self._pixmaps.clear()
        self._pending.clear()
        self._total_pages = 0
        self._page_spin.setMaximum(1)
        self._page_spin.setValue(1)
        self._total_label.setText("/ 0")
        self._rebuild_document()

    def set_total_pages(self, total: int):
        if total == self._total_pages:
            return
        self._total_pages = max(0, total)
        self._page_spin.setMaximum(max(1, total))
        self._total_label.setText(f"/ {total}")
        self._rebuild_document()

    def set_current_page(self, page: int):
        page = max(1, min(page, self._total_pages or 1))
        self._current_page = page
        self._page_spin.blockSignals(True)
        self._page_spin.setValue(page)
        self._page_spin.blockSignals(False)
        self._scroll_to_page(page)

    # ─── Construcción del documento ────────────────────────

    def _rebuild_document(self):
        self._doc_id += 1
        self._pixmaps.clear()
        self._pending.clear()

        while self._pages_layout.count():
            item = self._pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._page_labels = []
        self._empty_label = None
        if self._total_pages <= 0:
            empty = QLabel("Cargue un PDF para visualizar")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {self._palette['text_secondary']}; background: transparent;"
            )
            empty.setFont(get_font("body"))
            empty.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
            )
            self._empty_label = empty
            self._pages_layout.addWidget(empty)
            self._pages_container.setMinimumHeight(0)
            self._scroll.verticalScrollBar().setValue(0)
            return

        default_w = int(595 * self._zoom / 100)
        default_h = int(842 * self._zoom / 100)
        self._page_dims = [(default_w, default_h)] * self._total_pages

        for page in range(1, self._total_pages + 1):
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(default_w, default_h)
            label.setStyleSheet(
                f"color: {self._palette['text_disabled']}; "
                f"background-color: {self._palette['surface']}; "
                f"border: 1px solid {self._palette['outline_variant']};"
            )
            label.setText(f"Página {page}\nCargando\u2026")
            self._pages_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._page_labels.append(label)

        self._recompute_geometry()
        self._scroll.verticalScrollBar().setValue(0)
        self._render_visible()

    def _recompute_geometry(self):
        tops = []
        y = 0
        for w, h in self._page_dims:
            tops.append(y)
            y += h + _SPACING
        self._page_tops = tops

        total_h = sum(h for _, h in self._page_dims) + _SPACING * (self._total_pages - 1)
        max_w = max((w for w, _ in self._page_dims), default=0)
        self._pages_container.setMinimumHeight(total_h)
        self._pages_container.setMinimumWidth(max_w)

    # ─── Renderizado perezoso ──────────────────────────────

    def _render_visible(self):
        if not self._renderer or self._total_pages <= 0:
            return
        sb = self._scroll.verticalScrollBar()
        y0 = sb.value() - _BUFFER_PX
        y1 = sb.value() + self._scroll.viewport().height() + _BUFFER_PX

        for page in range(1, self._total_pages + 1):
            top = self._page_tops[page - 1]
            if top > y1:
                break
            height = self._page_dims[page - 1][1]
            if top + height < y0:
                continue
            if page in self._pixmaps or page in self._pending:
                continue
            self._pending.add(page)
            task = _PageRenderTask(self._renderer, page, self._zoom, self._doc_id)
            task.signals.rendered.connect(self._on_page_rendered)
            task.signals.failed.connect(self._on_page_failed)
            self._thread_pool.start(task)

    def _on_page_rendered(self, page: int, data: bytes, doc_id: int):
        if doc_id != self._doc_id or page > self._total_pages:
            return
        self._pending.discard(page)
        image = QImage()
        image.loadFromData(data)
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return
        self._pixmaps[page] = pixmap
        label = self._page_labels[page - 1]
        label.setPixmap(pixmap)
        label.setText("")
        label.setFixedSize(pixmap.size())
        self._page_dims[page - 1] = (pixmap.width(), pixmap.height())
        self._recompute_geometry()

    def _on_page_failed(self, page: int):
        self._pending.discard(page)

    # ─── Navegación ────────────────────────────────────────

    def _on_scroll(self, value: int):
        self._render_visible()
        vh = self._scroll.viewport().height()
        center = value + vh // 2
        idx = bisect.bisect_right(self._page_tops, center) - 1
        page = max(1, idx + 1)
        if page != self._current_page:
            self._current_page = page
            self._page_spin.blockSignals(True)
            self._page_spin.setValue(page)
            self._page_spin.blockSignals(False)
            self.page_changed.emit(page)

    def _scroll_to_page(self, page: int):
        if self._total_pages <= 0:
            return
        top = self._page_tops[page - 1]
        sb = self._scroll.verticalScrollBar()
        sb.setValue(max(0, top - 4))

    def _prev_page(self):
        if self._current_page > 1:
            self.set_current_page(self._current_page - 1)

    def _next_page(self):
        if self._current_page < self._total_pages:
            self.set_current_page(self._current_page + 1)

    def _on_page_spin_changed(self, value: int):
        self.set_current_page(value)

    # ─── Zoom ──────────────────────────────────────────────

    def _on_zoom_changed(self, value: int):
        self._zoom = value
        self.zoom_changed.emit(value)
        self._doc_id += 1
        self._pixmaps.clear()
        self._pending.clear()

        default_w = int(595 * self._zoom / 100)
        default_h = int(842 * self._zoom / 100)
        for page, label in enumerate(self._page_labels, start=1):
            label.setPixmap(QPixmap())
            label.setText(f"Página {page}\nCargando\u2026")
            label.setFixedSize(default_w, default_h)
            self._page_dims[page - 1] = (default_w, default_h)

        self._recompute_geometry()
        self._scroll_to_page(self._current_page)
        self._render_visible()

    def _adjust_zoom(self, delta: int):
        new_val = max(25, min(400, self._zoom_spin.value() + delta))
        self._zoom_spin.setValue(new_val)
