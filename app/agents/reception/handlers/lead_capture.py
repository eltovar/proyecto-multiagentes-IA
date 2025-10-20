"""
LeadCaptureHandler - Captura final de fecha y transferencia a LeadsalesAgent
Extraído de reception_agent.py (líneas 394-428)
"""

from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime


@dataclass
class LeadCaptureResult:
    """Resultado estructurado del LeadCaptureHandler"""
    response: str
    next_state: str
    transfer_to: str
    metadata: Dict[str, Any]


class LeadCaptureHandler:
    """
    Handler para captura final de lead y transferencia.

    Responsabilidades:
    - Capturar fecha de necesidad
    - Finalizar flujo de recepción
    - Transferir a LeadsalesAgent
    - Manejar límite de interacciones
    """

    def __init__(self, llm_service, state_manager, config: Dict[str, str]):
        """
        Args:
            llm_service: Servicio LLM (para futuras mejoras)
            state_manager: State Manager para persistencia
            config: Configuración con whatsapp_oficial
        """
        self.llm = llm_service
        self.state = state_manager
        self.config = config

        # WhatsApp oficial para contacto
        self.whatsapp_oficial = config.get("whatsapp_oficial", "324 551 6105")

    async def handle_date_response(
        self,
        message: str,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> LeadCaptureResult:
        """
        Última pregunta del flujo - Captura fecha y transfiere.

        Extraído de: _handle_respuesta_fecha_necesidad (líneas 394-414)

        Args:
            message: Respuesta del usuario con fecha
            conversation: Estado de la conversación
            interaction_count: Número de interacciones

        Returns:
            LeadCaptureResult con transferencia a LeadsalesAgent
        """
        name = conversation.get("customer_name", "")

        # Etapa 3: Gestión de Expectativas y Redirección
        response = f"""{name}, he registrado tu interés.

En breve, uno de nuestros asesores te contactará desde nuestro WhatsApp oficial, el {self.whatsapp_oficial}, para brindarte todos los detalles."""

        return LeadCaptureResult(
            response=response,
            next_state="STATE_FLUJO_COMPLETADO",
            transfer_to="LeadsalesAgent",
            metadata={
                "fecha_necesidad": message.strip(),
                "interaction_count": interaction_count,
                "flujo_recepcion_completado": True,
                "last_message_at": datetime.now().isoformat()
            }
        )

    async def handle_interaction_limit(
        self,
        conversation: Dict[str, Any],
        interaction_count: int
    ) -> LeadCaptureResult:
        """
        Maneja límite de 10 interacciones alcanzado.

        Extraído de: _handle_limite_interacciones (líneas 416-428)

        Args:
            conversation: Estado de la conversación
            interaction_count: Número de interacciones

        Returns:
            LeadCaptureResult con transferencia
        """
        response = f"""He registrado tu interés. Por favor contacta directamente a nuestro WhatsApp oficial {self.whatsapp_oficial} para continuar con tu consulta."""

        return LeadCaptureResult(
            response=response,
            next_state="LIMITE_ALCANZADO",
            transfer_to="LeadsalesAgent",
            metadata={
                "interaction_count": interaction_count,
                "last_message_at": datetime.now().isoformat()
            }
        )

    def get_flow_reminder(self, current_state: str) -> str:
        """
        Retorna mensaje recordatorio para mantener flujo.

        Extraído de: _mantener_flujo (líneas 430-439)

        Args:
            current_state: Estado actual de la conversación

        Returns:
            Mensaje recordatorio
        """
        flujo_messages = {
            "STATE_POLITICAS_PRESENTADAS": "Primero necesito tu nombre para continuar. ¿Me lo puedes compartir?",
            "STATE_RECOPILANDO_NOMBRE": "Tu nombre es importante para la atención personalizada. ¿Cuál es?",
            "STATE_PREGUNTA_CONTRATO_INMOBILIARIA": "Por favor responde: ¿Tienes contrato vigente con alguna inmobiliaria?",
            "STATE_PREGUNTA_SOLICITUD_LIBERTADOR": "Necesito saber: ¿Ya tienes solicitud aprobada por EL LIBERTADOR?",
            "STATE_PREGUNTA_FECHA_NECESIDAD": "¿Para que fecha necesitas el nuevo inmueble?"
        }
        return flujo_messages.get(current_state, "Sigamos con el proceso paso a paso.")
