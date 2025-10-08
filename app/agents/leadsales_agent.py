"""
LeadsalesAgent - Pure routing architecture
Core responsibilities: State routing and handler delegation
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from app.services.leadsales_service import LeadsalesService
from app.agents.leadsales.analyzers import ResponseGenerator
from app.agents.leadsales.handlers import EngagementHandler, CaptureHandler, CRMHandler
from app.config import (
    STATE_CAPTURANDO_DETALLES, STATE_PROFUNDIZANDO_NECESIDAD,
    STATE_CONFIRMANDO_INFORMACION, STATE_PROCESANDO_CRM, STATE_LEAD_CREADO
)

class LeadsalesAgent(BaseAgent):

    def __init__(self, llm_service=None, state_manager=None, leadsales_service=None):
        """
        Constructor con Dependency Injection.

        Args:
            llm_service: Servicio LLM inyectado (opcional)
            state_manager: State Manager inyectado (opcional)
            leadsales_service: Servicio Leadsales inyectado (opcional)
        """
        super().__init__("LeadsalesAgent", llm_service=llm_service, state_manager=state_manager)

        # ✅ Usar Leadsales Service inyectado o crear nuevo (backward compatibility)
        if leadsales_service:
            self.leadsales_service = leadsales_service
        else:
            self.leadsales_service = LeadsalesService()
            self.leadsales_service.initialize()

        # ✅ Inicializar LLM solo si necesario
        if self.llm_service and hasattr(self.llm_service, 'api_client') and not self.llm_service.api_client.initialized:
            self.llm_service.initialize()

        # Inicializar componentes con dependency injection
        response_generator = ResponseGenerator(self.llm_service)
        self.crm_handler = CRMHandler(self.leadsales_service, "324 551 6105", self)
        self.capture_handler = CaptureHandler(response_generator, self.crm_handler, self)
        self.engagement_handler = EngagementHandler(response_generator, self)

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        """LeadsalesAgent routing: transfers + conversion states"""
        current_state = conversation.get("state", "")

        # Transfer a LeadsalesAgent
        if current_state == "TRANSFERIDO":
            return conversation.get("transfer_metadata", {}).get("to_agent") == "LeadsalesAgent"

        # Estados de conversión
        return current_state in [
            "FLUJO_COMPLETADO", "CAPTURANDO_DETALLES", "PROFUNDIZANDO_NECESIDAD",
            "CONFIRMANDO_INFORMACION", "PROCESANDO_CRM"
        ]

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Pure routing - delegates to specialized handlers"""
        user_message = message_data.get("text", {}).get("body", "").strip()
        customer_name = conversation.get("customer_name", "")
        current_state = conversation.get("state", "TRANSFERIDO")

        if not self.validate_message(user_message):
            return self.create_response("Por favor, envía un mensaje válido.")

        # Setup context for handlers
        self.crm_handler.set_conversation_context(conversation, message_data.get("from"))

        try:
            # Route to appropriate handler based on state
            if current_state in ["TRANSFERIDO", "FLUJO_COMPLETADO"]:
                result = await self.engagement_handler.handle_initial_engagement(customer_name, conversation)
            elif current_state == STATE_CAPTURANDO_DETALLES:
                result = await self.capture_handler.handle_detail_capture(user_message, customer_name)
            elif current_state == STATE_PROFUNDIZANDO_NECESIDAD:
                result = await self.capture_handler.handle_need_deepening(user_message, customer_name, conversation)
            elif current_state == STATE_CONFIRMANDO_INFORMACION:
                result = await self.capture_handler.handle_information_confirmation(user_message, customer_name, conversation)
            else:
                result = await self.engagement_handler.handle_initial_engagement(customer_name, conversation)

            return self.create_response(result["response"], result.get("new_state"), result.get("data_updates"))

        except Exception as e:
            self.log_error("Error en LeadsalesAgent", e)
            result = await self.crm_handler.handle_error_fallback(customer_name)
            return self.create_response(result["response"], result.get("new_state"), result.get("data_updates"))
