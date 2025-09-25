"""
LLM Classifier: Clasificación de intenciones y análisis de mensajes.
Responsable de determinar el tipo de consulta y analizar mensajes de usuarios.
"""

import json
import google.generativeai as genai
from typing import Dict, Any

class LLMClassifier:

    def __init__(self, api_client):
        self.client = api_client

    def classify_intention(self, message: str) -> Dict[str, Any]:
        if not self.client.initialized:
            print("[LLMClassifier] Error: Cliente no inicializado")
            return {"type": "error", "confidence": 0.0}

        prompt = self._build_classification_prompt(message)

        try:
            response = self.client.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=200
                )
            )

            result = json.loads(response.text.strip())
            print(f"[LLMClassifier] Clasificación: {result.get('type')} (confianza: {result.get('confidence')})")

            return result

        except Exception as e:
            print(f"[LLMClassifier] Error clasificando intención: {e}")
            return {"type": "error", "confidence": 0.0, "reasoning": str(e)}

    def analyze_message_sentiment(self, message: str) -> str:
        if not self.client.initialized:
            return "neutral"

        prompt = f"""
        Analiza el sentimiento del siguiente mensaje y responde solo con una palabra:
        - "positivo": Si el mensaje es amigable, agradecido o entusiasta
        - "negativo": Si el mensaje es hostil, quejoso o frustrado
        - "neutral": Si el mensaje es informativo o neutro

        MENSAJE: "{message}"

        Respuesta (solo una palabra):
        """

        try:
            response = self.client.model.generate_content(prompt)
            sentiment = response.text.strip().lower()
            return sentiment if sentiment in ["positivo", "negativo", "neutral"] else "neutral"
        except:
            return "neutral"

    def detect_language(self, message: str) -> str:
        spanish_indicators = ["qué", "cómo", "dónde", "cuándo", "por favor", "gracias", "hola"]
        message_lower = message.lower()

        spanish_score = sum(1 for indicator in spanish_indicators if indicator in message_lower)
        return "spanish" if spanish_score > 0 else "unknown"

    def _build_classification_prompt(self, message: str) -> str:
        return f"""
        Clasifica el siguiente mensaje del usuario en una de estas categorías:

        CATEGORÍAS:
        - "question": El usuario hace una pregunta o busca información
        - "need": El usuario expresa una necesidad, quiere contratar o comprar algo
        - "greeting": Solo es un saludo sin intención clara
        - "unclear": El mensaje no es claro o no encaja en las otras categorías

        MENSAJE: "{message}"

        Responde SOLO con un JSON en este formato:
        {{"type": "categoria", "confidence": 0.8, "reasoning": "breve explicacion"}}
        """