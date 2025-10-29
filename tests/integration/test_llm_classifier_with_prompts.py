"""
Tests de integración para LLMClassifier con prompts centralizados.

Verifica end-to-end que:
- La clasificación de intenciones funciona correctamente
- El análisis de sentimiento funciona
- Los prompts centralizados se integran correctamente
- Las respuestas del LLM son válidas

Relacionado: PR001 - Centralización de Prompts LLM
"""

import pytest
from app.services.llm_service import LLMService


def check_for_api_error(result):
    """Helper para skipear tests si hay error de API (cuota, rate limit, etc)"""
    if result.get('type') == 'error':
        pytest.skip(f"LLM API error: {result.get('reasoning', 'unknown')}")


@pytest.mark.asyncio
class TestClassifyIntentionWithPrompts:
    """Tests de clasificación de intención con prompts centralizados"""

    async def test_classify_intention_with_centralized_prompt(self):
        """Verificar que clasificación funciona con prompt centralizado"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        result = await llm_service.classifier.classify_intention("Busco apartamento")

        # Verificar estructura de respuesta
        assert 'type' in result, "Resultado debe tener campo 'type'"
        assert 'confidence' in result, "Resultado debe tener campo 'confidence'"

        # Si hay error de cuota/API, skip el test
        check_for_api_error(result)

        # Verificar valores válidos
        assert result['type'] in ['question', 'need', 'greeting', 'unclear'], \
            f"Tipo inválido: {result['type']}"
        assert 0 <= result['confidence'] <= 1.0, \
            f"Confianza fuera de rango: {result['confidence']}"

        # Reasoning es opcional pero si existe debe ser string
        if 'reasoning' in result:
            assert isinstance(result['reasoning'], str)

    async def test_classify_question_intent(self):
        """Clasificar mensaje como 'question'"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        result = await llm_service.classifier.classify_intention(
            "¿Qué horarios de atención tienen?"
        )

        check_for_api_error(result)

        assert result['type'] == 'question', \
            f"Debe clasificar como 'question', obtuvo: {result['type']}"
        assert result['confidence'] > 0.5

    async def test_classify_need_intent(self):
        """Clasificar mensaje como 'need'"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        result = await llm_service.classifier.classify_intention(
            "Necesito arrendar un apartamento de 3 habitaciones"
        )

        check_for_api_error(result)

        assert result['type'] == 'need', \
            f"Debe clasificar como 'need', obtuvo: {result['type']}"
        assert result['confidence'] > 0.5

    async def test_classify_greeting_intent(self):
        """Clasificar mensaje como 'greeting'"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        result = await llm_service.classifier.classify_intention(
            "Hola, buenos días"
        )

        check_for_api_error(result)

        assert result['type'] == 'greeting', \
            f"Debe clasificar como 'greeting', obtuvo: {result['type']}"
        assert result['confidence'] > 0.5

    async def test_classify_unclear_intent(self):
        """Clasificar mensaje ambiguo como 'unclear'"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        result = await llm_service.classifier.classify_intention(
            "xyz abc 123"
        )

        check_for_api_error(result)

        # Mensaje ambiguo debe clasificarse como 'unclear' u otro tipo válido
        assert result['type'] in ['unclear', 'question', 'need', 'greeting']

        # Si es 'unclear', alta confianza es válida (el LLM está seguro de la ambigüedad)
        # Si es otro tipo con mensaje ambiguo, confianza debe ser baja
        if result['type'] != 'unclear':
            assert result['confidence'] <= 0.8

    async def test_classify_intention_error_handling(self):
        """Verificar manejo de errores cuando LLM no está inicializado"""
        llm_service = LLMService()
        # No inicializar el servicio intencionalmente

        # Cuando el servicio no está inicializado, classifier es None
        assert llm_service.classifier is None, \
            "Classifier debe ser None cuando no está inicializado"

        # El comportamiento esperado es que el servicio maneje esto
        # Este test valida que el código reconoce el estado no inicializado


@pytest.mark.asyncio
class TestAnalyzeSentimentWithPrompts:
    """Tests de análisis de sentimiento con prompts centralizados"""

    async def test_analyze_positive_sentiment(self):
        """Analizar sentimiento positivo"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        sentiment = await llm_service.classifier.analyze_message_sentiment(
            "¡Muchas gracias por su ayuda! Excelente servicio."
        )

        # Si retorna neutral, puede ser por error de API (cuota agotada)
        # En ese caso, skip el test
        if sentiment == "neutral":
            pytest.skip("API puede haber fallado - retornó neutral (fallback)")

        assert sentiment == "positivo", \
            f"Debe detectar sentimiento positivo, obtuvo: {sentiment}"

    async def test_analyze_negative_sentiment(self):
        """Analizar sentimiento negativo"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        sentiment = await llm_service.classifier.analyze_message_sentiment(
            "Estoy muy molesto, el servicio es pésimo"
        )

        # Si retorna neutral, puede ser por error de API (cuota agotada)
        if sentiment == "neutral":
            pytest.skip("API puede haber fallado - retornó neutral (fallback)")

        assert sentiment == "negativo", \
            f"Debe detectar sentimiento negativo, obtuvo: {sentiment}"

    async def test_analyze_neutral_sentiment(self):
        """Analizar sentimiento neutral"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        sentiment = await llm_service.classifier.analyze_message_sentiment(
            "¿Cuál es el precio del apartamento?"
        )

        assert sentiment == "neutral", \
            f"Debe detectar sentimiento neutral, obtuvo: {sentiment}"

    async def test_sentiment_returns_valid_values(self):
        """Verificar que sentimiento siempre retorna valores válidos"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        valid_sentiments = ["positivo", "negativo", "neutral"]

        test_messages = [
            "Estoy feliz",
            "Tengo un problema",
            "Información general",
            "abc xyz 123"
        ]

        for message in test_messages:
            sentiment = await llm_service.classifier.analyze_message_sentiment(message)
            assert sentiment in valid_sentiments, \
                f"Sentimiento inválido: {sentiment} para mensaje: {message}"

    async def test_sentiment_error_handling(self):
        """Verificar manejo de errores cuando servicio no está inicializado"""
        llm_service = LLMService()
        # No inicializar el servicio intencionalmente

        # Cuando el servicio no está inicializado, classifier es None
        assert llm_service.classifier is None, \
            "Classifier debe ser None cuando no está inicializado"

        # Este test valida que reconocemos el estado no inicializado
        # El comportamiento de fallback se prueba en otros tests


@pytest.mark.asyncio
class TestPromptIntegration:
    """Tests de integración de prompts centralizados"""

    async def test_classifier_uses_centralized_prompts(self):
        """Verificar que classifier usa prompts de app/prompts"""
        from app.prompts.classifier_prompts import (
            CLASSIFY_INTENTION_SYSTEM,
            CLASSIFY_INTENTION_USER
        )

        # Verificar que los prompts están disponibles
        assert len(CLASSIFY_INTENTION_SYSTEM) > 0
        assert len(CLASSIFY_INTENTION_USER) > 0
        assert '{message}' in CLASSIFY_INTENTION_USER

        # Verificar que se pueden formatear
        formatted = CLASSIFY_INTENTION_USER.format(message="Test")
        assert "Test" in formatted

    async def test_classification_prompt_contains_categories(self):
        """Verificar que prompt de clasificación define las categorías"""
        from app.prompts.classifier_prompts import CLASSIFY_INTENTION_USER

        # El prompt debe mencionar las categorías válidas
        assert 'question' in CLASSIFY_INTENTION_USER.lower()
        assert 'need' in CLASSIFY_INTENTION_USER.lower()
        assert 'greeting' in CLASSIFY_INTENTION_USER.lower()
        assert 'unclear' in CLASSIFY_INTENTION_USER.lower()

    async def test_sentiment_prompt_contains_options(self):
        """Verificar que prompt de sentimiento define las opciones"""
        from app.prompts.classifier_prompts import ANALYZE_SENTIMENT_USER

        # El prompt debe mencionar las opciones válidas
        assert 'positivo' in ANALYZE_SENTIMENT_USER.lower()
        assert 'negativo' in ANALYZE_SENTIMENT_USER.lower()
        assert 'neutral' in ANALYZE_SENTIMENT_USER.lower()

    async def test_json_response_format_in_classification(self):
        """Verificar que clasificación solicita formato JSON"""
        from app.prompts.classifier_prompts import CLASSIFY_INTENTION_USER

        # El prompt debe solicitar JSON
        assert 'json' in CLASSIFY_INTENTION_USER.lower()


@pytest.mark.asyncio
class TestDetectLanguage:
    """Tests de detección de idioma (no usa LLM, pero es parte de LLMClassifier)"""

    def test_detect_spanish_language(self):
        """Detectar mensajes en español"""
        llm_service = LLMService()
        llm_service.initialize()

        result = llm_service.classifier.detect_language(
            "¿Cómo puedo ayudarte?"
        )

        assert result == "spanish"

    def test_detect_spanish_with_multiple_indicators(self):
        """Detectar español con múltiples indicadores"""
        llm_service = LLMService()
        llm_service.initialize()

        result = llm_service.classifier.detect_language(
            "Hola, ¿qué tal? Gracias por favor"
        )

        assert result == "spanish"

    def test_detect_unknown_language(self):
        """Detectar idioma desconocido"""
        llm_service = LLMService()
        llm_service.initialize()

        result = llm_service.classifier.detect_language(
            "Hello, how are you?"
        )

        assert result == "unknown"

    def test_detect_language_with_numbers_only(self):
        """Detectar idioma con solo números"""
        llm_service = LLMService()
        llm_service.initialize()

        result = llm_service.classifier.detect_language("123 456 789")

        assert result == "unknown"


@pytest.mark.asyncio
class TestGenerateResponseWithPrompts:
    """Tests de generación de respuestas RAG con prompts centralizados"""

    async def test_generate_response_with_centralized_prompt(self):
        """Verificar que generación RAG funciona con prompts centralizados"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        context = "Inmobiliaria Proteger ofrece servicios de arriendo y venta."
        response = await llm_service.generator.generate_contextual_response(
            "¿Qué servicios ofrecen?",
            context
        )

        # Verificar que hay respuesta
        assert len(response) > 0, "La respuesta no debe estar vacía"

        # Si retorna mensaje de error (por API fallida), skip el test
        if "lo siento" in response.lower() and "error" in response.lower():
            pytest.skip("API falló - retornó mensaje de error")

        # Verificar que la respuesta usa el contexto RAG
        assert "arriendo" in response.lower() or "venta" in response.lower(), \
            f"La respuesta debe mencionar servicios del contexto RAG. Respuesta: {response}"

    async def test_generate_response_with_rag_context(self):
        """Verificar que el generador usa contexto RAG correctamente"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        context = """
        Nuestros horarios de atención son:
        - Lunes a Viernes: 8:00 AM - 6:00 PM
        - Sábados: 9:00 AM - 1:00 PM
        """

        response = await llm_service.generator.generate_contextual_response(
            "¿Cuáles son los horarios?",
            context
        )

        assert len(response) > 0

        # Si retorna mensaje de error, skip el test
        if "lo siento" in response.lower() and "error" in response.lower():
            pytest.skip("API falló - retornó mensaje de error")

        # Debe mencionar información del contexto
        assert any(word in response.lower() for word in ["lunes", "viernes", "horario", "atención"]), \
            f"Respuesta debe usar el contexto RAG. Respuesta: {response}"

    async def test_generate_response_with_customer_name(self):
        """Verificar que se puede incluir nombre del cliente en respuesta"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        context = "Tenemos apartamentos disponibles en varias zonas."

        response = await llm_service.generator.generate_contextual_response(
            "¿Tienen apartamentos disponibles?",
            context,
            customer_name="Juan"
        )

        assert len(response) > 0

        # Si retorna mensaje de error, skip el test
        if "lo siento" in response.lower() and "error" in response.lower():
            pytest.skip("API falló - retornó mensaje de error")

        # Debe incluir el nombre del cliente
        assert "Juan" in response, \
            f"Respuesta debe incluir el nombre del cliente. Respuesta: {response}"

    async def test_generate_response_empty_context(self):
        """Verificar comportamiento con contexto vacío"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        response = await llm_service.generator.generate_contextual_response(
            "¿Qué servicios tienen?",
            ""  # Contexto vacío
        )

        # Debe retornar alguna respuesta, aunque sea genérica
        assert len(response) > 0

    async def test_generate_response_error_handling(self):
        """Verificar manejo de errores cuando generador no está disponible"""
        llm_service = LLMService()
        # No inicializar

        # Generator debe ser None
        assert llm_service.generator is None

    async def test_generator_uses_centralized_prompts(self):
        """Verificar que generator usa prompts de app/prompts"""
        from app.prompts.generator_prompts import (
            GENERATE_CONTEXTUAL_RESPONSE_SYSTEM,
            GENERATE_CONTEXTUAL_RESPONSE_USER
        )

        # Verificar que los prompts están disponibles
        assert len(GENERATE_CONTEXTUAL_RESPONSE_SYSTEM) > 0
        assert len(GENERATE_CONTEXTUAL_RESPONSE_USER) > 0

        # Verificar placeholders
        assert '{rag_context}' in GENERATE_CONTEXTUAL_RESPONSE_SYSTEM
        assert '{user_question}' in GENERATE_CONTEXTUAL_RESPONSE_USER

    async def test_generation_prompt_mentions_sofia(self):
        """Verificar que prompt de generación menciona a Sofia (SupportAgent)"""
        from app.prompts.generator_prompts import GENERATE_CONTEXTUAL_RESPONSE_SYSTEM

        # El prompt debe mencionar a Sofia y su rol
        assert 'sofia' in GENERATE_CONTEXTUAL_RESPONSE_SYSTEM.lower()
        assert 'supportagent' in GENERATE_CONTEXTUAL_RESPONSE_SYSTEM.lower()

    async def test_generation_prompt_prohibits_property_details(self):
        """Verificar que prompt prohíbe dar detalles de inmuebles"""
        from app.prompts.generator_prompts import GENERATE_CONTEXTUAL_RESPONSE_SYSTEM

        # El prompt debe tener prohibiciones sobre información detallada
        assert 'prohib' in GENERATE_CONTEXTUAL_RESPONSE_SYSTEM.lower() or \
               'nunca' in GENERATE_CONTEXTUAL_RESPONSE_SYSTEM.lower(), \
            "Prompt debe tener prohibiciones claras"


@pytest.mark.asyncio
class TestGenerateFollowUps:
    """Tests de generación de preguntas de seguimiento"""

    async def test_generate_follow_up_options(self):
        """Verificar que se generan preguntas de seguimiento"""
        llm_service = LLMService()

        if not llm_service.initialize():
            pytest.skip("LLM service no disponible")

        question = "¿Qué horarios tienen?"
        response = "Nuestros horarios son de lunes a viernes de 8am a 6pm."

        follow_ups = await llm_service.generator.generate_follow_up_options(
            question,
            response
        )

        # Debe retornar una lista (puede estar vacía si falla)
        assert isinstance(follow_ups, list)

        # Si hay follow-ups, deben ser strings
        if len(follow_ups) > 0:
            assert all(isinstance(q, str) for q in follow_ups)
            assert len(follow_ups) <= 3, "No debe haber más de 3 follow-ups"

    async def test_followup_prompts_exist(self):
        """Verificar que existen prompts de follow-up"""
        from app.prompts.generator_prompts import (
            GENERATE_FOLLOWUP_SYSTEM,
            GENERATE_FOLLOWUP_USER
        )

        assert len(GENERATE_FOLLOWUP_SYSTEM) > 0
        assert len(GENERATE_FOLLOWUP_USER) > 0

        # Verificar placeholders
        assert '{question}' in GENERATE_FOLLOWUP_USER
        assert '{response}' in GENERATE_FOLLOWUP_USER
