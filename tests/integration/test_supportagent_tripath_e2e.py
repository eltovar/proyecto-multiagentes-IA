# -*- coding: utf-8 -*-
"""
Tests E2E para SupportAgent - Tri-Path RAG-First
Valida CAMINO 1 (inmueble), CAMINO 2 (departamento), CAMINO 3 (general)
"""

import pytest
import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agents.support_agent import SupportAgent
from app.state.manager import state_manager


@pytest.fixture
def support_agent():
    """Fixture: SupportAgent con servicios mockeados"""
    with patch('app.agents.support_agent.rag_system') as mock_rag:
        # Pre-configure mocks BEFORE agent initialization
        mock_rag.initialized = True
        mock_rag.search = AsyncMock()

        with patch('app.services.llm_service.LLMService') as mock_llm_class:
            mock_llm_instance = MagicMock()
            mock_llm_instance.api_client.initialized = True
            mock_llm_instance.api_client.client = AsyncMock()
            mock_llm_instance.initialize = MagicMock()  # No-op
            mock_llm_class.return_value = mock_llm_instance

            # Now create agent (won't block on initialization)
            agent = SupportAgent()
            agent.llm_service = mock_llm_instance
            agent.rag_system = mock_rag

            yield agent


@pytest.fixture
def conversation_data():
    """Fixture: Datos de conversación base"""
    return {
        "whatsapp_id": "+573001234567",
        "state": "INITIAL",
        "customer_name": "Juan Pérez"
    }


