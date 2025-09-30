"""
Response Generator for LeadsalesAgent
Extracted from leadsales_agent.py
Handles all LLM-based response generation and motivational messaging
"""

import random
from typing import Dict, Any


class ResponseGenerator:
    """Handles response generation for lead capture and engagement"""

    def __init__(self, llm_service):
        self.llm_service = llm_service

    def log_error(self, message: str, exception: Exception = None):
        """Simple error logging - will delegate to agent's log_error if needed"""
        error_msg = f"[ResponseGenerator] {message}"
        if exception:
            error_msg += f" - {type(exception).__name__}: {str(exception)}"
        print(error_msg)

    async def generate_initial_capture_response(self, customer_name: str) -> str:
        """Generar respuesta inicial altamente motivadora para captar información"""
        motivational_responses = [
            f"¡Excelente {customer_name}! Me emociona poder ayudarte con tu proyecto inmobiliario. Para conectarte con el asesor perfecto que haga realidad tu sueño, cuéntame: ¿Qué tipo de inmueble estás buscando y en qué zona te gustaría que estuviera?",

            f"¡Perfecto {customer_name}! Estás a un paso de encontrar tu inmueble ideal. Para asegurarme de que nuestro especialista tenga todo listo para ti, necesito conocer: ¿Buscas comprar, vender o arrendar? ¿Y qué características debe tener tu inmueble perfecto?",

            f"¡Increíble {customer_name}! Tu timing es perfecto. Para que nuestro equipo te prepare las mejores opciones desde ya, compárteme: ¿Qué inmueble tienes en mente y cuál es tu zona de interés principal?"
        ]

        return random.choice(motivational_responses)

    async def generate_deepening_response(self, customer_name: str, existing_needs: str) -> str:
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

    async def generate_follow_up_question(self, partial_info: str, customer_name: str) -> str:
        """Generar pregunta de seguimiento para obtener más información específica"""

        follow_up_questions = [
            f"¡Perfecto {customer_name}! Para que nuestro asesor tenga exactamente lo que buscas, ¿podrías contarme en qué zona te gustaría que estuviera y cuántas habitaciones necesitas?",

            f"¡Excelente {customer_name}! Me estás dando información muy valiosa. ¿Cuál es tu rango de presupuesto aproximado y hay alguna característica especial que sea importante para ti?",

            f"¡Genial {customer_name}! Para preparar las mejores opciones, ¿para cuándo necesitarías el inmueble y qué zona sería tu primera opción?"
        ]

        return random.choice(follow_up_questions)

    async def generate_final_capture_question(self, existing_info: str, customer_name: str) -> str:
        """Generar pregunta final para completar la información"""

        return f"¡Increíble {customer_name}! Con toda esta información nuestro asesor va a tener exactamente lo que necesitas. Solo para afinar los últimos detalles: ¿hay algún aspecto específico o preferencia adicional que sea importante para tu decisión?"