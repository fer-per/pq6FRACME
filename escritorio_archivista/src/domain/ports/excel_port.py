"""
Puerto abstracto para repositorio Excel.

Define la interfaz que la infraestructura debe implementar
para cargar inventarios archivísticos desde archivos Excel.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from src.domain.entities import InventoryRecord


class ExcelRepositoryPort(ABC):
    """Interfaz abstracta para acceso a archivos Excel."""

    @abstractmethod
    def cargar_registros(
        self,
        ruta: str,
        fila_inicio: int,
        fila_fin: int,
    ) -> List[InventoryRecord]:
        """
        Carga los registros del inventario desde un archivo Excel.

        Args:
            ruta: Ruta al archivo .xlsx.
            fila_inicio: Fila de inicio (basada en el Excel, incluyendo offset).
            fila_fin: Fila de fin.

        Returns:
            Lista de InventoryRecord.
        """
        ...

    @abstractmethod
    def extraer_metadatos(self, ruta: str) -> dict:
        """
        Extrae metadatos globales del Excel (siglo, acervo, etc.).

        Args:
            ruta: Ruta al archivo .xlsx.

        Returns:
            Dict con claves: "siglo", "acervo_num", "filepath".
        """
        ...
