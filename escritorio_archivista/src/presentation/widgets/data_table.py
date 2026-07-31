"""
Widget de tabla de datos reutilizable.

Tabla genérica con filas alternas, selección de fila,
y soporte para actualización reactiva desde listas de dataclasses.
"""
import logging
from typing import List, Optional, Callable

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from src.presentation.theme.colors import get_palette
from src.presentation.theme.fonts import get_font

logger = logging.getLogger(__name__)


class DataTable(QTableWidget):
    """
    Tabla de datos reutilizable con estilo profesional.

    Características:
    - Filas alternas con colores even/odd
    - Selección de fila completa
    - Emisión de señal al hacer click en fila
    - Actualización reactiva desde lista de objetos
    """

    row_clicked = Signal(int, object)  # (row_index, data_object)

    def __init__(
        self,
        columns: List[str],
        field_map: Optional[List[str]] = None,
        parent=None,
    ):
        """
        Args:
            columns: Nombres de columnas para el header.
            field_map: Nombres de atributos del dataclass (mismo orden que columns).
            parent: Widget padre.
        """
        super().__init__(parent)
        self._columns = columns
        self._field_map = field_map or columns
        self._data: list = []
        self._palette = get_palette()

        self._setup_table()

    def _setup_table(self):
        """Configura la tabla."""
        self.setColumnCount(len(self._columns))
        self.setHorizontalHeaderLabels(self._columns)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        # Header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setFont(get_font("body_sm_bold"))
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(60)

        # Señales
        self.cellClicked.connect(self._on_cell_clicked)

    def load_data(self, data: list):
        """
        Carga datos desde una lista de objetos (dataclasses o dicts).

        Args:
            data: Lista de objetos con atributos matching field_map.
        """
        self._data = data
        self.setRowCount(0)
        self.setRowCount(len(data))

        for row_idx, item in enumerate(data):
            for col_idx, field in enumerate(self._field_map):
                if isinstance(item, dict):
                    value = item.get(field, "")
                else:
                    value = getattr(item, field, "")

                cell = QTableWidgetItem(str(value))
                cell.setFont(get_font("body_sm"))

                # Colorear filas con estado REVISAR
                if hasattr(item, 'estado') and item.estado == "REVISAR":
                    cell.setForeground(QColor(self._palette["error"]))

                self.setItem(row_idx, col_idx, cell)

            self.setRowHeight(row_idx, 28)

    def get_data_at_row(self, row: int):
        """Retorna el objeto de datos en la fila indicada."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def filter_rows(self, text: str):
        """Filtra filas mostrando solo las que contienen el texto."""
        text = text.lower()
        for row in range(self.rowCount()):
            match = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.setRowHidden(row, not match)

    def clear_filter(self):
        """Muestra todas las filas."""
        for row in range(self.rowCount()):
            self.setRowHidden(row, False)

    def _on_cell_clicked(self, row: int, col: int):
        """Emite señal con datos de la fila clickeada."""
        data = self.get_data_at_row(row)
        if data is not None:
            self.row_clicked.emit(row, data)
