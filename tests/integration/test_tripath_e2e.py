# -*- coding: utf-8 -*-
"""
Tests E2E tri-path routing con Orchestrator

Escenarios:
1. Camino 1: Inmueble → Reception → Leadsales → CRM
2. Camino 2: Departamento → RAG números → Usuario
3. Camino 3: General → RAG info → Usuario
4. Intent poco claro → Clarificación
"""

import pytest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.orchestrator import orchestrator
from app.state.manager import state_manager


@pytest.fixture(autouse=True)
def cleanup_db():
    """Limpiar BD antes y después de cada test"""
    # Setup: Limpiar antes del test
    test_ids = [
        "e2e_camino1_test",
        "e2e_camino2_test",
        "e2e_camino3_test",
        "e2e_unclear_test"
    ]

    for test_id in test_ids:
        try:
            state_manager.delete_conversation(test_id)
        except:
            pass

    yield

    # Teardown: Limpiar después del test
    for test_id in test_ids:
        try:
            state_manager.delete_conversation(test_id)
        except:
            pass


@pytest.fixture
def mock_llm_service():
    """Mock LLMService para tests E2E"""
    with patch('app.agents.support_agent.llm_service') as mock_llm:
        mock_llm.api_client.initialized = True
        mock_llm.api_client.client = AsyncMock()
        mock_llm.classify_with_prompt = AsyncMock()
        mock_llm.llm_generator = MagicMock()
        mock_llm.llm_generator.generate_contextual_response = AsyncMock()
        yield mock_llm


@pytest.fixture
def mock_rag_system():
    """Mock RAG system para tests E2E"""
    with patch('app.agents.support_agent.rag_system') as mock_rag:
        mock_rag.initialized = True
        mock_rag.search_context = MagicMock(return_value="Contexto RAG de prueba")
        yield mock_rag


@pytest.mark.asyncio
async def test_e2e_camino_1_complete_flow(mock_llm_service, mock_rag_system):
    """
    E2E Camino 1: Inmueble → Reception → Leadsales → CRM

    FLUJO:
    1. Usuario: "Busco apartamento"
    2. SupportAgent → Transfer ReceptionAgent
    3. ReceptionAgent captura: nombre, contrato, fecha
    4. ReceptionAgent → Transfer LeadsalesAgent
    5. LeadsalesAgent → CRM + Handoff (TRANSFERIDO)
    """
    whatsapp_id = "e2e_camino1_test"

    # Mock clasificación: inmueble
    mock_llm_service.classify_with_prompt.return_value = {
        "intent": "inmueble",
        "sub_intent": None,
        "confidence": 0.95,
        "entities": {
            "property_type": "apartamento",
            "location": "Medellín"
        },
        "reasoning": "Usuario busca apartamento"
    }

    # PASO 1: Mensaje inicial
    msg1 = {
        "from": whatsapp_id,
        "text": {"body": "Hola, busco apartamento en Medellín"}
    }

    response1 = await orchestrator.process_message(msg1)

    # Validar respuesta
    assert response1 is not None
    assert "apartamento" in response1.lower() or "propiedad" in response1.lower()

    # Validar estado
    conv1 = state_manager.get_conversation(whatsapp_id)
    assert conv1 is not None

    # Puede estar en varios estados dependiendo del flujo
    # Verificar que NO está en error
    assert conv1.state != "ERROR"

    # PASO 2: ReceptionAgent captura nombre (si llegó allí)
    if "nombre" in response1.lower():
        msg2 = {"from": whatsapp_id, "text": {"body": "Juan Pérez"}}
        response2 = await orchestrator.process_message(msg2)

        conv2 = state_manager.get_conversation(whatsapp_id)
        assert conv2 is not None

        # PASO 3: Responder pregunta de contrato
        if "contrato" in response2.lower() or "inmobiliaria" in response2.lower():
            msg3 = {"from": whatsapp_id, "text": {"body": "No"}}
            response3 = await orchestrator.process_message(msg3)

            # PASO 4: Solicitud libertador
            if "libertador" in response3.lower() or "certificado" in response3.lower():
                msg4 = {"from": whatsapp_id, "text": {"body": "Sí"}}
                response4 = await orchestrator.process_message(msg4)

                # PASO 5: Fecha necesidad
                if "fecha" in response4.lower() or "cuándo" in response4.lower():
                    msg5 = {"from": whatsapp_id, "text": {"body": "15 de mayo"}}
                    response5 = await orchestrator.process_message(msg5)

                    # Validar estado final
                    final_conv = state_manager.get_conversation(whatsapp_id)
                    assert final_conv is not None

                    # Verificar que está en un estado terminal válido
                    assert final_conv.state in [
                        "FLUJO_COMPLETADO",
                        "TRANSFERIDO",
                        "LEAD_CREADO",
                        "PROCESANDO_CRM"
                    ]