@pytest.mark.asyncio
async def test_camino_1_inmueble_with_rag(support_agent, conversation_data):
    """
    Test E2E CAMINO 1: Usuario busca inmueble

    Flow:
    1. LLM clasifica como "inmueble" con confianza alta
    2. RAG encuentra contexto relevante
    3. LLM genera mensaje personalizado con RAG
    4. Transfer a ReceptionAgent con metadata
    """

    # Mock LLM classification response
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "inmueble",
        "sub_intent": None,
        "confidence": 0.95,
        "entities": {
            "property_type": "apartamento",
            "location": "Medellín",
            "action": "arrendar"
        },
        "reasoning": "Usuario busca apartamento en arriendo"
    })

    # Mock RAG search result
    support_agent.rag_system.search.return_value = {
        "context": "Para agendar visitas a apartamentos en Medellín, nuestros asesores te contactarán. Horario: lunes a viernes 9am-6pm.",
        "documents": [{"content": "Proceso de visitas...", "score": 0.89}],
        "phone_numbers": []
    }

    # Mock LLM message generation (TEXT mode)
    mock_message_gen = MagicMock()
    mock_message_gen.choices = [MagicMock()]
    mock_message_gen.choices[0].message.content = (
        "¡Perfecto Juan! Busco apartamentos en arriendo en Medellín. "
        "Te conectaré con nuestros asesores que te contactarán para agendar visitas. "
        "Horario de atención: lunes a viernes 9am-6pm."
    )

    # Setup mocks
    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        side_effect=[mock_classification, mock_message_gen]
    )

    # Execute
    message_data = {"text": "Busco apartamento en arriendo en Medellín"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "transfer_to" in result
    assert result["transfer_to"] == "ReceptionAgent"

    # Verify data_updates
    assert "data_updates" in result
    data_updates = result["data_updates"]
    assert data_updates["intent"] == "inmueble"
    assert data_updates["routing_path"] == "CAMINO_1_INMUEBLE"
    assert data_updates["rag_context_used"] == True

    # Verify classification was parsed
    classification = json.loads(data_updates["classification"])
    assert classification["intent"] == "inmueble"
    assert classification["entities"]["property_type"] == "apartamento"
    assert classification["entities"]["location"] == "Medellín"

    # Verify RAG was called
    support_agent.rag_system.search.assert_called_once()


@pytest.mark.asyncio
async def test_camino_2_departamento_with_phones(support_agent, conversation_data):
    """
    Test E2E CAMINO 2: Usuario necesita departamento específico

    Flow:
    1. LLM clasifica como "departamento" con sub_intent "reparaciones"
    2. RAG encuentra números de contacto
    3. Response incluye números extraídos
    4. Estado cambia a TRANSFERIDO (handoff)
    """

    # Mock LLM classification response
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "departamento",
        "sub_intent": "reparaciones",
        "confidence": 0.92,
        "entities": {},
        "reasoning": "Usuario reporta problema de reparación"
    })

    # Mock RAG search result with phone numbers
    support_agent.rag_system.search.return_value = {
        "context": "Departamento de Reparaciones: Contacto 3001234567",
        "documents": [{"content": "Reparaciones...", "score": 0.91}],
        "phone_numbers": ["3001234567", "3007654321"]
    }

    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        return_value=mock_classification
    )

    # Execute
    message_data = {"text": "Tengo una fuga de agua urgente"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "3001234567" in result["response"]  # Phone number in response
    assert "new_state" in result
    assert result["new_state"] == "TRANSFERIDO"  # ✅ Handoff activado

    # Verify data_updates
    assert "data_updates" in result
    data_updates = result["data_updates"]
    assert data_updates["intent"] == "departamento"
    assert data_updates["sub_intent"] == "reparaciones"
    assert data_updates["routing_path"] == "CAMINO_2_DEPARTAMENTO"
    assert "handoff_reason" in data_updates
    assert data_updates["handoff_reason"] == "department_reparaciones"

    # Verify phone numbers stored
    phone_numbers = json.loads(data_updates["phone_numbers"])
    assert len(phone_numbers) == 2
    assert "3001234567" in phone_numbers


@pytest.mark.asyncio
async def test_camino_2_departamento_fallback_config(support_agent, conversation_data):
    """
    Test E2E CAMINO 2: Fallback a DEPARTMENT_CONTACTS si RAG no tiene números

    Flow:
    1. LLM clasifica como "departamento" con sub_intent "propietarios"
    2. RAG no encuentra números
    3. Usa DEPARTMENT_CONTACTS como fallback
    4. Estado TRANSFERIDO
    """

    # Mock LLM classification
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "departamento",
        "sub_intent": "propietarios",
        "confidence": 0.88,
        "entities": {},
        "reasoning": "Consulta para propietarios"
    })

    # Mock RAG search without phone numbers
    support_agent.rag_system.search.return_value = {
        "context": "Información para propietarios...",
        "documents": [{"content": "...", "score": 0.85}],
        "phone_numbers": []  # Sin números en RAG
    }

    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        return_value=mock_classification
    )

    # Execute
    message_data = {"text": "Información para propietarios"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "new_state" in result
    assert result["new_state"] == "TRANSFERIDO"

    # Verify fallback to config
    data_updates = result["data_updates"]
    phone_numbers = json.loads(data_updates["phone_numbers"])
    assert len(phone_numbers) == 1
    # Verificar que usó el número de DEPARTMENT_CONTACTS["propietarios"]
    from app.config import DEPARTMENT_CONTACTS
    assert phone_numbers[0] == DEPARTMENT_CONTACTS["propietarios"]["phone"]


@pytest.mark.asyncio
async def test_camino_3_general_with_rag_llm(support_agent, conversation_data):
    """
    Test E2E CAMINO 3: Información general con RAG + LLM

    Flow:
    1. LLM clasifica como "general" con confianza media
    2. RAG encuentra contexto relevante
    3. LLM genera respuesta contextualizada
    4. No transfer, respuesta directa
    """

    # Mock LLM classification
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "general",
        "sub_intent": None,
        "confidence": 0.78,
        "entities": {},
        "reasoning": "Pregunta sobre horarios"
    })

    # Mock RAG search
    support_agent.rag_system.search.return_value = {
        "context": "Horario de atención: Lunes a viernes 9am-6pm. Sábados 10am-2pm.",
        "documents": [{"content": "Horarios...", "score": 0.87}],
        "phone_numbers": []
    }

    # Mock LLM contextual response generation
    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        return_value=mock_classification
    )

    # Mock generator
    support_agent.llm_service.llm_generator = MagicMock()
    support_agent.llm_service.llm_generator.generate_contextual_response = AsyncMock(
        return_value=(
            "¡Claro! Nuestro horario de atención es lunes a viernes de 9am a 6pm, "
            "y sábados de 10am a 2pm. ¿Hay algo más en lo que pueda ayudarte?"
        )
    )

    # Execute
    message_data = {"text": "¿Cuál es el horario de atención?"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "9am" in result["response"] or "horario" in result["response"].lower()
    assert "transfer_to" not in result  # No transfer para general

    # Verify RAG was used
    support_agent.rag_system.search.assert_called_once()

    # Verify LLM generator was called
    support_agent.llm_service.llm_generator.generate_contextual_response.assert_called_once()


@pytest.mark.asyncio
async def test_camino_3_general_without_rag_fallback(support_agent, conversation_data):
    """
    Test E2E CAMINO 3: Fallback cuando RAG no tiene contexto

    Flow:
    1. LLM clasifica como "general"
    2. RAG no encuentra contexto relevante
    3. Respuesta genérica de fallback
    """

    # Mock LLM classification
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "general",
        "sub_intent": None,
        "confidence": 0.65,
        "entities": {},
        "reasoning": "Pregunta genérica"
    })

    # Mock RAG search sin contexto
    support_agent.rag_system.search.return_value = {
        "context": "",  # Sin contexto
        "documents": [],
        "phone_numbers": []
    }

    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        return_value=mock_classification
    )

    # Execute
    message_data = {"text": "¿Tienen seguro de mascotas?"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "equipo" in result["response"].lower() or "mejor manera" in result["response"].lower()


@pytest.mark.asyncio
async def test_low_confidence_fallback_to_reception(support_agent, conversation_data):
    """
    Test: Confianza baja → Transfer a ReceptionAgent

    Flow:
    1. LLM clasifica con confianza < 0.5
    2. Transfer automático a ReceptionAgent
    """

    # Mock LLM classification con baja confianza
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "unclear",
        "sub_intent": None,
        "confidence": 0.35,
        "entities": {},
        "reasoning": "Mensaje ambiguo"
    })

    support_agent.rag_system.search.return_value = {
        "context": "",
        "documents": [],
        "phone_numbers": []
    }

    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        return_value=mock_classification
    )

    # Execute
    message_data = {"text": "xyz abc"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "transfer_to" in result
    assert result["transfer_to"] == "ReceptionAgent"


@pytest.mark.asyncio
async def test_rag_search_error_handling(support_agent, conversation_data):
    """
    Test: Manejo de errores en RAG search

    Flow:
    1. RAG search falla con excepción
    2. Continúa flujo sin contexto RAG
    3. No crashea, usa fallback
    """

    # Mock LLM classification
    mock_classification = MagicMock()
    mock_classification.choices = [MagicMock()]
    mock_classification.choices[0].message.content = json.dumps({
        "intent": "general",
        "confidence": 0.7,
        "entities": {},
        "reasoning": "Test"
    })

    # Mock RAG search que falla
    support_agent.rag_system.search.side_effect = Exception("RAG service unavailable")

    support_agent.llm_service.api_client.client.chat.completions.create = AsyncMock(
        return_value=mock_classification
    )

    # Execute
    message_data = {"text": "Test message"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert - No crashea
    assert "response" in result
    assert isinstance(result["response"], str)
