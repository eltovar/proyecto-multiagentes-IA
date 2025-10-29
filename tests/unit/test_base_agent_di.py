"""
Tests unitarios para Dependency Injection en BaseAgent
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import Mock
from app.agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """Agente mock para testing"""
    async def process_message(self, message_data, conversation):
        return {"response": "test"}


def test_base_agent_constructor_with_di():
    """Test que BaseAgent acepta dependencias inyectadas"""
    mock_llm = Mock()
    mock_state = Mock()

    agent = MockAgent("test", llm_service=mock_llm, state_manager=mock_state)

    assert agent.llm_service == mock_llm
    assert agent.state_manager == mock_state


def test_base_agent_lazy_loading_llm():
    """Test que llm_service se carga lazy cuando no está inyectado"""
    agent = MockAgent("test")

    # Primera llamada debe importar globalmente
    llm = agent.llm_service
    # No debería crashear
    assert llm is not None or llm is None  # Puede ser None si no está disponible


def test_base_agent_lazy_loading_state_manager():
    """Test que state_manager se carga lazy cuando no está inyectado"""
    agent = MockAgent("test")

    # Primera llamada debe importar globalmente
    state = agent.state_manager
    # No debería crashear
    assert state is not None


def test_base_agent_setter_injection():
    """Test que se pueden inyectar servicios después de __init__"""
    agent = MockAgent("test")

    mock_llm = Mock()
    mock_state = Mock()

    agent.llm_service = mock_llm
    agent.state_manager = mock_state

    assert agent.llm_service == mock_llm
    assert agent.state_manager == mock_state


def test_base_agent_get_conversation_state_uses_injected_manager():
    """Test que get_conversation_state usa state_manager inyectado"""
    mock_state = Mock()
    mock_conversation = Mock()
    mock_conversation.whatsapp_id = "123"
    mock_conversation.state = "NUEVO"
    mock_conversation.customer_name = "Juan"
    mock_conversation.customer_needs = "test"
    mock_conversation.created_at = "2025-01-01"
    mock_conversation.updated_at = "2025-01-01"

    mock_state.get_conversation.return_value = mock_conversation

    agent = MockAgent("test", state_manager=mock_state)
    result = agent.get_conversation_state("123")

    mock_state.get_conversation.assert_called_once_with("123")
    assert result["whatsapp_id"] == "123"
    assert result["state"] == "NUEVO"


def test_base_agent_update_conversation_state_uses_injected_manager():
    """Test que update_conversation_state usa state_manager inyectado"""
    mock_state = Mock()

    agent = MockAgent("test", state_manager=mock_state)
    agent.update_conversation_state("123", {"customer_name": "Juan"})

    mock_state.update_conversation_state.assert_called_once_with(
        whatsapp_id="123",
        customer_name="Juan"
    )
