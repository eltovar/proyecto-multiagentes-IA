'''
    Agente de saludo, recopilacion de nombre y necesidad del cliente.
    Maneja estados: NUEVO, RECOPILANDO_NOMBRE, RECOPILANDO
'''

from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent

STATE_NUEVO = "NUEVO"
STATE_ESPERANDO_RESPUESTA_INICIAL = "ESPERANDO_RESPUESTA_INICIAL"
STATE_RECOPILANDO_NOMBRE = "RECOPILANDO_NOMBRE"
STATE_RECOPILANDO_NECESIDAD = "RECOPILANDO_NECESIDAD"

class ReceptionAgent(BaseAgent):

    def __init__(self):
        super().__init__("reception")

        # Inicializar LLM service si está disponible
        if self.llm_service and not self.llm_service.api_client.initialized:
            self.llm_service.initialize()

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        valid_states = [STATE_NUEVO, STATE_ESPERANDO_RESPUESTA_INICIAL, STATE_RECOPILANDO_NOMBRE, STATE_RECOPILANDO_NECESIDAD]
        return conversation.get("state") in valid_states

    async def process_message(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
        message = message_data.get("text", {}).get("body", "")
        whatsapp_id = message_data.get("from")

        if not self.validate_message(message):
            return self.create_response("Por favor, envía un mensaje válido.")

        current_state = conversation.get("state", STATE_NUEVO)
        customer_name = conversation.get("customer_name")

        self.log_action("Procesando mensaje", {"state": current_state, "has_name": bool(customer_name)})

        try:
            if current_state == STATE_NUEVO:
                return await self._handle_greeting(customer_name)
            elif current_state == STATE_ESPERANDO_RESPUESTA_INICIAL:
                return await self._handle_initial_response(message, whatsapp_id)
            elif current_state == STATE_RECOPILANDO_NOMBRE:
                return await self._handle_name_collection(message, whatsapp_id)
            elif current_state == STATE_RECOPILANDO_NECESIDAD:
                return await self._handle_need_collection(message, customer_name, whatsapp_id)
            else:
                self.log_error(f"Estado desconocido: {current_state}")
                return await self._handle_greeting(customer_name)

        except Exception as e:
            self.log_error("Error procesando mensaje", e)
            return self.create_response("Disculpa, ocurrió un error. Un asesor se pondrá en contacto contigo.")

    async def _handle_greeting(self, customer_name: Optional[str] = None) -> Dict[str, Any]:
        # Flujo fijo según especificación original: Primero pregunta qué necesita
        response = "Hola, soy Sofía de Inmobiliaria Proteger ¿En qué puedo ayudarte?"
        return self.create_response(response, new_state=STATE_ESPERANDO_RESPUESTA_INICIAL)

    async def _handle_initial_response(self, message: str, whatsapp_id: str) -> Dict[str, Any]:
        # Flujo simple: Cualquier respuesta → Pedir nombre
        response = "Me regalas tu nombre por favor?"
        return self.create_response(response, new_state=STATE_RECOPILANDO_NOMBRE,
                                  data_updates={"customer_needs": message})

    async def _handle_name_collection(self, message: str, whatsapp_id: str) -> Dict[str, Any]:
        # Extraer y validar nombre del usuario
        name = self._extract_name(message)
        if not name:
            return self.create_response("No pude identificar tu nombre. ¿Podrías escribirlo de nuevo?",
                                      new_state=STATE_RECOPILANDO_NOMBRE)

        response = f"Perfecto, {name}! Un asesor pronto se estará comunicando contigo"
        return self.create_response(response, new_state="TRANSFERIDO", transfer_to="LeadsalesAgent",
                                  data_updates={"customer_name": name})

    async def _handle_need_collection(self, message: str, customer_name: str, whatsapp_id: str) -> Dict[str, Any]:
        # Clasificar intención y transferir al agente apropiado
        from app.config import settings

        if settings.fixed_flow_mode:
            # Modo fijo: Transfer directo a Leadsales sin clasificación
            response = f"Perfecto {customer_name}, un asesor pronto se estará comunicando contigo"
            return self.create_response(response, new_state="TRANSFERIDO", transfer_to="LeadsalesAgent",
                                      data_updates={"customer_needs": message})
        else:
            # Modo clasificación LLM: Decidir entre Support y Leadsales
            return await self._classify_and_transfer(message, customer_name, whatsapp_id)

    def _extract_name(self, message: str) -> Optional[str]:
        clean_message = message.strip()
        words = clean_message.split()

        # ✅ AÑADIR: Lista de respuestas negativas/inválidas
        invalid_responses = [
            "no", "nope", "na", "nada", "nunca", "ninguno", "ninguna",
            "si", "sí", "ok", "okay", "bueno", "bien", "vale",
            "hola", "que", "qué", "como", "cómo", "cuando", "cuándo"
        ]

        # Verificar si es una respuesta inválida
        if len(words) == 1 and words[0].lower() in invalid_responses:
            return None

        if 1 <= len(words) <= 3 and all(word.isalpha() and len(word) >= 2 for word in words):
            return " ".join(word.title() for word in words)

        lower_message = clean_message.lower()
        patterns = ["mi nombre es ", "me llamo ", "soy ", "nombre: "]
        for pattern in patterns:
            if pattern in lower_message:
                name_part = lower_message.split(pattern, 1)[1].strip()
                first_word = name_part.split()[0] if name_part.split() else ""
                if first_word.isalpha() and len(first_word) >= 2:
                    return first_word.title()
        return None

    async def _classify_and_transfer(self, message: str, customer_name: str, whatsapp_id: str) -> Dict[str, Any]:
        """
        Clasificación crítica usando LLM para decidir entre SupportAgent y LeadsalesAgent
        Ubicación especificada: app/agents/reception_agent.py
        Momento: Estado RECOPILANDO_NECESIDAD
        """
        try:
            # Verificar que LLM service esté disponible
            if not self.llm_service or not self.llm_service.api_client.initialized:
                self.log_error("LLM service no disponible, usando fallback")
                # Fallback con clasificación simple
                classification = self._classify_intent_simple(message)
            else:
                # Prompt de clasificación según especificación LLM
                classification_prompt = f"""
                Clasifica esta consulta del usuario:

                "pregunta" - Si es una consulta informativa general
                "necesidad" - Si expresa una necesidad específica de producto/servicio

                Consulta: "{message}"

                Responde SOLO con: pregunta o necesidad
                """

                # 🚨 LLAMADA A GEMINI API AQUÍ
                classification = await self.llm_service.classify_intent(classification_prompt)

            if classification == "pregunta":
                response = f"Entiendo {customer_name}, tienes preguntas. Te conecto con nuestro especialista."
                return self.create_response(response, transfer_to="SupportAgent",
                                          data_updates={"customer_needs": message})

            elif classification == "necesidad":
                response = f"¡Excelente {customer_name}! Te conecto con un asesor especializado."
                return self.create_response(response, new_state="TRANSFERIDO", transfer_to="LeadsalesAgent",
                                          data_updates={"customer_needs": message})

            else:
                # Fallback si clasificación no es clara
                response = f"{customer_name}, ¿podrías ser más específico? ¿Tienes preguntas o necesitas algún servicio?"
                return self.create_response(response, new_state=STATE_RECOPILANDO_NECESIDAD)

        except Exception as e:
            self.log_error("Error en clasificación LLM", e)
            # Fallback en caso de error: ir a Leadsales como default
            response = f"Perfecto {customer_name}, un asesor se pondrá en contacto contigo"
            return self.create_response(response, new_state="TRANSFERIDO", transfer_to="LeadsalesAgent",
                                      data_updates={"customer_needs": message})

    def _classify_intent_simple(self, message: str) -> str:
        """Clasificación simple sin LLM (fallback cuando LLM no está disponible)"""
        lower_msg = message.lower()
        question_indicators = ["qué", "cómo", "cuándo", "dónde", "por qué", "cuál", "?"]
        need_indicators = ["necesito", "quiero", "busco", "requiero", "contratar", "comprar", "vender"]

        question_score = sum(1 for indicator in question_indicators if indicator in lower_msg)
        need_score = sum(1 for indicator in need_indicators if indicator in lower_msg)

        if question_score > need_score and question_score > 0:
            return "pregunta"
        elif need_score > question_score and need_score > 0:
            return "necesidad"
        return "necesidad"  # Default fallback

    def _classify_intent(self, message: str) -> str:
        """Clasificación simple sin LLM (para modo fixed_flow_mode)"""
        lower_msg = message.lower()
        question_indicators = ["qué", "cómo", "cuándo", "dónde", "por qué", "cuál", "?"]
        need_indicators = ["necesito", "quiero", "busco", "requiero", "contratar"]

        question_score = sum(1 for indicator in question_indicators if indicator in lower_msg)
        need_score = sum(1 for indicator in need_indicators if indicator in lower_msg)

        if question_score > need_score and question_score > 0:
            return "question"
        elif need_score > question_score and need_score > 0:
            return "need"
        return "unclear"