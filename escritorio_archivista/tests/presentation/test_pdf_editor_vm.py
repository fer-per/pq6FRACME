"""Tests para PDFEditorVM — exclusiones/reordenamiento y recálculo de pg_pdf."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from PySide6.QtCore import QCoreApplication

from src.domain.entities import InventoryRecord
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.viewmodels.pdf_editor_vm import PDFEditorVM
from src.application.container import Container

_app = QCoreApplication.instance() or QCoreApplication([])


def _make_record(folios: str, rid: str) -> InventoryRecord:
    return InventoryRecord(
        id=rid, fila=1, registro=rid, escribano="Test",
        protocolo="1", folios=folios, pg_pdf="", titulo="Test",
    )


def _session_data(records, total=10, **kwargs):
    data = {
        "pag_pdf_inicio": 1,
        "pdf_total_pages": total,
        "active_pages": list(range(1, total + 1)),
        "segmentos": [],
        "overrides": {},
        "page_map": {},
        "exclusiones": [],
        "records": records,
        "exclusions": [],
        "suggestions": [],
        "incidencias_validadas": [],
        "fila_datos_inicio": 12,
        "fila_inicio": 12,
        "fila_fin": 0,
    }
    data.update(kwargs)
    return data


def _make_vm(records):
    state = AppStateVM()
    state.from_dict(_session_data(records))
    return state, PDFEditorVM(Container(), state)


class TestTogglePageRecalculaMapeo:
    def test_excluir_pagina_renumera_el_mapeo(self):
        r1 = _make_record("001r-001v", "#0001")
        r2 = _make_record("002r-002v", "#0002")
        r3 = _make_record("003r-003v", "#0003")
        state, vm = _make_vm([r1, r2, r3])

        emitted = []
        state.records_changed.connect(lambda: emitted.append(1))

        vm.toggle_page(2)  # excluir la hoja 2

        assert state.active_pages == [1, 3, 4, 5, 6, 7, 8, 9, 10]
        # pg_pdf muestra posiciones renumeradas (1,2,3...) como el editor
        assert r1.pg_pdf == "1-2"
        assert r2.pg_pdf == "3-4"
        assert r3.pg_pdf == "5-6"
        assert emitted, "records_changed debe emitirse para refrescar la tabla"

    def test_reincluir_pagina_restaura_la_secuencia(self):
        r1 = _make_record("001r-002v", "#0001")
        state, vm = _make_vm([r1])

        vm.toggle_page(2)
        assert state.active_pages == [1, 3, 4, 5, 6, 7, 8, 9, 10]

        vm.toggle_page(2)  # reincluir
        assert state.active_pages == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert r1.pg_pdf == "1-4"

    def test_mover_pagina_conserva_posiciones_secuenciales(self):
        """Reordenar afecta la vista previa, no la numeración secuencial.

        pg_pdf es la posición renumerada (1,2,3...); mover una hoja arriba/
        abajo solo cambia el orden de la secuencia activa de la vista previa.
        """
        r1 = _make_record("001r", "#0001")
        r2 = _make_record("002r", "#0002")
        r3 = _make_record("003r", "#0003")
        state, vm = _make_vm([r1, r2, r3])

        # Mover la hoja 3 (índice 2) a la primera posición (índice 0)
        vm.move_page(2, 0)

        assert state.active_pages == [3, 1, 2, 4, 5, 6, 7, 8, 9, 10]
        assert r1.pg_pdf == "1"
        assert r2.pg_pdf == "2"
        assert r3.pg_pdf == "3"

    def test_undo_restaura_el_mapeo_anterior(self):
        r1 = _make_record("001r", "#0001")
        r2 = _make_record("002r", "#0002")
        r3 = _make_record("003r", "#0003")
        state, vm = _make_vm([r1, r2, r3])

        vm.toggle_page(2)
        assert state.active_pages == [1, 3, 4, 5, 6, 7, 8, 9, 10]
        assert r2.pg_pdf == "2"

        vm.undo()
        assert state.active_pages == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert r2.pg_pdf == "2"