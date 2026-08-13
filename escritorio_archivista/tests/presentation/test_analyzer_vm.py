"""Tests de AnalyzerVM — al aplicar paginación manual se recalcula pg_pdf de inmediato."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from PySide6.QtCore import QCoreApplication

from src.domain.entities import InventoryRecord
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.analyzer_vm import AnalyzerVM

_app = QCoreApplication.instance() or QCoreApplication([])


def _make_record(folios: str, id: str, pg_pdf_manual: str = "",
                 comparte_hoja: bool = False) -> InventoryRecord:
    return InventoryRecord(
        id=id, fila=1, registro=id, escribano="Test",
        protocolo="1", folios=folios, pg_pdf="", titulo="Test",
        pg_pdf_manual=pg_pdf_manual, comparte_hoja=comparte_hoja,
        estado="VALIDADO",
    )


def _make_state() -> AppStateVM:
    state = AppStateVM()
    state.pdf_total_pages = 100
    state.active_pages = list(range(1, 101))
    state.records = [
        _make_record("001r", "#0001"),
        _make_record("002r-003v", "#0002"),
    ]
    return state


class TestApplyChangesRecalculaPgPdf:
    def test_aplica_rango_manual_y_actualiza_pg_pdf(self):
        state = _make_state()
        vm = AnalyzerVM(container=None, state=state)

        vm.apply_changes("#0002", {"pg_pdf_manual": "7-8"})

        record = state.records[1]
        assert record.pg_pdf_manual == "7-8"
        assert record.pg_pdf == "7-8"

    def test_rango_manual_respeta_pg_pdf_manual_existente(self):
        state = _make_state()
        state.records[1].pg_pdf_manual = "7-8"
        vm = AnalyzerVM(container=None, state=state)

        vm.apply_changes("#0002", {"pg_pdf_manual": "10-12"})

        assert state.records[1].pg_pdf == "10-12"

    def test_limpiar_manual_recalcula_automatico(self):
        state = _make_state()
        state.records[1].pg_pdf_manual = "7-8"
        vm = AnalyzerVM(container=None, state=state)

        vm.apply_changes("#0002", {"pg_pdf_manual": ""})

        record = state.records[1]
        assert record.pg_pdf_manual == ""
        assert record.pg_pdf  # vuelve al valor automático
