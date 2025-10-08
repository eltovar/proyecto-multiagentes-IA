# -*- coding: utf-8 -*-
"""
Tests unitarios para ServiceContainer
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from app.core.service_container import ServiceContainer


@pytest.fixture(autouse=True)
def reset_container():
    """Reset singleton before each test"""
    ServiceContainer._instance = None
    yield
    ServiceContainer._instance = None


def test_service_container_singleton():
    """Test que ServiceContainer es singleton"""
    container1 = ServiceContainer()
    container2 = ServiceContainer()

    assert container1 is container2
    assert id(container1) == id(container2)


def test_service_container_initialization():
    """Test inicialización básica"""
    container = ServiceContainer()

    # No inicializados aún (lazy loading)
    assert container._llm_service is None
    assert container._rag_system is None
    assert container._state_manager is None


def test_service_container_lazy_loading_llm():
    """Test que LLM service se inicializa lazy"""
    container = ServiceContainer()

    # Primera llamada inicializa
    llm = container.llm_service
    assert llm is not None
    assert container._llm_service is not None

    # Segunda llamada retorna mismo
    llm2 = container.llm_service
    assert llm is llm2
    assert id(llm) == id(llm2)


def test_service_container_get_all_services():
    """Test que get_all_services retorna dict correcto"""
    container = ServiceContainer()
    services = container.get_all_services()

    assert isinstance(services, dict)
    assert 'llm_service' in services
    assert 'rag_system' in services
    assert 'state_manager' in services
    assert 'leadsales_service' in services


def test_service_container_health_check():
    """Test health_check"""
    container = ServiceContainer()
    health = container.health_check()

    assert isinstance(health, dict)
    assert 'llm_service' in health
    assert 'rag_system' in health
    assert 'state_manager' in health
    assert 'leadsales_service' in health
