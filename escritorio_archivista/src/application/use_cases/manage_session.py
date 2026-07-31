"""
Caso de uso: Gestionar Sesión.

Orquesta el guardado y carga del estado completo de la aplicación.
"""
import logging
from typing import Optional

from src.domain.ports.session_port import SessionRepositoryPort

logger = logging.getLogger(__name__)


class GestionarSesionUseCase:
    """Caso de uso para guardar y cargar sesiones."""

    def __init__(self, session_repo: SessionRepositoryPort):
        self._session_repo = session_repo

    def guardar(self, ruta: str, estado: dict) -> None:
        """
        Guarda el estado completo de la aplicación.

        Args:
            ruta: Ruta al archivo de sesión.
            estado: Diccionario con todo el estado a persistir.
        """
        logger.info("Guardando sesión...")
        self._session_repo.guardar(ruta, estado)
        logger.info("Sesión guardada en: %s", ruta)

    def cargar(self, ruta: str) -> dict:
        """
        Carga el estado de una sesión guardada.

        Args:
            ruta: Ruta al archivo de sesión.

        Returns:
            Diccionario con el estado cargado.
        """
        logger.info("Cargando sesión desde: %s", ruta)
        datos = self._session_repo.cargar(ruta)
        if datos:
            logger.info("Sesión cargada exitosamente.")
        else:
            logger.warning("No se encontró sesión previa.")
        return datos
