"""
Orchestrator basado en Factory Pattern.
Crea agentes fresh en cada request = hot reload automático.
"""

import time
from typing import Dict, Any, Optional
from app.core.agent_factory import AgentFactoryRegistry
from app.core.service_container import ServiceContainer
from app.state.manager import get_conversation_state, update_conversation_state, STATE_TRANSFERIDO
from app.services.whatsapp_service import send_message


class FactoryOrchestrator:
    """
    Orchestrator que usa Factory Pattern para crear agentes fresh.
    No mantiene instancias de agentes en memoria → hot reload natural.
    """

    def __init__(self, container: Optional['DIContainer'] = None):
        """
        Args:
            container: DIContainer opcional. Si no se provee, usa ServiceContainer por defecto.
        """
        # Factory registry
        self.factory_registry = AgentFactoryRegistry()

        # Service container (servicios compartidos, NO se recargan)
        # Si se provee DIContainer, usarlo; sino, usar ServiceContainer legacy
        if container is not None:
            self.di_container = container
            self.service_container = None  # No usar ServiceContainer si hay DIContainer
        else:
            self.di_container = None
            self.service_container = ServiceContainer()

        # Prioridad de agentes
        self.agent_priority = ["SupportAgent", "ReceptionAgent", "LeadsalesAgent"]

        self.initialized = True
        self.log_action("FactoryOrchestrator inicializado",
                       f"Factories: {list(self.factory_registry._factories.keys())}")

    async def process_message(self, message_data: Dict[str, Any]) -> None:
        """
        Procesa mensaje creando agente fresh para cada request.
        = HOT RELOAD AUTOMÁTICO sin comandos ni watchdog.
        """
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
            self.log_action("Conversación transferida", "Ignorando - Humano al mando")
            return

        # ✅ Seleccionar agente (crea instancia FRESH)
        selected_agent = await self._select_agent(message_data, conversation)

        if not selected_agent:
            self.log_action("Error", "No se pudo seleccionar agente")
            await self._send_error_message(sender_id)
            return

        try:
            # Procesar mensaje
            result = await selected_agent.process_message(message_data, conversation)

            # Actualizar estado ANTES de transferencia
            await self._update_conversation_state(sender_id, result)

            # Enviar respuesta
            await send_message(sender_id, result["response"])

            # Manejar transferencia
            if result.get("transfer_to"):
                transfer_metadata = result.get("data_updates", {})
                await self._handle_agent_transfer(message_data, conversation,
                                                result["transfer_to"], transfer_metadata)

        except Exception as e:
            self.log_action("Error procesando mensaje", str(e))
            await self._send_error_message(sender_id)

    def get_agent(self, agent_name: str):
        """
        Obtiene agente por nombre (para tests y uso directo).
        Crea instancia FRESH usando Factory Pattern.

        Args:
            agent_name: Nombre del agente ("reception", "support", "leadsales")
        """
        # Mapeo de nombres legacy a nombres Factory
        factory_name_map = {
            "reception": "ReceptionAgent",
            "support": "SupportAgent",
            "leadsales": "LeadsalesAgent"
        }

        factory_name = factory_name_map.get(agent_name, agent_name)
        shared_services = self._get_shared_services()
        return self.factory_registry.create_agent(factory_name, shared_services)

    def _get_shared_services(self) -> Dict[str, Any]:
        """Obtiene servicios compartidos desde DIContainer o ServiceContainer"""
        if self.di_container:
            return self.di_container.get_all_services()
        else:
            return self.service_container.get_all_services()

    def select_agent(self, message: str, state: 'ConversationState'):
        """ Método síncrono simplificado para seleccionar agente (tests y uso directo)."""
        shared_services = self._get_shared_services()

        # Extraer atributos de ConversationState
        current_agent = getattr(state, 'current_agent', None)
        metadata = getattr(state, 'metadata', {})

        # Decisión basada en metadata y current_agent
        selected_agent_name = None

        # 1. Primer contacto (current_agent=None) → ReceptionAgent
        if current_agent is None:
            selected_agent_name = "ReceptionAgent"

        # 2. Metadata indica intención de conversión → LeadsalesAgent
        elif metadata.get("conversion_intent") or metadata.get("lead_qualified"):
            selected_agent_name = "LeadsalesAgent"

        # 3. Metadata indica pregunta informativa → SupportAgent
        elif metadata.get("last_intent") == "question":
            selected_agent_name = "SupportAgent"

        # 4. Mantener agente actual si existe (mapeo legacy → clase)
        elif current_agent:
            agent_map = {
                "reception": "ReceptionAgent",
                "support": "SupportAgent",
                "leadsales": "LeadsalesAgent",
                "ReceptionAgent": "ReceptionAgent",
                "SupportAgent": "SupportAgent",
                "LeadsalesAgent": "LeadsalesAgent"
            }
            selected_agent_name = agent_map.get(current_agent, "ReceptionAgent")

        # 5. Fallback: ReceptionAgent
        else:
            selected_agent_name = "ReceptionAgent"

        # Crear instancia fresh
        try:
            agent = self.factory_registry.create_agent(selected_agent_name, shared_services)
            return agent
        except Exception as e:
            print(f"[FactoryOrchestrator] Error creando {selected_agent_name}: {e}")
            # Fallback a ReceptionAgent si falla
            return self.factory_registry.create_agent("ReceptionAgent", shared_services)

    async def _select_agent(self, message_data: Dict[str, Any], conversation: Dict[str, Any]):
        """Lógica avanzada para seleccionar agente basado en estado y metadata"""
        shared_services = self._get_shared_services()
        current_state = conversation.get("state", "NUEVO")
        current_agent = conversation.get("current_agent")

        # Decisión directa basada en estado de conversación
        selected_agent_name = None

        # 1. Primer contacto o estado NUEVO → ReceptionAgent (prioridad por defecto)
        if current_state == "NUEVO" or current_agent is None:
            selected_agent_name = "ReceptionAgent"
            self.log_action("Selección", "Primer contacto → ReceptionAgent")

        # 2. Estados de conversión (LeadsalesAgent)
        elif current_state in ["FLUJO_COMPLETADO", "CAPTURANDO_DETALLES",
                              "PROFUNDIZANDO_NECESIDAD", "CONFIRMANDO_INFORMACION",
                              "PROCESANDO_CRM"]:
            selected_agent_name = "LeadsalesAgent"
            self.log_action("Selección", f"Estado conversión ({current_state}) → LeadsalesAgent")

        # 3. Transferencia explícita → usar target agent
        elif current_state == "TRANSFERIDO":
            transfer_to = conversation.get("transfer_metadata", {}).get("to_agent")
            if transfer_to in ["SupportAgent", "ReceptionAgent", "LeadsalesAgent"]:
                selected_agent_name = transfer_to
                self.log_action("Selección", f"Transferencia → {transfer_to}")
            else:
                # Fallback si transfer_to no es válido
                selected_agent_name = "SupportAgent"
                self.log_action("Selección", f"Transferencia inválida → SupportAgent (fallback)")

        # 4. Estados activos de SupportAgent
        elif current_state in ["CONSULTANDO", "CONSULTA_RAG", "ESPERANDO_PREGUNTA"]:
            selected_agent_name = "SupportAgent"
            self.log_action("Selección", f"Estado consulta ({current_state}) → SupportAgent")

        # 5. Estados de ReceptionAgent
        elif current_state in ["CAPTURANDO_NOMBRE", "CAPTURANDO_NECESIDAD",
                              "CLASIFICANDO_INTENCION", "DECIDIENDO_RUTA"]:
            selected_agent_name = "ReceptionAgent"
            self.log_action("Selección", f"Estado recepción ({current_state}) → ReceptionAgent")

        # 6. Mantener agente actual si ya está asignado
        elif current_agent in ["SupportAgent", "ReceptionAgent", "LeadsalesAgent"]:
            selected_agent_name = current_agent
            self.log_action("Selección", f"Continuar en {current_agent} (estado: {current_state})")

        # 7. Fallback: SupportAgent (más robusto que None)
        else:
            selected_agent_name = "SupportAgent"
            self.log_action("Selección", f"Estado desconocido ({current_state}) → SupportAgent (fallback)")

        # Crear instancia FRESH del agente seleccionado
        try:
            agent = self.factory_registry.create_agent(selected_agent_name, shared_services)
            self.log_action("Agente creado (fresh)", selected_agent_name)
            return agent
        except Exception as e:
            self.log_action("Error creando agente", f"{selected_agent_name}: {str(e)}")
            return None

    async def _handle_agent_transfer(self, message_data: Dict[str, Any],
                                    conversation: Dict[str, Any], target_agent_name: str,
                                    transfer_metadata: Dict[str, Any] = None) -> None:
        """Transferencia entre agentes (crea instancia fresh del target)"""
        self.log_action("Transferencia de agente", f"Hacia: {target_agent_name}")

        # Actualizar metadata de transferencia
        sender_id = message_data["from"]
        transfer_data = {
            "current_agent": target_agent_name,
            "transfer_metadata": transfer_metadata or {},
            "last_transfer_time": time.time()
        }

        # Persistir cambios
        from app.state.manager import state_manager
        state_manager.update_conversation_state(sender_id, **transfer_data)

        # Obtener conversación actualizada
        updated_conversation = state_manager.get_conversation(sender_id)
        conversation_dict = {
            "whatsapp_id": updated_conversation.whatsapp_id,
            "state": updated_conversation.state,
            "customer_name": updated_conversation.customer_name,
            "customer_needs": updated_conversation.customer_needs,
            "current_agent": getattr(updated_conversation, 'current_agent', target_agent_name),
            "transfer_metadata": getattr(updated_conversation, 'transfer_metadata', {})
        }

        # ✅ Crear instancia FRESH del target agent
        shared_services = self._get_shared_services()
        target_agent = self.factory_registry.create_agent(target_agent_name, shared_services)

        try:
            result = await target_agent.process_message(message_data, conversation_dict)

            await send_message(sender_id, result["response"])
            await self._update_conversation_state(sender_id, result)

        except Exception as e:
            self.log_action("Error en transferencia", str(e))
            await self._send_error_message(sender_id)

    async def _update_conversation_state(self, sender_id: str, result: Dict[str, Any]) -> None:
        """Actualizar estado con validación robusta"""
        new_state = result.get("new_state")
        data_updates = result.get("data_updates", {})

        if new_state:
            update_conversation_state(
                whatsapp_id=sender_id,
                new_state=new_state,
                data=data_updates
            )
            self.log_action("Estado actualizado", f"Nuevo estado: {new_state}")
        elif data_updates:
            from app.state.manager import state_manager
            state_result = state_manager.update_conversation_state(
                whatsapp_id=sender_id,
                **data_updates
            )
            if state_result:
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
                    "Un asesor se comunicará contigo muy pronto.")
        await send_message(sender_id, error_msg)

    def log_action(self, action: str, details: str = ""):
        print(f"[FACTORY-ORCHESTRATOR] {action}: {details}")

    def health_check(self) -> Dict[str, Any]:
        """Health check incluyendo servicios"""
        # Health check de servicios según el container usado
        if self.di_container:
            services_health = self.di_container.health_check()
        else:
            services_health = self.service_container.health_check()

        return {
            "status": "healthy",
            "orchestrator": "factory_based",
            "factories_registered": len(self.factory_registry._factories),
            "container_type": "DIContainer" if self.di_container else "ServiceContainer",
            "services": services_health
        }
