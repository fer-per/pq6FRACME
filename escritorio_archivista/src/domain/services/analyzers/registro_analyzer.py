"""
Analizador de número de registro — valida la numeración de los registros.

Detecta:
1. REGISTRO — registro vacío o "0" (warning)
2. REGISTRO — formato no numérico (warning)
3. REGISTRO — número fuera de orden dentro del mismo protocolo (warning)

El número de registro admite una letra final (ej. "11A", "11B", "5A"):
se consideran registros distintos y ordenan después del número base
("11" < "11A" < "11B"). El mismo número puede repetirse siempre que la
secuencia dentro del protocolo se mantenga en orden (no descendente).
"""
import logging
import re
from typing import List

from src.domain.entities import AnalysisResult, AnalysisError, InventoryRecord

logger = logging.getLogger(__name__)


def analizar_registro(records: List[InventoryRecord]) -> AnalysisResult:
    """
    Evalúa la columna de número de registro de cada registro.

    Args:
        records: Lista de registros del inventario.

    Returns:
        AnalysisResult con las advertencias encontradas.
    """
    advertencias: List[AnalysisError] = []
    ultimo_por_protocolo: dict = {}
    validos = 0

    for record in records:
        valor = (record.registro or "").strip()

        # 1. Registro vacío o cero: filas de índice/sub-encabezado o horas
        # mal interpretadas por el Excel.
        if not valor or valor == "0":
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="REGISTRO",
                descripcion=(
                    "El registro no tiene número: podría ser una fila de "
                    "índice, sub-encabezado o una hora mal interpretada."
                ),
                valor_actual=valor or "(vacío)",
                valor_esperado="Número de registro",
                fatal=False,
            ))
            continue

        # 2. Formato no numérico: números con una sola letra final son
        # válidos ("11A", "11B", "5A"); el resto se marca.
        if not re.fullmatch(r"\d+[A-Za-z]?", valor):
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="REGISTRO",
                descripcion=(
                    f"El registro '{valor}' no es un número válido "
                    "(posible fila de índice o anotación)."
                ),
                valor_actual=valor,
                valor_esperado="Número de registro (ej. 11, 11A, 11B)",
                fatal=False,
            ))
            continue

        # 3. Orden dentro del protocolo: el mismo número puede repetirse,
        # pero la secuencia no debe descender (regresión).
        clave = _clave_registro(valor)
        protocolo = (record.protocolo or "").strip()
        prev = ultimo_por_protocolo.get(protocolo)
        if prev is not None and clave < prev[0]:
            advertencias.append(AnalysisError(
                record_id=record.id,
                fila=record.fila,
                tipo="REGISTRO",
                descripcion=(
                    f"El registro N° {valor} está fuera de orden: el "
                    f"registro anterior del mismo protocolo era el "
                    f"{prev[1]}."
                ),
                valor_actual=valor,
                valor_esperado=f">= registro anterior ({prev[1]})",
                fatal=False,
            ))
            continue
        ultimo_por_protocolo[protocolo] = (clave, valor)
        validos += 1

    return AnalysisResult(
        nombre="Analizador de Número de Registro",
        total_revisados=len(records),
        errores=[],
        advertencias=advertencias,
        info_extra={"registros_validos": validos},
    )


def _clave_registro(valor: str):
    """
    Clave comparable de un número de registro.

    Devuelve ``(numero_base, rango_letra)``: ``11`` → (11, 0),
    ``11A`` → (11, 1), ``11B`` → (11, 2). Permite ordenar la secuencia
    respetando la letra final. Retorna None si el formato no es válido.
    """
    match = re.fullmatch(r"(\d+)([A-Za-z])?", valor)
    if not match:
        return None
    base = int(match.group(1))
    letra = match.group(2)
    rango = ord(letra.upper()) - ord("A") + 1 if letra else 0
    return (base, rango)
