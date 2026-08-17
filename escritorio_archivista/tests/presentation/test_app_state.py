"""Tests para AppStateVM — recálculo de pg_pdf al cargar sesión."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from PySide6.QtCore import QCoreApplication

from src.domain.entities import InventoryRecord, ExclusionRule
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.constants import DEFAULT_OUTPUT_DIR

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


class TestPaginaFisicaAPosicion:
    """Conversión página física → posición en la secuencia activa (vista previa)."""

    def test_sin_exclusiones_posicion_igual_a_pagina(self):
        state = AppStateVM()
        state.pdf_total_pages = 660
        assert state.pagina_fisica_a_posicion(5) == 5

    def test_con_exclusiones_mapea_a_posicion_activa(self):
        state = AppStateVM()
        state.pdf_total_pages = 4
        state.active_pages = [1, 3, 4]  # se excluyó la 2
        assert state.pagina_fisica_a_posicion(1) == 1
        assert state.pagina_fisica_a_posicion(3) == 2
        assert state.pagina_fisica_a_posicion(4) == 3

    def test_con_reordenamiento_mapea_a_posicion(self):
        state = AppStateVM()
        state.pdf_total_pages = 4
        state.active_pages = [2, 1, 3, 4]
        assert state.pagina_fisica_a_posicion(2) == 1
        assert state.pagina_fisica_a_posicion(1) == 2

    def test_pagina_excluida_devuelve_none(self):
        state = AppStateVM()
        state.pdf_total_pages = 4
        state.active_pages = [1, 3, 4]
        assert state.pagina_fisica_a_posicion(2) is None


class TestDirectorioSalidaPredeterminado:
    def test_output_dir_por_defecto_es_el_predeterminado(self):
        state = AppStateVM()
        assert state.output_dir == DEFAULT_OUTPUT_DIR

    def test_output_dir_no_vacio_aparece_sin_seleccionar(self):
        state = AppStateVM()
        assert state.output_dir

    def test_from_dict_sin_output_dir_mantiene_predeterminado(self):
        state = AppStateVM()
        state.from_dict(_session_data([], output_dir=None))
        assert state.output_dir == DEFAULT_OUTPUT_DIR

    def test_from_dict_con_output_dir_lo_usa(self):
        state = AppStateVM()
        state.from_dict(_session_data([], output_dir="C:/otra/carpeta"))
        assert state.output_dir == "C:/otra/carpeta"


class TestResetNuevaConfiguracion:
    def test_reset_limpia_estado_de_documento(self):
        state = AppStateVM()
        state.excel_path = "C:/inv.xlsx"
        state.pdf_path = "C:/pdf.pdf"
        state.output_dir = "C:/salida"
        state.records = [_make_record("001r", "#0001")]
        state.exclusions = [
            ExclusionRule(id="E1", tipo="SALTO", desde=1, hasta=2, motivo="Test")
        ]
        state.profile_name = "proto16"
        state.pag_pdf_inicio = 5

        state.reset()

        assert state.excel_path is None
        assert state.pdf_path is None
        assert state.output_dir == DEFAULT_OUTPUT_DIR
        assert state.records == []
        assert state.exclusions == []
        assert state.suggestions == []
        assert state.profile_name is None
        assert state.pag_pdf_inicio == 1

    def test_reset_conserva_tema_y_vista_dual(self):
        state = AppStateVM()
        state.dark_mode = True
        state.dual_view_active = False

        state.reset()

        assert state.dark_mode is True
        assert state.dual_view_active is False

    def test_reset_vacia_y_emite_sin_fallar(self):
        state = AppStateVM()
        state.reset()
        assert state.records == []
        assert state.profile_name is None

    def test_profile_name_se_guarda(self):
        state = AppStateVM()
        assert state.profile_name is None
        state.profile_name = "proto16"
        assert state.profile_name == "proto16"
