"""
DTOs de la capa de aplicación.

Objetos de transferencia de datos entre la capa de aplicación
y la capa de presentación. No contienen lógica de negocio.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from src.domain.entities import (
    InventoryRecord,
    AnalysisResult,
    AnalysisError,
    SugerenciaCorreccion,
)


@dataclass
class ResultadoCarga:
    """Resultado del caso de uso CargarInventario."""
    records: List[InventoryRecord]
    suggestions: List[SugerenciaCorreccion]
    errors: List[AnalysisError]
    metadata: dict = field(default_factory=dict)
    # metadata: filepath, acervo_detectado, total_records, errores_count


@dataclass
class ResultadoAnalisis:
    """Resultado del caso de uso AnalizarDatos."""
    folios_result: Optional[AnalysisResult] = None
    topica_result: Optional[AnalysisResult] = None
    cronica_result: Optional[AnalysisResult] = None
    coverage_result: Optional[AnalysisResult] = None
    suggestions: List[SugerenciaCorreccion] = field(default_factory=list)
    records: List[InventoryRecord] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class InfoArchivo:
    """Información sobre un archivo generado."""
    path: str
    filename: str
    tipo: str = "FRAGMENTO_PDF"


@dataclass
class ResultadoFragmentacion:
    """Resultado del caso de uso FragmentarPDF."""
    archivos_creados: List[InfoArchivo] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
    total_exitos: int = 0
    total_fallos: int = 0
    metadata: dict = field(default_factory=dict)
