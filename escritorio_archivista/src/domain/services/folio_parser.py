"""
Parser de folios notariales.

Los folios notariales siguen el formato: NNNr (recto) o NNNv (verso).
Un rango se escribe NNNr-NNNv.

Este módulo NO depende de ninguna librería externa.
"""
import re
from typing import Optional, Tuple

FolioTuple = Tuple[int, str, int, str]  # (desde_num, desde_cara, hasta_num, hasta_cara)


def parse_folios(folio_str: str) -> Optional[FolioTuple]:
    """
    Parsea un string de foliación notarial.

    Entradas válidas: "001r", "1r", "001r-002v", "1r-2v", "5"
    Retorna None si el formato es inválido.

    Returns:
        Tupla (desde_num, desde_cara, hasta_num, hasta_cara) o None.
    """
    if not folio_str or not isinstance(folio_str, str):
        return None
    folio_str = folio_str.strip().lower()
    # Normalizar espacios alrededor del guion: "99v - 100v" -> "99v-100v"
    folio_str = re.sub(r'\s+', '', folio_str)

    # Intentar rango: "NNNr-NNNv"
    rango_match = re.match(r'(\d+)([rv])?-(\d+)([rv])?', folio_str)
    if rango_match:
        desde_num = int(rango_match.group(1))
        desde_cara = rango_match.group(2) or 'r'
        hasta_num = int(rango_match.group(3))
        hasta_cara = rango_match.group(4) or 'v'
        return desde_num, desde_cara, hasta_num, hasta_cara

    # Intentar folio único: "NNNr" o "NNN"
    unico_match = re.match(r'(\d+)([rv])?$', folio_str)
    if unico_match:
        num = int(unico_match.group(1))
        cara = unico_match.group(2) or 'r'
        return num, cara, num, cara

    return None


def folio_to_int(num: int, cara: str) -> int:
    """
    Convierte folio (num, cara) a entero plano.

    1r=1, 1v=2, 2r=3, 2v=4...
    """
    if cara == 'r':
        return num * 2 - 1
    return num * 2


def int_to_folio(n: int) -> Tuple[int, str]:
    """
    Inversa de folio_to_int.

    1→(1,'r'), 2→(1,'v'), 3→(2,'r'), 4→(2,'v')...
    """
    if n % 2 == 1:
        return (n + 1) // 2, 'r'
    return n // 2, 'v'


def format_folio(num: int, cara: str) -> str:
    """Formatea como '003r', '001v', etc."""
    return f"{num:03d}{cara}"


def calculate_suggested_range(prev_record, current_record) -> Optional[str]:
    """
    Calcula el rango de folios sugerido para el registro actual
    basándose en dónde terminó el registro anterior.

    Si el anterior terminó en "005v", el actual debería empezar en "006r".
    El span del rango sugerido es igual al span del rango actual.

    Args:
        prev_record: Registro anterior (con atributo .folios)
        current_record: Registro actual (con atributo .folios)

    Returns:
        String del rango sugerido (ej: "006r-007v") o None.
    """
    parsed_prev = parse_folios(prev_record.folios)
    if parsed_prev is None:
        return None
    _, _, hasta_num, hasta_cara = parsed_prev
    start_int = folio_to_int(hasta_num, hasta_cara) + 1

    parsed_current = parse_folios(current_record.folios)
    if parsed_current is None:
        return None
    desde_num, desde_cara, hasta_num_c, hasta_cara_c = parsed_current
    span = folio_to_int(hasta_num_c, hasta_cara_c) - folio_to_int(desde_num, desde_cara)
    end_int = start_int + span

    start_num, start_cara = int_to_folio(start_int)
    end_num, end_cara = int_to_folio(end_int)
    return f"{format_folio(start_num, start_cara)}-{format_folio(end_num, end_cara)}"
