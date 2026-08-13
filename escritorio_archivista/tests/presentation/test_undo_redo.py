"""Tests para la pila de Deshacer/Rehacer por analizador."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.presentation.undo_redo import UndoRedo


def _accion(antes="1r", despues="2r"):
    return {
        "desc": "corrección",
        "revert": [("#0001", "folios", antes)],
        "apply": [("#0001", "folios", despues)],
    }


class TestUndoRedo:
    def test_pila_vacia_sin_acciones(self):
        h = UndoRedo()
        assert not h.can_undo
        assert not h.can_redo
        assert h.undo() is None
        assert h.redo() is None

    def test_primer_deshacer_devuelve_la_ultima_accion(self):
        h = UndoRedo()
        h.push(_accion("1r", "2r"))
        h.push(_accion("2r", "3r"))

        accion = h.undo()
        assert accion["revert"][0][2] == "2r"  # segunda acción
        assert h.can_redo
        assert h.can_undo

    def test_rehacer_restaura_la_accion_deshecha(self):
        h = UndoRedo()
        h.push(_accion("1r", "2r"))
        h.undo()

        accion = h.redo()
        assert accion["apply"][0][2] == "2r"
        assert not h.can_redo

    def test_nueva_accion_limpia_la_pila_de_rehacer(self):
        h = UndoRedo()
        h.push(_accion("1r", "2r"))
        h.undo()
        assert h.can_redo

        h.push(_accion("1r", "9r"))
        assert not h.can_redo
        # El primera deshacer devuelve la acción nueva, no la que se había deshecho
        assert h.undo()["revert"][0][2] == "1r"

    def test_limite_descarta_las_mas_antiguas(self):
        h = UndoRedo(limit=2)
        h.push(_accion("a", "b"))
        h.push(_accion("b", "c"))
        h.push(_accion("c", "d"))

        # Solo caben 2 (la más antigua "a->b" se descartó)
        assert h.undo()["revert"][0][2] == "c"
        assert h.undo()["revert"][0][2] == "b"
        assert h.undo() is None

    def test_clear_vacia_todo(self):
        h = UndoRedo()
        h.push(_accion())
        h.clear()
        assert not h.can_undo
        assert not h.can_redo