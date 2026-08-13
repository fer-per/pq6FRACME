"""
Cargador del archivo maestro de mapeo de datos del inventario.

Lee el JSON ``resources/mapa_maestro.json`` que define dónde se
ubican los metadatos (filas/columnas del encabezado) y cómo mapear
las columnas de datos del Excel. Si el archivo no existe o contiene
errores, se usan los valores por defecto definidos en el dominio.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.domain.value_objects import (
    COLUMN_ALIASES,
    FALLBACK_COLUMNS,
    SIGLO_FILA,
    ESCRIBANO_FILA,
    ACERVO_FILA,
)

logger = logging.getLogger(__name__)

# Ruta por defecto del archivo maestro de mapeo
DEFAULT_MAPEO_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "resources", "mapa_maestro.json"
)


@dataclass(frozen=True)
class UbicacionMetadato:
    """Fila y columna (1-based) donde vive un metadato en el Excel."""
    fila: int
    columna: int


@dataclass(frozen=True)
class MapeoColumna:
    """Aliases y columna de respaldo por índice para mapear una columna."""
    aliases: Tuple[str, ...] = ()
    indice_fallback: Optional[int] = None


@dataclass(frozen=True)
class MapeoMaestro:
    """Configuración completa de ubicación de datos del inventario."""
    metadatos: Dict[str, UbicacionMetadato] = field(default_factory=dict)
    columnas: Dict[str, MapeoColumna] = field(default_factory=dict)
    version: int = 1

    def ubicacion_metadato(self, campo: str) -> Optional[UbicacionMetadato]:
        """Devuelve la ubicación de un metadato o None si no está mapeado."""
        return self.metadatos.get(campo)


def mapeo_por_defecto() -> MapeoMaestro:
    """Construye el mapeo por defecto definido en el dominio."""
    metadatos = {
        "siglo": UbicacionMetadato(fila=SIGLO_FILA, columna=1),
        "escribano": UbicacionMetadato(fila=ESCRIBANO_FILA, columna=1),
        "acervo": UbicacionMetadato(fila=ACERVO_FILA, columna=1),
    }
    columnas = {
        campo: MapeoColumna(
            aliases=tuple(aliases),
            indice_fallback=FALLBACK_COLUMNS.get(campo),
        )
        for campo, aliases in COLUMN_ALIASES.items()
    }
    return MapeoMaestro(metadatos=metadatos, columnas=columnas, version=1)


def _parsear_ubicacion(datos: dict) -> Optional[UbicacionMetadato]:
    """Parsea un dict '{fila, columna}' a UbicacionMetadato."""
    try:
        fila = int(datos.get("fila"))
        columna = int(datos.get("columna", 1))
    except (TypeError, ValueError):
        return None
    if fila <= 0 or columna <= 0:
        return None
    return UbicacionMetadato(fila=fila, columna=columna)


def _parsear_columna(datos: dict) -> MapeoColumna:
    """Parsea un dict con aliases e índice de respaldo a MapeoColumna."""
    aliases = datos.get("aliases", [])
    if isinstance(aliases, list):
        aliases = tuple(str(a) for a in aliases if str(a).strip())
    else:
        aliases = (str(aliases),) if str(aliases).strip() else ()

    indice = datos.get("indice_fallback")
    if isinstance(indice, (int, float)) and not isinstance(indice, bool):
        indice = int(indice)
    else:
        indice = None

    return MapeoColumna(aliases=aliases, indice_fallback=indice)


def cargar_mapeo_maestro(ruta: Optional[str] = None) -> MapeoMaestro:
    """Carga el mapa maestro desde un JSON, con fallback a los valores por defecto.

    Args:
        ruta: Ruta al JSON. Si es None, se usa la ubicación por defecto
            ``resources/mapa_maestro.json``.

    Returns:
        Configuración de mapeo lista para usar.
    """
    path = os.path.abspath(ruta or DEFAULT_MAPEO_FILE)

    if not os.path.exists(path):
        logger.warning(
            "Archivo maestro de mapeo no encontrado en %s; usando valores por defecto.",
            path,
        )
        return mapeo_por_defecto()

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(
            "No se pudo leer el archivo maestro de mapeo %s (%s); "
            "usando valores por defecto.",
            path, e,
        )
        return mapeo_por_defecto()

    # Tomar defectos como base y sobreescribir con lo definido en el JSON
    base = mapeo_por_defecto()

    metadatos = dict(base.metadatos)
    for campo, ubicacion in (data.get("metadatos") or {}).items():
        if isinstance(ubicacion, dict):
            parsed = _parsear_ubicacion(ubicacion)
            if parsed:
                metadatos[str(campo)] = parsed

    columnas = dict(base.columnas)
    for campo, mapeo in (data.get("columnas") or {}).items():
        if isinstance(mapeo, dict):
            columnas[str(campo)] = _parsear_columna(mapeo)

    version = int(data.get("version", 1))

    logger.info("Mapa maestro cargado desde %s (versión %d).", path, version)
    return MapeoMaestro(
        metadatos=metadatos,
        columnas=columnas,
        version=version,
    )