# -*- coding: utf-8 -*-
"""
Tests unitarios para FactoryOrchestrator
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from app.core.factory_orchestrator import FactoryOrchestrator


def test_factory_orchestrator_initialization():
    """Test inicialización básica"""
    orch = FactoryOrchestrator()

    assert orch.initialized is True
    assert orch.factory_registry is not None
    assert orch.service_container is not None
    assert orch.agent_priority is not None


def test_factory_orchestrator_has_correct_components():
    """Test que tiene componentes necesarios"""
    orch = FactoryOrchestrator()

    # Factory registry
    assert hasattr(orch, 'factory_registry')
    assert len(orch.factory_registry._factories) == 3

    # Service container
    assert hasattr(orch, 'service_container')

    # Agent priority
    assert hasattr(orch, 'agent_priority')
    assert isinstance(orch.agent_priority, list)


def test_factory_orchestrator_health_check_structure():
    """Test estructura de health check"""
    orch = FactoryOrchestrator()
    health = orch.health_check()

    assert "status" in health
    assert "orchestrator" in health
    assert "factories_registered" in health
    assert "services" in health

    assert health["orchestrator"] == "factory_based"
    assert health["factories_registered"] == 3


def test_factory_orchestrator_log_action():
    """Test que log_action no lanza errores"""
    orch = FactoryOrchestrator()

    # No debe lanzar excepción
    orch.log_action("Test action", "Test details")
    orch.log_action("Test without details")


@pytest.mark.asyncio
async def test_factory_orchestrator_send_error_message():
    """Test que _send_error_message no lanza errores"""
    from unittest.mock import patch, AsyncMock

    orch = FactoryOrchestrator()

    # Mock send_message usando patch
    with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
        await orch._send_error_message("test_user")

        # Verificar que se llamó
        assert mock_send.called
        assert mock_send.call_count == 1

        # Verificar argumentos
        call_args = mock_send.call_args
        assert call_args[0][0] == "test_user"
        assert "problema técnico" in call_args[0][1].lower() or "problema tecnico" in call_args[0][1].lower()
