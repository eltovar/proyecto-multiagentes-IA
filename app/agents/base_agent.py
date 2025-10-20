'''
    Clase base para todos los agentes.
    Define interfaz comun, loggin, estructura de respuesta y manejo de estado.
'''

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):

    def __init__(self, name: str, llm_service=None, state_manager=None):
        self.name = name
        self.agent_name = name  

        self._llm_service = llm_service
        self._state_manager = state_manager

        self.initialized = True

    @property
    def llm_service(self):
      
        if self._llm_service is not None:
            return self._llm_service
        try:
            from app.services.llm_service import llm_service
            return llm_service
        except ImportError:
            return None

    @llm_service.setter
    def llm_service(self, value):
        """Permite inyección de llm_service después de __init__"""
        self._llm_service = value

    @property
    def state_manager(self):
        
        if self._state_manager is not None:
            return self._state_manager

        try:
            from app.state.manager import state_manager
            return state_manager
        except ImportError:
            return None

    @state_manager.setter
    def state_manager(self, value):
        """Permite inyección de state_manager después de __init__"""
        self._state_manager = value

    #orquestador decide ruteo
    @abstractmethod
    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        pass
    
    #lógica de cada agente
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

    def create_response(self, response: str, new_state: Optional[str] = None,
                       transfer_to: Optional[str] = None, data_updates: Optional[Dict[str, Any]] = None,
                       **kwargs) -> Dict[str, Any]:
        """Respuesta estandarizada con validación"""

        result = {"response": response}

        # SIEMPRE incluir new_state (actual si no hay cambio)
        if new_state:
            result["new_state"] = new_state
        # Si no hay new_state pero hay conversación activa, mantener estado actual

        if transfer_to:
            result["transfer_to"] = transfer_to
            # CRÍTICO: Incluir metadata de transferencia
            transfer_reason = kwargs.get("transfer_reason", "agent_specialization")
            result["transfer_metadata"] = {
                "from_agent": self.name,
                "to_agent": transfer_to,
                "reason": transfer_reason
            }

        if data_updates:
            result["data_updates"] = data_updates

        # Agregar kwargs adicionales (excluyendo transfer_reason que ya se usó)
        for key, value in kwargs.items():
            if value is not None and key != "transfer_reason":
                result[key] = value

        return result

    def get_conversation_state(self, whatsapp_id: str) -> Dict[str, Any]:
        """Usa state_manager inyectado o global"""
        conversation = self.state_manager.get_conversation(whatsapp_id)
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
        """Usa state_manager inyectado o global"""
        try:
            self.state_manager.update_conversation_state(
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

    def get_agent_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "initialized": self.initialized,
            "type": self.__class__.__name__
        }