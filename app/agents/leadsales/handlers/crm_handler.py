"""
CRMHandler for LeadsalesAgent
Extracted from leadsales_agent.py
Handles CRM operations, lead creation, and success/error responses
"""

from typing import Dict, Any
from app.config import STATE_LEAD_CREADO
from app.agents.leadsales.demo import DemoVisualizer


class CRMHandler:
    """Handles CRM operations and lead management"""

    def __init__(self, leadsales_service, whatsapp_oficial="324 551 6105", logger=None):
        self.leadsales_service = leadsales_service
        self.whatsapp_oficial = whatsapp_oficial
        self.logger = logger
        self._current_conversation = None
        self._current_whatsapp_id = None

    def set_conversation_context(self, conversation: Dict[str, Any], whatsapp_id: str):
        """Set current conversation context for CRM operations"""
        self._current_conversation = conversation
        self._current_whatsapp_id = whatsapp_id

    def log_action(self, message: str, metadata: Dict[str, Any] = None):
        """Simple logging - will delegate to agent's log_action if needed"""
        if self.logger:
            self.logger.log_action(message, metadata)
        else:
            print(f"[CRMHandler] {message}: {metadata or {}}")

    def log_error(self, message: str, exception: Exception = None):
        """Simple error logging - will delegate to agent's log_error if needed"""
        if self.logger:
            self.logger.log_error(message, exception)
        else:
            error_msg = f"[CRMHandler] {message}"
            if exception:
                error_msg += f" - {type(exception).__name__}: {str(exception)}"
            print(error_msg)

    async def proceed_to_crm_creation(self, complete_needs: str, customer_name: str) -> Dict[str, Any]:
        """Crear lead en CRM con información completa"""

        # Obtener whatsapp_id de la conversación o de metadata si está disponible
        whatsapp_id = self._current_conversation.get("whatsapp_id") if self._current_conversation else ""
        if not whatsapp_id:
            whatsapp_id = getattr(self, '_current_whatsapp_id', "")

        self.log_action("Starting CRM lead creation", {
            "customer": customer_name,
            "needs_length": len(complete_needs),
            "whatsapp_id": whatsapp_id[:10] + "..." if whatsapp_id else "N/A"
        })

        try:
            # Preparar datos adicionales del lead
            additional_data = {
                "lead_quality": "high",
                "capture_method": "conversational_ai",
                "information_completeness": "complete",
                "conversion_agent": "LeadsalesAgent",
                "customer_engagement": "active"
            }

            # Incluir información del flujo de recepción si está disponible
            if self._current_conversation:
                for key in ["tiene_contrato_inmobiliaria", "inmobiliaria_actual",
                           "tiene_solicitud_libertador", "fecha_necesidad"]:
                    if key in self._current_conversation:
                        additional_data[key] = self._current_conversation[key]

            # Crear lead en Leadsales CRM
            lead_result = await self.leadsales_service.create_lead(
                customer_name=customer_name,
                whatsapp_id=whatsapp_id,
                customer_needs=complete_needs,
                additional_data=additional_data
            )

            if lead_result.get("success", False):
                # Lead creado exitosamente
                return await self.handle_successful_lead_creation(customer_name, lead_result)
            else:
                # Error en creación de lead
                return await self.handle_lead_creation_error(customer_name, lead_result)

        except Exception as e:
            self.log_error("Error creando lead en CRM", e)
            return await self.handle_error_fallback(customer_name)

    async def handle_successful_lead_creation(self, customer_name: str, lead_result: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar creación exitosa de lead - Mensaje final de confirmación"""

        lead_id = lead_result.get("lead_id", lead_result.get("id", "N/A"))

        self.log_action("Lead created successfully", {
            "customer": customer_name,
            "lead_id": lead_id,
            "demo_mode": lead_result.get("demo_mode", False)
        })

        # DEMO VISUALIZATION
        if lead_result.get("demo_mode", False):
            DemoVisualizer.display_crm_preview(customer_name, lead_result)

        # Mensaje final con gestión de expectativas
        final_message = f"""¡Excelente {customer_name}! Con la información que me has dado, he creado un registro detallado para nuestro asesor.

Te contactarán en breve desde el {self.whatsapp_oficial} para continuar tu proceso de la mano.

¡Gracias por confiar en Inmobiliaria Proteger para hacer realidad tu proyecto inmobiliario!"""

        return {
            "response": final_message,
            "new_state": STATE_LEAD_CREADO,
            "data_updates": {
                "lead_id": lead_id,
                "lead_created": True,
                "conversion_completed": True,
                "demo_data": lead_result.get("customer_data"),  # Para debugging
                "final_stage": "success"
            }
        }

    async def handle_lead_creation_error(self, customer_name: str, lead_result: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar error en creación de lead"""

        self.log_error("Lead creation failed", None)

        error_message = f"""¡No te preocupes {customer_name}! Aunque hay un pequeño inconveniente técnico, he registrado toda tu información.

Nuestro equipo se pondrá en contacto contigo manualmente desde el {self.whatsapp_oficial} en las próximas horas.

¡Tu proyecto inmobiliario está en las mejores manos!"""

        return {
            "response": error_message,
            "new_state": "LEAD_ERROR",
            "data_updates": {
                "lead_error": True,
                "error_details": lead_result.get("error", "Unknown"),
                "manual_follow_up_required": True
            }
        }

    async def handle_error_fallback(self, customer_name: str) -> Dict[str, Any]:
        """Fallback en caso de error general"""

        self.log_error("General error fallback activated", None)

        fallback_message = f"""¡Tranquilo {customer_name}! He registrado tu interés en nuestros servicios.

Un especialista de nuestro equipo se comunicará contigo desde el {self.whatsapp_oficial} para continuar personalmente con tu proceso.

¡Gracias por elegirnos!"""

        return {
            "response": fallback_message,
            "new_state": "ERROR_FALLBACK",
            "data_updates": {"fallback_activated": True}
        }