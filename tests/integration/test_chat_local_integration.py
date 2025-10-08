# -*- coding: utf-8 -*-
"""
Tests de integración para chat_local.py con FactoryOrchestrator
Verifica que el flujo tri-path funciona correctamente en el chat local
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state
from app.state.crud_operations import ConversationCRUD


@pytest.fixture(scope="function")
def cleanup_test_conversation():
    """Limpia conversación de prueba antes y después del test"""
    test_phone = "573123456789"
    crud = ConversationCRUD()

    # Limpiar antes
    try:
        crud.delete_conversation(test_phone)
    except:
        pass

    yield test_phone

    # Limpiar después
    try:
        crud.delete_conversation(test_phone)
    except:
        pass


@pytest.mark.asyncio
async def test_chat_local_uses_factory_orchestrator(cleanup_test_conversation):
    """Test que chat_local.py usa FactoryOrchestrator correctamente"""
    from chat_local import initialize_system, process_user_message

    initialize_database()
    test_phone = cleanup_test_conversation

    # Inicializar sistema
    orchestrator = await initialize_system()

    # Verificar que es FactoryOrchestrator
    from app.core.factory_orchestrator import FactoryOrchestrator
    assert isinstance(orchestrator, FactoryOrchestrator)
    assert orchestrator.initialized is True

    # Limpiar conversación si existe
    crud = ConversationCRUD()
    try:
        crud.delete_conversation(test_phone)
    except:
        pass

    # Procesar mensaje simple
    await process_user_message("Hola", orchestrator)

    # Verificar que se creó conversación
    conversation = get_conversation_state(test_phone)
    assert conversation is not None
    assert conversation["state"] in ["NUEVO", "POLITICAS_PRESENTADAS", "RECOPILANDO_NOMBRE"]


@pytest.mark.asyncio
async def test_chat_local_tri_path_support_agent(cleanup_test_conversation):
    """Test que el flujo tri-path funciona con SupportAgent"""
    from chat_local import initialize_system, process_user_message

    initialize_database()
    test_phone = cleanup_test_conversation

    orchestrator = await initialize_system()

    # Mensaje que debería activar SupportAgent
    await process_user_message("¿Cuáles son sus horarios de atención?", orchestrator)

    # Verificar que se procesó
    conversation = get_conversation_state(test_phone)
    assert conversation is not None


@pytest.mark.asyncio
async def test_chat_local_hot_reload_creates_fresh_agents(cleanup_test_conversation):
    """Test que cada mensaje crea agentes fresh (hot reload)"""
    from chat_local import initialize_system
    from app.core.factory_orchestrator import FactoryOrchestrator

    initialize_database()
    test_phone = cleanup_test_conversation

    orchestrator = await initialize_system()

    # Crear conversación inicial
    update_conversation_state(test_phone, "NUEVO")
    conversation = get_conversation_state(test_phone)

    message_data = {
        "from": test_phone,
        "text": {"body": "Hola"}
    }

    # Seleccionar agente 2 veces
    agent1 = await orchestrator._select_agent(message_data, conversation)
    agent2 = await orchestrator._select_agent(message_data, conversation)

    # Verificar que son instancias diferentes (fresh)
    assert agent1 is not None
    assert agent2 is not None
    assert agent1 is not agent2
    assert id(agent1) != id(agent2)


@pytest.mark.asyncio
async def test_chat_local_handles_transferido_state(cleanup_test_conversation):
    """Test que el chat local maneja correctamente el estado TRANSFERIDO"""
    from chat_local import initialize_system, process_user_message

    initialize_database()
    test_phone = cleanup_test_conversation

    orchestrator = await initialize_system()

    # Crear conversación en estado TRANSFERIDO
    update_conversation_state(test_phone, "TRANSFERIDO")

    # Intentar procesar mensaje
    await process_user_message("Hola después de transferir", orchestrator)

    # Verificar que se reseteo la conversación (comportamiento esperado del chat local)
    conversation = get_conversation_state(test_phone)
    assert conversation is not None
    # El estado debería ser NUEVO después del reset
    assert conversation["state"] == "NUEVO"


@pytest.mark.asyncio
async def test_chat_local_process_message_captures_response(cleanup_test_conversation):
    """Test que process_user_message captura la respuesta correctamente"""
    from chat_local import initialize_system, process_user_message

    initialize_database()
    test_phone = cleanup_test_conversation

    orchestrator = await initialize_system()

    # Capturar output de print
    import io
    from contextlib import redirect_stdout

    output = io.StringIO()

    with redirect_stdout(output):
        await process_user_message("Hola", orchestrator)

    output_text = output.getvalue()

    # Verificar que hay output de Sofia
    assert "[Sofia]" in output_text or "[Asistente]" in output_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
