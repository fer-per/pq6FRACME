"""
Puerto abstracto para constructor de jerarquía documental.

Define la interfaz para generar la estructura de carpetas
de 11 niveles para la clasificación archivística.

Cada nivel que carece del dato correspondiente usa un nombre de
respaldo (SIN ...) y se continúa con los niveles siguientes, de modo
que la estructura de 11 niveles siempre se construye de forma íntegra.
"""
from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities import InventoryRecord


class HierarchyBuilderPort(ABC):
    """Interfaz abstracta para construir rutas jerárquicas."""

    @abstractmethod
    def construir_ruta(
        self,
        record: InventoryRecord,
        output_dir: str,
        acervo_num: str = "",
        escribano: str = "",
        siglo: str = "",
    ) -> str:
        """
        Construye la ruta completa de carpetas para un registro.

        Args:
            record: Registro del inventario.
            output_dir: Directorio base de salida.
            acervo_num: Número de acervo documental (metadato del Excel).
            escribano: Escribano global del fondo (metadato del Excel).
            siglo: Siglo romano del fondo (metadato del Excel).

        Returns:
            Ruta completa al archivo PDF de destino.
        """
        ...
