"""
Tests para validar centralización de prompts LLM.

Verifica que:
- No hay prompts hardcodeados en servicios
- Todos los servicios importan desde app/prompts
- Los placeholders funcionan correctamente
- La estructura de prompts es consistente

Relacionado: PR001 - Centralización de Prompts LLM
"""

import pytest
import inspect
from app.services import llm_classifier, llm_generator, llm_service


class TestNoHardcodedPrompts:
    """Verificar que no hay prompts hardcodeados en servicios"""

    def test_no_hardcoded_prompts_in_llm_classifier(self):
        """LLMClassifier no debe tener prompts hardcodeados"""
        source = inspect.getsource(llm_classifier.LLMClassifier)

        # No debe haber strings multilinea largos (prompts)
        assert '"""Eres' not in source, "Prompt hardcodeado detectado en LLMClassifier"
        assert '"""Clasifica' not in source, "Prompt hardcodeado detectado en LLMClassifier"
        assert 'f"""Eres' not in source, "F-string prompt hardcodeado detectado"

    def test_no_hardcoded_prompts_in_llm_generator(self):
        """LLMGenerator no debe tener prompts hardcodeados"""
        source = inspect.getsource(llm_generator.LLMGenerator)

        assert '"""Eres' not in source, "Prompt hardcodeado detectado en LLMGenerator"
        assert 'SupportAgent (Sofia)' not in source, "Prompt hardcodeado detectado en LLMGenerator"

    def test_no_hardcoded_prompts_in_llm_service(self):
        """LLMService no debe tener prompts largos hardcodeados en métodos críticos"""
        # Verificar método classify_intent
        source = inspect.getsource(llm_service.LLMService.classify_intent)

        assert '"role": "system", "content": "Eres' not in source, \
            "Prompt hardcodeado en classify_intent"


class TestImportsFromPrompts:
    """Verificar que los módulos importan correctamente desde app/prompts"""

    def test_llm_classifier_imports_from_prompts(self):
        """LLMClassifier debe importar prompts centralizados"""
        import app.services.llm_classifier as classifier_module

        # Verificar que tiene acceso a los prompts
        source = inspect.getsource(classifier_module)
        assert 'from app.prompts.classifier_prompts import' in source, \
            "LLMClassifier debe importar de classifier_prompts"

    def test_llm_generator_imports_from_prompts(self):
        """LLMGenerator debe importar prompts centralizados"""
        import app.services.llm_generator as generator_module

        source = inspect.getsource(generator_module)
        assert 'from app.prompts.generator_prompts import' in source, \
            "LLMGenerator debe importar de generator_prompts"

    def test_llm_service_imports_from_prompts(self):
        """LLMService debe importar prompts centralizados"""
        import app.services.llm_service as service_module

        source = inspect.getsource(service_module)
        assert 'from app.prompts.llm_service_prompts import' in source, \
            "LLMService debe importar de llm_service_prompts"


class TestPromptPlaceholders:
    """Verificar que los placeholders funcionan correctamente"""

    def test_classifier_prompts_have_message_placeholder(self):
        """Prompts de clasificación deben tener placeholder {message}"""
        from app.prompts.classifier_prompts import (
            CLASSIFY_INTENTION_USER,
            ANALYZE_SENTIMENT_USER
        )

        # Verificar que tienen el placeholder
        assert '{message}' in CLASSIFY_INTENTION_USER
        assert '{message}' in ANALYZE_SENTIMENT_USER

        # Verificar que se pueden formatear
        formatted1 = CLASSIFY_INTENTION_USER.format(message="Test message")
        assert "Test message" in formatted1
        assert "{message}" not in formatted1

        formatted2 = ANALYZE_SENTIMENT_USER.format(message="Estoy feliz")
        assert "Estoy feliz" in formatted2

    def test_generator_prompts_have_correct_placeholders(self):
        """Prompts de generación deben tener placeholders correctos"""
        from app.prompts.generator_prompts import (
            GENERATE_CONTEXTUAL_RESPONSE_SYSTEM,
            GENERATE_CONTEXTUAL_RESPONSE_USER,
            GENERATE_FOLLOWUP_USER
        )

        # Verificar placeholders
        assert '{rag_context}' in GENERATE_CONTEXTUAL_RESPONSE_SYSTEM
        assert '{user_question}' in GENERATE_CONTEXTUAL_RESPONSE_USER
        assert '{question}' in GENERATE_FOLLOWUP_USER
        assert '{response}' in GENERATE_FOLLOWUP_USER

        # Verificar formateo
        formatted = GENERATE_CONTEXTUAL_RESPONSE_SYSTEM.format(
            rag_context="Contexto de prueba"
        )
        assert "Contexto de prueba" in formatted
        assert "{rag_context}" not in formatted

    def test_llm_service_prompts_have_message_placeholder(self):
        """Prompts de LLMService deben tener placeholder {message}"""
        from app.prompts.llm_service_prompts import (
            CLASSIFY_QUESTION_VS_NEED_USER
        )

        assert '{message}' in CLASSIFY_QUESTION_VS_NEED_USER

        formatted = CLASSIFY_QUESTION_VS_NEED_USER.format(message="¿Qué horarios tienen?")
        assert "¿Qué horarios tienen?" in formatted
        assert "{message}" not in formatted


