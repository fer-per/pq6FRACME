"""
Widget de barra de búsqueda reutilizable.

Incluye campo de texto con ícono de búsqueda,
debounce de 300ms, y botón de limpiar.
"""
from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtGui import QIcon

from src.presentation.theme.fonts import get_font
from src.presentation.theme.colors import get_palette
from src.presentation.theme.icons import tinted_pixmap
from src.presentation.constants import ICON_SEARCH


class SearchBar(QWidget):
    """
    Barra de búsqueda con debounce integrado.

    Emite search_changed después de 300ms sin escritura.
    """

    search_changed = Signal(str)  # Texto de búsqueda
    search_cleared = Signal()

    def __init__(self, placeholder: str = "Buscar...", parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._emit_search)

        self._setup_ui(placeholder)

    def _setup_ui(self, placeholder: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Campo de búsqueda
        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setFont(get_font("body"))
        self._input.setFixedHeight(32)
        self._search_action = self._input.addAction(
            QIcon(), QLineEdit.ActionPosition.LeadingPosition
        )
        self._set_search_icon(False)
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        # Botón limpiar
        self._clear_btn = QPushButton("✕")
        self._clear_btn.setFixedSize(32, 32)
        self._clear_btn.setProperty("flat", True)
        self._clear_btn.setToolTip("Limpiar búsqueda")
        self._clear_btn.clicked.connect(self._clear)
        self._clear_btn.setVisible(False)
        layout.addWidget(self._clear_btn)

    def _set_search_icon(self, dark: bool):
        """Aplica la lupa recolorizada según el tema."""
        pix = tinted_pixmap(ICON_SEARCH, dark).scaled(
            16, 16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._search_action.setIcon(QIcon(pix))

    def apply_theme(self, dark: bool):
        """Reaplica el ícono de búsqueda según el tema."""
        self._palette = get_palette(dark)
        self._set_search_icon(dark)

    def _on_text_changed(self, text: str):
        """Reinicia el timer de debounce."""
        self._clear_btn.setVisible(bool(text))
        self._debounce_timer.start()

    def _emit_search(self):
        """Emite la señal de búsqueda."""
        self.search_changed.emit(self._input.text())

    def _clear(self):
        """Limpia el campo de búsqueda."""
        self._input.clear()
        self.search_cleared.emit()

    def text(self) -> str:
        """Retorna el texto actual."""
        return self._input.text()
