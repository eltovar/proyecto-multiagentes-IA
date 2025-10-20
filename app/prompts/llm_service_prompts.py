"""
Prompts específicos para LLMService.

Este módulo contiene los prompts utilizados por llm_service.py para:
- Clasificación binaria (pregunta vs necesidad)
- Clasificación genérica con prompts personalizados
- Fallback basado en keywords (no requiere prompt LLM)

Autor: Sistema centralizado de prompts
Fecha: 2025-10-16
Relacionado: PR001 - Centralización de Prompts LLM
"""

# ============================================================================
# CLASIFICACIÓN BINARIA: Pregunta vs Necesidad
# ============================================================================

CLASSIFY_QUESTION_VS_NEED_SYSTEM = """Eres un clasificador preciso. Responde SOLO con 'pregunta' o 'necesidad'."""

CLASSIFY_QUESTION_VS_NEED_USER = """MENSAJE DEL USUARIO:
{message}

INSTRUCCIONES:
- Si el usuario hace una pregunta o busca información → 'pregunta'
- Si el usuario expresa una necesidad, quiere comprar/contratar → 'necesidad'

Responde SOLO con una palabra (sin puntuación)."""


# ============================================================================
# CLASIFICACIÓN GENÉRICA CON PROMPT CUSTOMIZADO
# ============================================================================
# Nota: No requiere prompt específico en este módulo.
# El prompt se pasa como parámetro desde el caller.


# ============================================================================
# FALLBACK CLASSIFICATION (solo keywords, no LLM)
# ============================================================================
# Nota: No requiere prompt LLM.
# Esta clasificación usa lógica de keywords como fallback cuando el LLM falla.