"""
Routing Classifier para SupportAgent
Decide el routing apropiado basado en la clasificación
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RoutingDecision:
    """Decisión de routing"""
    route_type: str  # "property", "department", "general"
    handler: str  # Handler específico a usar
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RoutingClassifier:
    """
    Clasifica el routing apropiado basado en la intención del usuario.

    Routes disponibles:
    - property: Consultas sobre inmuebles específicos → PropertyHandler
    - department: Transferencia a departamentos → DepartmentHandler
    - general: Consultas generales → GeneralHandler
    """

    def __init__(self):
        """Inicializa el clasificador de routing"""
        logger.info("RoutingClassifier inicializado")

    def decide_route(
        self,
        classification: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Decide el route apropiado basado en la clasificación.

        Args:
            classification: Resultado de clasificación de intención
            rag_context: Contexto de búsqueda RAG (opcional)

        Returns:
            RoutingDecision con tipo de route y handler
        """
        intent = classification.get("intent", "other")
        confidence = classification.get("confidence", 0.0)

        # Routing por intención
        if intent == "property_inquiry":
            return RoutingDecision(
                route_type="property",
                handler="PropertyHandler",
                confidence=confidence,
                reasoning=f"Intención: {intent} - Consulta sobre inmueble",
                metadata={"requires_rag": True}
            )

        if intent == "department_transfer":
            # Extraer departamento de entidades
            entities = classification.get("entities", {})
            department = entities.get("department", "general")

            return RoutingDecision(
                route_type="department",
                handler="DepartmentHandler",
                confidence=confidence,
                reasoning=f"Solicitud de transferencia a {department}",
                metadata={"target_department": department}
            )

        # Por defecto: general handler
        return RoutingDecision(
            route_type="general",
            handler="GeneralHandler",
            confidence=confidence,
            reasoning=f"Intención: {intent} - Consulta general",
            metadata={"requires_rag": True}
        )