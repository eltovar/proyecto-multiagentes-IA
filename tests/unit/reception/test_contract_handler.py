"""
Tests unitarios para ContractHandler
"""

import pytest
from unittest.mock import Mock
from app.agents.reception.handlers.contract import ContractHandler, ContractResult


@pytest.fixture
def mock_llm():
    """Mock del servicio LLM"""
    return Mock()


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
        "youtube_link": "https://youtube.com/test",
        "solicitud_gratis_link": "https://test.com/solicitud",
        "politicas_link": "https://test.com/politicas"
    }


@pytest.fixture
def contract_handler(mock_llm, mock_state_manager, config):
    """Instancia de ContractHandler con mocks"""
    return ContractHandler(mock_llm, mock_state_manager, config)


@pytest.mark.asyncio
async def test_handle_contract_question_success(contract_handler):
    """Test: Pregunta sobre contrato con inmobiliaria"""
    conversation = {"state": "STATE_NOMBRE_OBTENIDO", "customer_name": "Juan"}
    interaction_count = 3

    result = await contract_handler.handle_contract_question(conversation, interaction_count)

    assert isinstance(result, ContractResult)
    assert result.next_state == "PREGUNTA_CONTRATO_INMOBILIARIA"
    assert result.next_state == "STATE_PREGUNTA_CONTRATO_INMOBILIARIA"
    assert "contrato vigente" in result.response.lower()
    assert result.metadata["interaction_count"] == 3


@pytest.mark.asyncio
async def test_handle_contract_response_yes(contract_handler):
    """Test: Usuario tiene contrato"""
    message = "Sí, tengo contrato"
    result = await contract_handler.handle_contract_response(message, {}, 4)

    assert result.next_state == "STATE_PREGUNTA_CUAL_INMOBILIARIA"
    assert result.metadata["tiene_contrato_inmobiliaria"] is True


@pytest.mark.asyncio
async def test_handle_contract_response_no(contract_handler):
    """Test: Usuario NO tiene contrato"""
    message = "No tengo"
    result = await contract_handler.handle_contract_response(message, {}, 4)

    assert result.next_state == "STATE_PREGUNTA_SOLICITUD_LIBERTADOR"
    assert result.metadata["tiene_contrato_inmobiliaria"] is False
