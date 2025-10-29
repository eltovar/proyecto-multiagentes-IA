"""
ReceptionAgent - Stub Implementation
TODO: Implementar funcionalidad completa usando handlers y states
"""

from typing import Dict, Any, Awaitable, Callable
from datetime import datetime
from app.agents.base_agent import BaseAgent
from app.config.business_hours import BusinessHoursConfig
from app.agents.reception.states.conversation import ReceptionState


class ReceptionAgent(BaseAgent):
    """
    Agente de recepción para WhatsApp.

    Responsabilidades:
    - Validación de horario laboral
    - Captura inicial de datos (nombre, necesidades)
    - Presentación de políticas
    - Routing a SupportAgent o LeadsalesAgent
    """
    def __init__(self, llm_service=None, state_manager=None, rag_system=None, state_machine=None, handlers=None):
        """ Constructor del ReceptionAgent """
        super().__init__("reception", llm_service=llm_service, state_manager=state_manager)
        self.rag_system = rag_system
        self.state_machine = state_machine
        self.handlers = handlers or {}

        # Handlers disponibles vía factory
        self.greeting_handler = self.handlers.get('greeting')
        self.contract_handler = self.handlers.get('contract')
        self.lead_capture_handler = self.handlers.get('lead')

        # Contador de interacciones (para tests)
        self.interaction_count = 0

    async def process_message(
        self, message_data: Dict[str, Any], conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario usando arquitectura basada en handlers.

        Flujo:
        1. Extrae mensaje y estado actual
        2. Valida límite de interacciones (10 máx)
        3. Delega a _route_by_state para procesamiento específicos
        """
        message = message_data.get("text", {}).get("body", "")
        current_state = conversation.get("state", "NUEVO")

        # Incrementar contador de interacciones
        self.interaction_count += 1

        self.log_action(
            "Procesando mensaje",
            f"Estado: {current_state}, Interacción #{self.interaction_count}, Mensaje: {message[:50]}..."
        )

        # Validar límite de interacciones (seguridad anti-spam)
        if self.interaction_count >= 10:
            self.log_action(
                "Límite de interacciones alcanzado",
                f"Total: {self.interaction_count}"
            )

            result = await self.lead_capture_handler.handle_interaction_limit(
                conversation,
                self.interaction_count
            )
            return self._format_handler_result(result)

        # Routing dinámico por estado
        return await self._route_by_state(message, current_state, conversation)

    def _format_handler_result(
        self, result, current_state: str = None
    ) -> Dict[str, Any]:
        """
        Normaliza resultados de handlers a formato esperado.
        Integra validación FSM si se proporciona current_state.
        """
        # Normalización de formato
        if isinstance(result, dict):
            # Validación de formato
            if "response" not in result:
                self.log_action(
                    "WARNING: Handler devolvió resultado sin 'response'",
                    f"Keys presentes: {list(result.keys())}"
                )
            formatted = result
        else:
            # Soporte para GreetingResult, ContractResult, LeadCaptureResult
            formatted = {
                "response": getattr(result, 'response', ''),
                "new_state": getattr(result, 'next_state', None),
                "data_updates": getattr(result, 'metadata', {})
            }

            # LeadCaptureResult incluye transfer_to
            if hasattr(result, 'transfer_to'):
                formatted["transfer_to"] = result.transfer_to

            # Validación final
            if not formatted.get("response"):
                self.log_action(
                    "WARNING: Resultado formateado sin 'response' válida",
                    f"Result type: {type(result).__name__}"
                )

        # Validación FSM si se proporciona current_state
        if current_state is not None:
            new_state = formatted.get("new_state", current_state)
            formatted = self._validate_and_transition(current_state, new_state, formatted)

        return formatted

    def _validate_and_transition(
        self, current_state: str, new_state: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valida transición de estado usando ConversationStateMachine antes de aplicarla.
        """
        if new_state == current_state:
            self.log_action(
                "Sin cambio de estado",
                f"Estado: {current_state}"
            )
            return result

        # Validar transición con FSM
        if not self.state_machine:
            self.log_action(
                "WARNING: state_machine no disponible",
                "Permitiendo transición sin validación"
            )
            return result

        if self.state_machine.is_valid_transition(current_state, new_state):
            # Transición válida
            self.log_action(
                "✓ Transición FSM VÁLIDA",
                f"{current_state} → {new_state}"
            )
            return result
        else:
            # Transición inválida - Bloquear y loguear
            self.log_action(
                "✗ ERROR: Transición FSM INVÁLIDA bloqueada",
                f"Intento: {current_state} → {new_state}"
            )

            # Fallback de seguridad
            return {
                "response": "Disculpa, hubo un error en el flujo de conversación. Un asesor te ayudará en breve.",
                "new_state": current_state,  # Mantener estado actual
                "transfer_to": "support",
                "data_updates": {
                    "error": "invalid_fsm_transition",
                    "attempted_transition": f"{current_state} → {new_state}",
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _handle_unknown_state(self, current_state: str) -> Dict[str, Any]:
        """
        Fallback para estados no mapeados en el router.

        Estrategia defensiva:
        - Mantiene estado actual (evita romper flujo)
        - Registra error en logs
        - Solicita repetición al usuario
        """
        self.log_action(
            "Estado desconocido detectado",
            f"Estado sin handler: {current_state}"
        )

        return {
            "response": "Disculpa, hubo un error temporal. ¿Podrías repetir tu mensaje?",
            "new_state": current_state,  # Preservar estado actual
            "data_updates": {
                "error": "unknown_state",
                "problematic_state": current_state,
                "timestamp": datetime.now().isoformat()
            }
        }

    async def _handle_nuevo(
        self, message: str, conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handler para estado NUEVO - Primera interacción del usuario.

        Flujo:
        1. Valida horario laboral
        2. Si fuera de horario → mensaje automático + estado FUERA_DE_HORARIO
        3. Si en horario → delega a greeting_handler para saludo + políticas
        """
        # Validación de horario laboral
        if not BusinessHoursConfig.is_business_hours():
            self.log_action(
                "Mensaje fuera de horario",
                f"Interacción #{self.interaction_count}"
            )

            return {
                "response": BusinessHoursConfig.get_out_of_hours_message(),
                "new_state": "FUERA_DE_HORARIO",
                "data_updates": {
                    "business_hours_valid": False,
                    "checked_at": datetime.now().isoformat(),
                    "interaction_count": self.interaction_count
                }
            }

        # Dentro de horario → Saludo inicial con políticas
        self.log_action(
            "Iniciando saludo",
            f"Estado: NUEVO, Interacción #{self.interaction_count}"
        )

        result = await self.greeting_handler.handle_initial_greeting(
            conversation,
            self.interaction_count
        )

        return self._format_handler_result(result)

    async def _handle_name_collection(
        self, message: str, conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handler para captura de nombre del cliente.

        Estados aplicables:
        - POLITICAS_PRESENTADAS: Primera solicitud de nombre
        - RECOPILANDO_NOMBRE: Reintentos de captura

        Flujo:
        1. Intenta extraer nombre usando LLM
        2. Si éxito → confirma con handle_name_success
        3. Si falla → insiste con handle_name_request_fallback (máx 2 intentos)
        """
        self.log_action(
            "Capturando nombre",
            f"Mensaje: {message[:50]}..., Interacción #{self.interaction_count}"
        )

        # Intentar extracción con LLM
        name = await self.greeting_handler.extract_name_with_llm(
            message,
            conversation
        )

        if name:
            # Nombre extraído exitosamente
            self.log_action(
                "Nombre extraído",
                f"Nombre: {name}"
            )

            result = await self.greeting_handler.handle_name_success(
                name=name,
                interaction_count=self.interaction_count
            )
        else:
            # Fallback - solicitar nombre nuevamente
            attempt = conversation.get("name_capture_attempt", 0) + 1

            self.log_action(
                "Nombre no detectado - Fallback",
                f"Intento #{attempt}"
            )

            result = await self.greeting_handler.handle_name_request_fallback(
                conversation=conversation,
                interaction_count=self.interaction_count,
                attempt=attempt
            )

        return self._format_handler_result(result)

    async def _route_by_state(
        self, message: str, current_state: str, conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Router dinámico basado en el estado actual de la conversación.

        Orquesta handlers especializados según el estado:
        - Estados de saludo/nombre → GreetingHandler
        - Estados de contrato → ContractHandler
        - Estados de captura final → LeadCaptureHandler
        """
        self.log_action(
            "Routing por estado",
            f"Estado: {current_state}, Interacción #{self.interaction_count}"
        )

        # Mapa estado → handler (usando ReceptionState enum)
        router_map = {
            ReceptionState.NUEVO.value: lambda: self._handle_nuevo(message, conversation),

            ReceptionState.POLITICAS_PRESENTADAS.value: lambda: self._handle_name_collection(message, conversation),

            ReceptionState.RECOPILANDO_NOMBRE.value: lambda: self._handle_name_collection(message, conversation),

            ReceptionState.NOMBRE_OBTENIDO.value: lambda: self.contract_handler.handle_contract_question(
                conversation, self.interaction_count
            ),

            ReceptionState.PREGUNTA_CONTRATO_INMOBILIARIA.value: lambda: self.contract_handler.handle_contract_response(
                message, conversation, self.interaction_count
            ),

            ReceptionState.PREGUNTA_CUAL_INMOBILIARIA.value: lambda: self.contract_handler.handle_which_company_response(
                message, conversation, self.interaction_count
            ),

            ReceptionState.PREGUNTA_SOLICITUD_LIBERTADOR.value: lambda: self.contract_handler.handle_libertador_response(
                message, conversation, self.interaction_count
            ),

            ReceptionState.PREGUNTA_FECHA_NECESIDAD.value: lambda: self.lead_capture_handler.handle_date_response(
                message, conversation, self.interaction_count
            ),
        }

        # Obtener handler para estado actual
        handler = router_map.get(current_state)

        if not handler:
            self.log_action(
                "Routing Fallback: Estado sin Handler",
                f"Estado: {current_state}"
            )
            # Transferencia de emergencia
            return self.create_response(
                "Disculpa, tu solicitud ha caído en un estado inesperado. Un asesor te ayudará.",
                new_state=current_state,
                transfer_to="support"
            )

        # Ejecutar handler (todos son async)
        result = await handler()

        # Normalizar resultado y validar transición FSM
        # La validación FSM está integrada en _format_handler_result
        return self._format_handler_result(result, current_state=current_state)

    def create_response(
        self,
        response: str,
        new_state: str = None,
        transfer_to: str = None,
        data_updates: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Helper para crear respuestas estructuradas"""
        result = {"response": response}

        if new_state:
            result["new_state"] = new_state
        if transfer_to:
            result["transfer_to"] = transfer_to
        if data_updates:
            result["data_updates"] = data_updates

        return result
