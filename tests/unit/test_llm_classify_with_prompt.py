# -*- coding: utf-8 -*-
"""
Tests unitarios para LLMService.classify_with_prompt()
Valida clasificación tri-path con prompts personalizados
"""

import pytest
import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.llm_service import LLMService


@pytest.fixture
def llm_service():
    """Fixture: LLMService con API mockeada"""
    service = LLMService()
    service.api_client.initialized = True
    service.api_client.client = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_classify_with_prompt_json_success(llm_service):
    """Test clasificación exitosa en modo JSON"""

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "intent": "inmueble",
        "sub_intent": None,
        "confidence": 0.92,
        "entities": {
            "property_type": "apartamento",
            "location": "Medellín",
            "action": "arrendar"
        },
        "reasoning": "Usuario busca propiedad específica"
    })

    # Setup mock
    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await llm_service.classify_with_prompt(
        prompt="Clasifica: Busco apartamento en Medellín",
        response_format="json"
    )

    # Assert
    assert isinstance(result, dict)
    assert result["intent"] == "inmueble"
    assert result["confidence"] == 0.92
    assert result["entities"]["property_type"] == "apartamento"
    assert result["entities"]["location"] == "Medellín"

    # Verify API was called with correct parameters
    llm_service.api_client.client.chat.completions.create.assert_called_once()
    call_kwargs = llm_service.api_client.client.chat.completions.create.call_args[1]
    assert call_kwargs["temperature"] == 0.3
    assert call_kwargs["max_tokens"] == 500
    assert call_kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_classify_with_prompt_text_mode(llm_service):
    """Test clasificación en modo texto libre"""

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "El usuario busca un apartamento en arriendo"

    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await llm_service.classify_with_prompt(
        prompt="Resume: Busco apartamento",
        response_format="text"
    )

    # Assert
    assert isinstance(result, str)
    assert "apartamento" in result.lower()
    assert "arriendo" in result.lower()

    # Verify response_format was None
    call_kwargs = llm_service.api_client.client.chat.completions.create.call_args[1]
    assert call_kwargs["response_format"] is None


@pytest.mark.asyncio
async def test_classify_with_prompt_timeout(llm_service):
    """Test manejo de timeout después de 3 segundos"""

    # Mock timeout
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(5)  # Simular respuesta lenta

    llm_service.api_client.client.chat.completions.create = AsyncMock(side_effect=slow_response)

    # Execute & Assert
    with pytest.raises(asyncio.TimeoutError):
        await llm_service.classify_with_prompt(
            prompt="Test timeout",
            response_format="json"
        )


@pytest.mark.asyncio
async def test_classify_with_prompt_invalid_json(llm_service):
    """Test manejo de JSON inválido"""

    # Mock response con JSON mal formado
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "{'invalid': json}"  # JSON inválido

    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute & Assert
    with pytest.raises(json.JSONDecodeError):
        await llm_service.classify_with_prompt(
            prompt="Test",
            response_format="json"
        )


@pytest.mark.asyncio
async def test_classify_with_prompt_incomplete_json(llm_service):
    """Test JSON válido pero incompleto (sin intent o confidence)"""

    # Mock response sin campos requeridos
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "reasoning": "Usuario pregunta algo"
        # Falta intent y confidence
    })

    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute & Assert
    with pytest.raises(ValueError) as exc_info:
        await llm_service.classify_with_prompt(
            prompt="Test",
            response_format="json"
        )

    assert "intent" in str(exc_info.value) or "confidence" in str(exc_info.value)


@pytest.mark.asyncio
async def test_classify_with_prompt_api_not_initialized():
    """Test error cuando API no está inicializada"""

    service = LLMService()
    service.api_client.initialized = False

    # Execute & Assert
    with pytest.raises(RuntimeError) as exc_info:
        await service.classify_with_prompt(
            prompt="Test",
            response_format="json"
        )

    assert "no inicializada" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_classify_with_prompt_departamento(llm_service):
    """Test clasificación de consulta departamental"""

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "intent": "departamento",
        "sub_intent": "reparaciones",
        "confidence": 0.88,
        "entities": {},
        "reasoning": "Usuario reporta problema de mantenimiento"
    })

    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await llm_service.classify_with_prompt(
        prompt="Clasifica: Tengo una fuga de agua urgente",
        response_format="json"
    )

    # Assert
    assert result["intent"] == "departamento"
    assert result["sub_intent"] == "reparaciones"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_classify_with_prompt_general(llm_service):
    """Test clasificación de información general"""

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "intent": "general",
        "sub_intent": None,
        "confidence": 0.85,
        "entities": {},
        "reasoning": "Usuario pregunta sobre la empresa"
    })

    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await llm_service.classify_with_prompt(
        prompt="Clasifica: ¿Cuál es su horario de atención?",
        response_format="json"
    )

    # Assert
    assert result["intent"] == "general"
    assert result["sub_intent"] is None


@pytest.mark.asyncio
async def test_classify_with_prompt_unclear(llm_service):
    """Test clasificación de mensaje ambiguo"""

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "intent": "unclear",
        "sub_intent": None,
        "confidence": 0.3,
        "entities": {},
        "reasoning": "Mensaje demasiado vago"
    })

    llm_service.api_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await llm_service.classify_with_prompt(
        prompt="Clasifica: hola",
        response_format="json"
    )

    # Assert
    assert result["intent"] == "unclear"
    assert result["confidence"] < 0.5
