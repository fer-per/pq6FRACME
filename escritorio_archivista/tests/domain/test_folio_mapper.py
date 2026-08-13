"""Tests para folio_mapper.py."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.domain.services.folio_mapper import (
    FolioMapper,
    Segmento,
    mapper_from_config,
)
from src.domain.entities import InventoryRecord, ExclusionRule


def _make_record(folios: str, id: str = "#0001") -> InventoryRecord:
    return InventoryRecord(
        id=id, fila=1, registro="001", escribano="Test",
        protocolo="1", folios=folios, pg_pdf="", titulo="Test",
    )


# ─── FolioMapper básico ─────────────────────────────────────

class TestFolioMapperBasic:
    """Tests para mapeo lineal sin segmentos ni exclusiones."""

    def test_mapeo_lineal_simple(self):
        """1r=1, 1v=2, 2r=3, 2v=4."""
        mapper = FolioMapper(pag_pdf_inicio=1)
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("001r-002v")
        assert pages == [1, 2, 3, 4]

    def test_mapeo_con_offset(self):
        """Si pag_pdf_inicio=5, el folio 1r → pág 5."""
        mapper = FolioMapper(pag_pdf_inicio=5)
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("001r-001v")
        assert pages == [5, 6]

    def test_folio_unico(self):
        mapper = FolioMapper(pag_pdf_inicio=1)
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("003r")
        assert pages == [1]  # Es el primer folio procesado

    def test_folio_invalido(self):
        mapper = FolioMapper()
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_pages("abc") is None

    def test_rango_string(self):
        mapper = FolioMapper(pag_pdf_inicio=1)
        mapper.start_sequence()
        result = mapper.folio_str_to_pdf_range("001r-002v")
        assert result == "1-4"

    def test_rango_string_unico(self):
        mapper = FolioMapper(pag_pdf_inicio=1)
        mapper.start_sequence()
        result = mapper.folio_str_to_pdf_range("001r")
        assert result == "1"

    def test_rango_string_invalido(self):
        mapper = FolioMapper()
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_range("abc") is None

    def test_secuencia_multiples_registros(self):
        """Procesar dos registros secuenciales."""
        mapper = FolioMapper(pag_pdf_inicio=1)
        mapper.start_sequence()
        p1 = mapper.folio_str_to_pdf_pages("001r-001v")
        p2 = mapper.folio_str_to_pdf_pages("002r-002v")
        assert p1 == [1, 2]
        assert p2 == [3, 4]


# ─── FolioMapper con páginas ignoradas ──────────────────────

class TestFolioMapperIgnored:
    """Tests con páginas ignoradas."""

    def test_pagina_ignorada(self):
        """Si pág 2 está ignorada, se salta."""
        mapper = FolioMapper(pag_pdf_inicio=1, ignoradas=[2])
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("001r-001v")
        # 1r → pág 1, 1v → skip 2 → pág 3
        assert pages == [1, 3]


# ─── FolioMapper con segmentos ──────────────────────────────

class TestFolioMapperSegments:
    """Tests con segmentos (puntos de quiebre)."""

    def test_segmento_cambia_offset(self):
        """Un segmento en folio 3r redirige a pág PDF 100."""
        seg = Segmento("003r", 100)
        mapper = FolioMapper(pag_pdf_inicio=1, segmentos=[seg])
        mapper.start_sequence()
        # Primeros folios: 1r→1, 1v→2, 2r→3, 2v→4
        p1 = mapper.folio_str_to_pdf_pages("001r-002v")
        assert p1 == [1, 2, 3, 4]
        # Folio 3r activa el segmento → pág 100
        p2 = mapper.folio_str_to_pdf_pages("003r-003v")
        assert p2 == [100, 101]


# ─── mapper_from_config ─────────────────────────────────────

class TestMapperFromConfig:
    """Tests para la factory mapper_from_config."""

    def test_config_basica(self):
        mapper = mapper_from_config(pag_pdf_inicio=1)
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("001r-001v")
        assert pages == [1, 2]

    def test_config_con_exclusiones(self):
        excl = ExclusionRule(
            id="E1", tipo="IGNORAR", desde=2, hasta=3, motivo="Test"
        )
        mapper = mapper_from_config(pag_pdf_inicio=1, exclusiones=[excl])
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("001r-002v")
        # 1r→1, 1v→skip 2,3→4, 2r→5, 2v→6
        assert pages == [1, 4, 5, 6]

    def test_config_con_segmentos(self):
        segs = [{"folio_inicio": "002r", "pag_pdf_inicio": 50}]
        mapper = mapper_from_config(pag_pdf_inicio=1, segmentos=segs)
        mapper.start_sequence()
        p1 = mapper.folio_str_to_pdf_pages("001r-001v")
        assert p1 == [1, 2]
        p2 = mapper.folio_str_to_pdf_pages("002r-002v")
        assert p2 == [50, 51]

    def test_exclusion_tipo_salto_no_ignora_paginas(self):
        """Solo exclusiones tipo IGNORAR generan páginas a saltar."""
        excl = ExclusionRule(
            id="E1", tipo="SALTO", desde=2, hasta=3, motivo="Test"
        )
        mapper = mapper_from_config(pag_pdf_inicio=1, exclusiones=[excl])
        mapper.start_sequence()
        pages = mapper.folio_str_to_pdf_pages("001r-002v")
        assert pages == [1, 2, 3, 4]

    def test_max_pdf_page(self):
        mapper = mapper_from_config(pag_pdf_inicio=1)
        records = [
            _make_record("001r-002v", "#0001"),
            _make_record("003r-005v", "#0002"),
        ]
        max_p = mapper.max_pdf_page(records)
        assert max_p == 10  # 5v = folio int 10

    def test_max_pdf_page_respeta_pg_pdf_manual(self):
        """max_pdf_page debe respetar el rango manual de paginación."""
        mapper = mapper_from_config(pag_pdf_inicio=1)
        r1 = _make_record("001r-002v", "#0001")
        r2 = _make_record("003r", "#0002")
        r2.pg_pdf_manual = "7"
        r3 = _make_record("004r", "#0003")
        # Sin respetar el manual: r2→5, r3→6 (max 6).
        # Respetándolo: r2→7 (contador a 8), r3→8 (max 8).
        assert mapper.max_pdf_page([r1, r2, r3]) == 8

    def test_max_pdf_page_respeta_comparte_hoja(self):
        """max_pdf_page debe respetar comparte_hoja (arranca en la hoja anterior)."""
        mapper = mapper_from_config(pag_pdf_inicio=1)
        r1 = _make_record("001r-002v", "#0001")
        r2 = _make_record("003r", "#0002")
        r2.comparte_hoja = True
        r3 = _make_record("004r", "#0003")
        # Sin compartir: r2→5, r3→6 (max 6).
        # Compartiendo: r2→4 (misma hoja que el final de r1), r3→5 (max 5).
        assert mapper.max_pdf_page([r1, r2, r3]) == 5

    def test_paginas_descartadas_no_cuentan(self):
        """Una página descartada en el editor PDF se salta y no cuenta."""
        # PDF físico 1..4 donde la 2 es duplicada; el usuario la descarta
        mapper = mapper_from_config(
            pag_pdf_inicio=1,
            active_pages=[1, 3, 4],
            total_pdf_pages=4,
        )
        mapper.start_sequence()
        # 1r→1, 1v→skip 2 →3
        assert mapper.folio_str_to_pdf_pages("001r-001v") == [1, 3]
        # 2r→4, 2v→5
        assert mapper.folio_str_to_pdf_pages("002r-002v") == [4, 5]

    def test_sin_paginas_activas_no_ignora(self):
        mapper = mapper_from_config(pag_pdf_inicio=1, total_pdf_pages=4)
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_pages("001r-001v") == [1, 2]


class TestManualOverrideConExclusion:
    """El rango manual se interpreta en la sucesión renumerada y respeta
    las páginas descartadas en el editor PDF."""

    def _mapper(self, active_pages, total):
        return mapper_from_config(
            pag_pdf_inicio=1, active_pages=active_pages, total_pdf_pages=total
        )

    def test_manual_no_reintroduce_pagina_excluida(self):
        """Pág. física 2 excluida; manual '1-2' (sucesión) → [1,3]."""
        mapper = self._mapper([1, 3, 4], 4)
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_pages("001r-001v", override="1-2") == [1, 3]

    def test_sucesion_continua_despues_del_manual(self):
        """Tras el manual, el contador sigue desde la última página física."""
        mapper = self._mapper([1, 3, 4], 4)
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_pages("001r-001v", override="1-2") == [1, 3]
        assert mapper.folio_str_to_pdf_pages("002r-002v") == [4, 5]

    def test_manual_rango_largo_con_exclusion(self):
        """Rango manual de varias páginas traducido contra la sucesión activa."""
        active = [1, 3, 4, 5, 6, 7]
        mapper = self._mapper(active, 7)
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_pages("001r-003v", override="2-5") == [3, 4, 5, 6]

    def test_manual_sin_exclusion_se_mantiene_literal(self):
        """Sin páginas descartadas, el rango manual es literal (compatibilidad)."""
        mapper = mapper_from_config(pag_pdf_inicio=1)
        mapper.start_sequence()
        assert mapper.folio_str_to_pdf_pages("001r-001v", override="5-6") == [5, 6]

    def test_format_pages_preserva_huecos(self):
        assert FolioMapper.format_pages([1, 5, 6, 7]) == "1,5-7"
        assert FolioMapper.format_pages([373, 374, 375]) == "373-375"
        assert FolioMapper.format_pages([7]) == "7"
        assert FolioMapper.format_pages([]) is None
