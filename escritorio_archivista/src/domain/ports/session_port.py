"""
Puerto abstracto para repositorio de sesión.

Define la interfaz para guardar/cargar el estado de la aplicación.
"""
from abc import ABC, abstractmethod
from typing import Any


class SessionRepositoryPort(ABC):
    """Interfaz abstracta para persistencia de sesión."""

    @abstractmethod
    def guardar(self, ruta: str, datos: dict) -> None:
        """
        Guarda el estado completo de la sesión.

        Args:
            ruta: Ruta al archivo de sesión.
            datos: Diccionario con todos los datos a persistir.
        """
        ...

    @abstractmethod
    def cargar(self, ruta: str) -> dict:
        """
        Carga el estado completo de la sesión.

        Args:
            ruta: Ruta al archivo de sesión.

        Returns:
            Diccionario con los datos cargados.
        """
        ...
