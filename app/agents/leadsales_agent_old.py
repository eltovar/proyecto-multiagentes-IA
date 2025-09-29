'''
    Especialista en CRM - Creacion de lead y handoff a asesor humano.
    Integra con Leadsales via API para crear leads automaticamente.
'''

from typing import Dict, Any
from .base_agent import BaseAgent
from app.services.leadsales_service import LeadsalesService
from app.state.manager import STATE_LISTO_PARA_TRANSFERIR, STATE_TRANSFERIDO

class LeadsalesAgent(BaseAgent):

    def __init__(self):
        super().__init__("LeadsalesAgent")
        self.leadsales_service = LeadsalesService()

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        return False

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        self.log_action("Iniciando creación de lead en Leadsales")

        customer_name = conversation.get("customer_name", "No proporcionado")
        customer_needs = conversation.get("customer_needs", "")
        whatsapp_id = message_data["from"]

        try:
            # lead_data solo para datos adicionales si se requieren
            lead_result = await self.leadsales_service.create_lead(
                customer_name,
                whatsapp_id,
                customer_needs,
                None # o algún diccionario si tienes datos extra
                )

            self.log_action("Lead creado exitosamente", f"ID: {lead_result.get('id', 'N/A')}")

            handoff_message = (f"¡Perfecto, {customer_name}! 🎉\n\n"
                             f"He registrado tu solicitud en nuestro sistema. "
                             f"Un especialista de nuestro equipo se pondrá en contacto contigo "
                             f"desde este mismo número en los próximos minutos.\n\n"
                             f"¡Gracias por confiar en nosotros!")

            return {
                "response": handoff_message,
                "new_state": STATE_TRANSFERIDO,
                "data_updates": {
                    "lead_id": lead_result.get("id"),
                    "handoff_activated": True
                },
                "transfer_to": None
            }

        except Exception as e:
            self.log_error("Error creando lead", e)

            error_message = (f"Disculpa, {customer_name}. "
                           f"Hay un problema técnico temporal. "
                           f"Un asesor se comunicará contigo manualmente muy pronto. "
                           f"¡Gracias por tu paciencia!")

            return {
                "response": error_message,
                "new_state": conversation["state"],
                "data_updates": {"error_occurred": True},
                "transfer_to": None
            }