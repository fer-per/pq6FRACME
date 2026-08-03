"""Tests del servicio PDF y del flujo de fragmentación con lector reutilizable."""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import MagicMock

from src.infrastructure.pdf_service import PDFService
from src.application.use_cases.fragment_pdf import FragmentarPDFUseCase
from src.domain.entities import InventoryRecord


def _crear_pdf_maestro(path: str, total_paginas: int = 10) -> str:
    """Crea un PDF de prueba con una etiqueta de texto por página."""
    import fitz

    doc = fitz.open()
    for i in range(total_paginas):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), f"PAGINA_{i + 1}", fontsize=12)
    doc.save(path)
    doc.close()
    return path


def _texto_de(path: str) -> str:
    """Extrae el texto plano de un PDF."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    try:
        return " ".join(page.extract_text() or "" for page in reader.pages)
    finally:
        reader.close()


class TestPDFService:
    """Tests del servicio PDF con reutilización del lector."""

    def setup_method(self):
        self.service = PDFService()
        self.tmp_dir = tempfile.mkdtemp()
        self.maestro = os.path.join(self.tmp_dir, "maestro.pdf")
        _crear_pdf_maestro(self.maestro, total_paginas=10)

    def test_obtener_total_paginas(self):
        assert self.service.obtener_total_paginas(self.maestro) == 10

    def test_extraer_paginas_reutilizando_lector(self):
        lector = self.service.abrir(self.maestro)
        try:
            destino = os.path.join(self.tmp_dir, "frag.pdf")
            self.service.extraer_paginas(lector, [1, 2], destino)

            destino2 = os.path.join(self.tmp_dir, "frag2.pdf")
            self.service.extraer_paginas(lector, [4], destino2)
        finally:
            self.service.cerrar(lector)

        texto_1 = _texto_de(destino)
        assert "PAGINA_1" in texto_1
        assert "PAGINA_2" in texto_1
        assert "PAGINA_3" not in texto_1
        assert "PAGINA_4" in _texto_de(destino2)

    def test_extraer_paginas_fuera_de_rango_se_omite(self):
        lector = self.service.abrir(self.maestro)
        try:
            destino = os.path.join(self.tmp_dir, "frag.pdf")
            self.service.extraer_paginas(lector, [1, 999], destino)
        finally:
            self.service.cerrar(lector)

        texto = _texto_de(destino)
        assert "PAGINA_1" in texto
        assert "PAGINA_999" not in texto

    def test_extraer_paginas_sin_paginas_validas_no_crea_archivo(self):
        lector = self.service.abrir(self.maestro)
        try:
            destino = os.path.join(self.tmp_dir, "vacio.pdf")
            self.service.extraer_paginas(lector, [999], destino)
        finally:
            self.service.cerrar(lector)

        assert not os.path.exists(destino)

    def test_cerrar_con_none_no_falla(self):
        self.service.cerrar(None)

    def test_cerrar_cierra_el_flujo_del_lector(self):
        lector = self.service.abrir(self.maestro)
        self.service.cerrar(lector)
        assert lector.stream.closed


class TestFragmentarPDFUseCase:
    """Tests del caso de uso con lector abierto una sola vez."""

    def _record(self, id="#0001", folios="001r-002v") -> InventoryRecord:
        return InventoryRecord(
            id=id, fila=10, registro="001", escribano="García",
            protocolo="1", folios=folios, pg_pdf="1-2",
            titulo="Compraventa",
        )

    def test_abre_el_lector_una_vez_y_cierra_siempre(self):
        pdf_service = MagicMock()
        hierarchy = MagicMock()
        uc = FragmentarPDFUseCase(pdf_service, hierarchy)

        tmp_dir = tempfile.mkdtemp()
        dest = os.path.join(tmp_dir, "out", "acervo", "registro.pdf")
        hierarchy.construir_ruta.return_value = dest

        records = [self._record()]

        uc.ejecutar(
            records=records,
            pdf_path="maestro.pdf",
            output_dir=tmp_dir,
            acervo_num="7",
            pag_pdf_inicio=1,
        )

        # El PDF maestro se abre UNA sola vez y se cierra siempre
        pdf_service.abrir.assert_called_once_with("maestro.pdf")
        lector = pdf_service.abrir.return_value
        pdf_service.cerrar.assert_called_once_with(lector)

        # extraer_paginas reutiliza el mismo lector
        pdf_service.extraer_paginas.assert_called_once_with(lector, [1, 2, 3, 4], dest)
        assert records[0].estado == "FRAGMENTADO"

    def test_cierra_lector_aun_con_error_en_extraccion(self):
        pdf_service = MagicMock()
        hierarchy = MagicMock()
        uc = FragmentarPDFUseCase(pdf_service, hierarchy)

        pdf_service.extraer_paginas.side_effect = OSError("Disco lleno")

        tmp_dir = tempfile.mkdtemp()
        dest = os.path.join(tmp_dir, "out", "registro.pdf")
        hierarchy.construir_ruta.return_value = dest

        records = [self._record()]

        result = uc.ejecutar(
            records=records,
            pdf_path="maestro.pdf",
            output_dir=tmp_dir,
            acervo_num="7",
            pag_pdf_inicio=1,
        )

        assert result.total_fallos == 1
        assert result.total_exitos == 0
        pdf_service.cerrar.assert_called_once()
