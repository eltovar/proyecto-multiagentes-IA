"""
LLM Generator: Generación de respuestas contextuales y follow-ups.
Responsable de crear respuestas usando RAG, saludos y opciones de seguimiento.
Migrado a OpenAI para mejor integración RAG con system/user prompts.
"""

import json
from typing import List, Optional
from app.config import settings
from app.monitoring.logger import get_logger
from app.prompts.generator_prompts import (
    GENERATE_CONTEXTUAL_RESPONSE_SYSTEM,
    GENERATE_CONTEXTUAL_RESPONSE_USER,
    GENERATE_FOLLOWUP_SYSTEM,
    GENERATE_FOLLOWUP_USER
)

logger = get_logger(__name__)

class LLMGenerator: #Generacion de respuestas con RAG

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
            system_prompt = GENERATE_CONTEXTUAL_RESPONSE_SYSTEM.format(rag_context=context)
            user_prompt = GENERATE_CONTEXTUAL_RESPONSE_USER.format(user_question=user_question)

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
            logger.error("Error generando respuesta", exc_info=e)
            customer_greeting = f", {customer_name}" if customer_name else ""
            return f"Lo siento{customer_greeting}, ocurrió un error procesando tu consulta. Un especialista se pondrá en contacto contigo pronto."

    async def generate_follow_up_options(self, question: str, response: str) -> List[str]:
        if not self.client.initialized:
            return []

        try:
            response = await self.client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": GENERATE_FOLLOWUP_SYSTEM},
                    {"role": "user", "content": GENERATE_FOLLOWUP_USER.format(question=question, response=response)}
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
            logger.error("Error generando follow-ups", exc_info=e)
            return []

    def generate_greeting_message(self, user_name: str) -> str:
        greetings = [
            f"¡Hola {user_name}! Es un gusto saludarte. ¿En qué puedo ayudarte hoy?",
            f"¡Bienvenido/a {user_name}! Estoy aquí para ayudarte. ¿Qué necesitas?",
            f"¡Hola {user_name}! Gracias por contactarnos. ¿Cómo puedo asistirte?"
        ]
        import random
        return random.choice(greetings)