"""
LLM Service Coordinador: Interface principal para agentes.
Coordina entre LLMClassifier y LLMGenerator para procesamiento completo.
"""

import google.generativeai as genai
from typing import Dict, Any, List, Optional
from app.config import settings
from .llm_classifier import LLMClassifier
from .llm_generator import LLMGenerator

class LLMAPIClient:

    def __init__(self):
        self.model = None
        self.initialized = False

    def initialize(self) -> bool:
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
            self.initialized = True
            print("[LLMService] API inicializada correctamente")
            return True
        except Exception as e:
            print(f"[LLMService] Error inicializando API: {e}")
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

    def health_check(self) -> Dict[str, Any]:
        if not self.api_client.initialized:
            return {"status": "unhealthy", "reason": "API no inicializada"}

        try:
            test_response = self.api_client.model.generate_content("Test")
            return {
                "status": "healthy",
                "model": settings.gemini_model,
                "modules": {"classifier": "ok", "generator": "ok"}
            }
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}

llm_service = LLMService()