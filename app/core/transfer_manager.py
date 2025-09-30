"""Gestion de transferencias entre agentes - Maximo 60 lineas"""

from typing import Dict, Any
from app.utils.error_logger import log_error, log_info

class TransferManager:
    """Maneja transferencias entre agentes"""

    def __init__(self, agent_manager):
        self.agent_manager = agent_manager

    async def handle_transfer(
        self,
        agent_response: Dict[str, Any],
        conversation,
        whatsapp_id: str
    ) -> Dict[str, Any]:
        """Ejecuta transferencia entre agentes"""

        transfer_to = agent_response.get("transfer_to")
        if not transfer_to:
            return {"status": "no_transfer", "message": "Sin transferencia solicitada"}

        print(f"[TransferManager] Procesando transferencia a: {transfer_to}")

        # En FASE 1A, solo reception disponible
        if transfer_to not in ["reception"]:
            print(f"[TransferManager] Transferencia a {transfer_to} no disponible en FASE 1A")
            return {
                "status": "transfer_deferred",
                "message": f"Transferencia a {transfer_to} sera implementada en fases posteriores",
                "response": "Un asesor especializado se pondra en contacto contigo pronto."
            }

        # Verificar que el agente destino exista
        target_agent = self.agent_manager.get_agent(transfer_to)
        if not target_agent:
            print(f"[TransferManager] Agente destino '{transfer_to}' no existe")
            return {
                "status": "transfer_error",
                "message": f"Agente {transfer_to} no disponible"
            }

        # Ejecutar transferencia
        try:
            transfer_message = agent_response.get("transfer_message", "")
            transfer_response = await target_agent.process_message(
                transfer_message, conversation
            )

            print(f"[TransferManager] Transferencia a {transfer_to} exitosa")
            return {
                "status": "transferred",
                "from_agent": "previous",
                "to_agent": transfer_to,
                "response": transfer_response.get("response"),
                "new_state": transfer_response.get("new_state"),
                "handoff_activated": transfer_response.get("handoff_activated", False)
            }

        except Exception as e:
            log_error("TransferManager", "Error en transferencia", e, {"transfer_to": transfer_to})
            return {
                "status": "transfer_error",
                "message": f"Error transfiriendo a {transfer_to}: {str(e)}"
            }

    def can_transfer_to(self, agent_name: str) -> bool:
        """Verifica si se puede transferir a un agente"""
        return self.agent_manager.get_agent(agent_name) is not None