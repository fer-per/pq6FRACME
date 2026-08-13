"""Tests de WorkspaceView.refresh_from_state — conserva correcciones al cargar sesión."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from PySide6.QtCore import QCoreApplication

from src.domain.entities import InventoryRecord
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.views.workspace_view import WorkspaceView

_app = QCoreApplication.instance() or QCoreApplication([])


def _make_record(folios: str, id: str, pg_pdf_manual: str = "",
                 comparte_hoja: bool = False) -> InventoryRecord:
    return InventoryRecord(
        id=id, fila=1, registro=id, escribano="Test",
        protocolo="1", folios=folios, pg_pdf="", titulo="Test",
        pg_pdf_manual=pg_pdf_manual, comparte_hoja=comparte_hoja,
        estado="VALIDADO",
    )


class _StubVM:
    def __init__(self):
        self.load_inventory_calls = 0
        self.set_pdf_path_calls = 0

    def load_inventory(self):
        self.load_inventory_calls += 1

    def set_pdf_path(self, path):
        self.set_pdf_path_calls += 1


class _StubSpin:
    def setValue(self, value):
        pass


class _StubText:
    def setText(self, value):
        pass


class _StubDrop:
    def __init__(self, path=None):
        self._path = path

    def set_file(self, path):
        self._path = path


class _StubTable:
    def __init__(self):
        self.last_records = None

    def load_data(self, records):
        self.last_records = records


class _StubLabel:
    def setText(self, value):
        self._text = value


class _StubState:
    def __init__(self, records, excel_path, pdf_path):
        self.records = records
        self.excel_path = excel_path
        self.pdf_path = pdf_path
        self.fila_datos_inicio = 12
        self.fila_inicio = 12
        self.fila_fin = 0
        self.pag_pdf_inicio = 1
        self.folio_inicio = "001r"


class TestRefreshFromState:
    """Al cargar una configuración guardada, los records vienen restaurados
    con sus correcciones manuales; no se deben recrear desde el Excel."""

    def _make_view(self, state) -> WorkspaceView:
        view = WorkspaceView.__new__(WorkspaceView)
        view._state = state
        view._vm = _StubVM()
        view._excel_drop = _StubDrop()
        view._pdf_drop = _StubDrop()
        view._fila_datos_inicio_spin = _StubSpin()
        view._fila_inicio_spin = _StubSpin()
        view._fila_fin_spin = _StubSpin()
        view._pag_pdf_spin = _StubSpin()
        view._folio_inicio_input = _StubText()
        view._table = _StubTable()
        view._count_label = _StubLabel()
        return view

    def test_no_recarga_inventario_si_hay_records_restaurados(self, tmp_path):
        """Con records de la sesión (y sus correcciones), no se re-lee el Excel."""
        excel = tmp_path / "inv.xlsx"
        excel.write_bytes(b"dummy")
        pdf = tmp_path / "maestro.pdf"
        pdf.write_bytes(b"dummy")
        records = [_make_record("001r-002v", "#0001", pg_pdf_manual="7-8")]
        state = _StubState(records, str(excel), str(pdf))

        view = self._make_view(state)
        view.refresh_from_state()

        assert view._vm.load_inventory_calls == 0
        assert view._vm.set_pdf_path_calls == 1

    def test_recarga_inventario_si_no_hay_records(self, tmp_path):
        """Sin records (config nueva sin inventario), sí se carga del Excel."""
        excel = tmp_path / "inv.xlsx"
        excel.write_bytes(b"dummy")
        pdf = tmp_path / "maestro.pdf"
        pdf.write_bytes(b"dummy")
        state = _StubState([], str(excel), str(pdf))

        view = self._make_view(state)
        view.refresh_from_state()

        assert view._vm.load_inventory_calls == 1
        assert view._vm.set_pdf_path_calls == 1
