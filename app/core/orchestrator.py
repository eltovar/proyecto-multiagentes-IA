
from typing import Dict, Any, List, Optional
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

        conversation = get_conversation_state(sender_id)
        if not conversation:
            update_conversation_state(sender_id, "NUEVO")
            conversation = get_conversation_state(sender_id)

        if conversation["state"] == STATE_TRANSFERIDO:
            self.log_action("Conversación transferida", "Ignorando mensaje - Humano al mando")
            return

        selected_agent = await self._select_agent(message_data, conversation)

        if not selected_agent:
            self.log_action("Error", "No se pudo seleccionar agente apropiado")
            await self._send_error_message(sender_id)
            return

        try:
            result = await selected_agent.process_message(message_data, conversation)

            await send_message(sender_id, result["response"])

            await self._update_conversation_state(sender_id, result)

            if result.get("transfer_to"):
                await self._handle_agent_transfer(message_data, conversation, result["transfer_to"])

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

    async def _handle_agent_transfer(self, message_data: Dict[str, Any], conversation: Dict[str, Any], target_agent_name: str) -> None:
        self.log_action("Transferencia de agente", f"Hacia: {target_agent_name}")

        if target_agent_name not in self.agents:
            self.log_action("Error", f"Agente {target_agent_name} no existe")
            return

        target_agent = self.agents[target_agent_name]

        try:
            result = await target_agent.process_message(message_data, conversation)

            sender_id = message_data["from"]
            await send_message(sender_id, result["response"])

            await self._update_conversation_state(sender_id, result)

        except Exception as e:
            self.log_action("Error en transferencia", str(e))
            await self._send_error_message(message_data["from"])

    async def _update_conversation_state(self, sender_id: str, result: Dict[str, Any]) -> None:
        update_conversation_state(
            whatsapp_id=sender_id,
            new_state=result["new_state"],
            data=result.get("data_updates", {})
        )

        self.log_action("Estado actualizado", f"Nuevo estado: {result['new_state']}")

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