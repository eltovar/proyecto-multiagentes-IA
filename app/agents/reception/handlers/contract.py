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
        """
        Args:
            llm_service: Servicio LLM (para futuras mejoras)
            state_manager: State Manager para persistencia
            config: Configuración con links (youtube_link, solicitud_gratis_link)
        """
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
        """
        Pregunta obligatoria 1: Contrato con inmobiliaria

        Extraído de: _handle_pregunta_contrato_inmobiliaria (líneas 304-314)
        """
        response = "¿Actualmente tienes un contrato vigente con alguna inmobiliaria?"

        return ContractResult(
            response=response,
            next_state="STATE_PREGUNTA_CONTRATO_INMOBILIARIA",
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

        Extraído de: _handle_respuesta_contrato (líneas 316-343)

        Returns:
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
                next_state="STATE_PREGUNTA_SOLICITUD_LIBERTADOR",
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
                next_state="STATE_PREGUNTA_CUAL_INMOBILIARIA",
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
                next_state="STATE_PREGUNTA_SOLICITUD_LIBERTADOR",
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
            next_state="STATE_PREGUNTA_SOLICITUD_LIBERTADOR",
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
        Procesa respuesta sobre solicitud El Libertador.

        Extraído de: _handle_respuesta_solicitud_libertador (líneas 359-392)

        Returns:
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
                next_state="STATE_PREGUNTA_FECHA_NECESIDAD",
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
                next_state="STATE_PREGUNTA_FECHA_NECESIDAD",
                metadata={
                    "tiene_solicitud_libertador": True,
                    "interaction_count": interaction_count,
                    "last_message_at": datetime.now().isoformat()
                }
            )
