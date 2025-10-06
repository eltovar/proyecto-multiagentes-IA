"""
StateManager Coordinador: Interface principal para gestión de estado.
Coordina entre módulos especializados: CRUD, Transitions, Queries.
acade central para gestionar, leer y actualizar el estado persistente de las conversaciones
"""

from typing import Optional, Dict, Any
from app.state.models import ConversationState
from .crud_operations import ConversationCRUD
from .state_transitions import StateTransitionManager
from .query_operations import ConversationQueries

STATE_NUEVO = "NUEVO"
STATE_RECOPILANDO_NOMBRE = "RECOPILANDO_NOMBRE"
STATE_RECOPILANDO_NECESIDAD = "RECOPILANDO_NECESIDAD"
STATE_LISTO_PARA_TRANSFERIR = "LISTO_PARA_TRANSFERIR"
STATE_TRANSFERIDO = "TRANSFERIDO"

class StateManager:

    def __init__(self):
        self.crud = ConversationCRUD()
        self.transitions = StateTransitionManager()
        self.queries = ConversationQueries()

    def get_conversation(self, whatsapp_id: str) -> Optional[ConversationState]:
        return self.crud.get_conversation(whatsapp_id)

    def get_or_create_conversation(self, whatsapp_id: str) -> ConversationState:
        conversation = self.crud.get_conversation(whatsapp_id)
        return conversation if conversation else self.crud.create_conversation(whatsapp_id)

    def update_conversation_state(self, whatsapp_id: str, new_state: str = None, **data):
        if new_state:
            return self.transitions.update_conversation_state(whatsapp_id, new_state, data)
        else:
            return self.crud.update_conversation_data(whatsapp_id, data)

    #verifican si la conversación ha sido transferida a un humano 
    def update_with_validation(self, whatsapp_id: str, state: str, data: Dict[str, Any]) -> bool:
        if self.transitions.is_conversation_transferred(whatsapp_id):
            print(f"[StateManager] Handoff activo - operación bloqueada para {whatsapp_id}")
            return False

        return self.transitions.update_conversation_state(whatsapp_id, state, data)

    def is_conversation_transferred(self, whatsapp_id: str) -> bool:
        return self.transitions.is_conversation_transferred(whatsapp_id)

    def get_conversations_by_state(self, state: str):
        return self.queries.get_conversations_by_state(state)

    def get_stats(self) -> Dict[str, Any]:
        return self.queries.get_stats()

    def health_check(self) -> Dict[str, Any]:
        try:
            stats = self.get_stats()
            return {
                "status": "healthy",
                "total_conversations": stats["total_conversations"],
                "active_handoffs": stats["active_handoffs"],
                "modules": {
                    "crud": "operational",
                    "transitions": "operational",
                    "queries": "operational"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "modules": {"status": "error"}
            }

def get_conversation_state(whatsapp_id: str) -> Optional[Dict[str, Any]]:
    manager = StateManager()
    conversation = manager.get_conversation(whatsapp_id)

    if conversation:
        return {
            "whatsapp_id": conversation.whatsapp_id,
            "state": conversation.state,
            "customer_name": conversation.customer_name,
            "customer_needs": conversation.customer_needs,
            "lead_id": conversation.lead_id
        }
    return None

def update_conversation_state(whatsapp_id: str, new_state: str, data: Dict[str, Any] = None):
    manager = StateManager()
    return manager.update_conversation_state(whatsapp_id, new_state, **(data or {}))

state_manager = StateManager()