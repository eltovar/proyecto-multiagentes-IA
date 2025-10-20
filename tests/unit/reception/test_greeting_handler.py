"""Tests unitarios para GreetingHandler"""
import pytest
from unittest.mock import AsyncMock, Mock
from app.agents.reception.handlers.greeting import GreetingHandler, GreetingResult


@pytest.fixture
def mock_llm():
    """Mock del servicio LLM"""
    llm = Mock()
    llm.classify_intent_and_extract_entities = AsyncMock(
        return_value={
            "nombre": "Carlos",
            "intent": "greeting",
            "confidence": 0.9
        }
    )
    return llm


@pytest.fixture
def mock_state_manager():
    """Mock del state manager"""
    state = Mock()
    state.get_conversation = Mock(return_value=None)
    state.update_conversation_state = Mock(return_value=True)
    return state


@pytest.fixture
def config():
    """Configuración de prueba"""
    return {
        "politicas_link": "https://test.com/politicas",
        "youtube_link": "https://youtube.com/test",
        "solicitud_gratis_link": "https://test.com/solicitud"
    }


@pytest.fixture
def greeting_handler(mock_llm, mock_state_manager, config):
    """Instancia de GreetingHandler con mocks"""
    return GreetingHandler(mock_llm, mock_state_manager, config)


@pytest.mark.asyncio
async def test_handle_initial_greeting_success(greeting_handler):
    """Test: Saludo inicial exitoso"""
    conversation = {"state": "NUEVO"}
    interaction_count = 1

    result = await greeting_handler.handle_initial_greeting(conversation, interaction_count)

    assert isinstance(result, GreetingResult)
    assert result.next_state == "STATE_POLITICAS_PRESENTADAS"
    assert "Sofia" in result.response
    assert result.metadata["interaction_count"] == 1
    assert result.metadata["state"] == "STATE_RECOPILANDO_NOMBRE"