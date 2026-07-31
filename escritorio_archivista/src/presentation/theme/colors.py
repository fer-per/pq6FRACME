"""
Paleta de colores del sistema de diseño.

Inspirada en Obsidian/VSCode/JetBrains con tonos carmesí.
"""

LIGHT_PALETTE = {
    # Primarios
    "primary":             "#570013",
    "primary_container":   "#800020",
    "on_primary":          "#ff828a",
    "background":          "#fcf9f8",
    "surface":             "#ffffff",
    "surface_low":         "#f6f3f2",
    "surface_container":   "#f0edec",
    "surface_high":        "#eae7e7",
    "surface_highest":     "#e5e2e1",
    "outline":             "#8c7071",
    "outline_variant":     "#e0bfbf",
    "tertiary":            "#32131c",
    "on_tertiary":         "#e5e1df",
    "secondary":           "#7c535d",
    "secondary_container": "#ffc9d5",

    # Estados
    "success":             "#1a5c2e",
    "success_bg":          "#d1fae5",
    "error":               "#b91c1c",
    "error_bg":            "#fee2e2",
    "warning":             "#b45309",
    "warning_bg":          "#fef3c7",
    "info":                "#1e3a5f",
    "info_bg":             "#dbeafe",

    # Consola de logs
    "console_info":        "#a8c4d4",
    "console_warn":        "#f5a742",
    "console_success":     "#4cde7e",
    "console_error":       "#ff6b6b",

    # Selección
    "selected_bg":         "#f0e8ec",

    # Texto
    "text_primary":        "#1a1a1a",
    "text_secondary":      "#5a5a5a",
    "text_disabled":       "#9e9e9e",
}

DARK_PALETTE = {
    # Primarios
    "primary":             "#ffb1b8",
    "primary_container":   "#93001a",
    "on_primary":          "#5f1126",
    "background":          "#1a1110",
    "surface":             "#211a19",
    "surface_low":         "#2b2220",
    "surface_container":   "#352c2a",
    "surface_high":        "#403634",
    "surface_highest":     "#4b413f",
    "outline":             "#a08c8d",
    "outline_variant":     "#534344",
    "tertiary":            "#1a0e12",
    "on_tertiary":         "#d4d0ce",
    "secondary":           "#e6bdc7",
    "secondary_container": "#633b45",

    # Estados
    "success":             "#4ade80",
    "success_bg":          "#1a3a2a",
    "error":               "#f87171",
    "error_bg":            "#3a1a1a",
    "warning":             "#fbbf24",
    "warning_bg":          "#3a2a1a",
    "info":                "#60a5fa",
    "info_bg":             "#1a2a3a",

    # Consola
    "console_info":        "#7ec8e3",
    "console_warn":        "#f5a742",
    "console_success":     "#4cde7e",
    "console_error":       "#ff6b6b",

    # Selección
    "selected_bg":         "#3a2a2e",

    # Texto
    "text_primary":        "#ece0de",
    "text_secondary":      "#b0a4a2",
    "text_disabled":       "#6e6462",
}


def get_palette(dark: bool = False) -> dict:
    """Retorna la paleta de colores según el tema."""
    return DARK_PALETTE if dark else LIGHT_PALETTE
