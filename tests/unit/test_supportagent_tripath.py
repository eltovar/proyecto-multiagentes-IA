# -*- coding: utf-8 -*-
"""
Tests unitarios para SupportAgent - Tri-Path Routing
Valida CAMINO 1 (inmueble), CAMINO 2 (departamento), CAMINO 3 (general)
"""

import pytest
import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture
def mock_services():
    """Mock LLM and RAG services before importing agent"""
    with patch('app.agents.support_agent.llm_service') as mock_llm, \
         patch('app.agents.support_agent.rag_system') as mock_rag:

        # Configure LLM mock
        mock_llm.api_client.initialized = True
        mock_llm.api_client.client = AsyncMock()
        mock_llm.initialize = MagicMock(return_value=True)
        mock_llm.classify_with_prompt = AsyncMock()

        # Configure RAG mock
        mock_rag.initialized = True
        mock_rag.initialize = MagicMock(return_value=True)
        mock_rag.search = AsyncMock()

        yield mock_llm, mock_rag


@pytest.fixture
def support_agent(mock_services):
    """Create SupportAgent with mocked services"""
    from app.agents.support_agent import SupportAgent

    mock_llm, mock_rag = mock_services
    agent = SupportAgent()

    # Ensure mocks are assigned
    agent.llm_service = mock_llm
    agent.rag_system = mock_rag

    return agent


@pytest.fixture
def conversation_data():
    """Base conversation data"""
    return {
        "whatsapp_id": "+573001234567",
        "state": "INITIAL",
        "customer_name": "Juan Pérez"
    }


