"""Tests para la capa de aplicación."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import MagicMock, patch
from src.domain.entities import InventoryRecord, ExclusionRule, AnalysisError
from src.application.dto import ResultadoCarga, ResultadoAnalisis, ResultadoFragmentacion
from src.application.use_cases.analyze_data import AnalizarDatosUseCase
from src.application.use_cases.manage_exclusions import GestionarExclusionesUseCase
from src.application.use_cases.load_inventory import CargarInventarioUseCase


def _rec(
    id: str = "#0001", fila: int = 10, folios: str = "001r-002v",
    data_topica: str = "Ciudad", fecha_inicio: str = "15/03/1891",
    **kwargs
) -> InventoryRecord:
    return InventoryRecord(
        id=id, fila=fila, registro="001", escribano="García",
        protocolo="1", folios=folios, pg_pdf="", titulo="Compraventa",
        data_topica=data_topica, fecha_inicio=fecha_inicio, **kwargs,
    )


# ═══════════════════════════════════════════════════════════════
# ANALIZAR DATOS USE CASE
# ═══════════════════════════════════════════════════════════════

class TestAnalizarDatosUseCase:
    """Tests para el caso de uso AnalizarDatos."""

    def test_analisis_sin_errores(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="003r-004v"),
        ]
        uc = AnalizarDatosUseCase()
        result = uc.ejecutar(records)

        assert isinstance(result, ResultadoAnalisis)
        assert result.folios_result is not None
        assert result.topica_result is not None
        assert result.cronica_result is not None
        assert result.folios_result.ok

    def test_analisis_con_salto(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="005r-006v"),
        ]
        uc = AnalizarDatosUseCase()
        result = uc.ejecutar(records)

        assert result.folios_result is not None
        assert len(result.folios_result.advertencias) == 1

    def test_analisis_con_coverage(self):
        records = [_rec(id="#0001", folios="001r-002v")]
        uc = AnalizarDatosUseCase()
        result = uc.ejecutar(records, total_pdf_pages=10)

        assert result.coverage_result is not None
        assert result.coverage_result.ok

    def test_analisis_sin_coverage_cuando_no_hay_pdf(self):
        records = [_rec()]
        uc = AnalizarDatosUseCase()
        result = uc.ejecutar(records, total_pdf_pages=0)

        assert result.coverage_result is None

    def test_records_con_error_marcados_revisar(self):
        records = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="001r-003v"),  # Repetido
        ]
        uc = AnalizarDatosUseCase()
        result = uc.ejecutar(records)

        revisar = [r for r in result.records if r.estado == "REVISAR"]
        assert len(revisar) >= 1


# ═══════════════════════════════════════════════════════════════
# GESTIONAR EXCLUSIONES USE CASE
# ═══════════════════════════════════════════════════════════════

class TestGestionarExclusionesUseCase:
    """Tests para el caso de uso GestionarExclusiones."""

    def test_agregar_salto(self):
        uc = GestionarExclusionesUseCase()
        result = uc.agregar_salto([], desde=5, hasta=10, motivo="Folios en blanco")

        assert len(result) == 1
        assert result[0].tipo == "SALTO"
        assert result[0].desde == 5
        assert result[0].hasta == 10

    def test_agregar_ignorar(self):
        uc = GestionarExclusionesUseCase()
        result = uc.agregar_ignorar(
            [], desde=2, hasta=3, motivo="Portada",
            tipo_contenido="Portada",
        )

        assert len(result) == 1
        assert result[0].tipo == "IGNORAR"
        assert result[0].tipo_contenido == "Portada"

    def test_eliminar_exclusion(self):
        uc = GestionarExclusionesUseCase()
        excl = ExclusionRule(id="E1", tipo="SALTO", desde=5, hasta=10, motivo="Test")
        result = uc.eliminar_exclusion([excl], "E1")

        assert len(result) == 0

    def test_eliminar_inexistente(self):
        uc = GestionarExclusionesUseCase()
        excl = ExclusionRule(id="E1", tipo="SALTO", desde=5, hasta=10, motivo="Test")
        result = uc.eliminar_exclusion([excl], "E99")

        assert len(result) == 1  # No se eliminó nada

    def test_inmutabilidad(self):
        """agregar_salto no modifica la lista original."""
        uc = GestionarExclusionesUseCase()
        original = []
        result = uc.agregar_salto(original, desde=1, hasta=5, motivo="Test")

        assert len(original) == 0
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════
# CARGAR INVENTARIO USE CASE
# ═══════════════════════════════════════════════════════════════

class TestCargarInventarioUseCase:
    """Tests para el caso de uso CargarInventario con mock."""

    def test_carga_con_mock(self):
        mock_repo = MagicMock()
        mock_repo.extraer_metadatos.return_value = {
            "filepath": "test.xlsx",
            "siglo": "XIX",
            "acervo_num": "7",
        }
        mock_repo.cargar_registros.return_value = [
            _rec(id="#0001", folios="001r-002v"),
            _rec(id="#0002", fila=11, folios="003r-004v"),
        ]

        uc = CargarInventarioUseCase(mock_repo)
        result = uc.ejecutar("test.xlsx", fila_inicio=10, fila_fin=500)

        assert isinstance(result, ResultadoCarga)
        assert len(result.records) == 2
        assert result.metadata["total_records"] == 2
        mock_repo.cargar_registros.assert_called_once()

    def test_carga_con_errores_marca_revisar(self):
        mock_repo = MagicMock()
        mock_repo.extraer_metadatos.return_value = {"filepath": "t.xlsx", "siglo": "", "acervo_num": "7"}
        mock_repo.cargar_registros.return_value = [
            _rec(id="#0001", folios="abc"),  # Formato inválido
        ]

        uc = CargarInventarioUseCase(mock_repo)
        result = uc.ejecutar("t.xlsx", fila_inicio=10, fila_fin=500)

        assert len(result.errors) >= 1
        revisar = [r for r in result.records if r.estado == "REVISAR"]
        assert len(revisar) == 1
