"""
Constructor de jerarquía documental de 11 niveles.

Genera las rutas de carpetas para organizar los fragmentos PDF
siguiendo la estructura archivística definida.
"""
import logging
import os
import re
from typing import Optional

from src.domain.entities import InventoryRecord
from src.domain.ports.hierarchy_port import HierarchyBuilderPort
from src.domain.value_objects import (
    TITLE_CLASSIFICATION,
    TITLE_DEFAULT,
    MONTH_NAMES,
    ROMAN_TO_ARABIC,
    INVALID_FILENAME_CHARS,
)

logger = logging.getLogger(__name__)


class HierarchyBuilder(HierarchyBuilderPort):
    """
    Implementación del constructor de jerarquía de 11 niveles.

    Niveles:
    1. ACERVO DOCUMENTAL NUMERO {acervo_num}
    2. SIGLO {siglo_arabigo}
    3. FONDO DOCUMENTAL
    4. {escribano}
    5. {año}
    6. PROTOCOLO {protocolo}
    7. REGISTRO {id sin #}
    8. {titulo_estandar} (clasificación)
    9. {mes}
    10. {interesado1}
    11. {interesado2}.pdf (nombre del archivo)
    """

    def construir_ruta(
        self,
        record: InventoryRecord,
        output_dir: str,
        acervo_num: str,
    ) -> str:
        """Construye la ruta completa de 11 niveles para un registro."""

        anio, mes = self._extraer_anio_mes(record)
        siglo_arabigo = (anio // 100) + 1 if anio else 19

        # Nivel 1: Acervo
        n1 = f"ACERVO DOCUMENTAL NUMERO {acervo_num}"

        # Nivel 2: Siglo
        n2 = f"SIGLO {siglo_arabigo}"

        # Nivel 3: Fondo Documental (constante)
        n3 = "FONDO DOCUMENTAL"

        # Nivel 4: Escribano
        n4 = self._sanitize(record.escribano or "SIN_ESCRIBANO")

        # Nivel 5: Año
        n5 = str(anio) if anio else "SIN_ANIO"

        # Nivel 6: Protocolo
        n6 = f"PROTOCOLO {self._sanitize(record.protocolo or '0')}"

        # Nivel 7: Registro (ID sin #)
        registro_id = record.id.replace("#", "")
        n7 = f"REGISTRO {registro_id}"

        # Nivel 8: Título clasificado
        n8 = self._clasificar_titulo(record.titulo)

        # Nivel 9: Mes
        n9 = MONTH_NAMES.get(mes, "1. ENERO")

        # Nivel 10: Interesado 1
        n10 = self._sanitize(record.interesado1) if record.interesado1 else f"Interesado_A_{registro_id}"

        # Nivel 11: Nombre del archivo (Interesado 2 + .pdf)
        if record.interesado2:
            n11 = f"{self._sanitize(record.interesado2)}.pdf"
        else:
            n11 = f"{registro_id}.pdf"

        full_path = os.path.join(
            output_dir, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11
        )

        # Manejo de colisiones
        full_path = self._resolver_colision(full_path)

        return full_path

    def _clasificar_titulo(self, titulo: str) -> str:
        """Clasifica el título del documento."""
        if not titulo:
            return TITLE_DEFAULT
        titulo_lower = titulo.lower()
        for keyword, classification in TITLE_CLASSIFICATION.items():
            if keyword in titulo_lower:
                return classification
        return TITLE_DEFAULT

    def _extraer_anio_mes(self, record: InventoryRecord):
        """
        Extrae año y mes de fecha_inicio.

        Intenta varios formatos. Fallback: busca 4 dígitos en registro.
        """
        anio, mes = None, 1

        if record.fecha_inicio:
            # Formato d/m/yyyy
            match = re.match(
                r'(\d{1,2})/(\d{1,2})/(\d{4})', record.fecha_inicio
            )
            if match:
                mes = int(match.group(2))
                anio = int(match.group(3))
                return anio, mes

            # Formato yyyy-mm-dd
            match = re.match(
                r'(\d{4})-(\d{1,2})-(\d{1,2})', record.fecha_inicio
            )
            if match:
                anio = int(match.group(1))
                mes = int(match.group(2))
                return anio, mes

            # Buscar 4 dígitos
            match = re.search(r'(\d{4})', record.fecha_inicio)
            if match:
                anio = int(match.group(1))
                return anio, mes

        # Fallback: buscar en campo registro
        if record.registro:
            match = re.search(r'(\d{4})', record.registro)
            if match:
                anio = int(match.group(1))
                return anio, mes

        # Default
        return 1891, 1

    @staticmethod
    def _sanitize(name: str) -> str:
        """
        Sanitiza un nombre para uso en sistema de archivos Windows.

        Reemplaza caracteres inválidos, colapsa espacios y underscores.
        """
        if not name:
            return "SIN_NOMBRE"

        # Reemplazar caracteres inválidos
        for char in INVALID_FILENAME_CHARS:
            name = name.replace(char, '_')

        # Colapsar múltiples espacios y underscores
        name = re.sub(r'[\s_]+', ' ', name).strip()

        if not name:
            return "SIN_NOMBRE"

        return name

    @staticmethod
    def _resolver_colision(full_path: str) -> str:
        """Si la ruta ya existe, agrega _2, _3... al nombre del archivo."""
        if not os.path.exists(full_path):
            return full_path

        base, ext = os.path.splitext(full_path)
        counter = 2
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"
