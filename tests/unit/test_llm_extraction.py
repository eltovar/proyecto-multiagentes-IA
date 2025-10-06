# -*- coding: utf-8 -*-
"""
Test Suite: LLM Extraction - PR #1 Fundamentos
==============================================

Tests unitarios para classify_intent_and_extract_entities()
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.llm_service import LLMService
from tests.mocks.openai_mock import MockOpenAIClient


@pytest.fixture
def mock_llm_service():
    """LLM service con OpenAI mockeado."""
    service = LLMService()
    service.api_client.initialized = True
    mock_client = MockOpenAIClient()
    service.api_client.client = mock_client
    return service


@pytest.mark.asyncio
async def test_extract_name_from_greeting(mock_llm_service):
    """Test: Extraccion de nombre en saludo."""
    message = "Hola, soy Carlos Andres"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert result["nombre"] is not None
    assert result["intent"] in ["greeting", "property_search"]
    assert result["confidence"] > 0.8


@pytest.mark.asyncio
async def test_extract_property_search_intent(mock_llm_service):
    """Test: Deteccion de busqueda de inmueble."""
    message = "Busco apartamento en Chapinero de 2 millones"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert result["intent"] == "property_search"
    assert result["entities"]["property_type"] == "apartamento"
    assert "Chapinero" in result["entities"].get("location", "")
    assert result["entities"]["budget"] == 2000000


@pytest.mark.asyncio
async def test_extract_support_intent(mock_llm_service):
    """Test: Deteccion de intencion de soporte."""
    message = "Tengo un problema con mi casa, hay una gotera"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert result["intent"] == "support"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_extract_job_intent(mock_llm_service):
    """Test: Deteccion de busqueda de empleo."""
    message = "Busco trabajo como asesor inmobiliario"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert result["intent"] == "job"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_fallback_classification_on_api_failure(mock_llm_service):
    """Test: Fallback a keywords si LLM falla."""
    mock_llm_service.api_client.initialized = False
    
    message = "Busco apartamento"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert result["intent"] in ["property_search", "unclear"]
    assert result["confidence"] <= 0.65
    assert "fallback" in result.get("reasoning", "").lower()


@pytest.mark.asyncio
async def test_extract_greeting_without_name(mock_llm_service):
    """Test: Saludo simple sin nombre."""
    message = "Hola, buenos dias"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert result["intent"] == "greeting"


@pytest.mark.asyncio
async def test_response_structure(mock_llm_service):
    """Test: Validar estructura de respuesta."""
    message = "Hola"
    result = await mock_llm_service.classify_intent_and_extract_entities(message)
    
    assert "nombre" in result
    assert "intent" in result
    assert "confidence" in result
    assert "entities" in result
    assert "reasoning" in result
    
    assert isinstance(result["confidence"], (int, float))
    assert isinstance(result["entities"], dict)
    assert 0.0 <= result["confidence"] <= 1.0
