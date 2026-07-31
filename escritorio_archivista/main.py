"""
Sistema de Gestión y Fragmentación Documental (SGFD)
Punto de entrada principal de la aplicación.
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Punto de entrada principal."""
    logger.info("Iniciando Sistema de Gestión y Fragmentación Documental...")

    try:
        from src.presentation.app import create_app
        app = create_app(sys.argv)
        sys.exit(app.exec())
    except ImportError:
        logger.warning(
            "Módulo de presentación no disponible. "
            "Ejecute los módulos de dominio/aplicación directamente."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
