'''
    Clase base para todos los agentes.
    Define interfaz comun, loggin, estructura de respuesta y manejo de estado.
'''

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.state.manager import state_manager

# Import condicional para evitar errores
try:
    from app.services.llm_service import llm_service
except ImportError:
    llm_service = None

class BaseAgent(ABC):

    def __init__(self, name: str):
        self.name = name
        self.agent_name = name  # Compatibilidad con código existente
        self.llm_service = llm_service
        self.initialized = True

    @abstractmethod
    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def log_action(self, action: str, details: str = ""):
        print(f"[{self.name}] {action}: {details}")

    def log_error(self, error: str, exception: Exception = None, context: Dict[str, Any] = None):
        error_msg = f"[{self.name}] ERROR: {error}"
        if exception:
            error_msg += f" - {type(exception).__name__}: {str(exception)}"
        if context:
            error_msg += f" - Context: {context}"
        print(error_msg)

    def create_response(self, response: str, new_state: Optional[str] = None, transfer_to: Optional[str] = None, data_updates: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        result = {"response": response}

        if new_state:
            result["new_state"] = new_state
        if transfer_to:
            result["transfer_to"] = transfer_to
        if data_updates:
            result["data_updates"] = data_updates

        for key, value in kwargs.items():
            if value is not None:
                result[key] = value
        return result

    def get_conversation_state(self, whatsapp_id: str) -> Dict[str, Any]:
        conversation = state_manager.get_conversation(whatsapp_id)
        if conversation:
            return {
                "whatsapp_id": conversation.whatsapp_id,
                "state": conversation.state,
                "customer_name": conversation.customer_name,
                "customer_needs": conversation.customer_needs,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at
            }
        return {}

    def update_conversation_state(self, whatsapp_id: str, updates: Dict[str, Any]):
        try:
            state_manager.update_conversation_state(
                whatsapp_id=whatsapp_id,
                **updates
            )
        except Exception as e:
            self.log_error("Error actualizando estado de conversación", e)

    def validate_message(self, message: str) -> bool:
        if not message or not message.strip():
            self.log_error("Mensaje vacío recibido")
            return False
        if len(message) > 4000:
            self.log_error("Mensaje demasiado largo", context={"length": len(message)})
            return False
        return True

    def is_question(self, message: str) -> bool:
        question_indicators = ["?", "qué", "cómo", "cuándo", "dónde", "por qué", "cuál"]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in question_indicators)

    def get_agent_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "initialized": self.initialized,
            "type": self.__class__.__name__
        }