"""
Puerto abstracto para servicio PDF.

Define la interfaz para operaciones con documentos PDF:
obtener páginas, extraer fragmentos y renderizar previsualizaciones.
"""
from abc import ABC, abstractmethod
from typing import List, Any


class PDFServicePort(ABC):
    """Interfaz abstracta para operaciones con PDF."""

    @abstractmethod
    def obtener_total_paginas(self, ruta: str) -> int:
        """
        Obtiene el total de páginas de un PDF.

        Args:
            ruta: Ruta al archivo PDF.

        Returns:
            Número total de páginas.
        """
        ...

    @abstractmethod
    def abrir(self, ruta: str) -> Any:
        """
        Abre un PDF para extracción reutilizable.

        Abre el documento una sola vez para que la extracción de múltiples
        fragmentos no re-cargue el archivo completo en memoria por cada
        fragmento.

        Args:
            ruta: Ruta al PDF maestro.

        Returns:
            Lector opaco del PDF (depende de la implementación). Debe
            liberarse con ``cerrar``.
        """
        ...

    @abstractmethod
    def cerrar(self, lector: Any) -> None:
        """
        Libera los recursos del lector abierto con ``abrir``.

        Args:
            lector: Lector devuelto por ``abrir``.
        """
        ...

    @abstractmethod
    def extraer_paginas(
        self,
        lector: Any,
        paginas: List[int],
        ruta_destino: str,
    ) -> None:
        """
        Extrae páginas de un PDF ya abierto y las guarda en un nuevo archivo.

        Args:
            lector: Lector devuelto por ``abrir``.
            paginas: Lista de números de página (1-based).
            ruta_destino: Ruta donde guardar el PDF resultante.
        """
        ...

    @abstractmethod
    def renderizar_pagina(
        self,
        ruta: str,
        num_pagina: int,
        zoom: int = 100,
    ) -> Any:
        """
        Renderiza una página del PDF como imagen.

        Args:
            ruta: Ruta al PDF.
            num_pagina: Número de página (1-based).
            zoom: Nivel de zoom en porcentaje.

        Returns:
            Imagen renderizada (formato depende de la implementación).
        """
        ...
