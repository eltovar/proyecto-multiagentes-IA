"""
GreetingHandler - Manejo de saludos y captura de nombre
Extraído de reception_agent.py (líneas 223-302)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class GreetingResult:
    """Resultado estructurado del GreetingHandler"""
    response: str
    next_state: str
    metadata: Dict[str, Any]


class GreetingHandler:
    """
    Handler especializado para:
    - Saludo inicial con políticas de privacidad
    - Captura de nombre del cliente (con fallback LLM)
    - Confirmación de nombre exitoso
    """

    def __init__(self, llm_service, state_manager, config: Dict[str, str]):
        """
        Args:
            llm_service: Servicio LLM para extracción de nombre
            state_manager: State Manager para persistencia
            config: Configuración con links (politicas_link, etc.)
        """
        self.llm = llm_service
        self.state = state_manager
        self.config = config

        # Links obligatorios del flujo
        self.politicas_link = config.get("politicas_link", "https://inmobiliariaproteger.com/politicas")

    async def handle_initial_greeting(
        self,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> GreetingResult:
        """
        Etapa 1: Saludo inicial + Políticas de Privacidad

        Extraído de: _handle_saludo_inicial (líneas 223-238)
        """
        response = f"""Hola, soy Sofia de Inmobiliaria Proteger

Al escribir aceptas nuestras Politicas de Privacidad ({self.politicas_link})

¿Me podrias indicar tu nombre por favor?"""

        return GreetingResult(
            response=response,
            next_state="POLITICAS_PRESENTADAS",
            metadata={
                "interaction_count": interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def handle_name_request_fallback(
        self,
        conversation: Dict[str, Any],
        interaction_count: int,
        attempt: int = 1
    ) -> GreetingResult:
        """
        Insiste en captura de nombre si LLM falló.

        Extraído de:
        - _handle_recopilar_nombre_llm_fallback (líneas 242-252)
        - _handle_validar_nombre_llm_fallback (líneas 254-265)
        """
        if attempt == 1:
            response = "Para brindarte la mejor atención, necesito tu nombre. ¿Podrías indicármelo por favor?"
        else:
            response = "Tu nombre es clave para que nuestro asesor te brinde una atención personalizada. ¿Me lo puedes compartir?"

        return GreetingResult(
            response=response,
            next_state="RECOPILANDO_NOMBRE",
            metadata={
                "interaction_count": interaction_count,
                "last_message_at": datetime.now().isoformat(),
                "name_capture_attempt": attempt
            }
        )

    async def handle_name_success(
        self,
        name: str,
        interaction_count: int,
        extra_updates: Optional[Dict[str, Any]] = None
    ) -> GreetingResult:
        """
        Nombre obtenido exitosamente, continuar flujo.

        Extraído de:
        - _handle_nombre_exitoso (líneas 270-281)
        - _handle_nombre_exitoso_with_updates (líneas 283-302)

        Args:
            name: Nombre del cliente
            extra_updates: Updates adicionales de LLM (extracted_data, etc.)
        """
        response = f"Perfecto {name}, ahora necesito hacerte unas preguntas rápidas para conectarte con el asesor ideal."

        # Metadata base
        metadata = {
            "customer_name": name,
            "interaction_count": interaction_count,
            "last_message_at": datetime.now().isoformat()
        }

        # Combinar con extra_updates si existen
        if extra_updates:
            metadata.update(extra_updates)

        return GreetingResult(
            response=response,
            next_state="NOMBRE_OBTENIDO",
            metadata=metadata
        )

    async def extract_name_with_llm(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Intenta extraer nombre usando LLM.

        Returns:
            Nombre extraído o None si falla
        """
        try:
            if not self.llm or not hasattr(self.llm, 'classify_intent_and_extract_entities'):
                return None

            extraction = await self.llm.classify_intent_and_extract_entities(
                message=message,
                context=context
            )

            return extraction.get("nombre")

        except Exception as e:
            print(f"[GreetingHandler] Error extrayendo nombre con LLM: {e}")
            return None
