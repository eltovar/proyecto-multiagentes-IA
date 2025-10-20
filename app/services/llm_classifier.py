"""
Clasificacion de intenciones usando LLM
"""


import json
from typing import Dict, Any
from app.config import settings
from app.monitoring.logger import get_logger
from app.prompts.classifier_prompts import (
    CLASSIFY_INTENTION_SYSTEM,
    CLASSIFY_INTENTION_USER,
    ANALYZE_SENTIMENT_SYSTEM,
    ANALYZE_SENTIMENT_USER
)

logger = get_logger(__name__)

class LLMClassifier:

    def __init__(self, api_client):
        self.client = api_client

    async def classify_intention(self, message: str) -> Dict[str, Any]:
        if not self.client.initialized:
            logger.error("Cliente no inicializado")
            return {"type": "error", "confidence": 0.0}

        try:
            response = await self.client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": CLASSIFY_INTENTION_SYSTEM},
                    {"role": "user", "content": CLASSIFY_INTENTION_USER.format(message=message)}
                ],
                response_format={"type": "json_object"},  # CRÍTICO: Garantiza JSON válido
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response.choices[0].message.content.strip())
            print(f"[LLMClassifier] Clasificación: {result.get('type')} (confianza: {result.get('confidence')})")

            return result

        except Exception as e:
            logger.error("Error clasificando intención", exc_info=e)
            return {"type": "error", "confidence": 0.0, "reasoning": str(e)}

    async def analyze_message_sentiment(self, message: str) -> str:
        if not self.client.initialized:
            return "neutral"

        try:
            response = await self.client.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": ANALYZE_SENTIMENT_SYSTEM},
                    {"role": "user", "content": ANALYZE_SENTIMENT_USER.format(message=message)}
                ],
                temperature=0.1,
                max_tokens=10
            )

            sentiment = response.choices[0].message.content.strip().lower()
            return sentiment if sentiment in ["positivo", "negativo", "neutral"] else "neutral"
        except:
            return "neutral"

    def detect_language(self, message: str) -> str:
        spanish_indicators = ["qué", "cómo", "dónde", "cuándo", "por favor", "gracias", "hola"]
        message_lower = message.lower()

        spanish_score = sum(1 for indicator in spanish_indicators if indicator in message_lower)
        return "spanish" if spanish_score > 0 else "unknown"