"""
Value Objects y constantes del dominio.

Contiene constantes inmutables que encapsulan reglas de negocio.
No depende de ninguna librería externa.
"""

# ─── Excel Parsing ───────────────────────────────────────────
HEADER_ROWS = 2                 # Filas de encabezado de columna
DEFAULT_DATA_START_ROW = 19     # Fila (1-based) donde empiezan los datos por defecto

# ─── Folio Analysis ─────────────────────────────────────────
YEAR_MIN = 1500           # Año mínimo válido para documentos históricos
YEAR_MAX = 2100           # Año máximo válido
MAX_IGNORED_ITERATIONS = 2000  # Límite de seguridad para bucles de páginas ignoradas

# ─── Mapeo de columnas Excel ────────────────────────────────
COLUMN_ALIASES = {
    "registro": [
        "n° de registro", "numero de registro", "registro", "id", "expediente",
    ],
    "escribano": [
        "escribano", "notario",
    ],
    "protocolo": [
        "n° de prot", "protocolo", "prot", "tomo",
    ],
    "folios": [
        "n° de folios", "folios", "rango", "paginas",
    ],
    "titulo": [
        "titulo", "escritura", "asunto",
    ],
    "data_topica": [
        "data top", "lugar", "topica",
    ],
    "fecha_inicio": [
        "fecha inicial", "data cronica 1", "inicial", "inicio",
    ],
    "fecha_fin": [
        "fecha final", "data cronica 2", "final", "fin",
    ],
    "interesado1": [
        "interesado 1", "interesado",
    ],
    "interesado2": [
        "interesado 2",
    ],
}

# ─── Columnas fallback por índice ────────────────────────────
FALLBACK_COLUMNS = {
    "titulo": 7,          # Columna H (índice 7)
    "fecha_inicio": 5,    # Columna 6 (índice 5)
}

# ─── Filas a ignorar (sub-encabezados) ──────────────────────
SKIP_ROW_KEYWORDS = [
    "protocolo", "registro", "fecha", "data cronica",
]

# ─── Filas de anotación/instrucciones (no son datos) ────────
ANNOTATION_KEYWORDS = [
    "nombres y apellidos", "recto v=verso", "sin espacio",
    "mayuscula", "fecha corta",
]

# ─── Valores a tratar como vacío ─────────────────────────────
EMPTY_VALUES = {"nan", "nat", "none", ""}

# ─── Clasificación de títulos para jerarquía ────────────────
TITLE_CLASSIFICATION = {
    "compraventa": "COMPRAVENTA",
    "testamento": "TESTAMENTO",
    "poder": "PODER_NOTARIAL",
    "arrendamiento": "ARRENDAMIENTO",
    "hipoteca": "HIPOTECA",
}
TITLE_DEFAULT = "ESCRITURA_VARIAS"

# ─── Meses para jerarquía ───────────────────────────────────
MONTH_NAMES = {
    1: "1. ENERO",
    2: "2. FEBRERO",
    3: "3. MARZO",
    4: "4. ABRIL",
    5: "5. MAYO",
    6: "6. JUNIO",
    7: "7. JULIO",
    8: "8. AGOSTO",
    9: "9. SEPTIEMBRE",
    10: "10. OCTUBRE",
    11: "11. NOVIEMBRE",
    12: "12. DICIEMBRE",
}

# ─── Números romanos a arábigos ─────────────────────────────
ROMAN_TO_ARABIC = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
    "XXI": 21,
}

# ─── Caracteres inválidos para nombres de archivo (Windows) ─
INVALID_FILENAME_CHARS = r'\/*?:"<>|'
