"""
Puerto abstracto para constructor de jerarquía documental.

Define la interfaz para generar la estructura de carpetas
de 11 niveles para la clasificación archivística.

Excepción: si el registro no tiene fecha, la ruta se recorta y
el PDF se guarda directamente en la carpeta del escribano.
"""
from abc import ABC, abstractmethod

from src.domain.entities import InventoryRecord


class HierarchyBuilderPort(ABC):
    """Interfaz abstracta para construir rutas jerárquicas."""

    @abstractmethod
    def construir_ruta(
        self,
        record: InventoryRecord,
        output_dir: str,
        acervo_num: str,
    ) -> str:
        """
        Construye la ruta completa de carpetas para un registro.

        Args:
            record: Registro del inventario.
            output_dir: Directorio base de salida.
            acervo_num: Número de acervo documental.

        Returns:
            Ruta completa al archivo PDF de destino.
        """
        ...
