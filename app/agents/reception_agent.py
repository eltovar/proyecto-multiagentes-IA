'''
    Agente de saludo, recopilacion de nombre y necesidad del cliente.
    Maneja estados: NUEVO, RECOPILANDO_NOMBRE, RECOPILANDO
'''

from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent

STATE_NUEVO = "NUEVO"
STATE_RECOPILANDO_NOMBRE = "RECOPILANDO_NOMBRE"
STATE_RECOPILANDO_NECESIDAD = "RECOPILANDO_NECESIDAD"

class ReceptionAgent(BaseAgent):

    def __init__(self):
        
        super().__init__("reception")

    async def can_handle(self, message_data: Dict[str, Any], conversation: Dict[str, Any]) -> bool:
        valid_states = [STATE_NUEVO, STATE_RECOPILANDO_NOMBRE, STATE_RECOPILANDO_NECESIDAD]
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
        if customer_name:
            response = f"¡Hola {customer_name}! Te recordamos. ¿En qué puedo ayudarte hoy?"
            return self.create_response(response, new_state=STATE_RECOPILANDO_NECESIDAD)
        else:
            response = "¡Hola! Bienvenido. Para ayudarte mejor, ¿me podrías decir tu nombre?"
            return self.create_response(response, new_state=STATE_RECOPILANDO_NOMBRE)

    async def _handle_name_collection(self, message: str, whatsapp_id: str) -> Dict[str, Any]:
        name = self._extract_name(message)
        if not name:
            return self.create_response("No pude identificar tu nombre. ¿Podrías escribirlo de nuevo?",
                                      new_state=STATE_RECOPILANDO_NOMBRE)

        response = f"Perfecto, {name}! Es un gusto conocerte. ¿En qué puedo ayudarte?"
        self.update_conversation_state(whatsapp_id, {"customer_name": name})
        return self.create_response(response, new_state=STATE_RECOPILANDO_NECESIDAD,
                                  data_updates={"customer_name": name})

    async def _handle_need_collection(self, message: str, customer_name: str, whatsapp_id: str) -> Dict[str, Any]:
        intent_type = self._classify_intent(message)

        if intent_type == "question":
            response = f"Entiendo {customer_name}, tienes preguntas. Te conecto con nuestro especialista."
            self.update_conversation_state(whatsapp_id, {"customer_needs": message})
            return self.create_response(response, transfer_to="support",
                                      data_updates={"customer_needs": message})

        elif intent_type == "need":
            response = f"¡Excelente {customer_name}! Te conecto con un asesor especializado."
            self.update_conversation_state(whatsapp_id, {"customer_needs": message})
            return self.create_response(response, transfer_to="leadsales",
                                      data_updates={"customer_needs": message})

        else:
            response = f"{customer_name}, ¿podrías ser más específico? ¿Tienes preguntas o necesitas algún servicio?"
            return self.create_response(response, new_state=STATE_RECOPILANDO_NECESIDAD)

    def _extract_name(self, message: str) -> Optional[str]:
        clean_message = message.strip()
        words = clean_message.split()

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

    def _classify_intent(self, message: str) -> str:
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