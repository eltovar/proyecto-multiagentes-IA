"""
GeneralHandler - Camino 3: Consultas generales
Maneja preguntas generales que no caen en propiedad ni departamento
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class GeneralHandlerResult:
    """Resultado del handler general"""
    response: str
    next_state: str
    clarification_needed: bool = False
    data_updates: Optional[Dict[str, Any]] = None


class GeneralHandler:
    """
    Handler para CAMINO 3: Consultas generales

    Extrae logica de support_agent.py lineas ~486-554
    Maneja preguntas no especificas usando RAG + LLM
    """

    def __init__(self, llm_service, state_manager, config: Dict[str, Any]):
        self.llm = llm_service
        self.state = state_manager
        self.config = config

    async def handle_general_query(
        self,
        classification: Dict[str, Any],
        rag_result: Dict[str, Any],
        customer_name: str
    ) -> GeneralHandlerResult:
        """
        Procesa consulta general usando RAG + LLM.

        Args:
            classification: Resultado de IntentClassifier
            rag_result: Resultado de busqueda RAG
            customer_name: Nombre del cliente

        Returns:
            GeneralHandlerResult con respuesta generada
        """

        # TODO: Implementar logica completa cuando se migre desde support_agent.py
        # Por ahora, respuesta basica

        rag_context = rag_result.get("context", "")
        confidence = classification.get("confidence", 0.0)

        # Si hay contexto RAG, generar respuesta personalizada
        if rag_context and confidence > 0.5:
            response = await self._generate_rag_response(
                query=classification.get("entities", {}).get("query", ""),
                rag_context=rag_context,
                customer_name=customer_name
            )
            next_state = "GENERAL_ANSWERED"
            clarification = False
        else:
            # Pedir clarificacion si confianza es baja
            response = f"{customer_name}, podrias darme mas detalles sobre tu consulta?"
            next_state = "CLARIFICATION_NEEDED"
            clarification = True

        return GeneralHandlerResult(
            response=response,
            next_state=next_state,
            clarification_needed=clarification
        )

    async def _generate_rag_response(
        self,
        query: str,
        rag_context: str,
        customer_name: str
    ) -> str:
        """
        Genera respuesta usando RAG + LLM.

        TODO: Implementar llamada a LLM con prompt adecuado
        """

        # Respuesta placeholder
        if rag_context:
            return f"{customer_name}, basado en nuestra informacion: {rag_context[:200]}..."
        else:
            return f"{customer_name}, dejame verificar esa informacion y te respondo enseguida."
