"""
LLM Service Coordinador: Interface principal para agentes.
Coordina entre LLMClassifier y LLMGenerator para procesamiento completo.
Migrado a OpenAI ChatGPT-4o mini para mayor precisión.
"""

import openai
import asyncio
from typing import Dict, Any, List, Optional
from app.config import settings
from .llm_classifier import LLMClassifier
from .llm_generator import LLMGenerator
from app.utils.error_logger import log_error, log_info

class LLMAPIClient:

    def __init__(self):
        self.client = None
        self.initialized = False

    def initialize(self) -> bool:
        try:
            self.client = openai.AsyncOpenAI(
                api_key=settings.openai_api_key
            )
            self.initialized = True
            log_info("LLMService", "OpenAI API inicializada correctamente")
            return True
        except Exception as e:
            log_error("LLMService", "Error inicializando OpenAI API", e)
            return False

class LLMService:

    def __init__(self):
        self.api_client = LLMAPIClient()
        self.classifier = None
        self.generator = None

    def initialize(self) -> bool:
        if not self.api_client.initialize():
            return False

        self.classifier = LLMClassifier(self.api_client)
        self.generator = LLMGenerator(self.api_client)
        return True

    def classify_intention(self, message: str) -> Dict[str, Any]:
        if not self.classifier:
            return {"type": "error", "confidence": 0.0}
        return self.classifier.classify_intention(message)

    def generate_contextual_response(
        self,
        user_question: str,
        context: str,
        customer_name: Optional[str] = None
    ) -> str:
        if not self.generator:
            return "Servicio no disponible"
        return self.generator.generate_contextual_response(user_question, context, customer_name)

    def generate_follow_up_options(self, user_question: str, response: str) -> List[str]:
        if not self.generator:
            return []
        return self.generator.generate_follow_up_options(user_question, response)

    def process_user_message(self, message: str, context: str = "") -> Dict[str, Any]:
        classification = self.classify_intention(message)

        result = {
            "classification": classification,
            "processed": True
        }

        if context and classification.get("type") == "question":
            response = self.generate_contextual_response(message, context)
            follow_ups = self.generate_follow_up_options(message, response)
            result.update({
                "response": response,
                "follow_ups": follow_ups
            })

        return result

    async def classify_intent(self, classification_prompt: str) -> str:
        """
        Clasificación específica para reception_agent: retorna 'pregunta' o 'necesidad'
        Migrado a OpenAI con mayor precisión.
        """
        if not self.api_client.initialized:
            return "necesidad"  # Fallback por defecto

        try:
            response = await self.api_client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": "Eres un clasificador preciso. Responde SOLO con 'pregunta' o 'necesidad'."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().lower()

            # Validar que la respuesta sea correcta
            if result in ["pregunta", "necesidad"]:
                return result
            else:
                # Fallback: si contiene palabras clave de pregunta
                if any(word in classification_prompt.lower() for word in ["qué", "cómo", "cuándo", "dónde", "por qué", "cuál", "?"]):
                    return "pregunta"
                else:
                    return "necesidad"

        except Exception as e:
            log_error("LLMService", "Error en classify_intent", e)
            return "necesidad"  # Fallback por defecto

    def health_check(self) -> Dict[str, Any]:
        if not self.api_client.initialized:
            return {"status": "unhealthy", "reason": "API no inicializada"}

        try:
            # Note: Health check simplified for OpenAI
            return {
                "status": "healthy",
                "model": settings.llm_model_name,
                "provider": "OpenAI",
                "modules": {"classifier": "ok", "generator": "ok"}
            }
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}

llm_service = LLMService()