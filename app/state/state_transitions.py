"""
StateTransitionManager: Gestión de transiciones de estado y Handoff Protocol.
Responsable de validar cambios de estado y proteger conversaciones transferidas.
"""

from typing import Dict, Any
from datetime import datetime
from app.state.models import get_database_connection
from app.state.crud_operations import ConversationCRUD

class StateTransitionManager:

    def __init__(self):
        self.crud = ConversationCRUD()
        self.valid_states = ["NUEVO", "RECOPILANDO_NOMBRE", "RECOPILANDO_NECESIDAD", "TRANSFERIDO"]

    def update_conversation_state(self, whatsapp_id: str, new_state: str, data: Dict[str, Any] = None) -> bool:
        if new_state not in self.valid_states:
            print(f"[StateTransitions] Estado inválido: {new_state}")
            return False

        conversation = self.crud.get_conversation(whatsapp_id)

        if conversation and conversation.state == "TRANSFERIDO":
            print(f"[StateTransitions] HANDOFF ACTIVO - Bloqueado para {whatsapp_id}")
            return False

        if not conversation:
            conversation = self.crud.create_conversation(whatsapp_id)

        if not self.can_transition_to(conversation.state, new_state):
            print(f"[StateTransitions] Transición inválida: {conversation.state} -> {new_state}")
            return False

        conn = get_database_connection()
        cursor = conn.cursor()

        update_fields = ["state = ?", "updated_at = ?"]
        params = [new_state, datetime.now()]

        if data:
            for key, value in data.items():
                if key in ["customer_name", "customer_needs", "lead_id"] and value:
                    update_fields.append(f"{key} = ?")
                    params.append(value)

        params.append(whatsapp_id)

        cursor.execute(f"""
            UPDATE conversations
            SET {', '.join(update_fields)}
            WHERE whatsapp_id = ?
        """, params)

        conn.commit()
        conn.close()

        print(f"[StateTransitions] Estado actualizado: {whatsapp_id} -> {new_state}")
        return True

    def can_transition_to(self, current_state: str, new_state: str) -> bool:
        valid_transitions = {
            "NUEVO": ["RECOPILANDO_NOMBRE", "TRANSFERIDO"],
            "RECOPILANDO_NOMBRE": ["RECOPILANDO_NECESIDAD", "TRANSFERIDO"],
            "RECOPILANDO_NECESIDAD": ["TRANSFERIDO"],
            "TRANSFERIDO": []
        }

        if current_state == "TRANSFERIDO":
            return False

        return new_state in valid_transitions.get(current_state, [])

    def is_conversation_transferred(self, whatsapp_id: str) -> bool:
        conversation = self.crud.get_conversation(whatsapp_id)
        return conversation is not None and conversation.state == "TRANSFERIDO"

    def activate_handoff_protocol(self, whatsapp_id: str) -> bool:
        return self.update_conversation_state(whatsapp_id, "TRANSFERIDO")

    def get_conversation_status(self, whatsapp_id: str) -> Dict[str, Any]:
        conversation = self.crud.get_conversation(whatsapp_id)
        if not conversation:
            return {"exists": False, "handoff_active": False}

        return {
            "exists": True,
            "state": conversation.state,
            "handoff_active": conversation.state == "TRANSFERIDO",
            "customer_name": conversation.customer_name,
            "customer_needs": conversation.customer_needs
        }