class TestPromptStructure:
    """Verificar estructura consistente de prompts"""

    def test_prompts_are_strings(self):
        """Todos los prompts deben ser strings"""
        from app.prompts.classifier_prompts import (
            CLASSIFY_INTENTION_SYSTEM,
            ANALYZE_SENTIMENT_SYSTEM
        )

        assert isinstance(CLASSIFY_INTENTION_SYSTEM, str)
        assert isinstance(ANALYZE_SENTIMENT_SYSTEM, str)

    def test_prompts_are_not_empty(self):
        """Prompts no deben estar vacíos"""
        from app.prompts.classifier_prompts import (
            CLASSIFY_INTENTION_SYSTEM,
            CLASSIFY_INTENTION_USER
        )
        from app.prompts.generator_prompts import (
            GENERATE_CONTEXTUAL_RESPONSE_SYSTEM
        )

        assert len(CLASSIFY_INTENTION_SYSTEM) > 0
        assert len(CLASSIFY_INTENTION_USER) > 0
        assert len(GENERATE_CONTEXTUAL_RESPONSE_SYSTEM) > 0

    def test_system_prompts_have_clear_instructions(self):
        """Prompts del sistema deben tener instrucciones claras"""
        from app.prompts.classifier_prompts import CLASSIFY_INTENTION_SYSTEM
        from app.prompts.generator_prompts import GENERATE_CONTEXTUAL_RESPONSE_SYSTEM

        # Verificar que son prompts instructivos
        assert len(CLASSIFY_INTENTION_SYSTEM) > 20, "System prompt demasiado corto"
        assert len(GENERATE_CONTEXTUAL_RESPONSE_SYSTEM) > 100, \
            "System prompt de generación debe tener instrucciones detalladas"


class TestPromptExports:
    """Verificar que __init__.py exporta correctamente"""

    def test_prompts_init_exports_all_new_prompts(self):
        """__init__.py debe exportar todos los prompts nuevos"""
        from app.prompts import (
            CLASSIFY_INTENTION_SYSTEM,
            CLASSIFY_INTENTION_USER,
            GENERATE_CONTEXTUAL_RESPONSE_SYSTEM,
            GENERATE_FOLLOWUP_SYSTEM,
            CLASSIFY_QUESTION_VS_NEED_SYSTEM,
            ANALYZE_SENTIMENT_SYSTEM
        )

        # Verificar que se pueden importar
        assert CLASSIFY_INTENTION_SYSTEM is not None
        assert CLASSIFY_INTENTION_USER is not None
        assert GENERATE_CONTEXTUAL_RESPONSE_SYSTEM is not None
        assert GENERATE_FOLLOWUP_SYSTEM is not None
        assert CLASSIFY_QUESTION_VS_NEED_SYSTEM is not None
        assert ANALYZE_SENTIMENT_SYSTEM is not None

    def test_prompts_init_has_all_in_all_list(self):
        """__init__.py debe incluir nuevos prompts en __all__"""
        import app.prompts as prompts_module

        expected_exports = [
            'CLASSIFY_INTENTION_SYSTEM',
            'GENERATE_CONTEXTUAL_RESPONSE_SYSTEM',
            'CLASSIFY_QUESTION_VS_NEED_SYSTEM'
        ]

        for export in expected_exports:
            assert export in prompts_module.__all__, \
                f"{export} debe estar en __all__"


class TestObsoleteMethodsRemoved:
    """Verificar que métodos obsoletos fueron eliminados"""

    def test_build_classification_prompt_not_in_llm_classifier(self):
        """_build_classification_prompt debe haber sido eliminado"""
        source = inspect.getsource(llm_classifier.LLMClassifier)

        # El método no debe existir en el código fuente
        assert '_build_classification_prompt' not in source, \
            "_build_classification_prompt debe haber sido eliminado"

    def test_build_response_prompt_not_in_llm_generator(self):
        """_build_response_prompt debe haber sido eliminado"""
        source = inspect.getsource(llm_generator.LLMGenerator)

        assert '_build_response_prompt' not in source, \
            "_build_response_prompt debe haber sido eliminado"
