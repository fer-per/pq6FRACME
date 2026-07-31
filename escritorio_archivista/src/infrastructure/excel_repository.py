"""
Repositorio Excel — implementación del ExcelRepositoryPort.

Carga inventarios archivísticos desde archivos Excel (.xlsx)
usando pandas + openpyxl, con mapeo inteligente de columnas.
"""
import logging
import re
from typing import List, Optional

import pandas as pd

from src.domain.entities import InventoryRecord
from src.domain.ports.excel_port import ExcelRepositoryPort
from src.domain.value_objects import (
    SKIPROWS,
    HEADER_ROWS,
    EXCEL_OFFSET,
    COLUMN_ALIASES,
    FALLBACK_COLUMNS,
    SKIP_ROW_KEYWORDS,
    EMPTY_VALUES,
)

logger = logging.getLogger(__name__)


class ExcelRepository(ExcelRepositoryPort):
    """Implementación concreta del repositorio Excel."""

    def cargar_registros(
        self,
        ruta: str,
        fila_inicio: int,
        fila_fin: int,
    ) -> List[InventoryRecord]:
        """Carga registros del inventario Excel."""
        logger.info("Cargando registros desde: %s", ruta)

        df = pd.read_excel(
            ruta,
            skiprows=SKIPROWS,
            header=[0, 1],
            engine='openpyxl',
        )

        # Aplanar MultiIndex de columnas
        df.columns = [
            ' '.join(str(c) for c in col).strip()
            if isinstance(col, tuple) else str(col)
            for col in df.columns
        ]

        # Mapear columnas
        col_map = self._mapear_columnas(df.columns.tolist())
        logger.info("Columnas mapeadas: %s", col_map)

        records: List[InventoryRecord] = []
        record_counter = 0

        for idx, row in df.iterrows():
            fila_real = int(idx) + EXCEL_OFFSET + 1

            # Filtrar por rango de filas
            if fila_real < fila_inicio or fila_real > fila_fin:
                continue

            # Verificar si es sub-encabezado
            first_cell = self._safe_str(row.iloc[0])
            if any(kw in first_cell.lower() for kw in SKIP_ROW_KEYWORDS):
                continue

            # Extraer valores
            registro = self._get_col(row, col_map, "registro")
            escribano = self._get_col(row, col_map, "escribano")
            folios = self._get_col(row, col_map, "folios")

            # Ignorar filas vacías
            if not registro and not escribano and not folios:
                continue

            record_counter += 1
            protocolo = self._get_col(row, col_map, "protocolo")
            protocolo = self._normalizar_protocolo(protocolo)

            records.append(InventoryRecord(
                id=f"#{record_counter:04d}",
                fila=fila_real,
                registro=registro,
                escribano=escribano,
                protocolo=protocolo,
                folios=folios,
                pg_pdf="",  # Se calcula después con el mapper
                titulo=self._get_col(row, col_map, "titulo"),
                fecha_inicio=self._get_col(row, col_map, "fecha_inicio"),
                fecha_fin=self._get_col(row, col_map, "fecha_fin"),
                interesado1=self._get_col(row, col_map, "interesado1"),
                interesado2=self._get_col(row, col_map, "interesado2"),
                data_topica=self._get_col(row, col_map, "data_topica"),
            ))

        logger.info("Cargados %d registros.", len(records))
        return records

    def extraer_metadatos(self, ruta: str) -> dict:
        """Extrae metadatos globales del Excel."""
        logger.info("Extrayendo metadatos de: %s", ruta)

        metadatos = {
            "filepath": ruta,
            "siglo": "",
            "acervo_num": "7",
        }

        try:
            df_header = pd.read_excel(
                ruta, header=None, nrows=SKIPROWS, engine='openpyxl'
            )

            for idx, row in df_header.iterrows():
                for cell in row:
                    cell_str = self._safe_str(cell)

                    # Buscar siglo: "Sección: XIX"
                    if "secci" in cell_str.lower():
                        match = re.search(
                            r'[:\s]+([IVXLCDM]+)', cell_str, re.IGNORECASE
                        )
                        if match:
                            metadatos["siglo"] = match.group(1).upper()

                    # Buscar acervo: "Código del fondo: N07"
                    if "c\u00f3digo" in cell_str.lower() or "codigo" in cell_str.lower():
                        match = re.search(r'N?(\d+)', cell_str)
                        if match:
                            metadatos["acervo_num"] = match.group(1)

        except Exception as e:
            logger.warning("Error extrayendo metadatos: %s", e)

        return metadatos

    def _mapear_columnas(self, columnas: List[str]) -> dict:
        """Mapea nombres de columnas del Excel a campos del modelo."""
        col_map = {}
        columnas_lower = [c.lower() for c in columnas]

        for campo, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                for i, col_lower in enumerate(columnas_lower):
                    if alias in col_lower:
                        col_map[campo] = i
                        break
                if campo in col_map:
                    break

        # Fallbacks por índice
        for campo, idx in FALLBACK_COLUMNS.items():
            if campo not in col_map and idx < len(columnas):
                col_map[campo] = idx

        return col_map

    def _get_col(self, row, col_map: dict, campo: str) -> str:
        """Obtiene el valor de una columna mapeada como string limpio."""
        if campo not in col_map:
            return ""
        idx = col_map[campo]
        if idx >= len(row):
            return ""
        val = row.iloc[idx]
        return self._safe_str(val)

    @staticmethod
    def _safe_str(val) -> str:
        """Convierte un valor a string, tratando NaN/None como vacío."""
        if val is None:
            return ""
        s = str(val).strip()
        if s.lower() in EMPTY_VALUES:
            return ""
        return s

    @staticmethod
    def _normalizar_protocolo(val: str) -> str:
        """Normaliza protocolo: si es float entero (ej: '3.0'), convierte a '3'."""
        if not val:
            return ""
        try:
            f = float(val)
            if f == int(f):
                return str(int(f))
        except (ValueError, TypeError):
            pass
        return val
