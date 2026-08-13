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
        fila_datos_inicio: int,
        fila_inicio: int,
        fila_fin: int,
    ) -> List[InventoryRecord]:
        """
        Carga los registros del inventario desde un archivo Excel.

        Args:
            ruta: Ruta al archivo .xlsx.
            fila_datos_inicio: Fila 1-based del Excel donde empiezan los datos.
                Determina cuántas filas saltar y el offset de numeración.
            fila_inicio: Fila de inicio del rango a incluir.
            fila_fin: Fila de fin del rango a incluir.

        Returns:
            Lista de InventoryRecord.
        """
        ...

    @abstractmethod
    def extraer_metadatos(self, ruta: str, fila_datos_inicio: int) -> dict:
        """
        Extrae metadatos globales del Excel (siglo, acervo, etc.).

        Args:
            ruta: Ruta al archivo .xlsx.
            fila_datos_inicio: Fila 1-based donde empiezan los datos; limita
                la lectura a las filas de cabecera.

        Returns:
            Dict con claves: "siglo", "escribano", "acervo_num", "filepath".
        """
        ...

    @abstractmethod
    def detectar_fila_inicio_datos(self, ruta: str) -> Optional[int]:
        """
        Detecta la fila 1-based del Excel donde empiezan los datos.

        Localiza la primera fila que parece encabezado de columna
        (contiene nombres como registro/escribano/protocolo/folios)
        y devuelve la fila de inicio de datos = encabezado + HEADER_ROWS.

        Args:
            ruta: Ruta al archivo .xlsx.

        Returns:
            Fila 1-based donde empiezan los datos, o None si no se detecta.
        """
        ...

    @abstractmethod
    def guardar_registros(
        self,
        ruta: str,
        fila_datos_inicio: int,
        records: List[InventoryRecord],
    ) -> int:
        """
        Escribe de vuelta los valores de los registros en el Excel.

        Solo se sobrescriben las columnas localizadas por el mapa maestro
        y los registros con ``fila`` válida. Las celdas cuyo valor en el
        registro está vacío no se tocan.

        Args:
            ruta: Ruta al archivo .xlsx (se modifica en disco).
            fila_datos_inicio: Fila 1-based donde empiezan los datos.
            records: Registros con las correcciones ya aplicadas en memoria.

        Returns:
            Cantidad de celdas escritas.
        """
        ...
