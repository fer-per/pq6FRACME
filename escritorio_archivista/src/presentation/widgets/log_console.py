"""
Widget de consola de logs interactiva.

Muestra mensajes del sistema con colores por tipo
(INFO, WARN, SUCCESS, ERR) en una consola estilo terminal.
"""
import logging
from typing import List

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont

from src.domain.entities import SystemLog
from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class LogConsole(QWidget):
    """
    Consola de logs estilo terminal con colores por tipo de mensaje.

    Colores:
    - INFO: azul claro
    - WARN: naranja
    - SUCCESS: verde
    - ERR: rojo
    """

    def __init__(self, title: str = "CONSOLA DE SISTEMA", parent=None):
        super().__init__(parent)
        self._palette = get_palette()
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header de la consola
        header = QWidget()
        header.setFixedHeight(28)
        header.setStyleSheet(
            f"background-color: {self._palette['tertiary']}; "
            f"border-top-left-radius: 6px; border-top-right-radius: 6px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel(f"─── {title} ───")
        title_label.setFont(get_font("mono"))
        title_label.setStyleSheet(
            f"color: {self._palette['on_tertiary']}; background: transparent;"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Indicador de estado
        self._status_label = QLabel("● LISTO")
        self._status_label.setFont(get_font("mono"))
        self._status_label.setStyleSheet(
            f"color: {self._palette['console_success']}; background: transparent;"
        )
        header_layout.addWidget(self._status_label)

        layout.addWidget(header)

        # Área de texto
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(get_font("mono"))
        self._text_edit.setStyleSheet(
            f"background-color: {self._palette['tertiary']}; "
            f"color: {self._palette['on_tertiary']}; "
            f"border: none; "
            f"border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; "
            f"padding: 6px 10px;"
        )
        self._text_edit.setMinimumHeight(80)
        layout.addWidget(self._text_edit)

    def add_log(self, log: SystemLog):
        """Agrega un mensaje de log con formato y color."""
        color = self._get_color(log.tipo)
        prefix_fmt = QTextCharFormat()
        prefix_fmt.setForeground(QColor(self._palette['on_tertiary']))
        prefix_fmt.setFont(get_font("mono"))

        tipo_fmt = QTextCharFormat()
        tipo_fmt.setForeground(QColor(color))
        tipo_fmt.setFont(get_font("mono"))
        tipo_fmt.setFontWeight(QFont.Weight.Bold)

        msg_fmt = QTextCharFormat()
        msg_fmt.setForeground(QColor(self._palette['on_tertiary']))
        msg_fmt.setFont(get_font("mono"))

        cursor = self._text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        cursor.insertText(f"[{log.timestamp}] ", prefix_fmt)
        cursor.insertText(f"[{log.tipo}] ", tipo_fmt)
        cursor.insertText(f"{log.mensaje}\n", msg_fmt)

        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    def add_logs(self, logs: List[SystemLog]):
        """Agrega múltiples logs."""
        for log in logs:
            self.add_log(log)

    def set_status(self, text: str, tipo: str = "INFO"):
        """Actualiza el indicador de estado."""
        color = self._get_color(tipo)
        self._status_label.setText(f"● {text}")
        self._status_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

    def clear(self):
        """Limpia la consola."""
        self._text_edit.clear()

    def _get_color(self, tipo: str) -> str:
        """Retorna el color para un tipo de log."""
        tipo = tipo.upper()
        if tipo == "SUCCESS":
            return self._palette['console_success']
        elif tipo == "WARN":
            return self._palette['console_warn']
        elif tipo == "ERR" or tipo == "ERROR":
            return self._palette['console_error']
        return self._palette['console_info']
