"""Tests para la capa de infraestructura."""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.domain.entities import InventoryRecord, ExclusionRule, SugerenciaCorreccion
from src.infrastructure.session_repository import SessionRepository
from src.infrastructure.hierarchy_builder import HierarchyBuilder


# ═══════════════════════════════════════════════════════════════
# SESSION REPOSITORY
# ═══════════════════════════════════════════════════════════════

class TestSessionRepository:
    """Tests para el repositorio de sesión JSON."""

    def setup_method(self):
        self.repo = SessionRepository()
        self.tmp_dir = tempfile.mkdtemp()
        self.session_path = os.path.join(self.tmp_dir, "test_session.json")

    def test_guardar_y_cargar_datos_simples(self):
        datos = {
            "excel_path": "test.xlsx",
            "pdf_path": "test.pdf",
            "fila_inicio": 10,
            "fila_fin": 500,
        }
        self.repo.guardar(self.session_path, datos)
        cargados = self.repo.cargar(self.session_path)

        assert cargados["excel_path"] == "test.xlsx"
        assert cargados["fila_inicio"] == 10

    def test_guardar_y_cargar_records(self):
        record = InventoryRecord(
            id="#0001", fila=10, registro="001", escribano="García",
            protocolo="1", folios="001r-002v", pg_pdf="1-4",
            titulo="Compraventa",
        )
        datos = {"records": [record]}
        self.repo.guardar(self.session_path, datos)
        cargados = self.repo.cargar(self.session_path)

        assert len(cargados["records"]) == 1
        assert isinstance(cargados["records"][0], InventoryRecord)
        assert cargados["records"][0].id == "#0001"
        assert cargados["records"][0].escribano == "García"

    def test_guardar_y_cargar_exclusions(self):
        excl = ExclusionRule(
            id="E1", tipo="SALTO", desde=5, hasta=10, motivo="Test"
        )
        datos = {"exclusions": [excl]}
        self.repo.guardar(self.session_path, datos)
        cargados = self.repo.cargar(self.session_path)

        assert len(cargados["exclusions"]) == 1
        assert isinstance(cargados["exclusions"][0], ExclusionRule)
        assert cargados["exclusions"][0].tipo == "SALTO"

    def test_cargar_archivo_inexistente(self):
        cargados = self.repo.cargar("/ruta/inexistente.json")
        assert cargados == {}

    def test_excel_path_inexistente_limpia_datos(self):
        datos = {
            "excel_path": "/ruta/inexistente.xlsx",
            "records": [{"id": "#0001", "fila": 10, "registro": "001",
                         "escribano": "X", "protocolo": "1",
                         "folios": "1r", "pg_pdf": "1", "titulo": "T"}],
            "exclusions": [],
            "suggestions": [],
        }
        # Guardar directamente como JSON (simular archivo existente)
        os.makedirs(os.path.dirname(self.session_path) or '.', exist_ok=True)
        with open(self.session_path, 'w') as f:
            json.dump(datos, f)

        cargados = self.repo.cargar(self.session_path)
        assert cargados["records"] == []

    def test_guardar_y_cargar_suggestions(self):
        sug = SugerenciaCorreccion(
            id="SUG_001", registro_id="#0001", tipo_error="SALTO",
            descripcion="Salto detectado", valor_actual="005r",
            valor_sugerido="003r", escribano="García",
            folios_original="005r", rango_sugerido="003r-004v",
            paginas_pdf="9-12", paginas_sugeridas="5-8",
        )
        datos = {"suggestions": [sug]}
        self.repo.guardar(self.session_path, datos)
        cargados = self.repo.cargar(self.session_path)

        assert len(cargados["suggestions"]) == 1
        assert isinstance(cargados["suggestions"][0], SugerenciaCorreccion)


# ═══════════════════════════════════════════════════════════════
# HIERARCHY BUILDER
# ═══════════════════════════════════════════════════════════════

class TestHierarchyBuilder:
    """Tests para el constructor de jerarquía de 11 niveles."""

    def setup_method(self):
        self.builder = HierarchyBuilder()

    def test_ruta_completa(self):
        record = InventoryRecord(
            id="#0001", fila=10, registro="001", escribano="García López",
            protocolo="3", folios="001r-002v", pg_pdf="1-4",
            titulo="Compraventa de finca", fecha_inicio="15/03/1891",
            interesado1="Juan Pérez", interesado2="María López",
            data_topica="Guadalajara",
        )
        ruta = self.builder.construir_ruta(record, "C:/output", "7")

        assert "ACERVO DOCUMENTAL NUMERO 7" in ruta
        assert "SIGLO 19" in ruta
        assert "FONDO DOCUMENTAL" in ruta
        assert "García López" in ruta
        assert "1891" in ruta
        assert "PROTOCOLO 3" in ruta
        assert "REGISTRO 0001" in ruta
        assert "COMPRAVENTA" in ruta
        assert "3. MARZO" in ruta
        assert "Juan Pérez" in ruta
        assert "María López.pdf" in ruta

    def test_clasificacion_titulo_testamento(self):
        record = InventoryRecord(
            id="#0002", fila=11, registro="002", escribano="López",
            protocolo="1", folios="003r", pg_pdf="5",
            titulo="Testamento abierto", fecha_inicio="01/06/1891",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7")
        assert "TESTAMENTO" in ruta

    def test_clasificacion_titulo_default(self):
        record = InventoryRecord(
            id="#0003", fila=12, registro="003", escribano="López",
            protocolo="1", folios="004r", pg_pdf="7",
            titulo="Documento especial", fecha_inicio="01/06/1891",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7")
        assert "ESCRITURA_VARIAS" in ruta

    def test_sanitize_caracteres_invalidos(self):
        result = HierarchyBuilder._sanitize('Nombre<>Inválido:Test')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result

    def test_sanitize_vacio(self):
        assert HierarchyBuilder._sanitize("") == "SIN_NOMBRE"

    def test_fallback_sin_fecha(self):
        record = InventoryRecord(
            id="#0004", fila=13, registro="004", escribano="Test",
            protocolo="1", folios="005r", pg_pdf="9", titulo="Test",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7")
        # Debe usar el default (1891)
        assert "1891" in ruta

    def test_formato_fecha_yyyy_mm_dd(self):
        record = InventoryRecord(
            id="#0005", fila=14, registro="005", escribano="Test",
            protocolo="1", folios="006r", pg_pdf="11", titulo="Test",
            fecha_inicio="1895-07-20",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7")
        assert "1895" in ruta
        assert "7. JULIO" in ruta

    def test_interesado_vacio_usa_id(self):
        record = InventoryRecord(
            id="#0006", fila=15, registro="006", escribano="Test",
            protocolo="1", folios="007r", pg_pdf="13", titulo="Test",
            fecha_inicio="15/03/1891",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7")
        assert "Interesado_A_0006" in ruta
        assert "0006.pdf" in ruta
