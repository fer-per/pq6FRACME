"""
Pila de Deshacer/Rehacer para los analizadores.

Cada analizador tiene su propia instancia ``UndoRedo``. Una acción es un
dict con dos listas de entradas ``(record_id, campo, valor)``:

- ``revert``: valores a restaurar al deshacer (estado anterior).
- ``apply``: valores a restaurar al rehacer (estado posterior).

El campo especial ``"@validated"`` guarda el conjunto de incidencias
validadas (``set`` serializable) en lugar de un atributo del registro.
"""
from typing import List

from PySide6.QtCore import QObject, Signal


class UndoRedo(QObject):
    """Historial de acciones con soporte de deshacer/rehacer por analizador."""

    changed = Signal()

    def __init__(self, parent=None, limit: int = 50):
        super().__init__(parent)
        self._limit = limit
        self._undo: List[dict] = []
        self._redo: List[dict] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def push(self, action: dict):
        """Registra una acción nueva y limpia la pila de rehacer."""
        self._undo.append(action)
        if len(self._undo) > self._limit:
            self._undo.pop(0)
        self._redo.clear()
        self.changed.emit()

    def undo(self) -> dict:
        """Saca la acción más reciente para deshacerla."""
        if not self._undo:
            return None
        action = self._undo.pop()
        self._redo.append(action)
        self.changed.emit()
        return action

    def redo(self) -> dict:
        """Saca la acción más reciente de la pila de rehacer."""
        if not self._redo:
            return None
        action = self._redo.pop()
        self._undo.append(action)
        self.changed.emit()
        return action

    def clear(self):
        """Borra todo el historial."""
        self._undo.clear()
        self._redo.clear()
        self.changed.emit()