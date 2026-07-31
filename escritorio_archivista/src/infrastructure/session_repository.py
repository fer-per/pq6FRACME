"""
Repositorio de sesión — implementación del SessionRepositoryPort.

Guarda/carga el estado completo de la aplicación en formato JSON.
"""
import json
import logging
import os
from dataclasses import asdict
from typing import List

from src.domain.entities import (
    InventoryRecord,
    ExclusionRule,
    SugerenciaCorreccion,
)
from src.domain.ports.session_port import SessionRepositoryPort

logger = logging.getLogger(__name__)


class SessionRepository(SessionRepositoryPort):
    """Implementación concreta de persistencia de sesión en JSON."""

    def guardar(self, ruta: str, datos: dict) -> None:
        """
        Guarda el estado de la sesión a un archivo JSON.

        Serializa automáticamente dataclasses usando dataclasses.asdict().
        """
        logger.info("Guardando sesión en: %s", ruta)

        serializable = {}
        for key, value in datos.items():
            if isinstance(value, list) and value and hasattr(value[0], '__dataclass_fields__'):
                serializable[key] = [asdict(item) for item in value]
            else:
                serializable[key] = value

        os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)

        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

        logger.info("Sesión guardada exitosamente.")

    def cargar(self, ruta: str) -> dict:
        """
        Carga el estado de la sesión desde un archivo JSON.

        Reconstruye dataclasses desde los dicts almacenados.
        Si el excel_path no existe en disco, limpia records/exclusions/suggestions.
        """
        logger.info("Cargando sesión desde: %s", ruta)

        if not os.path.exists(ruta):
            logger.warning("Archivo de sesión no encontrado: %s", ruta)
            return {}

        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        # Verificar si el Excel aún existe
        excel_path = datos.get("excel_path", "")
        if excel_path and not os.path.exists(excel_path):
            logger.warning(
                "Excel '%s' no existe. Limpiando datos dependientes.", excel_path
            )
            datos["records"] = []
            datos["exclusions"] = []
            datos["suggestions"] = []

        # Reconstruir dataclasses
        if "records" in datos and isinstance(datos["records"], list):
            datos["records"] = [
                InventoryRecord(**r) for r in datos["records"]
            ]

        if "exclusions" in datos and isinstance(datos["exclusions"], list):
            datos["exclusions"] = [
                ExclusionRule(**e) for e in datos["exclusions"]
            ]

        if "suggestions" in datos and isinstance(datos["suggestions"], list):
            datos["suggestions"] = [
                SugerenciaCorreccion(**s) for s in datos["suggestions"]
            ]

        logger.info("Sesión cargada exitosamente.")
        return datos
