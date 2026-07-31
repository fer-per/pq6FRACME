"""
Enumeraciones del dominio.
"""
from enum import Enum


class EstadoRecord(str, Enum):
    """Estados posibles de un registro del inventario."""
    REVISAR = "REVISAR"
    VALIDADO = "VALIDADO"
    FRAGMENTADO = "FRAGMENTADO"


class TipoExclusion(str, Enum):
    """Tipos de regla de exclusión."""
    SALTO = "SALTO"
    IGNORAR = "IGNORAR"
