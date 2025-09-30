
import time
from typing import Dict, Any, Optional
from app.agents.reception_agent import ReceptionAgent
from app.agents.support_agent import SupportAgent
from app.agents.leadsales_agent import LeadsalesAgent
from app.agents.base_agent import BaseAgent
from app.state.manager import get_conversation_state, update_conversation_state, STATE_TRANSFERIDO
from app.services.whatsapp_service import send_message

class AgentOrchestrator:

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "ReceptionAgent": ReceptionAgent(),
            "SupportAgent": SupportAgent(),
            "LeadsalesAgent": LeadsalesAgent()
        }

        self.agent_priority = ["ReceptionAgent", "SupportAgent", "LeadsalesAgent"]
        self.initialized = True

        self.log_action("Orquestador inicializado", f"Agentes disponibles: {list(self.agents.keys())}")

    async def process_message(self, message_data: Dict[str, Any]) -> None:
        sender_id = message_data["from"]
        user_message = message_data["text"]["body"]

        self.log_action("Mensaje recibido", f"De: {sender_id}, Mensaje: {user_message[:50]}...")

        # Obtener o crear conversación
        conversation = get_conversation_state(sender_id)
        if not conversation:
            update_conversation_state(sender_id, "NUEVO")
            conversation = get_conversation_state(sender_id)

        # Verificar Handoff Protocol
        if conversation["state"] == STATE_TRANSFERIDO:
            self.log_action("Conversación transferida", "Ignorando mensaje - Humano al mando")
            return

        # Seleccionar agente apropiado
        selected_agent = await self._select_agent(message_data, conversation)

        if not selected_agent:
            self.log_action("Error", "No se pudo seleccionar agente apropiado")
            await self._send_error_message(sender_id)
            return

        try:
            # Procesar mensaje con agente seleccionado
            result = await selected_agent.process_message(message_data, conversation)

            # CRÍTICO: Actualizar estado ANTES de procesar transferencia
            await self._update_conversation_state(sender_id, result)

            # Enviar respuesta
            await send_message(sender_id, result["response"])

            # Manejar transferencia si es necesaria
            if result.get("transfer_to"):
                transfer_metadata = result.get("transfer_metadata", {})
                await self._handle_agent_transfer(message_data, conversation,
                                                result["transfer_to"], transfer_metadata)

        except Exception as e:
            self.log_action("Error procesando mensaje", str(e))
            await self._send_error_message(sender_id)

    async def _select_agent(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Optional[BaseAgent]:
        for agent_name in self.agent_priority:
            agent = self.agents[agent_name]
            if await agent.can_handle(message_data, conversation):
                self.log_action("Agente seleccionado", agent_name)
                return agent

        return None

    async def _handle_agent_transfer(self, message_data: Dict[str, Any],
                                    conversation: Dict[str, Any], target_agent_name: str,
                                    transfer_metadata: Dict[str, Any] = None) -> None:
        """Transferencia robusta entre agentes con metadata"""

        self.log_action("Transferencia de agente", f"Hacia: {target_agent_name}")

        if target_agent_name not in self.agents:
            self.log_action("Error", f"Agente {target_agent_name} no existe")
            return

        # PASO 1: Actualizar metadata de transferencia en conversación
        sender_id = message_data["from"]
        transfer_data = {
            "current_agent": target_agent_name,
            "transfer_metadata": transfer_metadata or {},
            "last_transfer_time": time.time()
        }

        # PASO 2: Persistir cambios ANTES de transferir
        from app.state.manager import state_manager
        state_manager.update_conversation_state(sender_id, **transfer_data)

        # PASO 3: Obtener conversación actualizada
        updated_conversation = state_manager.get_conversation(sender_id)
        conversation_dict = {
            "whatsapp_id": updated_conversation.whatsapp_id,
            "state": updated_conversation.state,
            "customer_name": updated_conversation.customer_name,
            "customer_needs": updated_conversation.customer_needs,
            "current_agent": getattr(updated_conversation, 'current_agent', target_agent_name),
            "transfer_metadata": getattr(updated_conversation, 'transfer_metadata', {})
        }

        # PASO 4: Procesar con target agent usando conversación actualizada
        target_agent = self.agents[target_agent_name]

        try:
            result = await target_agent.process_message(message_data, conversation_dict)

            # PASO 5: Enviar respuesta y actualizar estado
            await send_message(sender_id, result["response"])
            await self._update_conversation_state(sender_id, result)

        except Exception as e:
            self.log_action("Error en transferencia", str(e))
            await self._send_error_message(sender_id)

    async def _update_conversation_state(self, sender_id: str, result: Dict[str, Any]) -> None:
        """Actualizar estado con validación robusta"""

        # Validar si hay cambios de estado
        new_state = result.get("new_state")
        data_updates = result.get("data_updates", {})

        if new_state:
            # Actualizar estado + datos
            update_conversation_state(
                whatsapp_id=sender_id,
                new_state=new_state,
                data=data_updates
            )
            self.log_action("Estado actualizado", f"Nuevo estado: {new_state}")
        elif data_updates:
            # Solo actualizar datos, mantener estado actual
            from app.state.manager import state_manager
            result = state_manager.update_conversation_state(
                whatsapp_id=sender_id,
                **data_updates
            )
            if result:
                self.log_action("Datos actualizados", f"Updates: {list(data_updates.keys())}")
            else:
                # Si falla, intentar crear conversación nueva
                update_conversation_state(
                    whatsapp_id=sender_id,
                    new_state="NUEVO",
                    data=data_updates
                )
                self.log_action("Conversación creada con datos", f"Updates: {list(data_updates.keys())}")

    async def _send_error_message(self, sender_id: str) -> None:
        error_msg = ("Disculpa, hay un problema técnico temporal. "
                    "Un asesor se comunicará contigo muy pronto. ¡Gracias por tu paciencia!")
        await send_message(sender_id, error_msg)

    def log_action(self, action: str, details: str = ""):
        print(f"[ORCHESTRATOR] {action}: {details}")

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "agents_count": len(self.agents),
            "agents": list(self.agents.keys())
        }

orchestrator = AgentOrchestrator()