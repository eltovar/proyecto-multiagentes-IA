"""
CaptureHandler for LeadsalesAgent
Extracted from leadsales_agent.py
Handles information capture and need deepening
"""

from typing import Dict, Any
from app.config import STATE_PROFUNDIZANDO_NECESIDAD, STATE_CONFIRMANDO_INFORMACION
from app.agents.leadsales.analyzers import InformationAnalyzer


class CaptureHandler:
    """Handles customer information capture and need analysis"""

    def __init__(self, response_generator, crm_handler, logger=None):
        self.response_generator = response_generator
        self.crm_handler = crm_handler
        self.logger = logger

    def log_action(self, message: str, metadata: Dict[str, Any] = None):
        """Simple logging - will delegate to agent's log_action if needed"""
        if self.logger:
            self.logger.log_action(message, metadata)
        else:
            print(f"[CaptureHandler] {message}: {metadata or {}}")

    async def handle_detail_capture(self, user_message: str, customer_name: str) -> Dict[str, Any]:
        """Capturar detalles específicos de la necesidad"""

        # Analizar si el mensaje contiene información útil
        has_sufficient_info = InformationAnalyzer.analyze_completeness(user_message)

        self.log_action("Detail capture analysis", {
            "customer": customer_name,
            "message_preview": user_message[:50],
            "has_sufficient_info": has_sufficient_info
        })

        if has_sufficient_info:
            # Información suficiente, proceder a CRM
            return await self.crm_handler.proceed_to_crm_creation(user_message, customer_name)
        else:
            # Necesita más información específica
            response = await self.response_generator.generate_follow_up_question(user_message, customer_name)
            return {
                "response": response,
                "new_state": STATE_PROFUNDIZANDO_NECESIDAD,
                "data_updates": {
                    "partial_needs": user_message,
                    "conversion_stage": "capturing_details"
                }
            }

    async def handle_need_deepening(self, user_message: str, customer_name: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Profundizar en la necesidad para obtener información de alta calidad"""

        # Consolidar información existente
        existing_needs = conversation.get("customer_needs", "")
        partial_needs = conversation.get("partial_needs", "")

        consolidated_info = f"{existing_needs} {partial_needs} {user_message}".strip()

        self.log_action("Need deepening analysis", {
            "customer": customer_name,
            "consolidated_length": len(consolidated_info),
            "message_preview": user_message[:50]
        })

        # Verificar si ya tenemos suficiente información para crear lead de calidad
        is_complete = InformationAnalyzer.analyze_completeness(consolidated_info)

        if is_complete:
            return await self.crm_handler.proceed_to_crm_creation(consolidated_info, customer_name)
        else:
            # Una pregunta más específica para cerrar la información
            final_question = await self.response_generator.generate_final_capture_question(consolidated_info, customer_name)
            return {
                "response": final_question,
                "new_state": STATE_CONFIRMANDO_INFORMACION,
                "data_updates": {
                    "consolidated_needs": consolidated_info,
                    "conversion_stage": "final_capture"
                }
            }

    async def handle_information_confirmation(self, user_message: str, customer_name: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Confirmación final de información antes de crear lead"""

        # Consolidar toda la información
        final_needs = conversation.get("consolidated_needs", "") + " " + user_message

        self.log_action("Information confirmation", {
            "customer": customer_name,
            "final_needs_length": len(final_needs.strip())
        })

        # Proceder directamente a crear lead
        return await self.crm_handler.proceed_to_crm_creation(final_needs.strip(), customer_name)