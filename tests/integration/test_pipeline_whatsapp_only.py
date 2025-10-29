import pytest
from app.core.factory_orchestrator import FactoryOrchestrator
from app.state.models import ConversationState
from app.state.manager import state_manager


@pytest.mark.asyncio
async def test_full_conversation_flow_whatsapp_only():
    """Test flujo completo sin detección de canales (usando FactoryOrchestrator)"""
    conversation_id = "integration_test_whatsapp_001"
    orchestrator = FactoryOrchestrator()

    # 1. Primer contacto → ReceptionAgent
    message_data1 = {
        "from": conversation_id,
        "text": {"body": "Hola, necesito información sobre apartamentos"}
    }

    # Obtener o crear conversación inicial
    conversation1 = state_manager.get_or_create_conversation(conversation_id)

    # Convertir a dict para process_message
    conv_dict1 = {
        "whatsapp_id": conversation1.whatsapp_id,
        "state": conversation1.state,
        "customer_name": conversation1.customer_name,
        "current_agent": None
    }

    agent1 = await orchestrator._select_agent(message_data1, conv_dict1)
    assert agent1 is not None

    result1 = await agent1.process_message(message_data1, conv_dict1)
    assert result1 is not None
    assert "response" in result1

    # Verificar que estado NO contiene campo channel
    state = state_manager.get_conversation(conversation_id)
    assert not hasattr(state, 'channel')


@pytest.mark.asyncio
async def test_orchestrator_without_channel_parameter():
    """FactoryOrchestrator funciona sin parámetro channel"""
    conversation_id = "test_no_channel_param"
    orchestrator = FactoryOrchestrator()

    # Crear estado
    state = ConversationState(conversation_id=conversation_id, current_agent=None)

    # ✅ Llamada sin channel (debe funcionar)
    agent = orchestrator.select_agent("Hola, busco casa", state)

    assert agent is not None
    assert hasattr(agent, 'process_message')

    # Verificar que estado NO tiene campo channel
    assert not hasattr(state, 'channel')