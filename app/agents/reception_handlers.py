
from typing import Dict, Any, Optional

class ReceptionHandlers:

    def __init__(self, agent_name: str = "reception"):
        self.agent_name = agent_name

    async def handle_greeting(self, customer_name: Optional[str] = None) -> Dict[str, Any]:
        """Maneja saludo inicial"""
        if customer_name:
            # Cliente que regresa
            response = (
                f"Hola {customer_name}! Te recordamos de conversaciones anteriores. "
                f"En que puedo ayudarte hoy?"
            )
            return {
                "response": response,
                "new_state": "RECOPILANDO_NECESIDAD"
            }
        else:
            # Nuevo cliente
            response = (
                "Hola! Bienvenido a nuestro servicio. "
                "Para poder ayudarte mejor, me podrias decir tu nombre?"
            )
            return {
                "response": response,
                "new_state": "RECOPILANDO_NOMBRE"
            }

    async def handle_name_collection(self, user_message: str) -> Dict[str, Any]:
        """Procesa recopilacion de nombre"""
        name = self._extract_name(user_message)
        if not name:
            return {"response": "No pude identificar tu nombre claramente. Podrias escribirlo de nuevo? Solo tu nombre, por favor.", "new_state": "RECOPILANDO_NOMBRE"}
        response = f"Perfecto, {name}! Es un gusto conocerte. En que puedo ayudarte hoy? Cuentame que necesitas."
        return {"response": response, "new_state": "RECOPILANDO_NECESIDAD", "customer_name": name}

    async def handle_need_collection(self, user_message: str, customer_name: str) -> Dict[str, Any]:
        """Procesa recopilacion de necesidades"""
        # Clasificar tipo de necesidad
        intent_result = await self.classify_intent(user_message)

        if intent_result["type"] == "question":
            # Es una pregunta - transferir a soporte
            response = (
                f"Entiendo {customer_name}, tienes algunas preguntas. "
                f"Te voy a conectar con nuestro especialista que podra "
                f"brindarte toda la informacion que necesitas."
            )
            return {
                "response": response,
                "transfer_to": "support",
                "transfer_message": user_message,
                "customer_needs": user_message
            }

        elif intent_result["type"] == "need":
            # Es una necesidad concreta - transferir a leadsales
            response = (
                f"Excelente {customer_name}! Veo que tienes una necesidad especifica. "
                f"He registrado tu solicitud y te voy a conectar con un asesor "
                f"especializado que podra ayudarte con exactamente lo que necesitas."
            )
            return {
                "response": response,
                "transfer_to": "leadsales",
                "transfer_message": user_message,
                "customer_needs": user_message
            }

        else:
            # Mensaje poco claro
            response = (
                f"Gracias {customer_name}. Para poder ayudarte mejor, "
                f"podrias ser un poco mas especifico sobre lo que necesitas? "
                f"Por ejemplo, tienes alguna pregunta o necesitas algun servicio en particular?"
            )
            return {
                "response": response,
                "new_state": "RECOPILANDO_NECESIDAD"
            }

    async def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Clasifica intencion del usuario"""
        message_lower = user_message.lower().strip()

        question_indicators = ["que", "como", "cuando", "donde", "por que", "cuanto", "cual", "quiero saber", "necesito informacion", "puedes decirme", "me puedes decir", "?"]
        need_indicators = ["necesito", "quiero", "busco", "me interesa", "requiero", "comprar", "contratar", "adquirir", "solicitar"]
        question_score = sum(1 for indicator in question_indicators if indicator in message_lower)
        need_score = sum(1 for indicator in need_indicators if indicator in message_lower)

        if question_score > need_score and question_score > 0:
            return {"type": "question", "confidence": min(question_score * 0.3, 1.0)}
        elif need_score > question_score and need_score > 0:
            return {"type": "need", "confidence": min(need_score * 0.3, 1.0)}
        else:
            return {"type": "unclear", "confidence": 0.2}

    def _extract_name(self, message: str) -> Optional[str]:
        """Extrae nombre del mensaje usando heuristicas"""
        clean_message = message.strip()
        words = clean_message.split()

        # Mensaje que contiene solo el nombre
        if 1 <= len(words) <= 3 and all(word.isalpha() for word in words):
            return " ".join(word.title() for word in words)
        lower_message = clean_message.lower()
        name_patterns = ["mi nombre es ", "me llamo ", "soy ", "mi nombre: ", "nombre: "]
        for pattern in name_patterns:
            if pattern in lower_message:
                name_part = lower_message.split(pattern, 1)[1].strip()
                first_word = name_part.split()[0] if name_part.split() else ""
                if first_word.isalpha() and len(first_word) >= 2:
                    return first_word.title()

        return None