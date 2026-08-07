"""Tests para AppStateVM — recálculo de pg_pdf al cargar sesión."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from PySide6.QtCore import QCoreApplication

from src.domain.entities import InventoryRecord
from src.presentation.viewmodels.app_state import AppStateVM

_app = QCoreApplication.instance() or QCoreApplication([])


def _make_record(folios: str, id: str) -> InventoryRecord:
    return InventoryRecord(
        id=id, fila=1, registro=id, escribano="Test",
        protocolo="1", folios=folios, pg_pdf="", titulo="Test",
    )


def _session_data(records, **kwargs):
    data = {
        "pag_pdf_inicio": 1,
        "pdf_total_pages": 100,
        "active_pages": list(range(1, 101)),
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
        "folio_inicio": "001r",
    }
    data.update(kwargs)
    return data


class TestRecalcularPgPdf:
    def test_recalcula_pg_pdf_al_cargar_sesion(self):
        """La sesión guarda pg_pdf viejos; al cargar se recalculan."""
        r1 = _make_record("001r-002v", "#0001")
        r2 = _make_record("003r", "#0002")
        r3 = _make_record("004r", "#0003")
        for r in (r1, r2, r3):
            r.pg_pdf = "99"  # valor viejo guardado

        state = AppStateVM()
        state.from_dict(_session_data([r1, r2, r3]))

        assert r1.pg_pdf == "1-4"
        assert r2.pg_pdf == "5"
        assert r3.pg_pdf == "6"

    def test_recalcula_respetando_pg_pdf_manual(self):
        """El rango manual se conserva y el contador continúa desde él."""
        r1 = _make_record("001r-002v", "#0001")
        r2 = _make_record("003r", "#0002")
        r2.pg_pdf_manual = "7"
        r3 = _make_record("004r", "#0003")
        for r in (r1, r2, r3):
            r.pg_pdf = "99"

        state = AppStateVM()
        state.from_dict(_session_data([r1, r2, r3]))

        assert r2.pg_pdf == "7"
        assert r3.pg_pdf == "8"

    def test_recalcula_sin_registros_no_falla(self):
        state = AppStateVM()
        state.from_dict(_session_data([]))
        assert state.records == []