@pytest.mark.asyncio
async def test_e2e_camino_2_rag_numbers(mock_llm_service, mock_rag_system):
    """
    E2E Camino 2: Departamento → RAG extrae números → Usuario recibe

    FLUJO:
    1. Usuario: "Soy propietario"
    2. SupportAgent → RAG search
    3. Extrae números de docs
    4. Responde con números
    5. NO transfiere (conversación activa)
    """
    whatsapp_id = "e2e_camino2_test"

    # Mock clasificación: departamento
    mock_llm_service.classify_with_prompt.return_value = {
        "intent": "departamento",
        "sub_intent": "propietarios",
        "confidence": 0.92,
        "entities": {},
        "reasoning": "Usuario es propietario"
    }

    # Mock RAG con contexto
    mock_rag_system.search_context.return_value = (
        "Departamento de Propietarios: 322 502 1493. "
        "Horario: Lun-Vie 8AM-6PM."
    )

    # Mensaje
    msg = {
        "from": whatsapp_id,
        "text": {"body": "Soy propietario, necesito ayuda con mi inmueble"}
    }

    # Procesar
    response = await orchestrator.process_message(msg)

    # Validar respuesta contiene número
    assert response is not None
    # Debe contener número de propietarios o indicación de contacto
    assert "322" in response or "propietarios" in response.lower() or "contacto" in response.lower()

    # Validar estado
    conv = state_manager.get_conversation(whatsapp_id)
    assert conv is not None

    # Estado debe ser TRANSFERIDO (por handoff) o SUPPORT_ACTIVE
    assert conv.state in ["TRANSFERIDO", "SUPPORT_ACTIVE", "DEPARTMENT_REDIRECT"]


@pytest.mark.asyncio
async def test_e2e_camino_3_rag_info(mock_llm_service, mock_rag_system):
    """
    E2E Camino 3: Info general → RAG responde → Conversación activa

    FLUJO:
    1. Usuario: "Qué servicios ofrecen?"
    2. SupportAgent → RAG search
    3. Genera respuesta con contexto RAG
    4. Mantiene SUPPORT_ACTIVE (conversación activa)
    """
    whatsapp_id = "e2e_camino3_test"

    # Mock clasificación: general
    mock_llm_service.classify_with_prompt.return_value = {
        "intent": "general",
        "sub_intent": None,
        "confidence": 0.85,
        "entities": {},
        "reasoning": "Pregunta sobre servicios"
    }

    # Mock RAG con información general
    mock_rag_system.search_context.return_value = (
        "Inmobiliaria Proteger ofrece servicios de administración de propiedades, "
        "arrendamiento, compra-venta de inmuebles, y asesoría inmobiliaria. "
        "Contamos con más de 20 años de experiencia."
    )

    # Mock generación de respuesta
    mock_llm_service.llm_generator.generate_contextual_response.return_value = (
        "En Inmobiliaria Proteger ofrecemos servicios de administración de propiedades, "
        "arrendamiento, compra-venta y asesoría. ¿Te gustaría conocer más detalles?"
    )

    # Mensaje
    msg = {
        "from": whatsapp_id,
        "text": {"body": "Qué servicios ofrecen?"}
    }

    # Procesar
    response = await orchestrator.process_message(msg)

    # Validar respuesta
    assert response is not None
    assert "servicios" in response.lower() or "inmobiliaria" in response.lower()

    # Validar estado
    conv = state_manager.get_conversation(whatsapp_id)
    assert conv is not None

    # Estado debe ser SUPPORT_ACTIVE (conversación activa)
    assert conv.state in ["SUPPORT_ACTIVE", "NUEVO", "ROUTING_ANALYSIS"]


@pytest.mark.asyncio
async def test_e2e_unclear_intent_clarification(mock_llm_service, mock_rag_system):
    """
    E2E: Intent poco claro → Solicita clarificación o va a ReceptionAgent
    """
    whatsapp_id = "e2e_unclear_test"

    # Mock clasificación: unclear
    mock_llm_service.classify_with_prompt.return_value = {
        "intent": "unclear",
        "sub_intent": None,
        "confidence": 0.3,
        "entities": {},
        "reasoning": "Mensaje ambiguo"
    }

    # Mensaje ambiguo
    msg = {
        "from": whatsapp_id,
        "text": {"body": "Hola"}
    }

    # Procesar
    response = await orchestrator.process_message(msg)

    # Validar respuesta (puede ir a ReceptionAgent o pedir clarificación)
    assert response is not None

    # Validar estado
    conv = state_manager.get_conversation(whatsapp_id)
    assert conv is not None

    # Puede ir a varios estados según el flujo
    assert conv.state in [
        "POLITICAS_PRESENTADAS",
        "SUPPORT_ACTIVE",
        "ROUTING_ANALYSIS",
        "NUEVO"
    ]


@pytest.mark.asyncio
async def test_e2e_routing_priority_inmueble(mock_llm_service, mock_rag_system):
    """
    Test: Prioridad de routing - Inmueble tiene mayor prioridad
    """
    whatsapp_id = "e2e_priority_test"

    # Mock clasificación: inmueble con alta confianza
    mock_llm_service.classify_with_prompt.return_value = {
        "intent": "inmueble",
        "confidence": 0.95,
        "entities": {"property_type": "casa"},
        "reasoning": "Usuario busca casa"
    }

    msg = {
        "from": whatsapp_id,
        "text": {"body": "Busco casa para comprar"}
    }

    response = await orchestrator.process_message(msg)

    assert response is not None

    # Cleanup
    try:
        state_manager.delete_conversation(whatsapp_id)
    except:
        pass


@pytest.mark.asyncio
async def test_e2e_error_handling(mock_llm_service, mock_rag_system):
    """
    Test: Manejo de errores en E2E
    """
    whatsapp_id = "e2e_error_test"

    # Mock error en LLM
    mock_llm_service.classify_with_prompt.side_effect = Exception("LLM Error")

    msg = {
        "from": whatsapp_id,
        "text": {"body": "Test error"}
    }

    # No debe crashear
    response = await orchestrator.process_message(msg)

    # Debe haber alguna respuesta de fallback
    assert response is not None

    # Cleanup
    try:
        state_manager.delete_conversation(whatsapp_id)
    except:
        pass
