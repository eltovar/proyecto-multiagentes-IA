"""
LLM Generator: Generación de respuestas contextuales y follow-ups.
Responsable de crear respuestas usando RAG, saludos y opciones de seguimiento.
Migrado a OpenAI para mejor integración RAG con system/user prompts.
"""

import json
from typing import List, Optional
from app.config import settings

class LLMGenerator:

    def __init__(self, api_client):
        self.client = api_client

    async def generate_contextual_response(
        self,
        user_question: str,
        context: str,
        customer_name: Optional[str] = None
    ) -> str:
        if not self.client.initialized:
            return "Lo siento, el servicio no está disponible en este momento."

        try:
            # System prompt especializado para SupportAgent
            system_prompt = f"""Eres el SupportAgent (Sofia) de "Inmobiliaria Proteger". Tu misión es proporcionar respuestas precisas y contextuales a consultas informativas.

CONTEXTO RAG DISPONIBLE:
{context}

PERSONALIDAD: Profesional, concisa y orientadora. Usa un tono de experto.

INSTRUCCIONES ESTRICTAS:
- CONTEXTO RAG: Utiliza exclusivamente el texto proporcionado por el sistema RAG para formular tu respuesta
- Si el contexto RAG responde a la pregunta, sé directo y preciso
- REDIRECCIÓN ADMINISTRATIVA: Si el usuario pregunta por temas fuera del RAG:
  * Pagos/Facturas/Cartera: "Claro, puedes comunicarte con el área de Cartera. [Proporciona el número o link correspondiente de la base de conocimiento]."
  * Reparaciones/Mantenimiento (inquilinos existentes): "Por supuesto, puedes escribir al área de Mantenimiento para que gestionen tu solicitud."
  * General: Si no encaja, "Con mucho gusto paso tu información a nuestro equipo para ver cuál es la mejor manera de ayudarte."

PROHIBICIONES INQUEBRANTABLES:
- NUNCA des información detallada sobre precios, ubicaciones o características de inmuebles
- Si te preguntan sobre inmuebles específicos, responde ÚNICAMENTE: "Esa información detallada la maneja directamente nuestro equipo de asesores. Ellos se pondrán en contacto contigo muy pronto para resolver todas tus dudas."
- NUNCA te identifiques como una IA

FORMATO DE RESPUESTA: Directa, profesional y sin saludos innecesarios."""

            user_prompt = f"Pregunta del cliente: {user_question}"

            response = await self.client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )

            generated_response = response.choices[0].message.content.strip()

            if customer_name:
                generated_response = f"Hola, {customer_name}!\n\n{generated_response}"

            print(f"[LLMGenerator] Respuesta contextual generada ({len(generated_response)} caracteres)")
            return generated_response

        except Exception as e:
            print(f"[LLMGenerator] Error generando respuesta: {e}")
            customer_greeting = f", {customer_name}" if customer_name else ""
            return f"Lo siento{customer_greeting}, ocurrió un error procesando tu consulta. Un especialista se pondrá en contacto contigo pronto."

    async def generate_follow_up_options(self, question: str, response: str) -> List[str]:
        if not self.client.initialized:
            return []

        try:
            response = await self.client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Genera 3 preguntas de seguimiento relevantes basadas en la conversación. Responde SOLO con un JSON array válido."
                    },
                    {
                        "role": "user",
                        "content": f"""Basado en esta conversación, genera 3 preguntas de seguimiento:

PREGUNTA ORIGINAL: "{question}"
RESPUESTA DADA: "{response}"

Formato: ["pregunta 1", "pregunta 2", "pregunta 3"]"""
                    }
                ],
                response_format={"type": "json_object"},  # Garantiza JSON válido
                temperature=0.7,
                max_tokens=300
            )

            follow_ups_json = json.loads(response.choices[0].message.content.strip())
            # Extract array from JSON object if needed
            if isinstance(follow_ups_json, dict) and 'questions' in follow_ups_json:
                return follow_ups_json['questions']
            elif isinstance(follow_ups_json, list):
                return follow_ups_json
            else:
                return []

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