@pytest.mark.asyncio
async def test_camino_1_inmueble_rag_message(support_agent, conversation_data, mock_services):
    """
    CAMINO 1: Inmueble con mensaje generado por RAG+LLM

    Verifica:
    - Classification intent = "inmueble"
    - Transfer a ReceptionAgent
    - Usa contexto RAG para generar mensaje
    - data_updates contiene rag_context_used = True
    """
    mock_llm, mock_rag = mock_services

    # Mock classification response
    mock_llm.api_client.client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "intent": "inmueble",
                        "sub_intent": None,
                        "confidence": 0.95,
                        "entities": {
                            "property_type": "apartamento",
                            "location": "Medellín"
                        },
                        "reasoning": "Usuario busca apartamento"
                    })
                )
            )]
        )
    )

    # Mock RAG search
    mock_rag.search.return_value = {
        "context": "Nuestros asesores te contactarán para agendar visitas a apartamentos.",
        "documents": [{"content": "Proceso de visitas...", "score": 0.89}],
        "phone_numbers": []
    }

    # Mock LLM message generation (TEXT mode)
    mock_llm.classify_with_prompt.return_value = (
        "¡Perfecto Juan! Te conectaré con nuestros asesores para agendar tu visita al apartamento."
    )

    # Execute
    message_data = {"text": "Busco apartamento en Medellín"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "transfer_to" in result
    assert result["transfer_to"] == "ReceptionAgent"

    # Verify data_updates
    assert "data_updates" in result
    data = result["data_updates"]
    assert data["intent"] == "inmueble"
    assert data["routing_path"] == "CAMINO_1_INMUEBLE"
    assert data["rag_context_used"] == True

    # Verify RAG was called
    mock_rag.search.assert_called_once()

    # Verify LLM message generation was called with TEXT mode
    assert mock_llm.classify_with_prompt.call_count > 0
    call_args = mock_llm.classify_with_prompt.call_args
    assert call_args[1]["response_format"] == "text"


@pytest.mark.asyncio
async def test_camino_2_departamento_transferido_state(support_agent, conversation_data, mock_services):
    """
    CAMINO 2: Departamento establece estado TRANSFERIDO

    Verifica:
    - Classification intent = "departamento"
    - new_state = "TRANSFERIDO" (handoff)
    - data_updates contiene handoff_reason
    """
    mock_llm, mock_rag = mock_services

    # Mock classification
    mock_llm.api_client.client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "intent": "departamento",
                        "sub_intent": "reparaciones",
                        "confidence": 0.92,
                        "entities": {},
                        "reasoning": "Usuario reporta problema de reparación"
                    })
                )
            )]
        )
    )

    # Mock RAG with phone numbers
    mock_rag.search.return_value = {
        "context": "Departamento de Reparaciones: 3001234567",
        "documents": [{"content": "Reparaciones...", "score": 0.91}],
        "phone_numbers": ["3001234567"]
    }

    # Execute
    message_data = {"text": "Tengo una fuga de agua urgente"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "new_state" in result
    assert result["new_state"] == "TRANSFERIDO"  # ✅ Estado correcto

    # Verify data_updates
    data = result["data_updates"]
    assert data["intent"] == "departamento"
    assert data["sub_intent"] == "reparaciones"
    assert data["routing_path"] == "CAMINO_2_DEPARTAMENTO"
    assert "handoff_reason" in data
    assert data["handoff_reason"] == "department_reparaciones"


@pytest.mark.asyncio
async def test_camino_2_fallback_department_contacts(support_agent, conversation_data, mock_services):
    """
    CAMINO 2: Fallback a DEPARTMENT_CONTACTS si RAG no tiene números

    Verifica:
    - Si RAG no tiene números, usa DEPARTMENT_CONTACTS
    - phone_numbers en data_updates contiene número de config
    """
    mock_llm, mock_rag = mock_services

    # Mock classification
    mock_llm.api_client.client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "intent": "departamento",
                        "sub_intent": "propietarios",
                        "confidence": 0.88,
                        "entities": {},
                        "reasoning": "Consulta para propietarios"
                    })
                )
            )]
        )
    )

    # Mock RAG without phone numbers
    mock_rag.search.return_value = {
        "context": "Información para propietarios...",
        "documents": [{"content": "...", "score": 0.85}],
        "phone_numbers": []  # Sin números
    }

    # Execute
    message_data = {"text": "Información para propietarios"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "new_state" in result
    assert result["new_state"] == "TRANSFERIDO"

    # Verify fallback
    data = result["data_updates"]
    phones = json.loads(data["phone_numbers"])
    assert len(phones) == 1

    # Verify phone is from config
    from app.config import DEPARTMENT_CONTACTS
    assert phones[0] == DEPARTMENT_CONTACTS["propietarios"]["phone"]


@pytest.mark.asyncio
async def test_camino_3_general_with_rag(support_agent, conversation_data, mock_services):
    """
    CAMINO 3: General usa RAG context

    Verifica:
    - Classification intent = "general"
    - No transfer (respuesta directa)
    - LLM generator usa contexto RAG
    """
    mock_llm, mock_rag = mock_services

    # Mock classification
    mock_llm.api_client.client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "intent": "general",
                        "confidence": 0.78,
                        "entities": {},
                        "reasoning": "Pregunta sobre horarios"
                    })
                )
            )]
        )
    )

    # Mock RAG
    mock_rag.search.return_value = {
        "context": "Horario: Lunes a viernes 9am-6pm.",
        "documents": [{"content": "Horarios...", "score": 0.87}],
        "phone_numbers": []
    }

    # Mock LLM generator
    mock_llm.llm_generator = MagicMock()
    mock_llm.llm_generator.generate_contextual_response = AsyncMock(
        return_value="Nuestro horario es lunes a viernes de 9am a 6pm."
    )

    # Execute
    message_data = {"text": "¿Cuál es el horario?"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "response" in result
    assert "transfer_to" not in result  # No transfer

    # Verify generator was called with context
    mock_llm.llm_generator.generate_contextual_response.assert_called_once()
    call_kwargs = mock_llm.llm_generator.generate_contextual_response.call_args[1]
    assert "context" in call_kwargs
    assert "Horario" in call_kwargs["context"]


@pytest.mark.asyncio
async def test_low_confidence_transfer(support_agent, conversation_data, mock_services):
    """
    Test: Confianza baja → Transfer a ReceptionAgent
    """
    mock_llm, mock_rag = mock_services

    # Mock classification con baja confianza
    mock_llm.api_client.client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "intent": "unclear",
                        "confidence": 0.35,
                        "entities": {},
                        "reasoning": "Mensaje ambiguo"
                    })
                )
            )]
        )
    )

    mock_rag.search.return_value = {
        "context": "",
        "documents": [],
        "phone_numbers": []
    }

    # Execute
    message_data = {"text": "xyz abc"}
    result = await support_agent.process_message(message_data, conversation_data)

    # Assert
    assert "transfer_to" in result
    assert result["transfer_to"] == "ReceptionAgent"
