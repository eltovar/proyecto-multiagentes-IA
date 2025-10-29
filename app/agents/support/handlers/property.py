"""
PropertyHandler - Camino 1: Consultas sobre inmuebles específicos
Extraído de support_agent.py (líneas 554-637)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PropertyHandlerResult:
    """Resultado estructurado del PropertyHandler"""
    response: str
    next_state: str
    transfer_to: Optional[str] = None
    data_updates: Optional[Dict[str, Any]] = None
    rag_context: Optional[str] = None


class PropertyHandler:
    """ usuario busca inmueble Sistema RAG busca respuesta"""

    def __init__(self, rag_system, llm_service):
        self.rag = rag_system
        self.llm = llm_service

    async def handle_property_request(
        self,
        classification: Dict[str, Any],
        rag_result: Dict[str, Any],
        customer_name: str
    ) -> PropertyHandlerResult:
        """ Maneja solicitud de búsqueda de inmuebles."""
        
        entities = classification.get("entities", {})
        property_type = entities.get("property_type", "propiedad")
        location = entities.get("location", "")
        rag_context = rag_result.get("context", "")

        # Intentar generar mensaje personalizado con RAG + LLM
        message = await self._generate_personalized_message(
            property_type=property_type,
            location=location,
            rag_context=rag_context,
            customer_name=customer_name
        )

        # Construir data_updates para transferencia
        data_updates = {
            "routing_path": "CAMINO_1_INMUEBLE",
            "intent": "inmueble",
            "classification": str(classification),
            "rag_context_used": bool(rag_context),
            "property_type": property_type,
            "location": location
        }

        return PropertyHandlerResult(
            response=message,
            next_state="TRANSFERIDO",
            transfer_to="ReceptionAgent",
            data_updates=data_updates,
            rag_context=rag_context
        )

    async def _generate_personalized_message(
        self,
        property_type: str,
        location: str,
        rag_context: str,
        customer_name: str
    ) -> str:
        """
        Genera mensaje personalizado usando RAG + LLM."""
        # Intentar generación con RAG + LLM
        if rag_context and self.llm and hasattr(self.llm, 'api_client') and self.llm.api_client.initialized:
            try:
                # Prompt para mensaje personalizado
                location_part = f' en {location}' if location else ''
                prompt = f"""Genera un mensaje breve (2-3 líneas) de bienvenida para un usuario que busca {property_type}{location_part}.

Contexto desde documentos RAG:
{rag_context[:500]}

Cliente: {customer_name or 'usuario'}

Instrucciones:
- Mensaje corto y profesional
- Menciona que lo conectarás con asesores
- Usa información del contexto RAG si es relevante (ej: proceso de citas, requisitos)
- Tono cercano pero profesional
- No uses emojis
- Máximo 3 líneas"""

                # Usar generate_with_prompt para generación de texto
                message = await self.llm.generate_with_prompt(
                    prompt=prompt,
                    response_format="text"
                )

                print(f"[PropertyHandler] Mensaje generado con RAG+LLM para {property_type}")

                # Manejar respuesta como string o dict
                if isinstance(message, dict):
                    message = message.get("response", str(message))

                return message.strip() if isinstance(message, str) else str(message)

            except Exception as e:
                print(f"[PropertyHandler] Error generando con RAG+LLM: {e}, usando fallback")
                return self._fallback_message(property_type, location, customer_name)
        else:
            # Sin RAG o LLM: mensaje genérico
            return self._fallback_message(property_type, location, customer_name)

    def _fallback_message(
        self,
        property_type: str,
        location: str,
        customer_name: str
    ) -> str:
        """ Mensaje fallback cuando RAG/LLM no están disponibles."""
        greeting = self._format_greeting(customer_name, "¡Perfecto")
        location_part = f" en {location}" if location else ""

        return (
            f"{greeting}! "
            f"Veo que buscas {property_type}{location_part}. "
            f"Te voy a conectar con nuestro equipo de asesores que te ayudarán "
            f"a encontrar la mejor opción y agendar una cita de visita."
        )

    @staticmethod
    def _format_greeting(customer_name: str, prefix: str = "") -> str:
        """ Formatear saludo con nombre del cliente. """
        if customer_name:
            return f"{prefix}, {customer_name}" if prefix else customer_name
        else:
            return prefix
