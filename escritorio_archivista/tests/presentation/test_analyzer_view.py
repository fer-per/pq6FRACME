"""Tests para la capa de presentación."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.domain.entities import InventoryRecord, AnalysisError
from src.presentation.views.analyzer_view import AnalyzerErrorTab


_COLUMNS = [
    ("Fila", "fila"),
    ("N° Reg", "registro"),
    ("Prot", "protocolo"),
    ("Folios", "folios"),
    ("Pág. PDF", "pg_pdf"),
    ("Título", "titulo"),
    ("Tipo", "tipo"),
    ("Descripción", "descripcion"),
    ("Valor Actual", "valor_actual"),
    ("Esperado", "valor_esperado"),
]


def _make_tab(columns=None):
    """Crea una instancia sin inicializar widgets Qt (solo lógica de filas)."""
    tab = AnalyzerErrorTab.__new__(AnalyzerErrorTab)
    tab._columns = columns if columns is not None else _COLUMNS
    return tab


class TestAnalyzerErrorTab:
    """Tests para la construcción de filas de la pestaña de errores."""

    def test_errores_se_asocian_por_id_de_registro(self):
        records = [
            InventoryRecord(
                id="#0001", fila=10, registro="001", escribano="X",
                protocolo="1", folios="001r", pg_pdf="1", titulo="T",
            ),
            InventoryRecord(
                id="#0002", fila=11, registro="002", escribano="X",
                protocolo="1", folios="002r", pg_pdf="2", titulo="T",
            ),
        ]
        error = AnalysisError(
            record_id="#0002", fila=11, tipo="FORMATO",
            descripcion="Salto detectado", valor_actual="002r",
            valor_esperado="003r",
        )
        tab = _make_tab()
        rows = tab._build_rows(records, [error])

        filas_con_error = [r for r in rows if r["_errors"]]
        assert len(filas_con_error) == 1
        assert filas_con_error[0]["_record"].id == "#0002"

    def test_error_global_se_muestra_como_fila_sintetica(self):
        """El error global de cobertura debe ser visible en la tabla."""
        records = [
            InventoryRecord(
                id="#0001", fila=10, registro="001", escribano="X",
                protocolo="1", folios="001r", pg_pdf="1", titulo="T",
            ),
        ]
        global_error = AnalysisError(
            record_id="GLOBAL", fila=0, tipo="COVERAGE",
            descripcion="El PDF tiene 5 páginas pero el inventario requiere 10.",
            valor_actual="5", valor_esperado="10", fatal=True,
        )
        tab = _make_tab()
        rows = tab._build_rows(records, [global_error])

        # 1 fila por registro + 1 fila sintética para el error global
        assert len(rows) == 2

        filas_con_error = [r for r in rows if r["_errors"]]
        assert len(filas_con_error) == 1

        row = filas_con_error[0]
        assert row["_record"] is None
        assert row["registro"] == "GLOBAL"
        assert row["fila"] == 0
        assert row["tipo"] == "COVERAGE"
        assert row["descripcion"] == global_error.descripcion
        assert row["valor_actual"] == "5"
        assert row["valor_esperado"] == "10"

    def test_error_global_tambien_con_errores_de_registro(self):
        """Coexisten filas sintéticas y filas de registro con errores."""
        records = [
            InventoryRecord(
                id="#0001", fila=10, registro="001", escribano="X",
                protocolo="1", folios="001r", pg_pdf="1", titulo="T",
            ),
        ]
        local = AnalysisError(
            record_id="#0001", fila=10, tipo="FORMATO",
            descripcion="Salto", valor_actual="1", valor_esperado="2",
        )
        global_error = AnalysisError(
            record_id="GLOBAL", fila=0, tipo="COVERAGE",
            descripcion="PDF insuficiente", valor_actual="5",
            valor_esperado="10", fatal=True,
        )
        tab = _make_tab()
        rows = tab._build_rows(records, [local, global_error])

        assert len(rows) == 2
        assert len([r for r in rows if r["_errors"]]) == 2
