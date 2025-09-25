"""
LLM Generator: Generación de respuestas contextuales y follow-ups.
Responsable de crear respuestas usando RAG, saludos y opciones de seguimiento.
"""

import json
import google.generativeai as genai
from typing import List, Optional
from app.config import settings

class LLMGenerator:

    def __init__(self, api_client):
        self.client = api_client

    def generate_contextual_response(
        self,
        user_question: str,
        context: str,
        customer_name: Optional[str] = None
    ) -> str:
        if not self.client.initialized:
            return "Lo siento, el servicio no está disponible en este momento."

        prompt = self._build_response_prompt(user_question, context, customer_name)

        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens
                )
            )

            generated_response = response.text.strip()

            if customer_name:
                generated_response = f"Hola, {customer_name}!\n\n{generated_response}"

            print(f"[LLMGenerator] Respuesta contextual generada ({len(generated_response)} caracteres)")
            return generated_response

        except Exception as e:
            print(f"[LLMGenerator] Error generando respuesta: {e}")
            customer_greeting = f", {customer_name}" if customer_name else ""
            return f"Lo siento{customer_greeting}, ocurrió un error procesando tu consulta. Un especialista se pondrá en contacto contigo pronto."

    def generate_follow_up_options(self, question: str, response: str) -> List[str]:
        if not self.client.initialized:
            return []

        prompt = f"""
        Basado en esta conversación, genera 3 preguntas de seguimiento que el usuario podría hacer.

        PREGUNTA ORIGINAL: "{question}"
        RESPUESTA DADA: "{response}"

        Genera 3 preguntas cortas y relevantes que el usuario podría hacer a continuación.
        Responde SOLO con un JSON array:
        ["pregunta 1", "pregunta 2", "pregunta 3"]
        """

        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=300
                )
            )

            follow_ups = json.loads(response.text.strip())
            return follow_ups if isinstance(follow_ups, list) else []

        except Exception as e:
            print(f"[LLMGenerator] Error generando follow-ups: {e}")
            return []

    def generate_greeting_message(self, user_name: str) -> str:
        greetings = [
            f"¡Hola {user_name}! Es un gusto saludarte. ¿En qué puedo ayudarte hoy?",
            f"¡Bienvenido/a {user_name}! Estoy aquí para ayudarte. ¿Qué necesitas?",
            f"¡Hola {user_name}! Gracias por contactarnos. ¿Cómo puedo asistirte?"
        ]
        import random
        return random.choice(greetings)

    def _build_response_prompt(self, user_question: str, context: str, customer_name: Optional[str] = None) -> str:
        customer_greeting = f", {customer_name}" if customer_name else ""

        return f"""
        Eres un asistente virtual experto y amigable. Responde a la pregunta del usuario usando SOLO la información del contexto proporcionado.

        CONTEXTO DISPONIBLE:
        {context}

        PREGUNTA DEL USUARIO: "{user_question}"

        INSTRUCCIONES:
        - Responde de manera clara y concisa
        - Usa SOLO información del contexto
        - Si el contexto no contiene la información, di que no tienes esa información específica
        - Mantén un tono profesional pero amigable
        - Al final, pregunta si necesita algo más

        RESPUESTA:
        """