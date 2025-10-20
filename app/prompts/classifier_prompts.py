"""
Prompts para clasificación de mensajes (LLMClassifier).

Este módulo contiene los prompts utilizados por llm_classifier.py para:
- Clasificación de intención (question, need, greeting, unclear)
- Análisis de sentimiento (positivo, negativo, neutral)

Autor: Sistema centralizado de prompts
Fecha: 2025-10-16
Relacionado: PR001 - Centralización de Prompts LLM
"""

# ============================================================================
# CLASIFICACIÓN DE INTENCIÓN
# ============================================================================

CLASSIFY_INTENTION_SYSTEM = """Eres un clasificador experto de intenciones de clientes inmobiliarios. Responde SIEMPRE en formato JSON válido."""

CLASSIFY_INTENTION_USER = """Clasifica el siguiente mensaje del usuario en una de estas categorías:

CATEGORÍAS:
- "question": El usuario hace una pregunta o busca información
- "need": El usuario expresa una necesidad, quiere contratar o comprar algo
- "greeting": Solo es un saludo sin intención clara
- "unclear": El mensaje no es claro o no encaja en las otras categorías

MENSAJE: "{message}"

Responde SOLO con un JSON en este formato:
{{"type": "categoria", "confidence": 0.8, "reasoning": "breve explicacion"}}"""


# ============================================================================
# ANÁLISIS DE SENTIMIENTO
# ============================================================================

ANALYZE_SENTIMENT_SYSTEM = """Analiza sentimientos. Responde solo: positivo, negativo o neutral."""

ANALYZE_SENTIMENT_USER = """Analiza el sentimiento del siguiente mensaje y responde solo con una palabra:
- "positivo": Si el mensaje es amigable, agradecido o entusiasta
- "negativo": Si el mensaje es hostil, quejoso o frustrado
- "neutral": Si el mensaje es informativo o neutro

MENSAJE: "{message}"

Respuesta (solo una palabra):"""
