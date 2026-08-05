"""
Utilidades de íconos sensibles al tema.

Los íconos silueta (generalmente negros) se recolorizan según el tema
activo para garantizar contraste: negro en tema claro y blanco en tema
oscuro. El resultado se cachea para no recomputar al alternar el tema.
"""
import tempfile
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

from src.presentation.theme.colors import get_palette

_MAX_CACHE = 256

_WHITE = "#FFFFFF"

_CACHE_DIR: Path | None = None


def _cache_dir() -> Path:
    """Directorio temporal para PNG generados en runtime (para QSS)."""
    global _CACHE_DIR
    if _CACHE_DIR is None:
        _CACHE_DIR = Path(tempfile.gettempdir()) / "escritorio_archivista_icons"
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


@lru_cache(maxsize=_MAX_CACHE)
def tinted_pixmap_color(path: str, color: str) -> QPixmap:
    """Devuelve el pixmap recolorizado con un color fijo, con caché.

    Conserva el canal alfa del ícono original y rellena su silueta con
    el color dado (formato ``#RRGGBB``).
    """
    source = QPixmap(path)
    if source.isNull():
        return QPixmap()

    tinted = QPixmap(source.size())
    tinted.fill(Qt.GlobalColor.transparent)

    painter = QPainter(tinted)
    painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_Source
    )
    painter.fillRect(tinted.rect(), QColor(color))
    painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_DestinationIn
    )
    painter.drawPixmap(0, 0, source)
    painter.end()
    return tinted


@lru_cache(maxsize=_MAX_CACHE)
def tinted_pixmap(path: str, dark: bool) -> QPixmap:
    """Devuelve el pixmap recolorizado según el tema, con caché.

    Conserva el canal alfa del ícono original y rellena su silueta con
    ``text_primary`` de la paleta activa.
    """
    return tinted_pixmap_color(path, get_palette(dark)["text_primary"])


def theme_icon(path: str, dark: bool) -> QIcon:
    """Ícono recolorizado según el tema, listo para asignar a un widget."""
    return QIcon(tinted_pixmap(path, dark))


def white_icon(path: str) -> QIcon:
    """Ícono siempre blanco, independiente del tema activo."""
    return QIcon(tinted_pixmap_color(path, _WHITE))


def tinted_pixmap_file(path: str, dark: bool, tag: str) -> str:
    """Guarda el pixmap recolorizado como PNG en caché y devuelve su ruta.

    Necesario para hojas de estilo QSS (``image: url(...)``), que no admiten
    recolorización en vivo. Devuelve la ruta en formato POSIX o ``""`` si el
    ícono no existe.
    """
    pix = tinted_pixmap(path, dark)
    if pix.isNull():
        return ""
    theme = "dark" if dark else "light"
    target = _cache_dir() / f"{tag}_{theme}.png"
    pix.save(str(target), "PNG")
    return target.as_posix()
