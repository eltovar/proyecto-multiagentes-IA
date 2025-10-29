# -*- coding: utf-8 -*-
"""
Tests unitarios para AgentFactory
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from app.core.agent_factory import (
    AgentFactory,
    ReceptionAgentFactory,
    SupportAgentFactory,
    LeadsalesAgentFactory,
    AgentFactoryRegistry
)
from app.core.service_container import ServiceContainer


def test_reception_agent_factory_creates_instance():
    """Test que ReceptionAgentFactory crea instancia"""
    factory = ReceptionAgentFactory()
    container = ServiceContainer()
    shared_services = container.get_all_services()

    agent = factory.create(shared_services)

    assert agent is not None
    assert hasattr(agent, 'process_message')


def test_support_agent_factory_creates_instance():
    """Test que SupportAgentFactory crea instancia"""
    factory = SupportAgentFactory()
    container = ServiceContainer()
    shared_services = container.get_all_services()

    agent = factory.create(shared_services)

    assert agent is not None
    assert hasattr(agent, 'process_message')


def test_leadsales_agent_factory_creates_instance():
    """Test que LeadsalesAgentFactory crea instancia"""
    factory = LeadsalesAgentFactory()
    container = ServiceContainer()
    shared_services = container.get_all_services()

    agent = factory.create(shared_services)

    assert agent is not None
    assert hasattr(agent, 'process_message')


def test_factory_creates_fresh_instances():
    """Test que factory crea instancias fresh cada vez"""
    factory = ReceptionAgentFactory()
    container = ServiceContainer()
    shared_services = container.get_all_services()

    agent1 = factory.create(shared_services)
    agent2 = factory.create(shared_services)

    # Diferentes instancias
    assert agent1 is not agent2
    assert id(agent1) != id(agent2)

    # Pero comparten servicios
    assert agent1.llm_service is agent2.llm_service


def test_agent_factory_registry_initialization():
    """Test que registry se inicializa con factories por defecto"""
    registry = AgentFactoryRegistry()

    # Factories por defecto
    assert 'ReceptionAgent' in registry._factories
    assert 'SupportAgent' in registry._factories
    assert 'LeadsalesAgent' in registry._factories


def test_agent_factory_registry_create_agent():
    """Test que registry puede crear agentes"""
    registry = AgentFactoryRegistry()
    container = ServiceContainer()
    shared_services = container.get_all_services()

    agent = registry.create_agent('SupportAgent', shared_services)

    assert agent is not None
    assert hasattr(agent, 'process_message')


def test_agent_factory_registry_invalid_agent():
    """Test que registry lanza error para agente no registrado"""
    registry = AgentFactoryRegistry()
    container = ServiceContainer()
    shared_services = container.get_all_services()

    with pytest.raises(ValueError, match="No hay factory registrada"):
        registry.create_agent('InvalidAgent', shared_services)


def test_agent_factory_registry_custom_registration():
    """Test que se pueden registrar factories personalizadas"""
    registry = AgentFactoryRegistry()

    # Crear factory custom
    class CustomFactory(AgentFactory):
        def create(self, shared_services):
            return "custom_agent"

    # Registrar
    registry.register('CustomAgent', CustomFactory())

    # Verificar registro
    assert 'CustomAgent' in registry._factories

    # Crear agente
    agent = registry.create_agent('CustomAgent', {})
    assert agent == "custom_agent"


def test_reception_agent_factory_injects_services_in_constructor():
    """Test que ReceptionAgentFactory inyecta servicios en constructor"""
    from unittest.mock import Mock

    factory = ReceptionAgentFactory()
    mock_llm = Mock()
    mock_state = Mock()

    shared_services = {
        'llm_service': mock_llm,
        'state_manager': mock_state
    }

    agent = factory.create(shared_services)

    # Verificar que los servicios fueron inyectados
    assert agent.llm_service == mock_llm
    assert agent.state_manager == mock_state


def test_support_agent_factory_injects_all_services():
    """Test que SupportAgentFactory inyecta LLM, State y RAG"""
    from unittest.mock import Mock

    factory = SupportAgentFactory()
    mock_llm = Mock()
    mock_state = Mock()
    mock_rag = Mock()

    shared_services = {
        'llm_service': mock_llm,
        'state_manager': mock_state,
        'rag_system': mock_rag
    }

    agent = factory.create(shared_services)

    assert agent.llm_service == mock_llm
    assert agent.state_manager == mock_state
    assert agent.rag_system == mock_rag


def test_leadsales_agent_factory_injects_services_in_constructor():
    """Test que LeadsalesAgentFactory inyecta servicios en constructor"""
    from unittest.mock import Mock

    factory = LeadsalesAgentFactory()
    mock_llm = Mock()
    mock_state = Mock()

    shared_services = {
        'llm_service': mock_llm,
        'state_manager': mock_state
    }

    agent = factory.create(shared_services)

    # Verificar que los servicios fueron inyectados
    assert agent.llm_service == mock_llm
    assert agent.state_manager == mock_state
