"""Tests para folio_parser.py."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.domain.services.folio_parser import (
    parse_folios,
    folio_to_int,
    int_to_folio,
    format_folio,
    calculate_suggested_range,
)
from src.domain.entities import InventoryRecord


# ─── parse_folios ────────────────────────────────────────────

class TestParseFolios:
    """Tests para la función parse_folios."""

    def test_rango_completo(self):
        assert parse_folios("001r-002v") == (1, 'r', 2, 'v')

    def test_rango_sin_ceros(self):
        assert parse_folios("1r-2v") == (1, 'r', 2, 'v')

    def test_rango_sin_caras(self):
        """Sin caras explícitas: default r para inicio, v para fin."""
        assert parse_folios("1-2") == (1, 'r', 2, 'v')

    def test_folio_unico_con_cara(self):
        assert parse_folios("001r") == (1, 'r', 1, 'r')

    def test_folio_unico_verso(self):
        assert parse_folios("5v") == (5, 'v', 5, 'v')

    def test_folio_unico_sin_cara(self):
        """Sin cara: default 'r'."""
        assert parse_folios("5") == (5, 'r', 5, 'r')

    def test_con_espacios(self):
        assert parse_folios("  001r-002v  ") == (1, 'r', 2, 'v')

    def test_mayusculas(self):
        """Debe normalizar a minúsculas."""
        assert parse_folios("001R-002V") == (1, 'r', 2, 'v')

    def test_none_input(self):
        assert parse_folios(None) is None

    def test_empty_string(self):
        assert parse_folios("") is None

    def test_texto_invalido(self):
        assert parse_folios("abc") is None

    def test_no_string(self):
        assert parse_folios(123) is None


# ─── folio_to_int ────────────────────────────────────────────

class TestFolioToInt:
    """Tests para folio_to_int."""

    def test_1r(self):
        assert folio_to_int(1, 'r') == 1

    def test_1v(self):
        assert folio_to_int(1, 'v') == 2

    def test_2r(self):
        assert folio_to_int(2, 'r') == 3

    def test_2v(self):
        assert folio_to_int(2, 'v') == 4

    def test_100r(self):
        assert folio_to_int(100, 'r') == 199

    def test_100v(self):
        assert folio_to_int(100, 'v') == 200


# ─── int_to_folio ────────────────────────────────────────────

class TestIntToFolio:
    """Tests para int_to_folio (inversa de folio_to_int)."""

    def test_1(self):
        assert int_to_folio(1) == (1, 'r')

    def test_2(self):
        assert int_to_folio(2) == (1, 'v')

    def test_3(self):
        assert int_to_folio(3) == (2, 'r')

    def test_4(self):
        assert int_to_folio(4) == (2, 'v')

    def test_roundtrip(self):
        """folio_to_int y int_to_folio son inversas."""
        for num in range(1, 50):
            for cara in ('r', 'v'):
                n = folio_to_int(num, cara)
                assert int_to_folio(n) == (num, cara)


# ─── format_folio ────────────────────────────────────────────

class TestFormatFolio:
    """Tests para format_folio."""

    def test_padding(self):
        assert format_folio(1, 'r') == "001r"

    def test_no_padding(self):
        assert format_folio(100, 'v') == "100v"

    def test_tres_digitos(self):
        assert format_folio(42, 'r') == "042r"


# ─── calculate_suggested_range ───────────────────────────────

def _make_record(folios: str) -> InventoryRecord:
    """Factory helper para crear un registro de prueba."""
    return InventoryRecord(
        id="#0001", fila=1, registro="001", escribano="Test",
        protocolo="1", folios=folios, pg_pdf="", titulo="Test",
    )


class TestCalculateSuggestedRange:
    """Tests para calculate_suggested_range."""

    def test_secuencia_normal(self):
        """Anterior termina en 002v → actual debería empezar en 003r."""
        prev = _make_record("001r-002v")
        curr = _make_record("005r-006v")  # span = 4
        result = calculate_suggested_range(prev, curr)
        # 002v (int=4) + 1 = 5 → 003r, span = 4, end = 8 → 004v
        assert result == "003r-004v"

    def test_folios_unicos(self):
        prev = _make_record("001r")
        curr = _make_record("003r")
        result = calculate_suggested_range(prev, curr)
        # prev ends at 1r (int=1), next starts at int=2 → 1v, span=0
        assert result == "001v-001v"

    def test_prev_invalido(self):
        prev = _make_record("abc")
        curr = _make_record("001r-002v")
        assert calculate_suggested_range(prev, curr) is None

    def test_curr_invalido(self):
        prev = _make_record("001r-002v")
        curr = _make_record("xyz")
        assert calculate_suggested_range(prev, curr) is None
