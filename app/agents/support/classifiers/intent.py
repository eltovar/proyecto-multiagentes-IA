"""
Intent Classifier para SupportAgent
Clasifica la intención del usuario usando LLM
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from app.services.llm_service import llm_service
from app.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClassificationResult:
    """Resultado de clasificación de intención"""
    intent: str
    sub_intent: Optional[str] = None
    confidence: float = 0.0
    entities: Dict[str, Any] = None
    reasoning: str = ""

    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


# Alias para backward compatibility
IntentClassification = ClassificationResult


class IntentClassifier:
    """ Clasifica la intención del usuario en conversaciones de soporte. """

    VALID_INTENTS = [
        "property_inquiry",
        "general_question",
        "department_transfer",
        "complaint",
        "information",
        "other"
    ]

    def __init__(self):
        """Inicializa el clasificador de intenciones"""
        self.llm = llm_service
        logger.info("IntentClassifier inicializado")

    async def classify(
        self,
        message: str,
        conversation: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """ Clasifica la intención del mensaje del usuario. """
        if not message or not message.strip():
            return ClassificationResult(
                intent="other",
                confidence=0.0,
                reasoning="Mensaje vacío"
            )

        try:
            # Llamar a LLM para clasificación (usando método correcto)
            result = await self.llm.classify_intent_and_extract_entities(
                message=message,
                context=conversation
            )

            # Parsear resultado
            intent = result.get("intent", "other")
            sub_intent = result.get("sub_intent")
            confidence = result.get("confidence", 0.0)
            entities = result.get("entities", {})
            reasoning = result.get("reasoning", "")

            # Mapeo de intents legacy a nuevos
            intent_mapping = {
                "property_search": "property_inquiry",
                "support": "complaint",
                "unclear": "other"
            }
            if intent in intent_mapping:
                intent = intent_mapping[intent]

            # Validar intención
            if intent not in self.VALID_INTENTS:
                logger.warning(f"Intención inválida: {intent}, usando 'other'")
                intent = "other"
                confidence = 0.5

            classification = ClassificationResult(
                intent=intent,
                sub_intent=sub_intent,
                confidence=confidence,
                entities=entities,
                reasoning=reasoning
            )

            logger.info(
                f"Clasificación: {intent} (confidence: {confidence:.2f})"
            )

            return classification

        except Exception as e:
            logger.error(f"Error clasificando intención: {e}", exc_info=e)

            # Fallback: clasificación básica por keywords
            return self._fallback_classification(message)

    def _build_classification_prompt(
        self,
        message: str,
        conversation: Optional[Dict[str, Any]]
    ) -> str:
        """Construye prompt para clasificación de intención"""
        prompt = f"""Clasifica la siguiente consulta de un cliente inmobiliario:

Mensaje: "{message}"

Intenciones posibles:
- property_inquiry: Consultas sobre un inmueble específico
- general_question: Preguntas generales sobre servicios
- department_transfer: Quiere hablar con departamento específico
- complaint: Queja o problema
- information: Solicita información general
- other: Otra intención

"""

        if conversation:
            history = conversation.get("message_history", [])
            if history:
                recent = history[-3:]  # Últimos 3 mensajes
                prompt += "\nContexto de conversación:\n"
                for msg in recent:
                    role = msg.get("role", "user")
                    text = msg.get("content", "")
                    prompt += f"{role}: {text}\n"

        prompt += """
Responde en formato JSON:
{
    "intent": "nombre_intencion",
    "sub_intent": "sub-categoría (opcional)",
    "confidence": 0.85,
    "entities": {"entidad": "valor"},
    "reasoning": "explicación breve"
}
"""

        return prompt

    def _fallback_classification(self, message: str) -> ClassificationResult:
        """Clasificación de fallback basada en keywords"""
        message_lower = message.lower()

        # Keywords para property_inquiry
        property_keywords = [
            "inmueble", "propiedad", "apartamento", "casa",
            "arriendo", "venta", "compra", "alquiler"
        ]

        # Keywords para department_transfer
        department_keywords = [
            "asesor", "hablar con", "transferir", "departamento",
            "cartera", "mantenimiento", "gerente"
        ]

        # Keywords para complaint
        complaint_keywords = [
            "queja", "problema", "mal", "insatisfecho",
            "reclamo", "molesto"
        ]

        # Clasificar por keywords
        if any(kw in message_lower for kw in property_keywords):
            return ClassificationResult(
                intent="property_inquiry",
                confidence=0.6,
                reasoning="Clasificación por keywords (fallback)"
            )

        if any(kw in message_lower for kw in department_keywords):
            return ClassificationResult(
                intent="department_transfer",
                confidence=0.6,
                reasoning="Clasificación por keywords (fallback)"
            )

        if any(kw in message_lower for kw in complaint_keywords):
            return ClassificationResult(
                intent="complaint",
                confidence=0.6,
                reasoning="Clasificación por keywords (fallback)"
            )

        # Por defecto: general_question
        return ClassificationResult(
            intent="general_question",
            confidence=0.5,
            reasoning="Clasificación por defecto (fallback)"
        )