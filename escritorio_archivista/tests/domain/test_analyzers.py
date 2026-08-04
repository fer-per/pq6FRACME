"""Tests para los 4 analizadores del dominio."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.domain.entities import InventoryRecord, ExclusionRule
from src.domain.services.analyzers.folio_analyzer import analizar_folios
from src.domain.services.analyzers.topica_analyzer import analizar_topica
from src.domain.services.analyzers.cronica_analyzer import analizar_cronica
from src.domain.services.analyzers.coverage_analyzer import analizar_coverage
from src.domain.services.folio_mapper import FolioMapper


def _rec(
    id: str = "#0001", fila: int = 10, folios: str = "001r-002v",
    data_topica: str = "Ciudad", fecha_inicio: str = "15/03/1891",
    pg_pdf: str = "1-4", protocolo: str = "1", **kwargs
) -> InventoryRecord:
    """Factory helper para registros de prueba."""
    return InventoryRecord(
        id=id, fila=fila, registro="001", escribano="García",
        protocolo=protocolo, folios=folios, pg_pdf=pg_pdf, titulo="Compraventa",
        data_topica=data_topica, fecha_inicio=fecha_inicio, **kwargs,
    )


# ═══════════════════════════════════════════════════════════════
# FOLIO ANALYZER
# ═══════════════════════════════════════════════════════════════

class TestFolioAnalyzer:

    def test_secuencia_correcta(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="003r-004v"),
        ]
        result = analizar_folios(records)
        assert result.ok
        assert result.total_revisados == 2

    def test_formato_invalido(self):
        records = [_rec(folios="abc")]
        result = analizar_folios(records)
        assert not result.ok
        assert len(result.errores) == 1
        assert result.errores[0].tipo == "FORMATO"
        assert result.errores[0].fatal is True

    def test_folio_repetido(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="001r-003v"),
        ]
        result = analizar_folios(records)
        assert len(result.errores) == 1
        assert result.errores[0].tipo == "REPETIDO"

    def test_solapamiento(self):
        records = [
            _rec(id="#0001", folios="001r-005v"),
            _rec(id="#0002", fila=11, folios="003r-006v"),
        ]
        result = analizar_folios(records)
        assert len(result.errores) == 1
        assert result.errores[0].tipo == "SOLAPAMIENTO"

    def test_salto_no_justificado(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="005r-006v"),
        ]
        result = analizar_folios(records)
        assert len(result.advertencias) == 1
        assert result.advertencias[0].tipo == "SALTO"

    def test_salto_con_exclusion(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="005r-006v"),
        ]
        exclusions = [
            ExclusionRule(id="E1", tipo="SALTO", desde=5, hasta=8, motivo="Ok")
        ]
        result = analizar_folios(records, exclusions)
        assert result.ok

    def test_lista_vacia(self):
        result = analizar_folios([])
        assert result.ok
        assert result.total_revisados == 0

    def test_folios_se_reinician_por_protocolo(self):
        records = [
            _rec(id="#0001", folios="001r-002v", protocolo="1"),
            _rec(id="#0002", fila=11, folios="003r-004v", protocolo="1"),
            _rec(id="#0003", fila=12, folios="001r-002v", protocolo="2"),
            _rec(id="#0004", fila=13, folios="003r-004v", protocolo="2"),
        ]
        result = analizar_folios(records)
        assert result.ok
        assert len(result.errores) == 0
        assert len(result.advertencias) == 0

    def test_repetido_dentro_del_mismo_protocolo(self):
        records = [
            _rec(id="#0001", folios="001r-002v", protocolo="2"),
            _rec(id="#0002", fila=11, folios="001r-003v", protocolo="2"),
        ]
        result = analizar_folios(records)
        assert len(result.errores) == 1
        assert result.errores[0].tipo == "REPETIDO"

    def test_cambio_de_protocolo_reinicia_secuencia_esperada(self):
        records = [
            _rec(id="#0001", folios="115v-117v", protocolo="1"),
            _rec(id="#0002", fila=11, folios="117r-117v", protocolo="2"),
        ]
        result = analizar_folios(records)
        # El protocolo 2 reinicia: 117r < 117v no debe generar SOLAPAMIENTO
        assert result.ok


# ═══════════════════════════════════════════════════════════════
# TOPICA ANALYZER
# ═══════════════════════════════════════════════════════════════

class TestTopicaAnalyzer:

    def test_topica_valida(self):
        records = [_rec(data_topica="Guadalajara")]
        result = analizar_topica(records)
        assert result.ok

    def test_topica_vacia(self):
        records = [_rec(data_topica="")]
        result = analizar_topica(records)
        assert len(result.advertencias) == 1
        assert "vacío" in result.advertencias[0].descripcion

    def test_topica_solo_digitos(self):
        records = [_rec(data_topica="12345")]
        result = analizar_topica(records)
        assert len(result.advertencias) == 1
        assert "dígitos" in result.advertencias[0].descripcion

    def test_topica_caracteres_invalidos(self):
        records = [_rec(data_topica="Ciudad<>Test")]
        result = analizar_topica(records)
        assert len(result.advertencias) == 1
        assert "inválidos" in result.advertencias[0].descripcion


# ═══════════════════════════════════════════════════════════════
# CRONICA ANALYZER
# ═══════════════════════════════════════════════════════════════

class TestCronicaAnalyzer:

    def test_secuencia_cronologica_correcta(self):
        records = [
            _rec(id="#0001", fecha_inicio="15/03/1891"),
            _rec(id="#0002", fila=11, fecha_inicio="20/06/1891"),
        ]
        result = analizar_cronica(records)
        assert result.ok

    def test_anio_fuera_de_rango(self):
        records = [_rec(fecha_inicio="01/01/1000")]
        result = analizar_cronica(records)
        assert len(result.errores) == 1
        assert "fuera del rango" in result.errores[0].descripcion

    def test_regresion_cronologica(self):
        records = [
            _rec(id="#0001", fecha_inicio="15/03/1891"),
            _rec(id="#0002", fila=11, fecha_inicio="20/06/1890"),
        ]
        result = analizar_cronica(records)
        assert len(result.errores) == 1
        assert "REGRESIÓN" in result.errores[0].descripcion

    def test_fecha_no_extraible(self):
        records = [_rec(fecha_inicio="sin fecha")]
        result = analizar_cronica(records)
        assert len(result.advertencias) == 1

    def test_formato_yyyy_mm_dd(self):
        records = [_rec(fecha_inicio="1891-03-15")]
        result = analizar_cronica(records)
        assert result.ok

    def test_mismos_anio_orden_invertido(self):
        records = [
            _rec(id="#0001", fecha_inicio="20/06/1891"),
            _rec(id="#0002", fila=11, fecha_inicio="15/03/1891"),
        ]
        result = analizar_cronica(records)
        # Debe haber advertencia, no error fatal
        assert len(result.advertencias) == 1
        assert len(result.errores) == 0

    def test_mismo_mes_dias_diferentes_no_advierten(self):
        records = [
            _rec(id="#0001", fecha_inicio="20/06/1891"),
            _rec(id="#0002", fila=11, fecha_inicio="05/06/1891"),
        ]
        result = analizar_cronica(records)
        # La sucesión se valida por mes: mismo mes no es regresión
        assert result.ok
        assert len(result.advertencias) == 0
        assert len(result.errores) == 0

    def test_regresion_de_mes_dentro_del_mismo_anio(self):
        records = [
            _rec(id="#0001", fecha_inicio="15/03/1891"),
            _rec(id="#0002", fila=11, fecha_inicio="10/02/1891"),
        ]
        result = analizar_cronica(records)
        assert len(result.advertencias) == 1
        assert "mes" in result.advertencias[0].descripcion
        assert len(result.errores) == 0


# ═══════════════════════════════════════════════════════════════
# COVERAGE ANALYZER
# ═══════════════════════════════════════════════════════════════

class TestCoverageAnalyzer:

    def test_cobertura_suficiente(self):
        records = [_rec(pg_pdf="1-4")]
        result = analizar_coverage(records, total_pdf_pages=10)
        assert result.ok
        assert result.info_extra["estado"] == "OK"

    def test_cobertura_insuficiente(self):
        records = [_rec(pg_pdf="1-20")]
        result = analizar_coverage(records, total_pdf_pages=10)
        assert not result.ok
        assert result.info_extra["estado"] == "INSUFICIENTE"

    def test_cobertura_con_mapper(self):
        records = [
            _rec(id="#0001", folios="001r-005v"),
        ]
        mapper = FolioMapper(pag_pdf_inicio=1)
        result = analizar_coverage(records, total_pdf_pages=20, mapper=mapper)
        assert result.ok
        assert result.info_extra["max_requerido"] == 10

    def test_cobertura_exacta(self):
        records = [_rec(pg_pdf="1-10")]
        result = analizar_coverage(records, total_pdf_pages=10)
        assert result.ok
        assert result.info_extra["diferencia"] == 0
