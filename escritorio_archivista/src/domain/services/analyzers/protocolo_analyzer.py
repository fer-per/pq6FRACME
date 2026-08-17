"""
Analizador de protocolo — valida la numeración de los protocolos.

Detecta:
1. PROTOCOLO — protocolo vacío (warning)
2. PROTOCOLO — formato no numérico (warning)
3. PROTOCOLO — regresión de protocolo dentro del mismo escribano (fatal)

Cada escribano tiene su propia secuencia de protocolos: la regresión
se evalúa por escribano, no a nivel global.
"""
import logging
import re
from typing import List

from src.domain.entities import AnalysisResult, AnalysisError, InventoryRecord

logger = logging.getLogger(__name__)


def analizar_protocolo(records: List[InventoryRecord]) -> AnalysisResult:
    """
    Evalúa la columna de protocolo de cada registro.

    Args:
        records: Lista de registros del inventario.

    Returns:
        AnalysisResult con errores y advertencias encontrados.
    """
    errores: List[AnalysisError] = []
    advertencias: List[AnalysisError] = []
    ultimo_por_escribano: dict = {}

    for record in records:
        valor = (record.protocolo or "").strip()
        escribano = (record.escribano or "").strip()

        # 1. Protocolo vacío
        if not valor:
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="PROTOCOLO",
                descripcion="El registro no indica protocolo.",
                valor_actual="(vacío)",
                valor_esperado="Número de protocolo",
                fatal=False,
            ))
            continue

        # 2. Formato no numérico
        if not re.fullmatch(r"\d+", valor):
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="PROTOCOLO",
                descripcion=(
                    f"El protocolo '{valor}' no es un número válido."
                ),
                valor_actual=valor,
                valor_esperado="Número de protocolo",
                fatal=False,
            ))
            continue

        # 3. Regresión dentro del mismo escribano
        num = int(valor)
        prev = ultimo_por_escribano.get(escribano)
        if prev is not None and num < prev:
            errores.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="PROTOCOLO",
                descripcion=(
                    f"REGRESIÓN DE PROTOCOLO: el protocolo {num} es "
                    f"anterior al último del mismo escribano ({prev})."
                ),
                valor_actual=str(num),
                valor_esperado=f">= {prev}",
                fatal=True,
            ))
            # No actualizar prev para no propagar cascada
            continue
        ultimo_por_escribano[escribano] = num

    return AnalysisResult(
        nombre="Analizador de Protocolo",
        total_revisados=len(records),
        errores=errores,
        advertencias=advertencias,
    )
