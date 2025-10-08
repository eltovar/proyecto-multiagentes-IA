"""
tests/integration/test_legacy_compatibility.py
==============================================
Test para validar que el código legacy (sin DI explícita) sigue funcionando
correctamente con el nuevo sistema de Factory Pattern.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agents.reception_agent import ReceptionAgent
from app.agents.support_agent import SupportAgent
from app.agents.leadsales_agent import LeadsalesAgent
from app.state.manager import state_manager, get_conversation_state


@pytest.fixture
def cleanup_test_user(request):
    """Fixture con ID único para evitar colisiones"""
    import uuid
    test_user = f"legacy_{uuid.uuid4().hex[:8]}"
    yield test_user


class TestLegacyCompatibility:
    """Test de compatibilidad con código legacy (sin DI explícita)"""

    def test_reception_agent_without_di_parameters(self):
        """Validar que ReceptionAgent funciona sin parámetros DI (legacy)"""
        # Crear agente sin pasar servicios (modo legacy)
        agent = ReceptionAgent()

        # Verificar que el agente se inicializó correctamente
        assert agent is not None, "Agent debe crearse sin errores"
        assert agent.name == "reception", "Debe tener nombre correcto"
        assert hasattr(agent, 'llm_service'), "Debe tener llm_service"
        assert hasattr(agent, 'state_manager'), "Debe tener state_manager"

    def test_support_agent_without_di_parameters(self):
        """Validar que SupportAgent funciona sin parámetros DI (legacy)"""
        # Crear agente sin pasar servicios (modo legacy)
        agent = SupportAgent()

        # Verificar inicialización
        assert agent is not None, "Agent debe crearse sin errores"
        assert agent.name == "SupportAgent", "Debe tener nombre correcto"
        assert hasattr(agent, 'llm_service'), "Debe tener llm_service"
        assert hasattr(agent, 'state_manager'), "Debe tener state_manager"
        assert hasattr(agent, 'rag_system'), "Debe tener rag_system"

    def test_leadsales_agent_without_di_parameters(self):
        """Validar que LeadsalesAgent funciona sin parámetros DI (legacy)"""
        # Crear agente sin pasar servicios (modo legacy)
        agent = LeadsalesAgent()

        # Verificar inicialización
        assert agent is not None, "Agent debe crearse sin errores"
        assert agent.name == "LeadsalesAgent", "Debe tener nombre correcto"
        assert hasattr(agent, 'llm_service'), "Debe tener llm_service"
        assert hasattr(agent, 'state_manager'), "Debe tener state_manager"
        assert hasattr(agent, 'leadsales_service'), "Debe tener leadsales_service"

    @pytest.mark.asyncio
    async def test_reception_agent_can_handle_legacy_mode(self, cleanup_test_user):
        """Validar que ReceptionAgent.can_handle() funciona en modo legacy"""
        user_id = cleanup_test_user
        agent = ReceptionAgent()

        # Test con mensaje de saludo (formato correcto)
        message_data = {'from': user_id, 'text': {'body': 'Hola'}}
        conversation = {'state': 'NUEVO', 'whatsapp_id': user_id}

        result = await agent.can_handle(message_data, conversation)

        # Debe retornar boolean
        assert isinstance(result, bool), "can_handle() debe retornar boolean"

    @pytest.mark.asyncio
    async def test_support_agent_can_handle_legacy_mode(self, cleanup_test_user):
        """Validar que SupportAgent.can_handle() funciona en modo legacy"""
        user_id = cleanup_test_user
        agent = SupportAgent()

        # Test con mensaje de consulta (formato correcto)
        message_data = {'from': user_id, 'text': {'body': '¿Cuánto cuesta el departamento?'}}
        conversation = {'state': 'NUEVO', 'whatsapp_id': user_id}

        result = await agent.can_handle(message_data, conversation)

        # Debe retornar boolean
        assert isinstance(result, bool), "can_handle() debe retornar boolean"

    @pytest.mark.asyncio
    async def test_agent_state_access_legacy_mode(self, cleanup_test_user):
        """Validar que agentes pueden acceder al estado en modo legacy"""
        user_id = cleanup_test_user

        # Crear conversación primero usando update_conversation_state (función module-level)
        from app.state.manager import update_conversation_state
        update_conversation_state(user_id, "NUEVO", data={'customer_name': 'TestUser'})

        # Crear agente sin DI
        agent = ReceptionAgent()

        # Acceder al estado via state_manager del agente (lazy loaded)
        state = agent.state_manager.get_conversation(user_id)

        # Verificar acceso al estado
        assert state is not None, "Debe poder acceder al estado"
        assert state.state == "NUEVO", "Debe leer el estado correctamente"
        assert state.customer_name == "TestUser", "Debe leer customer_name correctamente"

    def test_lazy_loading_creates_services_on_demand(self):
        """Validar que lazy loading crea servicios bajo demanda (legacy)"""
        agent = ReceptionAgent()

        # Acceder a llm_service debe activar lazy loading
        llm = agent.llm_service

        # Debe haber creado o recuperado el servicio
        assert llm is not None, "Lazy loading debe crear/recuperar llm_service"

        # Acceder a state_manager debe activar lazy loading
        state = agent.state_manager

        # Debe haber creado o recuperado el servicio
        assert state is not None, "Lazy loading debe crear/recuperar state_manager"
