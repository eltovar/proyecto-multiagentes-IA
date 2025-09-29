'''
    Agente de soporte que utiliza RAG para responder consultas.
    Sistema RAG con vectores de respuestas contextuales
'''

from typing import Dict, Any
from .base_agent import BaseAgent
from app.rag.rag_system import rag_system

class SupportAgent(BaseAgent):

    def __init__(self):
        super().__init__("SupportAgent")
        self.rag_system = rag_system

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        return False

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        user_message = message_data["text"]["body"]

        self.log_action("Procesando consulta con RAG", user_message[:50] + "...")

        rag_response = self.rag_system.get_context_for_query(user_message)

        full_response = (f"{rag_response}\n\n"
                        f"¿Hay algo más en lo que pueda ayudarte? "
                        f"O si tienes alguna necesidad específica, estaré encantado de conectarte con un especialista.")

        return {
            "response": full_response,
            "new_state": conversation["state"],
            "data_updates": {},
            "transfer_to": None
        }