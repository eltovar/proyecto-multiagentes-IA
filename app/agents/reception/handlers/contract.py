"""
ContractHandler - Lógica de contratos y solicitud El Libertador
Extraído de reception_agent.py (líneas 304-392)
"""

from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime


@dataclass
class ContractResult:
    """Resultado estructurado del ContractHandler"""
    response: str
    next_state: str
    metadata: Dict[str, Any]


class ContractHandler:
    """
    Handler especializado para:
    - Pregunta sobre contrato vigente con inmobiliaria
    - Captura de inmobiliaria actual (si aplica)
    - Pregunta sobre solicitud El Libertador
    - Orientación para aplicar a El Libertador (si no tiene)
    """

    def __init__(self, llm_service, state_manager, config: Dict[str, str]):
        self.llm = llm_service
        self.state = state_manager
        self.config = config

        # Links obligatorios del flujo
        self.youtube_link = config.get("youtube_link", "https://www.youtube.com/watch?v=xyz")
        self.solicitud_gratis_link = config.get("solicitud_gratis_link", "https://inmobiliariaproteger.com/solicitud-gratis")

    async def handle_contract_question(
        self,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> ContractResult:
        """ Pregunta obligatoria 1: Contrato con inmobiliaria """
        response = "¿Actualmente tienes un contrato vigente con alguna inmobiliaria?"
 
        return ContractResult(
            response=response,
            next_state="PREGUNTA_CONTRATO_INMOBILIARIA",
            metadata={
                "interaction_count": interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def handle_contract_response(
        self,
        message: str,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> ContractResult:
        """
        Procesa respuesta sobre contrato inmobiliaria.
            - Si tiene contrato → pregunta cuál inmobiliaria
            - Si no tiene → continúa a pregunta Libertador
        """
        respuesta_lower = message.lower().strip()

        # Keywords para detectar respuesta negativa (revisar primero)
        negative_keywords = ["no", "nop", "nope", "nunca", "jamás"]

        # Keywords para detectar respuesta positiva
        positive_keywords = ["sí", "si", "yes", "tengo", "claro"]

        # Verificar negativas primero para evitar falsos positivos como "no tengo"
        if any(palabra in respuesta_lower for palabra in negative_keywords):
            # No tiene contrato -> Continuar a solicitud Libertador
            return ContractResult(
                response="Perfecto. ¿Ya tienes una solicitud aprobada por EL LIBERTADOR?",
                next_state="PREGUNTA_SOLICITUD_LIBERTADOR",
                metadata={
                    "tiene_contrato_inmobiliaria": False,
                    "interaction_count": interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )
        elif any(palabra in respuesta_lower for palabra in positive_keywords):
            # Tiene contrato -> Preguntar cuál inmobiliaria
            return ContractResult(
                response="¿Con cuál inmobiliaria tienes el contrato?",
                next_state="PREGUNTA_CUAL_INMOBILIARIA",
                metadata={
                    "tiene_contrato_inmobiliaria": True,
                    "interaction_count": interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )
        else:
            # Caso ambiguo -> Asumir no tiene contrato
            return ContractResult(
                response="Perfecto. ¿Ya tienes una solicitud aprobada por EL LIBERTADOR?",
                next_state="PREGUNTA_SOLICITUD_LIBERTADOR",
                metadata={
                    "tiene_contrato_inmobiliaria": False,
                    "interaction_count": interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )

    async def handle_which_company_response(
        self,
        message: str,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> ContractResult:
        """
        Captura nombre de inmobiliaria actual.

        Extraído de: _handle_respuesta_cual_inmobiliaria (líneas 345-357)
        """
        return ContractResult(
            response="Entendido. ¿Ya tienes una solicitud aprobada por EL LIBERTADOR?",
            next_state="PREGUNTA_SOLICITUD_LIBERTADOR",
            metadata={
                "inmobiliaria_actual": message.strip(),
                "interaction_count": interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def handle_libertador_response(
        self,
        message: str,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> ContractResult:
        """
            - Si no tiene → muestra orientación con links
            - Si tiene → continúa directamente
        """
        respuesta_lower = message.lower().strip()

        # Keywords para detectar respuesta negativa
        negative_keywords = ["no", "nope", "aún no", "todavía no"]

        if any(palabra in respuesta_lower for palabra in negative_keywords):
            # No tiene solicitud -> Mostrar orientación y links
            response = f"""Te oriento para que puedas aplicar:

Video explicativo: {self.youtube_link}
Solicitud GRATIS: {self.solicitud_gratis_link}

¿Para que fecha necesitas el nuevo inmueble?"""

            return ContractResult(
                response=response,
                next_state="PREGUNTA_FECHA_NECESIDAD",
                metadata={
                    "tiene_solicitud_libertador": False,
                    "interaction_count": interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )
        else:
            # Sí tiene solicitud -> Continuar directamente
            return ContractResult(
                response="Excelente. ¿Para que fecha necesitas el nuevo inmueble?",
                next_state="PREGUNTA_FECHA_NECESIDAD",
                metadata={
                    "tiene_solicitud_libertador": True,
                    "interaction_count": interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )

    async def handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> ContractResult:
        """
        Método principal del handler. Determina la acción a tomar basada en el estado
        para completar la sección de contratos y El Libertador.

        Args:
            message_data: Datos del mensaje de WhatsApp
            conversation: Estado de la conversación

        Returns:
            ContractResult con respuesta y transición de estado
        """
        current_state = conversation.get("state")
        message = message_data.get("text", {}).get("body", "")
        interaction_count = conversation.get("interaction_count", 0) + 1

        # 1. ESTADO NOMBRE_OBTENIDO: Iniciar el flujo de contrato
        # Viene del GreetingHandler y es el punto de entrada para este handler
        if current_state == "NOMBRE_OBTENIDO":
            return await self.handle_contract_question(conversation, interaction_count)

        # 2. ESTADO PREGUNTA_CONTRATO_INMOBILIARIA: Procesar respuesta Sí/No de contrato
        if current_state == "PREGUNTA_CONTRATO_INMOBILIARIA":
            return await self.handle_contract_response(message, conversation, interaction_count)

        # 3. ESTADO PREGUNTA_CUAL_INMOBILIARIA: Capturar nombre de la inmobiliaria
        if current_state == "PREGUNTA_CUAL_INMOBILIARIA":
            return await self.handle_which_company_response(message, conversation, interaction_count)

        # 4. ESTADO PREGUNTA_SOLICITUD_LIBERTADOR: Procesar respuesta Sí/No de El Libertador
        if current_state == "PREGUNTA_SOLICITUD_LIBERTADOR":
            return await self.handle_libertador_response(message, conversation, interaction_count)

        # 5. Fallback: Si se llama en un estado que no debe manejar (ej: ya se preguntó todo)
        return ContractResult(
            response="Ya capturamos la información de tu contrato. Por favor, responde la última pregunta que te hice sobre la fecha que necesitas el inmueble.",
            next_state=current_state,
            metadata={}
        )
