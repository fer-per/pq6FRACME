"""
Entidades del dominio — dataclasses puras sin dependencias externas.

Cada entidad representa un concepto central del negocio archivístico.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class InventoryRecord:
    """Fila del inventario archivístico extraída del Excel."""
    id: str                        # "#0001", "#0002", etc.
    fila: int                      # Fila real en el Excel (para referencia)
    registro: str                  # Número de registro del documento
    escribano: str                 # Nombre del escribano/notario
    protocolo: str                 # Número de protocolo
    folios: str                    # Rango de folios (ej: "001r-002v")
    pg_pdf: str                    # Rango de páginas PDF calculado (ej: "1-4")
    titulo: str                    # Título estandarizado del documento
    estado: str = ""               # "", "REVISAR", "VALIDADO", "FRAGMENTADO"
    fecha_inicio: str = ""         # Data crónica 1 (ej: "15/03/1891")
    fecha_fin: str = ""            # Data crónica 2
    interesado1: str = ""          # Primer interesado
    interesado2: str = ""          # Segundo interesado
    interesado3: str = ""          # Tercer interesado
    data_topica: str = ""          # Lugar del acto jurídico
    comparte_hoja: bool = False    # Comparte la última hoja PDF con el registro anterior
    pg_pdf_manual: str = ""        # Rango de páginas PDF manual (vacío = calculado)


@dataclass
class ExclusionRule:
    """Regla de exclusión: justifica un salto o marca páginas a ignorar."""
    id: str                        # "EXCL_1", "EXCL_2"
    tipo: str                      # "SALTO" o "IGNORAR"
    desde: int                     # Folio o página de inicio
    hasta: int                     # Folio o página de fin
    motivo: str                    # Justificación textual
    tipo_contenido: Optional[str] = None  # "Hoja en Blanco", "Portada", "Separador", "Dañada"


@dataclass
class SystemLog:
    """Entrada de log para la consola interactiva."""
    timestamp: str                 # "HH:MM:SS"
    tipo: str                      # "INFO", "WARN", "SUCCESS", "ERR"
    mensaje: str

    @staticmethod
    def now(tipo: str, mensaje: str) -> "SystemLog":
        """Crea un log con timestamp actual."""
        ts = datetime.now().strftime("%H:%M:%S")
        return SystemLog(timestamp=ts, tipo=tipo, mensaje=mensaje)


@dataclass
class SugerenciaCorreccion:
    """Sugerencia automática para corregir un error detectado."""
    id: str                        # "SUG_001"
    registro_id: str               # ID del InventoryRecord afectado
    tipo_error: str                # "SALTO", "FORMATO", "SOLAPAMIENTO", etc.
    descripcion: str               # Texto legible del error
    valor_actual: str              # Valor que tiene el campo con error
    valor_sugerido: str            # Valor corregido propuesto
    escribano: str                 # Para contexto
    folios_original: str           # Folio original del registro
    rango_sugerido: str            # Rango de folios corregido
    paginas_pdf: str               # Páginas PDF actuales
    paginas_sugeridas: str         # Páginas PDF tras corrección
    fecha_original: str = ""
    fecha_validada: str = ""


@dataclass
class AnalysisError:
    """Error individual detectado por un analizador."""
    record_id: str
    fila: int
    tipo: str                      # "FORMATO", "SALTO", "SOLAPAMIENTO", "REPETIDO", "TOPICA", "CRONICA", "COVERAGE"
    descripcion: str
    valor_actual: str
    valor_esperado: str = ""
    fatal: bool = False            # True = bloqueante, False = warning


@dataclass
class AnalysisResult:
    """Resultado completo de un analizador."""
    nombre: str                    # Nombre legible del analizador
    total_revisados: int
    errores: List[AnalysisError] = field(default_factory=list)
    advertencias: List[AnalysisError] = field(default_factory=list)
    info_extra: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """True si no hay errores ni advertencias."""
        return len(self.errores) == 0 and len(self.advertencias) == 0

    @property
    def resumen(self) -> str:
        """Resumen textual del resultado."""
        if self.ok:
            return f"OK: {self.nombre}: {self.total_revisados} registros sin incidencias."
        total = len(self.errores) + len(self.advertencias)
        return f"WARN: {self.nombre}: {total} incidencia(s) en {self.total_revisados} registros."
