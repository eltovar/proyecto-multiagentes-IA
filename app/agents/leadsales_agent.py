'''
    LeadsalesAgent - Refactorizado con nuevo prompt especializado
    Responsabilidades: Captación de información específica, Conversión CRM, Procesamiento de leads
    Personalidad: Sofia (altamente enfocado, profesional, motivador)
'''

from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from app.services.leadsales_service import LeadsalesService

# Estados específicos del proceso de conversión
STATE_CAPTURANDO_DETALLES = "CAPTURANDO_DETALLES"
STATE_PROFUNDIZANDO_NECESIDAD = "PROFUNDIZANDO_NECESIDAD"
STATE_CONFIRMANDO_INFORMACION = "CONFIRMANDO_INFORMACION"
STATE_PROCESANDO_CRM = "PROCESANDO_CRM"
STATE_LEAD_CREADO = "LEAD_CREADO"

class LeadsalesAgent(BaseAgent):

    def __init__(self):
        super().__init__("LeadsalesAgent")
        self.leadsales_service = LeadsalesService()
        self.whatsapp_oficial = "324 551 6105"

        # Inicializar servicio Leadsales
        self.leadsales_service.initialize()

        # Inicializar LLM para generación de respuestas motivadoras
        if self.llm_service and not self.llm_service.api_client.initialized:
            self.llm_service.initialize()

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        """
        LeadsalesAgent maneja cuando:
        1. Transfer desde ReceptionAgent (flujo completado)
        2. Transfer desde SupportAgent (consulta inmueble específico)
        3. Estados de conversión en progreso
        """
        current_state = conversation.get("state", "")

        # CASO 1: Estado TRANSFERIDO + metadata de transferencia a LeadsalesAgent
        if current_state == "TRANSFERIDO":
            transfer_metadata = conversation.get("transfer_metadata", {})
            return transfer_metadata.get("to_agent") == "LeadsalesAgent"

        # CASO 2: Estados específicos de conversión (sin TRANSFERIDO)
        conversion_states = [
            "FLUJO_COMPLETADO",           # Desde ReceptionAgent
            "CAPTURANDO_DETALLES",        # En proceso conversión
            "PROFUNDIZANDO_NECESIDAD",
            "CONFIRMANDO_INFORMACION",
            "PROCESANDO_CRM"
        ]

        return current_state in conversion_states

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa mensaje enfocado en conversión y captación de información específica"""
        user_message = message_data.get("text", {}).get("body", "").strip()
        whatsapp_id = message_data.get("from")
        customer_name = conversation.get("customer_name", "")

        if not self.validate_message(user_message):
            return self.create_response("Por favor, envía un mensaje válido.")

        self.log_action("LeadsalesAgent procesando lead", {
            "customer": customer_name or "Anónimo",
            "message_preview": user_message[:50],
            "state": conversation.get("state", "N/A")
        })

        # Guardar referencia a conversación y whatsapp_id
        self._current_conversation = conversation
        self._current_whatsapp_id = whatsapp_id

        try:
            current_state = conversation.get("state", "TRANSFERIDO")

            # Máquina de estados de conversión
            if current_state in ["TRANSFERIDO", "FLUJO_COMPLETADO"]:
                return await self._handle_initial_engagement(customer_name, conversation)
            elif current_state == STATE_CAPTURANDO_DETALLES:
                return await self._handle_detail_capture(user_message, customer_name)
            elif current_state == STATE_PROFUNDIZANDO_NECESIDAD:
                return await self._handle_need_deepening(user_message, customer_name)
            elif current_state == STATE_CONFIRMANDO_INFORMACION:
                return await self._handle_information_confirmation(user_message, customer_name)
            else:
                # Estado no reconocido, empezar desde inicial
                return await self._handle_initial_engagement(customer_name, conversation)

        except Exception as e:
            self.log_error("Error en LeadsalesAgent", e)
            return await self._handle_error_fallback(customer_name)

    async def _handle_initial_engagement(self, customer_name: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Engagement inicial altamente motivador para obtener información específica"""

        # Verificar si ya tenemos información básica de la necesidad
        customer_needs = conversation.get("customer_needs", "")

        if customer_needs and len(customer_needs.strip()) > 10:
            # Tenemos información básica, profundizar
            response = await self._generate_deepening_response(customer_name, customer_needs)
            new_state = STATE_PROFUNDIZANDO_NECESIDAD
        else:
            # No tenemos información, capturar detalles iniciales
            response = await self._generate_initial_capture_response(customer_name)
            new_state = STATE_CAPTURANDO_DETALLES

        return self.create_response(
            response,
            new_state=new_state,
            data_updates={"conversion_stage": "initial_engagement"}
        )

    async def _generate_initial_capture_response(self, customer_name: str) -> str:
        """Generar respuesta inicial altamente motivadora para captar información"""
        motivational_responses = [
            f"¡Excelente {customer_name}! Me emociona poder ayudarte con tu proyecto inmobiliario. Para conectarte con el asesor perfecto que haga realidad tu sueño, cuéntame: ¿Qué tipo de inmueble estás buscando y en qué zona te gustaría que estuviera?",

            f"¡Perfecto {customer_name}! Estás a un paso de encontrar tu inmueble ideal. Para asegurarme de que nuestro especialista tenga todo listo para ti, necesito conocer: ¿Buscas comprar, vender o arrendar? ¿Y qué características debe tener tu inmueble perfecto?",

            f"¡Increíble {customer_name}! Tu timing es perfecto. Para que nuestro equipo te prepare las mejores opciones desde ya, compárteme: ¿Qué inmueble tienes en mente y cuál es tu zona de interés principal?"
        ]

        import random
        return random.choice(motivational_responses)

    async def _generate_deepening_response(self, customer_name: str, existing_needs: str) -> str:
        """Generar respuesta para profundizar en necesidad ya conocida"""

        # Usar LLM para generar respuesta contextual y motivadora
        if self.llm_service and self.llm_service.api_client.initialized:
            try:
                deepening_prompt = f"""
                El cliente {customer_name} ya expresó: "{existing_needs}"

                Genera una respuesta altamente motivadora para obtener MÁS detalles específicos como:
                - Número de habitaciones/baños
                - Rango de presupuesto
                - Zona específica o características especiales
                - Timeframe de necesidad

                Usa un tono profesional pero emocionante que genere leads de alta calidad.
                Máximo 2 líneas.
                """

                response = await self.llm_service.llm_generator.generate_contextual_response(
                    user_question=deepening_prompt,
                    context=f"Cliente: {customer_name}, Necesidad: {existing_needs}",
                    customer_name=customer_name
                )

                return response

            except Exception as e:
                self.log_error("Error generando respuesta de profundización", e)

        # Fallback: respuesta estática
        return f"¡Perfecto {customer_name}! Para asegurarme de que nuestro asesor tenga exactamente lo que buscas, cuéntame más detalles: ¿cuántas habitaciones necesitas, en qué rango de presupuesto estás pensando y hay alguna zona específica de tu preferencia?"

    async def _handle_detail_capture(self, user_message: str, customer_name: str) -> Dict[str, Any]:
        """Capturar detalles específicos de la necesidad"""

        # Analizar si el mensaje contiene información útil
        has_sufficient_info = await self._analyze_information_completeness(user_message)

        if has_sufficient_info:
            # Información suficiente, proceder a CRM
            return await self._proceed_to_crm_creation(user_message, customer_name)
        else:
            # Necesita más información específica
            response = await self._generate_follow_up_question(user_message, customer_name)
            return self.create_response(
                response,
                new_state=STATE_PROFUNDIZANDO_NECESIDAD,
                data_updates={
                    "partial_needs": user_message,
                    "conversion_stage": "capturing_details"
                }
            )

    async def _handle_need_deepening(self, user_message: str, customer_name: str) -> Dict[str, Any]:
        """Profundizar en la necesidad para obtener información de alta calidad"""

        # Consolidar información existente
        existing_needs = self._current_conversation.get("customer_needs", "")
        partial_needs = self._current_conversation.get("partial_needs", "")

        consolidated_info = f"{existing_needs} {partial_needs} {user_message}".strip()

        # Verificar si ya tenemos suficiente información para crear lead de calidad
        is_complete = await self._analyze_information_completeness(consolidated_info)

        if is_complete:
            return await self._proceed_to_crm_creation(consolidated_info, customer_name)
        else:
            # Una pregunta más específica para cerrar la información
            final_question = await self._generate_final_capture_question(consolidated_info, customer_name)
            return self.create_response(
                final_question,
                new_state=STATE_CONFIRMANDO_INFORMACION,
                data_updates={
                    "consolidated_needs": consolidated_info,
                    "conversion_stage": "final_capture"
                }
            )

    async def _handle_information_confirmation(self, user_message: str, customer_name: str) -> Dict[str, Any]:
        """Confirmación final de información antes de crear lead"""

        # Consolidar toda la información
        final_needs = self._current_conversation.get("consolidated_needs", "") + " " + user_message

        # Proceder directamente a crear lead
        return await self._proceed_to_crm_creation(final_needs.strip(), customer_name)

    async def _proceed_to_crm_creation(self, complete_needs: str, customer_name: str) -> Dict[str, Any]:
        """Crear lead en CRM con información completa"""

        # Obtener whatsapp_id de la conversación o de metadata si está disponible
        whatsapp_id = self._current_conversation.get("whatsapp_id") or getattr(self, '_current_whatsapp_id', "")

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
                return await self._handle_successful_lead_creation(customer_name, lead_result)
            else:
                # Error en creación de lead
                return await self._handle_lead_creation_error(customer_name, lead_result)

        except Exception as e:
            self.log_error("Error creando lead en CRM", e)
            return await self._handle_error_fallback(customer_name)

    async def _handle_successful_lead_creation(self, customer_name: str, lead_result: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar creación exitosa de lead - Mensaje final de confirmación"""

        lead_id = lead_result.get("lead_id", lead_result.get("id", "N/A"))

        # DEMO VISUALIZATION
        if lead_result.get("demo_mode", False):
            await self._display_demo_crm_preview(customer_name, lead_result)

        # Mensaje final con gestión de expectativas
        final_message = f"""¡Excelente {customer_name}! Con la información que me has dado, he creado un registro detallado para nuestro asesor.

Te contactarán en breve desde el {self.whatsapp_oficial} para continuar tu proceso de la mano.

¡Gracias por confiar en Inmobiliaria Proteger para hacer realidad tu proyecto inmobiliario!"""

        return self.create_response(
            final_message,
            new_state=STATE_LEAD_CREADO,
            data_updates={
                "lead_id": lead_id,
                "lead_created": True,
                "conversion_completed": True,
                "demo_data": lead_result.get("customer_data"),  # Para debugging
                "final_stage": "success"
            }
        )

    async def _handle_lead_creation_error(self, customer_name: str, lead_result: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar error en creación de lead"""

        error_message = f"""¡No te preocupes {customer_name}! Aunque hay un pequeño inconveniente técnico, he registrado toda tu información.

Nuestro equipo se pondrá en contacto contigo manualmente desde el {self.whatsapp_oficial} en las próximas horas.

¡Tu proyecto inmobiliario está en las mejores manos!"""

        return self.create_response(
            error_message,
            new_state="LEAD_ERROR",
            data_updates={
                "lead_error": True,
                "error_details": lead_result.get("error", "Unknown"),
                "manual_follow_up_required": True
            }
        )

    async def _handle_error_fallback(self, customer_name: str) -> Dict[str, Any]:
        """Fallback en caso de error general"""

        fallback_message = f"""¡Tranquilo {customer_name}! He registrado tu interés en nuestros servicios.

Un especialista de nuestro equipo se comunicará contigo desde el {self.whatsapp_oficial} para continuar personalmente con tu proceso.

¡Gracias por elegirnos!"""

        return self.create_response(
            fallback_message,
            data_updates={"fallback_activated": True}
        )

    async def _analyze_information_completeness(self, message: str) -> bool:
        """Analizar si el mensaje contiene información suficiente para crear lead de calidad"""

        message_lower = message.lower()

        # Criterios de completitud para lead de alta calidad
        quality_indicators = {
            "property_type": ["apartamento", "casa", "local", "oficina", "lote", "finca"],
            "transaction_type": ["comprar", "vender", "arrendar", "alquilar"],
            "location": ["zona", "sector", "barrio", "poblado", "centro", "norte", "sur"],
            "specs": ["habitacion", "baño", "metro", "piso", "parqueadero"],
            "budget": ["presupuesto", "precio", "valor", "millones", "pesos"]
        }

        categories_found = 0
        for category, keywords in quality_indicators.items():
            if any(keyword in message_lower for keyword in keywords):
                categories_found += 1

        # Considerar completo si tiene al menos 2 categorías de información
        return categories_found >= 2

    async def _generate_follow_up_question(self, partial_info: str, customer_name: str) -> str:
        """Generar pregunta de seguimiento para obtener más información específica"""

        follow_up_questions = [
            f"¡Perfecto {customer_name}! Para que nuestro asesor tenga exactamente lo que buscas, ¿podrías contarme en qué zona te gustaría que estuviera y cuántas habitaciones necesitas?",

            f"¡Excelente {customer_name}! Me estás dando información muy valiosa. ¿Cuál es tu rango de presupuesto aproximado y hay alguna característica especial que sea importante para ti?",

            f"¡Genial {customer_name}! Para preparar las mejores opciones, ¿para cuándo necesitarías el inmueble y qué zona sería tu primera opción?"
        ]

        import random
        return random.choice(follow_up_questions)

    async def _generate_final_capture_question(self, existing_info: str, customer_name: str) -> str:
        """Generar pregunta final para completar la información"""

        return f"¡Increíble {customer_name}! Con toda esta información nuestro asesor va a tener exactamente lo que necesitas. Solo para afinar los últimos detalles: ¿hay algún aspecto específico o preferencia adicional que sea importante para tu decisión?"

    def _extract_key_information(self, message: str) -> Dict[str, Any]:
        """Extraer información clave del mensaje para análisis"""

        message_lower = message.lower()
        extracted = {}

        # Extraer tipo de propiedad
        property_types = {
            "apartamento": ["apartamento", "apto"],
            "casa": ["casa", "vivienda"],
            "local": ["local", "comercial"],
            "oficina": ["oficina", "oficinas"]
        }

        for prop_type, keywords in property_types.items():
            if any(keyword in message_lower for keyword in keywords):
                extracted["property_type"] = prop_type
                break

        # Extraer números (posibles habitaciones, precio, etc.)
        import re
        numbers = re.findall(r'\d+', message)
        if numbers:
            extracted["numbers_mentioned"] = numbers

        return extracted

    async def _display_demo_crm_preview(self, customer_name: str, lead_result: Dict[str, Any]):
        """Muestra preview visual del CRM para demo"""
        customer_data = lead_result["customer_data"]
        crm_sim = lead_result["crm_simulation"]

        print("\n" + "="*60)
        print("*** SIMULACION CRM LEADSALES - LEAD CREADO ***")
        print("="*60)
        print(f"CLIENTE: {customer_data['name']}")
        print(f"WHATSAPP: {customer_data['whatsapp']}")
        print(f"NECESIDAD: {customer_data['needs'][:80]}...")
        print(f"CALIDAD: {customer_data['quality_score']}/100")
        print(f"ETIQUETAS: {', '.join(customer_data['tags'])}")
        print(f"PRIORIDAD: {customer_data['priority']}")
        print(f"CREADO: {customer_data['created_at']}")
        print(f"LEAD ID: {lead_result['lead_id']}")
        print("\nVISTA PREVIA CRM:")
        for key, value in crm_sim.items():
            if isinstance(value, list):
                print(f"   {key}: {', '.join(value)}")
            else:
                print(f"   {key}: {value}")
        print("="*60)
        print("*** DEMO: Lead enviado al pipeline de ventas ***")
        print("="*60 + "\n")