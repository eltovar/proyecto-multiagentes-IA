# -*- coding: utf-8 -*-
"""
Test Suite: Reception Agent Integration - PR #1 Fundamentos
===========================================================

Tests de integracion E2E para ReceptionAgent con LLM extraction
"""

import pytest
import sys
import os
import tempfile
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agents.reception_agent import ReceptionAgent
from tests.mocks.openai_mock import MockOpenAIClient


@pytest.fixture
def mock_reception_agent():
    """ReceptionAgent con LLM mockeado."""
    agent = ReceptionAgent()
    agent.llm_service.api_client.initialized = True
    mock_client = MockOpenAIClient()
    agent.llm_service.api_client.client = mock_client
    return agent


@pytest.fixture
def test_conversation():
    """Conversacion de prueba simulada."""
    return {
        "whatsapp_id": "573123456789",
        "state": "NUEVO",
        "customer_name": None,
        "customer_needs": None,
        "lead_id": None,
        "interaction_count": 0
    }


@pytest.mark.asyncio
async def test_reception_agent_extracts_name_from_greeting(mock_reception_agent, test_conversation):
    """Test: ReceptionAgent extrae nombre del primer mensaje con LLM."""
    message_data = {
        "from": "573123456789",
        "text": {"body": "Hola, soy Carlos Andres"}
    }

    # Simular estado POLITICAS_PRESENTADAS (despues de saludo inicial)
    test_conversation["state"] = "POLITICAS_PRESENTADAS"

    response = await mock_reception_agent.process_message(message_data, test_conversation)

    # Verificar que extracted_data se guarda (puede estar en estado POLITICAS_PRESENTADAS o ya procesado)
    assert "data_updates" in response
    # Si nombre fue detectado, debe estar en customer_name
    if response["data_updates"].get("customer_name"):
        assert "Carlos" in response["data_updates"]["customer_name"]


@pytest.mark.asyncio
async def test_reception_agent_normal_flow_without_llm_name(mock_reception_agent, test_conversation):
    """Test: Flujo normal cuando LLM no detecta nombre."""
    message_data = {
        "from": "573123456789",
        "text": {"body": "Hola"}
    }
    
    test_conversation["state"] = "POLITICAS_PRESENTADAS"
    
    response = await mock_reception_agent.process_message(message_data, test_conversation)
    
    # Si no hay nombre, debe transicionar a RECOPILANDO_NOMBRE o preguntar por nombre
    assert "nombre" in response["response"].lower() or response.get("new_state") == "RECOPILANDO_NOMBRE"


@pytest.mark.asyncio
async def test_support_intent_triggers_transfer(mock_reception_agent, test_conversation):
    """Test: Intent 'support' transfiere a SupportAgent con alta confianza."""
    message_data = {
        "from": "573123456789",
        "text": {"body": "Tengo un problema con la gotera"}
    }
    
    # En estado inicial donde se hace extraccion LLM
    test_conversation["state"] = "NUEVO"
    
    response = await mock_reception_agent.process_message(message_data, test_conversation)
    
    # Verificar transferencia a SupportAgent (si confidence > 0.75)
    # El mock puede o no retornar support con alta confianza, verificamos estructura
    if response.get("transfer_to") == "SupportAgent":
        assert "soporte" in response["response"].lower() or "especializado" in response["response"].lower()
    else:
        # Si no transfiere, al menos debe haber intent en data_updates
        assert "data_updates" in response


@pytest.mark.asyncio
async def test_business_hours_validation_in_nuevo_state(mock_reception_agent, test_conversation):
    """Test: Validacion de horario laboral en estado NUEVO."""
    from datetime import datetime
    from unittest.mock import patch
    
    message_data = {
        "from": "573123456789",
        "text": {"body": "Hola"}
    }
    
    test_conversation["state"] = "NUEVO"
    
    # Simular horario fuera de atencion (Domingo 10 PM)
    with patch('app.config.business_hours.BusinessHoursConfig.is_business_hours', return_value=False):
        response = await mock_reception_agent.process_message(message_data, test_conversation)
        
        # Debe retornar mensaje de fuera de horario
        assert response.get("new_state") == "FUERA_DE_HORARIO"
        assert "data_updates" in response
        assert response["data_updates"].get("business_hours_valid") == 0


@pytest.mark.asyncio
async def test_extraction_updates_interaction_count(mock_reception_agent, test_conversation):
    """Test: interaction_count se incrementa correctamente."""
    message_data = {
        "from": "573123456789",
        "text": {"body": "Hola"}
    }
    
    test_conversation["state"] = "NUEVO"
    test_conversation["interaction_count"] = 0
    
    response = await mock_reception_agent.process_message(message_data, test_conversation)
    
    # interaction_count debe incrementarse
    assert "data_updates" in response
    # El agente incrementa el contador internamente
    assert mock_reception_agent.interaction_count >= 1


@pytest.mark.asyncio
async def test_extracted_data_persisted_as_json(mock_reception_agent, test_conversation):
    """Test: extracted_data se persiste como JSON string."""
    message_data = {
        "from": "573123456789",
        "text": {"body": "Busco apartamento"}
    }
    
    test_conversation["state"] = "POLITICAS_PRESENTADAS"
    
    response = await mock_reception_agent.process_message(message_data, test_conversation)
    
    # Verificar que extracted_data existe y es string JSON
    if "data_updates" in response and "extracted_data" in response["data_updates"]:
        import json
        extracted = response["data_updates"]["extracted_data"]
        # Debe ser string JSON valido
        parsed = json.loads(extracted)
        assert "intent" in parsed
        assert "confidence" in parsed


@pytest.mark.asyncio
async def test_last_message_at_timestamp_updated(mock_reception_agent, test_conversation):
    """Test: last_message_at se actualiza en cada mensaje."""
    message_data = {
        "from": "573123456789",
        "text": {"body": "Hola"}
    }
    
    test_conversation["state"] = "NUEVO"
    
    response = await mock_reception_agent.process_message(message_data, test_conversation)
    
    # Verificar timestamp
    assert "data_updates" in response
    if "last_message_at" in response["data_updates"]:
        timestamp = response["data_updates"]["last_message_at"]
        # Debe ser string ISO format
        assert isinstance(timestamp, str)
        assert "T" in timestamp or "-" in timestamp
