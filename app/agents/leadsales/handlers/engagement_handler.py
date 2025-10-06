"""
EngagementHandler for LeadsalesAgent
Extracted from leadsales_agent.py
Handles initial engagement and motivation strategies
"""

from typing import Dict, Any
from app.config import STATE_CAPTURANDO_DETALLES, STATE_PROFUNDIZANDO_NECESIDAD


class EngagementHandler:
    
    """Handles initial customer engagement and conversation initiation"""

    def __init__(self, response_generator, logger=None):
        self.response_generator = response_generator
        self.logger = logger

    def log_action(self, message: str, metadata: Dict[str, Any] = None):
        """Simple logging - will delegate to agent's log_action if needed"""
        if self.logger:
            self.logger.log_action(message, metadata)
        else:
            print(f"[EngagementHandler] {message}: {metadata or {}}")

    async def handle_initial_engagement(self, customer_name: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Engagement inicial altamente motivador para obtener información específica"""

        # Verificar si ya tenemos información básica de la necesidad
        customer_needs = conversation.get("customer_needs", "")

        if customer_needs and len(customer_needs.strip()) > 10:
            # Tenemos información básica, profundizar
            response = await self.response_generator.generate_deepening_response(customer_name, customer_needs)
            new_state = STATE_PROFUNDIZANDO_NECESIDAD
        else:
            # No tenemos información, capturar detalles iniciales
            response = await self.response_generator.generate_initial_capture_response(customer_name)
            new_state = STATE_CAPTURANDO_DETALLES

        self.log_action("Initial engagement completed", {
            "customer": customer_name,
            "has_existing_needs": bool(customer_needs and len(customer_needs.strip()) > 10),
            "new_state": new_state
        })

        return {
            "response": response,
            "new_state": new_state,
            "data_updates": {"conversion_stage": "initial_engagement"}
        }