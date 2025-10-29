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
            next_state="FLUJO_COMPLETADO",
            transfer_to="leadsales",
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
            transfer_to="leadsales",
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
            "POLITICAS_PRESENTADAS": "Primero necesito tu nombre para continuar. ¿Me lo puedes compartir?",
            "RECOPILANDO_NOMBRE": "Tu nombre es importante para la atención personalizada. ¿Cuál es?",
            "PREGUNTA_CONTRATO_INMOBILIARIA": "Por favor responde: ¿Tienes contrato vigente con alguna inmobiliaria?",
            "PREGUNTA_SOLICITUD_LIBERTADOR": "Necesito saber: ¿Ya tienes solicitud aprobada por EL LIBERTADOR?",
            "PREGUNTA_FECHA_NECESIDAD": "¿Para que fecha necesitas el nuevo inmueble?"
        }
        return flujo_messages.get(current_state, "Sigamos con el proceso paso a paso.")

    async def handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> LeadCaptureResult:
        """
        Método principal del handler. Determina la acción a tomar basada en el estado
        para completar la captura de fecha y ejecutar la transferencia.

        Args:
            message_data: Datos del mensaje de WhatsApp
            conversation: Estado de la conversación

        Returns:
            LeadCaptureResult con respuesta, estado y transferencia
        """
        current_state = conversation.get("state")
        message = message_data.get("text", {}).get("body", "")
        interaction_count = conversation.get("interaction_count", 0) + 1

        # 1. ESTADO PREGUNTA_FECHA_NECESIDAD: Capturar la fecha y finalizar el flujo
        # Viene del ContractHandler y es el punto de finalización para la Recepción
        if current_state == "PREGUNTA_FECHA_NECESIDAD":
            # Nota: No se usa LLM para validar/extraer fecha en esta versión,
            # simplemente se guarda el mensaje del usuario como la fecha.
            return await self.handle_date_response(message, conversation, interaction_count)

        # 2. Fallback: Si el usuario responde cuando el flujo ya debería haber terminado,
        # o si el router lo envía aquí por error.

        # Intentar guiar al usuario si está atascado en un estado anterior (usando get_flow_reminder)
        # Esto es útil si el router mapea estados de otros handlers a este para manejo genérico
        # de mensajes fuera de flujo.
        if current_state not in ["FLUJO_COMPLETADO", "LIMITE_ALCANZADO", "TRANSFERIDO"]:
            reminder_response = self.get_flow_reminder(current_state)

            # Si el recordatorio devuelve un mensaje específico para el estado, se devuelve.
            if reminder_response != "Sigamos con el proceso paso a paso.":
                return LeadCaptureResult(
                    response=reminder_response,
                    next_state=current_state,
                    transfer_to=None,
                    metadata={"interaction_count": interaction_count}
                )

        # 3. Flujo completado / Estado final
        # Si el flujo ya está completo o en un estado final, se transfiere al asesor humano.
        return await self.handle_interaction_limit(conversation, interaction_count)
