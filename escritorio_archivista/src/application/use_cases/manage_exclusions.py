"""
Caso de uso: Gestionar Exclusiones.

Permite agregar y eliminar reglas de exclusión
(saltos de folio y páginas a ignorar).
"""
import logging
from typing import List

from src.domain.entities import ExclusionRule
from src.domain.enums import TipoExclusion

logger = logging.getLogger(__name__)


class GestionarExclusionesUseCase:
    """Caso de uso para gestionar exclusiones."""

    def agregar_salto(
        self,
        exclusiones: List[ExclusionRule],
        desde: int,
        hasta: int,
        motivo: str,
    ) -> List[ExclusionRule]:
        """
        Agrega una exclusión de tipo SALTO.

        Args:
            exclusiones: Lista actual de exclusiones.
            desde: Folio de inicio del salto.
            hasta: Folio de fin del salto.
            motivo: Justificación del salto.

        Returns:
            Nueva lista con la exclusión agregada.
        """
        new_id = f"EXCL_{len(exclusiones) + 1}"
        nueva = ExclusionRule(
            id=new_id,
            tipo=TipoExclusion.SALTO.value,
            desde=desde,
            hasta=hasta,
            motivo=motivo,
        )
        logger.info("Agregada exclusión SALTO: %s (folios %d-%d)", new_id, desde, hasta)
        return exclusiones + [nueva]

    def agregar_ignorar(
        self,
        exclusiones: List[ExclusionRule],
        desde: int,
        hasta: int,
        motivo: str,
        tipo_contenido: str = "",
    ) -> List[ExclusionRule]:
        """
        Agrega una exclusión de tipo IGNORAR.

        Args:
            exclusiones: Lista actual de exclusiones.
            desde: Página de inicio a ignorar.
            hasta: Página de fin a ignorar.
            motivo: Justificación.
            tipo_contenido: "Hoja en Blanco", "Portada", "Separador", "Dañada".

        Returns:
            Nueva lista con la exclusión agregada.
        """
        new_id = f"EXCL_{len(exclusiones) + 1}"
        nueva = ExclusionRule(
            id=new_id,
            tipo=TipoExclusion.IGNORAR.value,
            desde=desde,
            hasta=hasta,
            motivo=motivo,
            tipo_contenido=tipo_contenido or None,
        )
        logger.info("Agregada exclusión IGNORAR: %s (págs %d-%d)", new_id, desde, hasta)
        return exclusiones + [nueva]

    def eliminar_exclusion(
        self,
        exclusiones: List[ExclusionRule],
        excl_id: str,
    ) -> List[ExclusionRule]:
        """
        Elimina una exclusión por su ID.

        Args:
            exclusiones: Lista actual de exclusiones.
            excl_id: ID de la exclusión a eliminar.

        Returns:
            Nueva lista sin la exclusión eliminada.
        """
        nueva = [e for e in exclusiones if e.id != excl_id]
        if len(nueva) < len(exclusiones):
            logger.info("Eliminada exclusión: %s", excl_id)
        else:
            logger.warning("Exclusión no encontrada: %s", excl_id)
        return nueva
