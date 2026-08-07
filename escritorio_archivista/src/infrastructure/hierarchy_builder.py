"""
Constructor de jerarquía documental de 11 niveles.

Genera las rutas de carpetas para organizar los fragmentos PDF
siguiendo la estructura archivística definida.

Caso excepcional: cuando un registro no tiene fecha, el PDF se
guarda directamente en la carpeta del escribano, omitiendo los
niveles derivados de la fecha (SIGLO, AÑO, PROTOCOLO, etc.).
"""
import logging
import os
import re
from typing import Optional, Tuple

from src.domain.entities import InventoryRecord
from src.domain.ports.hierarchy_port import HierarchyBuilderPort
from src.domain.value_objects import (
    TITLE_DEFAULT,
    MONTH_NAMES,
    YEAR_MIN,
    YEAR_MAX,
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
    7. REGISTRO {registro} (número real del catálogo; fallback al ID interno)
    8. {titulo} (valor literal de la columna "titulo")
    9. {mes}
    10. {interesado1}
    11. {interesado2}.pdf (nombre del archivo)

    Excepción: si el registro no tiene fecha, se crea únicamente la
    carpeta "SIN FECHA" en la raíz del directorio de salida:
    {output_dir}/SIN FECHA/{interesado1}/{interesado2}.pdf

    Si dos PDFs comparten el mismo nombre dentro de la misma carpeta,
    se asigna una numeración sucesiva según el orden de creación:
    {nombre}.pdf, {nombre}_2.pdf, {nombre}_3.pdf, ...
    """

    def construir_ruta(
        self,
        record: InventoryRecord,
        output_dir: str,
        acervo_num: str,
    ) -> str:
        """Construye la ruta completa de 11 niveles para un registro."""
        anio, mes = self._extraer_anio_mes(record)

        if anio is None:
            full_path = self._ruta_sin_fecha(record, output_dir)
        else:
            full_path = self._ruta_con_fecha(
                record, output_dir, acervo_num, anio, mes
            )

        return self._resolver_colision(full_path)

    def _ruta_con_fecha(
        self,
        record: InventoryRecord,
        output_dir: str,
        acervo_num: str,
        anio: int,
        mes: int,
    ) -> str:
        """Construye la ruta completa (con fecha) de 11 niveles."""
        siglo_arabigo = (anio // 100) + 1
        registro_id = record.id.replace("#", "")

        n1 = f"ACERVO DOCUMENTAL NUMERO {acervo_num}"
        n2 = f"SIGLO {siglo_arabigo}"
        n3 = "FONDO DOCUMENTAL"
        n4 = self._sanitize(record.escribano or "SIN_ESCRIBANO")
        n5 = str(anio)
        n6 = f"PROTOCOLO {self._sanitize(record.protocolo or '0')}"
        n7 = self._nivel_registro(record, registro_id)
        n8 = self._nivel_titulo(record)
        n9 = MONTH_NAMES.get(mes, "1. ENERO")
        n10 = self._nivel_interesado1(record, registro_id)
        n11 = self._nombre_archivo(record, registro_id)

        return os.path.join(
            output_dir, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11
        )

    def _ruta_sin_fecha(
        self,
        record: InventoryRecord,
        output_dir: str,
    ) -> str:
        """
        Construye la ruta cuando el registro no tiene fecha.

        Se crea únicamente la carpeta "SIN FECHA" en la raíz del
        directorio de salida, con las carpetas de interesados:
        {output_dir}/SIN FECHA/{interesado1}/{pdf}
        """
        registro_id = record.id.replace("#", "")

        n_sin_fecha = "SIN FECHA"
        n10 = self._nivel_interesado1(record, registro_id)
        n11 = self._nombre_archivo(record, registro_id)

        return os.path.join(output_dir, n_sin_fecha, n10, n11)

    @staticmethod
    def _nombre_archivo(record: InventoryRecord, registro_id: str) -> str:
        """Genera el nombre del archivo PDF usando interesado 2, 1 o el ID."""
        nombre = HierarchyBuilder._primer_interesado(
            record.interesado2 or record.interesado1
        )
        if nombre:
            return f"{HierarchyBuilder._sanitize(nombre)}.pdf"
        return f"{registro_id}.pdf"

    @staticmethod
    def _primer_interesado(nombre: str) -> str:
        """
        Toma solo el primer interesado de un nombre compuesto.

        En el inventario, un interesado puede listar varias personas
        separadas por coma (ej: "Luis de Rueda, Juan de Mendoza"). Se
        usa únicamente el texto anterior a la primera coma, sin incluir
        la coma, para carpetas y nombres de archivo más cortos.
        """
        if not nombre:
            return ""
        return nombre.split(",", 1)[0].strip()

    @staticmethod
    def _nivel_registro(record: InventoryRecord, registro_id: str) -> str:
        """
        Genera el nivel REGISTRO usando el número real del catálogo.

        En el inventario, un mismo "Registro N°X" agrupa varias escrituras;
        usar el ID interno (generado por orden de fila) fragmentaría ese
        grupo en una carpeta por documento. Se usa ``record.registro`` cuando
        el valor es válido y, si no, se cae al ID interno para conservar
        rutas únicas.

        Args:
            record: Registro del inventario.
            registro_id: ID interno sin el prefijo '#'.

        Returns:
            Nombre del nivel, ej: "REGISTRO 3" o "REGISTRO 0001".
        """
        valor = (record.registro or "").strip()

        # Valores que no son un número de registro: vacío, hora mal
        # interpretada, filas de índice/sub-encabezado o anotaciones.
        if valor and valor not in ("0", "00:00:00") and ":" not in valor \
                and not re.search(r'(?i)(registro|protocolo|indice|salto)', valor):
            return f"REGISTRO {HierarchyBuilder._sanitize(valor)}"

        return f"REGISTRO {registro_id}"

    @staticmethod
    def _nivel_titulo(record: InventoryRecord) -> str:
        """
        Genera el nivel TITULO usando el valor literal de la columna.

        La carpeta del título de escritura se nombra con el texto
        exacto de la columna ``titulo``. Si está vacío, se usa un
        valor por defecto.
        """
        titulo = (record.titulo or "").strip()
        if not titulo:
            return TITLE_DEFAULT
        return HierarchyBuilder._sanitize(titulo)

    @staticmethod
    def _nivel_interesado1(record: InventoryRecord, registro_id: str) -> str:
        """Genera la carpeta del 1er interesado, con respaldo en el ID."""
        nombre = HierarchyBuilder._primer_interesado(record.interesado1)
        if nombre:
            return HierarchyBuilder._sanitize(nombre)
        return f"Interesado_A_{registro_id}"

    def _extraer_anio_mes(
        self, record: InventoryRecord
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrae año y mes de las fechas del registro.

        Busca una fecha válida en ``fecha_inicio`` y ``fecha_fin``. Como
        último recurso, intenta encontrar un año válido en el número de
        registro.

        Returns:
            Tupla ``(anio, mes)`` si hay una fecha válida; ``(None, None)``
            si el registro no tiene fecha.
        """
        for campo in (record.fecha_inicio, record.fecha_fin):
            if not campo:
                continue
            resultado = self._parsear_fecha(campo)
            if resultado is not None:
                return resultado

        # Fallback: buscar un año válido en el número de registro
        if record.registro:
            match = re.search(r'(\d{4})', record.registro)
            if match and self._es_anio_valido(int(match.group(1))):
                return int(match.group(1)), 1

        return None, None

    @staticmethod
    def _parsear_fecha(valor: str) -> Optional[Tuple[int, int]]:
        """
        Parsea una fecha textual en ``(anio, mes)``.

        Acepta formatos ``d/m/yyyy``, ``yyyy-mm-dd`` y cualquier año de
        4 dígitos dentro del texto. Devuelve ``None`` si no hay una fecha
        válida.
        """
        # Formato d/m/yyyy
        match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', valor)
        if match:
            mes, anio = int(match.group(2)), int(match.group(3))
            if 1 <= mes <= 12 and HierarchyBuilder._es_anio_valido(anio):
                return anio, mes
            return None

        # Formato yyyy-mm-dd
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', valor)
        if match:
            anio, mes = int(match.group(1)), int(match.group(2))
            if 1 <= mes <= 12 and HierarchyBuilder._es_anio_valido(anio):
                return anio, mes
            return None

        # Cualquier año de 4 dígitos dentro del texto
        match = re.search(r'(\d{4})', valor)
        if match and HierarchyBuilder._es_anio_valido(int(match.group(1))):
            return int(match.group(1)), 1

        return None

    @staticmethod
    def _es_anio_valido(anio: int) -> bool:
        """True si el año está dentro del rango histórico permitido."""
        return YEAR_MIN <= anio <= YEAR_MAX

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
        """
        Si la ruta ya existe, agrega numeración sucesiva al archivo.

        Ej: ``{nombre}.pdf`` → ``{nombre}_2.pdf`` → ``{nombre}_3.pdf``.
        La numeración sigue el orden de creación de los archivos.
        """
        if not os.path.exists(full_path):
            return full_path

        base, ext = os.path.splitext(full_path)
        counter = 2
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"
