# Gestiona las transiciones de estado de las conversaciones, aplicando validación de estados permitidos y bloqueando actualizaciones si el handoff (transferencia humana) está activo.
from typing import Dict, Any, Set
from datetime import datetime
from app.state.models import get_database_connection
from app.state.crud_operations import ConversationCRUD
from app.config import VALID_STATES


class StateTransitionManager:
    """ Gestor de transiciones de estado minimalista y eficiente """

    def __init__(self):
        """Initialize with optimized state validation."""
        self.crud = ConversationCRUD()
        # Convertir a set para O(1) lookup performance
        self._valid_states: Set[str] = set(VALID_STATES)

        # Cache para debugging (opcional en producción)
        self._transition_log = []

    def update_conversation_state(
        self,
        whatsapp_id: str,
        new_state: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """ Actualiza estado de conversación con validaciones esenciales."""

        # VALIDACIÓN 1: Estado debe ser válido
        if not self._is_valid_state(new_state):
            self._log_invalid_state(new_state)
            return False

        # VALIDACIÓN 2: Handoff Protocol
        if self._is_handoff_blocked(whatsapp_id):
            self._log_handoff_block(whatsapp_id)
            return False

        # VALIDACIÓN 3: Asegurar conversación existe
        conversation = self._ensure_conversation_exists(whatsapp_id)

        # EJECUCIÓN: Actualizar estado en base de datos
        success = self._execute_state_update(whatsapp_id, new_state, data or {})

        if success:
            self._log_successful_transition(whatsapp_id, new_state)

        return success

    def _is_valid_state(self, state: str) -> bool:
        """O(1) validation using set lookup."""
        return state in self._valid_states

    def _is_handoff_blocked(self, whatsapp_id: str) -> bool:
        """Check if conversation is under handoff protocol."""
        conversation = self.crud.get_conversation(whatsapp_id)
        return conversation is not None and conversation.state == "TRANSFERIDO"

    def _ensure_conversation_exists(self, whatsapp_id: str):
        """Create conversation if doesn't exist."""
        conversation = self.crud.get_conversation(whatsapp_id)
        if not conversation:
            conversation = self.crud.create_conversation(whatsapp_id)
        return conversation

    def _execute_state_update(
        self,
        whatsapp_id: str,
        new_state: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Execute atomic database update with field whitelist security.
        """
        try:
            conn = get_database_connection()
            cursor = conn.cursor()

            # Base fields always updated
            update_fields = ["state = ?", "updated_at = ?"]
            params = [new_state, datetime.now()]

            # Whitelist approach for security (based on actual DB schema)
            allowed_fields = {
                "customer_name", "customer_needs", "lead_id",
                "current_agent", "transfer_metadata"
                # Note: Campos como interaction_count se manejan en memoria por agentes
            }

            # Add whitelisted fields from data
            for key, value in data.items():
                if key in allowed_fields and value is not None:
                    update_fields.append(f"{key} = ?")
                    params.append(value)

            params.append(whatsapp_id)

            # Execute atomic update
            cursor.execute(f"""
                UPDATE conversations
                SET {', '.join(update_fields)}
                WHERE whatsapp_id = ?
            """, params)

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"[StateTransitions] [ERROR] DB Error: {e}")
            return False

    def _log_invalid_state(self, state: str) -> None:
        """Log invalid state with helpful debugging info."""
        print(f"[StateTransitions] [ERROR] Estado inválido: {state}")
        print(f"[StateTransitions] [INFO] Estados válidos: {len(self._valid_states)} disponibles")

        # Suggest similar states for debugging
        if len(state) > 3:
            similar = [s for s in self._valid_states if state.lower() in s.lower()][:3]
            if similar:
                print(f"[StateTransitions] [HINT] ¿Quisiste decir? {similar}")

    def _log_handoff_block(self, whatsapp_id: str) -> None:
        """Log handoff protocol activation."""
        print(f"[StateTransitions] [BLOCKED] HANDOFF ACTIVO - Bloqueado para {whatsapp_id}")

    def _log_successful_transition(self, whatsapp_id: str, new_state: str) -> None:
        """Log successful state transition."""
        short_id = whatsapp_id[-4:] if len(whatsapp_id) > 4 else whatsapp_id
        print(f"[StateTransitions] [OK] ...{short_id} -> {new_state}")

    # ================================
    # UTILITY METHODS (Public API)
    # ================================

    def is_conversation_transferred(self, whatsapp_id: str) -> bool:
        """Quick check if conversation is in handoff state."""
        return self._is_handoff_blocked(whatsapp_id)

    def activate_handoff_protocol(self, whatsapp_id: str) -> bool:
        """Convenience method to transfer conversation to human agent."""
        return self.update_conversation_state(whatsapp_id, "TRANSFERIDO")

    def get_conversation_status(self, whatsapp_id: str) -> Dict[str, Any]:
        """
        Return comprehensive conversation status for debugging/decisions.

        Returns:
            Dict with conversation existence, state, handoff status, and metadata
        """
        conversation = self.crud.get_conversation(whatsapp_id)

        if not conversation:
            return {
                "exists": False,
                "handoff_active": False,
                "state": None,
                "debug_info": "Conversation not found"
            }

        return {
            "exists": True,
            "state": conversation.state,
            "handoff_active": conversation.state == "TRANSFERIDO",
            "customer_name": getattr(conversation, 'customer_name', None),
            "customer_needs": getattr(conversation, 'customer_needs', None),
            "interaction_count": getattr(conversation, 'interaction_count', 0),
            "debug_info": f"Active conversation in {conversation.state}"
        }

    def get_valid_states(self) -> Set[str]:
        """Return set of valid states for external validation."""
        return self._valid_states.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Return system statistics for monitoring."""
        return {
            "total_valid_states": len(self._valid_states),
            "handoff_protocol_active": True,
            "version": "MVS-1.0",
            "performance_mode": "O(1) set lookups"
        }