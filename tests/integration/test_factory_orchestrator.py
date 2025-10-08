# -*- coding: utf-8 -*-
"""
Tests de integración para FactoryOrchestrator
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from app.core.factory_orchestrator import FactoryOrchestrator
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state


@pytest.fixture(scope="function")
def orchestrator():
    """Fixture que crea orchestrator fresh para cada test"""
    return FactoryOrchestrator()


@pytest.fixture(scope="function")
def test_message_data():
    """Fixture con mensaje de prueba"""
    return {
        "from": "test_user_123",
        "text": {"body": "Hola"}
    }


def test_factory_orchestrator_initialization(orchestrator):
    """Test que orchestrator se inicializa correctamente"""
    assert orchestrator.initialized is True
    assert orchestrator.factory_registry is not None
    assert orchestrator.service_container is not None
    assert len(orchestrator.agent_priority) == 3


def test_factory_orchestrator_health_check(orchestrator):
    """Test health check"""
    health = orchestrator.health_check()

    assert health["status"] == "healthy"
    assert health["orchestrator"] == "factory_based"
    assert health["factories_registered"] == 3
    assert "services" in health


@pytest.mark.asyncio
async def test_factory_orchestrator_select_agent_creates_fresh(orchestrator, test_message_data):
    """Test que _select_agent crea instancias fresh"""
    # Inicializar BD y conversación
    initialize_database()
    update_conversation_state("test_user_123", "NUEVO")
    conversation = get_conversation_state("test_user_123")

    # Seleccionar agente 2 veces
    agent1 = await orchestrator._select_agent(test_message_data, conversation)
    agent2 = await orchestrator._select_agent(test_message_data, conversation)

    # Verificar que son instancias diferentes (fresh)
    assert agent1 is not None
    assert agent2 is not None
    assert agent1 is not agent2
    assert id(agent1) != id(agent2)

    # Limpiar
    from app.state.crud_operations import ConversationCRUD
    crud = ConversationCRUD()
    crud.delete_conversation("test_user_123")


@pytest.mark.asyncio
async def test_factory_orchestrator_select_agent_shares_services(orchestrator, test_message_data):
    """Test que agentes fresh comparten servicios"""
    initialize_database()
    update_conversation_state("test_user_123", "NUEVO")
    conversation = get_conversation_state("test_user_123")

    # Seleccionar 2 agentes
    agent1 = await orchestrator._select_agent(test_message_data, conversation)
    agent2 = await orchestrator._select_agent(test_message_data, conversation)

    # Verificar que comparten servicios (singleton)
    assert agent1.llm_service is agent2.llm_service

    # Limpiar
    from app.state.crud_operations import ConversationCRUD
    crud = ConversationCRUD()
    crud.delete_conversation("test_user_123")


@pytest.mark.asyncio
async def test_factory_orchestrator_process_message_flow(orchestrator):
    """Test flujo completo de process_message"""
    from unittest.mock import patch, AsyncMock

    initialize_database()

    message_data = {
        "from": "test_user_456",
        "text": {"body": "Hola"}
    }

    # Mock send_message usando patch
    with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
        # Procesar mensaje
        await orchestrator.process_message(message_data)

        # Verificar que se llamó send_message
        assert mock_send.called
        assert mock_send.call_count >= 1

        # Verificar que se creó conversación
        conversation = get_conversation_state("test_user_456")
        assert conversation is not None

    # Limpiar
    from app.state.crud_operations import ConversationCRUD
    crud = ConversationCRUD()
    crud.delete_conversation("test_user_456")


@pytest.mark.asyncio
async def test_factory_orchestrator_respects_handoff_protocol(orchestrator):
    """Test que respeta Handoff Protocol (estado TRANSFERIDO)"""
    initialize_database()

    # Crear conversación transferida
    update_conversation_state("test_user_789", "TRANSFERIDO")

    message_data = {
        "from": "test_user_789",
        "text": {"body": "Hola después de transferencia"}
    }

    sent_messages = []
    async def mock_send(sender_id, message):
        sent_messages.append({"to": sender_id, "text": message})

    import app.services.whatsapp_service
    original_send = app.services.whatsapp_service.send_message
    app.services.whatsapp_service.send_message = mock_send

    try:
        # Procesar mensaje
        await orchestrator.process_message(message_data)

        # NO debe enviar respuesta (handoff activo)
        assert len(sent_messages) == 0

    finally:
        app.services.whatsapp_service.send_message = original_send

        # Limpiar
        from app.state.crud_operations import ConversationCRUD
        crud = ConversationCRUD()
        crud.delete_conversation("test_user_789")


def test_factory_orchestrator_agent_priority_correct(orchestrator):
    """Test que prioridad de agentes es correcta"""
    assert orchestrator.agent_priority == ["SupportAgent", "ReceptionAgent", "LeadsalesAgent"]
