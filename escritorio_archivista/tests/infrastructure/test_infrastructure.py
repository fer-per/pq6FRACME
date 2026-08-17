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
            "fila_datos_inicio": 12,
            "fila_inicio": 10,
            "fila_fin": 500,
        }
        self.repo.guardar(self.session_path, datos)
        cargados = self.repo.cargar(self.session_path)

        assert cargados["excel_path"] == "test.xlsx"
        assert cargados["fila_inicio"] == 10
        assert cargados["fila_datos_inicio"] == 12

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
        ruta = self.builder.construir_ruta(
            record, "C:/output", "7", "García López", "XIX"
        )

        assert "ACERVO DOCUMENTAL NUMERO 7" in ruta
        assert "SIGLO XIX" in ruta
        assert "FONDO DOCUMENTAL" in ruta
        assert "GARCÍA LÓPEZ" in ruta
        assert "1891" in ruta
        assert "PROTOCOLO 3" in ruta
        assert "REGISTRO 001" in ruta
        assert "COMPRAVENTA DE FINCA" in ruta
        assert "3. MARZO" in ruta
        assert "Juan Pérez" in ruta
        assert "María López.pdf" in ruta

    def test_carpetas_nivel_1_a_9_en_mayusculas_interesados_preservan_caso(self):
        """Los niveles 1-9 van en mayúsculas; interesado1 (carpeta) e
        interesado2 (archivo) conservan la grafía de la columna."""
        record = InventoryRecord(
            id="#0001", fila=10, registro="001", escribano="García",
            protocolo="3", folios="001r-002v", pg_pdf="1-4",
            titulo="Compraventa de finca", fecha_inicio="15/03/1891",
            interesado1="Juan de Rueda", interesado2="María López",
        )
        ruta = self.builder.construir_ruta(
            record, "/output", "7", "García", "XIX"
        )

        niveles = ruta[len("/output"):].strip(os.sep).split(os.sep)
        assert niveles[0] == "ACERVO DOCUMENTAL NUMERO 7"
        assert niveles[1] == "SIGLO XIX"
        assert niveles[2] == "FONDO DOCUMENTAL"
        assert niveles[3] == "GARCÍA"
        assert niveles[5] == "PROTOCOLO 3"
        assert niveles[6] == "REGISTRO 001"
        assert niveles[7] == "COMPRAVENTA DE FINCA"
        assert niveles[8] == "3. MARZO"
        assert niveles[9] == "Juan de Rueda"
        assert niveles[10] == "María López.pdf"

    def test_acervo_vacio_no_incluye_numero(self):
        record = InventoryRecord(
            id="#0001", fila=10, registro="001", escribano="García",
            protocolo="3", folios="001r", pg_pdf="1-4",
            titulo="Compraventa", fecha_inicio="15/03/1891",
            interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "", "García", "XIX")
        primer_nivel = ruta[len("/output") + 1:].split(os.sep)[0]
        assert primer_nivel == "ACERVO DOCUMENTAL"
        assert "NUMERO" not in primer_nivel

    def test_escribano_vacio_usa_respaldo(self):
        record = InventoryRecord(
            id="#0002", fila=11, registro="001", escribano="",
            protocolo="1", folios="001r", pg_pdf="1-4",
            titulo="Compraventa", fecha_inicio="15/03/1891",
            interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "", "XIX")
        assert "SIN ESCRIBANO" in ruta

    def test_siglo_vacio_se_calcula_del_año(self):
        record = InventoryRecord(
            id="#0002", fila=11, registro="001", escribano="García",
            protocolo="1", folios="001r", pg_pdf="1-4",
            titulo="Compraventa", fecha_inicio="15/03/1891",
            interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "García", "")
        assert "SIGLO XIX" in ruta

    def test_siglo_y_año_ausentes_usa_respaldo(self):
        record = InventoryRecord(
            id="#0002", fila=11, registro="001", escribano="García",
            protocolo="1", folios="001r", pg_pdf="1-4",
            titulo="Compraventa", interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "García", "")
        assert "SIN SIGLO" in ruta
        assert "SIN AÑO" in ruta

    def test_protocolo_vacio_usa_respaldo(self):
        record = InventoryRecord(
            id="#0004", fila=13, registro="001", escribano="García",
            protocolo="", folios="001r", pg_pdf="1-4",
            titulo="Compraventa", fecha_inicio="15/03/1891",
            interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "García", "XIX")
        assert "SIN PROTOCOLO" in ruta

    def test_registro_vacio_usa_respaldo(self):
        record = InventoryRecord(
            id="#0242", fila=275, registro="", escribano="García",
            protocolo="2", folios="079v-080v", pg_pdf="",
            titulo="DOTE", fecha_inicio="06/02/1568",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "García", "XVI")
        assert "SIN REGISTRO" in ruta
        assert "REGISTRO 0242" not in ruta

    def test_registro_invalido_usa_respaldo(self):
        record = InventoryRecord(
            id="#0342", fila=3608, registro="00:00:00", escribano="X",
            protocolo="3", folios="001r", pg_pdf="",
            titulo="PODER", fecha_inicio="06/02/1568",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "X", "XVI")
        assert "SIN REGISTRO" in ruta

    def test_titulo_vacio_usa_respaldo(self):
        record = InventoryRecord(
            id="#0003", fila=12, registro="003", escribano="López",
            protocolo="1", folios="004r", pg_pdf="7",
            titulo="", fecha_inicio="01/06/1891",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "López", "XIX")
        assert "SIN TITULO DE ESCRITURA" in ruta

    def test_mes_ausente_con_año_usa_respaldo(self):
        record = InventoryRecord(
            id="#0003", fila=12, registro="003", escribano="López",
            protocolo="1", folios="004r", pg_pdf="7",
            titulo="Documento", fecha_inicio="1891",
            interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "López", "XIX")
        assert "1891" in ruta
        assert "SIN MES" in ruta

    def test_interesados_truncan_en_primera_coma(self):
        """La carpeta del interesado 1 y el PDF solo usan el nombre previo a la coma."""
        record = InventoryRecord(
            id="#0204", fila=50, registro="006", escribano="Aguilar",
            protocolo="16", folios="281r-281v", pg_pdf="440-441",
            titulo="PODER", fecha_inicio="14/5/1586",
            interesado1="Luis de Rueda, Juan de Mendoza",
            interesado2="Don Melchor de Avalos del Castillo, Otro Más",
            data_topica="AREQUIPA",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Aguilar", "XVI")

        assert "Luis de Rueda" in ruta
        assert "Juan de Mendoza" not in ruta
        assert "," not in ruta
        assert "Don Melchor de Avalos del Castillo.pdf" in ruta
        assert "Otro Más" not in ruta

    def test_interesado_sin_coma_se_mantiene(self):
        record = InventoryRecord(
            id="#0411", fila=60, registro="012", escribano="Aguilar",
            protocolo="16", folios="513v-514r", pg_pdf="901-902",
            titulo="OBLIGACIÓN", fecha_inicio="6/9/1586",
            interesado1="Juan de Salazar", interesado2="Juan Mejía",
            data_topica="AREQUIPA",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Aguilar", "XVI")

        assert "Juan de Salazar" in ruta
        assert "Juan Mejía.pdf" in ruta

    def test_interesado1_vacio_usa_interesado2(self):
        """Nivel 10: sin interesado1, se usa el interesado2."""
        record = InventoryRecord(
            id="#0300", fila=70, registro="020", escribano="Aguilar",
            protocolo="16", folios="900r", pg_pdf="", titulo="PODER",
            fecha_inicio="6/9/1586",
            interesado1="", interesado2="ANDRÉS DE MARCHENA",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Aguilar", "XVI")
        assert "ANDRÉS DE MARCHENA" in ruta

    def test_interesado1_y_2_vacios_usa_interesado3(self):
        record = InventoryRecord(
            id="#0301", fila=71, registro="021", escribano="Aguilar",
            protocolo="16", folios="901r", pg_pdf="", titulo="PODER",
            fecha_inicio="6/9/1586",
            interesado1="", interesado2="", interesado3="TERCER INTERESADO",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Aguilar", "XVI")
        assert "TERCER INTERESADO" in ruta

    def test_interesados_todos_vacios_usa_ilegibles(self):
        """Nivel 10 y 11: sin interesados, carpeta y archivo con nombre ilegible."""
        record = InventoryRecord(
            id="#0302", fila=72, registro="022", escribano="Aguilar",
            protocolo="16", folios="902r", pg_pdf="", titulo="PODER",
            fecha_inicio="6/9/1586",
            interesado1="", interesado2="", interesado3="",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Aguilar", "XVI")
        assert "DATOS DE LOS INTERESADOS ILEGIBLES" in ruta
        assert ruta.endswith("DATOS DE LOS INTERESADOS ILEGIBLES.pdf")

    def test_nombre_pdf_sin_interesado2_usa_interesado1(self):
        """Nivel 11: sin interesado2, el archivo usa el interesado1."""
        record = InventoryRecord(
            id="#0008", fila=17, registro="008", escribano="Test",
            protocolo="1", folios="009r", pg_pdf="17", titulo="Test",
            fecha_inicio="15/03/1891",
            interesado1="MARIA DE SOLIER", interesado2="",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XIX")
        assert ruta.endswith("MARIA DE SOLIER.pdf")

    def test_nombre_pdf_sin_interesado1_ni_2_usa_interesado3(self):
        record = InventoryRecord(
            id="#0009", fila=18, registro="009", escribano="Test",
            protocolo="1", folios="010r", pg_pdf="19", titulo="Test",
            fecha_inicio="15/03/1891",
            interesado1="", interesado2="", interesado3="MANUEL DE LA CRUZ",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XIX")
        assert ruta.endswith("MANUEL DE LA CRUZ.pdf")

    def test_primer_interesado_vacio_no_rompe(self):
        assert HierarchyBuilder._primer_interesado("") == ""
        assert HierarchyBuilder._primer_interesado("Nombre único") == "Nombre único"
        assert HierarchyBuilder._primer_interesado("A, B, C") == "A"
        assert HierarchyBuilder._primer_interesado("  A , B  ") == "A"

    def test_interesados_truncan_en_coma_guion_o_parentesis(self):
        """El nombre de carpeta y archivo corta en coma, guion o paréntesis."""
        assert HierarchyBuilder._primer_interesado("Pedro Álvarez - Escribano") == "Pedro Álvarez"
        assert HierarchyBuilder._primer_interesado("Ana (hija de Pedro)") == "Ana"
        assert HierarchyBuilder._primer_interesado("Juan, Luis y Pedro") == "Juan"
        assert HierarchyBuilder._primer_interesado("  María - De Rueda  ") == "María"

    def test_titulo_usa_valor_literal_de_la_columna(self):
        """La carpeta del título usa el texto de la columna 'titulo', en mayúsculas."""
        record = InventoryRecord(
            id="#0002", fila=11, registro="002", escribano="López",
            protocolo="1", folios="003r", pg_pdf="5",
            titulo="Testamento abierto", fecha_inicio="01/06/1891",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "López", "XIX")
        assert "TESTAMENTO ABIERTO" in ruta
        assert "Testamento abierto" not in ruta

    def test_registro_usa_numero_real_del_catalogo(self):
        """El nivel REGISTRO usa el N° de registro del inventario, no el ID interno."""
        record = InventoryRecord(
            id="#0042", fila=51, registro="3", escribano="López",
            protocolo="1", folios="010r-011v", pg_pdf="19-21",
            titulo="PODER", fecha_inicio="01/06/1567",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "López", "XVI")
        assert "\\REGISTRO 3\\" in ruta or "/REGISTRO 3/" in ruta
        assert "REGISTRO 0042" not in ruta

    def test_registro_mismo_numero_agrupa_registros(self):
        """Varias escrituras del mismo Registro N° comparten carpeta."""
        base = {
            "escribano": "DIEGO DE AGUILAR", "protocolo": "1",
            "folios": "001r-001v", "pg_pdf": "1-2",
            "titulo": "PODER", "fecha_inicio": "07/05/1567",
        }
        r1 = InventoryRecord(id="#0001", fila=19, registro="1", **base)
        r2 = InventoryRecord(id="#0002", fila=20, registro="1", **base)

        p1 = self.builder.construir_ruta(r1, "/output", "7", "DIEGO DE AGUILAR", "XVI")
        p2 = self.builder.construir_ruta(r2, "/output", "7", "DIEGO DE AGUILAR", "XVI")

        assert "REGISTRO 1" in p1
        # La porción de la ruta hasta el nivel REGISTRO es idéntica
        assert p1.split("REGISTRO 1")[0] == p2.split("REGISTRO 1")[0]

    def test_sanitize_caracteres_invalidos(self):
        result = HierarchyBuilder._sanitize('Nombre<>Inválido:Test')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result

    def test_sanitize_vacio(self):
        assert HierarchyBuilder._sanitize("") == "SIN_NOMBRE"

    def test_sin_fecha_año_y_mes_usan_respaldo(self):
        """Sin fecha, los niveles AÑO y MES usan respaldo y el resto persiste."""
        record = InventoryRecord(
            id="#0004", fila=13, registro="004", escribano="Test",
            protocolo="1", folios="005r", pg_pdf="9", titulo="Test",
            interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XIX")
        assert "SIN AÑO" in ruta
        assert "SIN MES" in ruta
        assert "ACERVO DOCUMENTAL NUMERO 7" in ruta
        assert "FONDO DOCUMENTAL" in ruta
        assert "PROTOCOLO 1" in ruta
        assert "María López.pdf" in ruta

    def test_sin_fecha_fin_usa_fecha_fin(self):
        """Si fecha_inicio está vacía, se usa fecha_fin."""
        record = InventoryRecord(
            id="#0010", fila=19, registro="010", escribano="Test",
            protocolo="1", folios="011r", pg_pdf="21", titulo="Test",
            fecha_fin="20/06/1568",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XVI")
        assert "1568" in ruta
        assert "6. JUNIO" in ruta

    def test_fecha_invalida_año_y_mes_usan_respaldo(self):
        """Fecha con mes fuera de rango no es una fecha válida."""
        record = InventoryRecord(
            id="#0011", fila=20, registro="011", escribano="Test",
            protocolo="1", folios="012r", pg_pdf="23", titulo="Test",
            fecha_inicio="15/15/1891",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XIX")
        assert "SIN AÑO" in ruta
        assert "SIN MES" in ruta

    def test_numeracion_sucesiva_pdf_repetido(self, tmp_path):
        """PDFs con el mismo nombre en la misma carpeta se numeran por orden."""
        base = {
            "escribano": "García", "protocolo": "1",
            "folios": "001r", "pg_pdf": "1",
            "titulo": "Compraventa", "fecha_inicio": "15/03/1891",
            "interesado1": "Juan Pérez", "interesado2": "María López",
        }
        r1 = InventoryRecord(id="#0001", fila=19, registro="1", **base)
        r2 = InventoryRecord(id="#0002", fila=20, registro="1", **base)
        r3 = InventoryRecord(id="#0003", fila=21, registro="1", **base)

        p1 = self.builder.construir_ruta(r1, str(tmp_path), "7", "García", "XIX")
        os.makedirs(os.path.dirname(p1), exist_ok=True)
        with open(p1, 'w') as f:
            f.write("x")

        p2 = self.builder.construir_ruta(r2, str(tmp_path), "7", "García", "XIX")
        os.makedirs(os.path.dirname(p2), exist_ok=True)
        with open(p2, 'w') as f:
            f.write("x")

        p3 = self.builder.construir_ruta(r3, str(tmp_path), "7", "García", "XIX")

        assert p1.endswith("María López.pdf")
        assert p2.endswith("María López_2.pdf")
        assert p3.endswith("María López_3.pdf")

    def test_numeracion_sucesiva_sin_fecha(self, tmp_path):
        """La numeración sucesiva también aplica sin fecha (con escr. global)."""
        base = {
            "escribano": "DIEGO DE AGUILAR",
            "interesado1": "Juan Pérez", "interesado2": "María López",
        }
        r1 = InventoryRecord(
            id="#0001", fila=19, registro="", protocolo="1",
            folios="001r", pg_pdf="1", titulo="Test", **base,
        )
        r2 = InventoryRecord(
            id="#0002", fila=20, registro="", protocolo="1",
            folios="002r", pg_pdf="2", titulo="Test", **base,
        )

        p1 = self.builder.construir_ruta(r1, str(tmp_path), "7", "DIEGO DE AGUILAR", "XVI")
        os.makedirs(os.path.dirname(p1), exist_ok=True)
        with open(p1, 'w') as f:
            f.write("x")

        p2 = self.builder.construir_ruta(r2, str(tmp_path), "7", "DIEGO DE AGUILAR", "XVI")

        assert p1.endswith("María López.pdf")
        assert p2.endswith("María López_2.pdf")
        assert os.path.dirname(p1) == os.path.dirname(p2)

    def test_formato_fecha_yyyy_mm_dd(self):
        record = InventoryRecord(
            id="#0005", fila=14, registro="005", escribano="Test",
            protocolo="1", folios="006r", pg_pdf="11", titulo="Test",
            fecha_inicio="1895-07-20",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XIX")
        assert "1895" in ruta
        assert "7. JULIO" in ruta

    def test_nombre_pdf_usuario_interesado2(self):
        record = InventoryRecord(
            id="#0007", fila=16, registro="007", escribano="Test",
            protocolo="1", folios="008r", pg_pdf="15", titulo="Test",
            fecha_inicio="15/03/1891",
            interesado1="Juan Pérez", interesado2="María López",
        )
        ruta = self.builder.construir_ruta(record, "/output", "7", "Test", "XIX")
        assert ruta.endswith("María López.pdf")
