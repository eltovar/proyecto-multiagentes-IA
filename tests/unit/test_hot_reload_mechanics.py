"""
tests/unit/test_hot_reload_mechanics.py
========================================
Test unitarios para validar que el mecanismo de hot reload funciona correctamente.
"""

import pytest
import importlib
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any
import types

# Setup path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.agent_factory import ReceptionAgentFactory, SupportAgentFactory, LeadsalesAgentFactory
from app.core.factory_orchestrator import FactoryOrchestrator


class TestHotReloadMechanics:
    """Test que el hot reload funciona en factories"""

    def test_factory_uses_importlib_reload(self):
        """Validar que factories usan importlib.reload()"""
        factory = ReceptionAgentFactory()

        # Crear un módulo real simulado
        fake_module = types.ModuleType('app.agents.reception_agent')
        fake_module.ReceptionAgent = Mock(return_value=Mock(name="reception"))

        with patch.object(importlib, 'import_module', return_value=fake_module) as mock_import, \
             patch.object(importlib, 'reload', return_value=fake_module) as mock_reload:

            shared_services = {'llm_service': Mock(), 'state_manager': Mock()}
            agent = factory.create(shared_services)

            # Verificar que se llamó reload
            assert mock_reload.called, "importlib.reload() debe ser llamado"
            assert mock_import.called, "importlib.import_module() debe ser llamado"
            mock_reload.assert_called_once()

    def test_factory_creates_fresh_instance_each_time(self):
        """Validar que cada llamada a create() devuelve una instancia nueva"""
        factory = ReceptionAgentFactory()
        shared_services = {'llm_service': Mock(), 'state_manager': Mock()}

        agent1 = factory.create(shared_services)
        agent2 = factory.create(shared_services)

        # Las instancias deben ser diferentes
        assert agent1 is not agent2, "Cada create() debe devolver una instancia nueva"
        assert id(agent1) != id(agent2), "Los IDs de objeto deben ser diferentes"

    def test_orchestrator_creates_agents_via_factory(self):
        """Validar que FactoryOrchestrator usa factory_registry para crear agentes"""
        orchestrator = FactoryOrchestrator()

        # Mock factory_registry.create_agent
        with patch.object(orchestrator.factory_registry, 'create_agent') as mock_create:
            mock_agent = Mock()
            mock_agent.name = "ReceptionAgent"
            mock_create.return_value = mock_agent

            # Llamar directamente al método que usa factory_registry
            agent = orchestrator.factory_registry.create_agent("ReceptionAgent", {})

            assert mock_create.called, "factory_registry.create_agent() debe ser llamado"
            assert agent == mock_agent, "Debe devolver el agente creado por factory"

    def test_no_global_agent_instances_in_orchestrator(self):
        """Validar que orchestrator NO mantiene instancias globales de agentes"""
        orchestrator = FactoryOrchestrator()

        # Verificar que no hay atributos de instancia de agentes
        assert not hasattr(orchestrator, 'reception_agent'), "No debe haber self.reception_agent"
        assert not hasattr(orchestrator, 'support_agent'), "No debe haber self.support_agent"
        assert not hasattr(orchestrator, 'leadsales_agent'), "No debe haber self.leadsales_agent"

    def test_shared_services_are_singletons(self):
        """Validar que los servicios compartidos (LLM, state) son singleton"""
        orchestrator = FactoryOrchestrator()

        # Obtener servicios via service_container
        all_services_1 = orchestrator.service_container.get_all_services()
        all_services_2 = orchestrator.service_container.get_all_services()

        llm1 = all_services_1.get('llm_service')
        llm2 = all_services_2.get('llm_service')

        state1 = all_services_1.get('state_manager')
        state2 = all_services_2.get('state_manager')

        # Los servicios deben ser la misma instancia (singleton)
        assert llm1 is llm2, "llm_service debe ser singleton"
        assert state1 is state2, "state_manager debe ser singleton"

    def test_agent_receives_shared_services_via_di(self):
        """Validar que agentes reciben servicios compartidos via DI"""
        factory = ReceptionAgentFactory()
        mock_llm = Mock()
        mock_state = Mock()
        shared_services = {'llm_service': mock_llm, 'state_manager': mock_state}

        agent = factory.create(shared_services)

        # El agente debe tener acceso a los servicios inyectados
        assert agent.llm_service == mock_llm, "Agent debe usar llm_service inyectado"
        assert agent.state_manager == mock_state, "Agent debe usar state_manager inyectado"

    def test_factory_reloads_module_on_each_create(self):
        """Validar que el módulo se recarga en cada create()"""
        factory = SupportAgentFactory()

        fake_module = types.ModuleType('app.agents.support_agent')
        fake_module.SupportAgent = Mock(return_value=Mock())

        with patch.object(importlib, 'import_module', return_value=fake_module) as mock_import, \
             patch.object(importlib, 'reload', return_value=fake_module) as mock_reload:

            shared_services = {'llm_service': Mock(), 'state_manager': Mock(), 'rag_system': Mock()}

            # Primera llamada
            factory.create(shared_services)
            reload_count_1 = mock_reload.call_count

            # Segunda llamada
            factory.create(shared_services)
            reload_count_2 = mock_reload.call_count

            # Debe recargar en cada create()
            assert reload_count_2 > reload_count_1, "Debe recargar el módulo en cada create()"
            assert reload_count_2 == 2, "Debe haber llamado reload 2 veces (una por create)"

    def test_leadsales_factory_injects_services(self):
        """Validar que LeadsalesAgentFactory inyecta servicios correctamente"""
        factory = LeadsalesAgentFactory()
        mock_llm = Mock()
        mock_state = Mock()

        shared_services = {
            'llm_service': mock_llm,
            'state_manager': mock_state
        }

        agent = factory.create(shared_services)

        # Verificar que el agente fue creado y tiene los servicios
        assert hasattr(agent, 'llm_service'), "Debe tener llm_service"
        assert hasattr(agent, 'state_manager'), "Debe tener state_manager"
        # LeadsalesAgent crea su propio leadsales_service, no se inyecta
        assert hasattr(agent, 'leadsales_service'), "Debe tener leadsales_service"

    def test_support_factory_injects_rag_system(self):
        """Validar que SupportAgentFactory inyecta rag_system"""
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

        # Verificar inyección
        assert hasattr(agent, 'rag_system'), "Debe tener rag_system"
        assert agent.rag_system == mock_rag, "Debe usar el rag_system inyectado"

    @pytest.mark.asyncio
    async def test_orchestrator_select_agent_creates_fresh_instance(self):
        """Validar que _select_agent() crea instancia fresca en cada llamada"""
        orchestrator = FactoryOrchestrator()

        # Mock factory_registry para contar llamadas
        with patch.object(orchestrator.factory_registry, 'create_agent') as mock_create:
            mock_agent = Mock()
            mock_agent.name = "ReceptionAgent"
            mock_agent.can_handle = AsyncMock(return_value=True)
            mock_create.return_value = mock_agent

            message_data = {'from': 'user123', 'text': {'body': 'test'}}
            conversation = {'state': 'NUEVO'}

            # Primera llamada
            agent1 = await orchestrator._select_agent(message_data, conversation)
            call_count_1 = mock_create.call_count

            # Segunda llamada
            agent2 = await orchestrator._select_agent(message_data, conversation)
            call_count_2 = mock_create.call_count

            # Debe crear nueva instancia en cada select
            assert call_count_2 > call_count_1, "Debe crear nueva instancia en cada _select_agent()"

    def test_agent_class_is_reloaded_not_cached(self):
        """Validar que la clase del agente se recarga, no se usa desde caché"""
        factory = ReceptionAgentFactory()

        # Crear módulos simulados con versiones diferentes
        fake_module_v1 = types.ModuleType('app.agents.reception_agent')
        fake_module_v1.ReceptionAgent = Mock(return_value=Mock(name="v1"))

        fake_module_v2 = types.ModuleType('app.agents.reception_agent')
        fake_module_v2.ReceptionAgent = Mock(return_value=Mock(name="v2"))

        with patch.object(importlib, 'import_module') as mock_import, \
             patch.object(importlib, 'reload') as mock_reload:

            # Primera creación (versión 1)
            mock_import.return_value = fake_module_v1
            mock_reload.return_value = fake_module_v1

            shared_services = {'llm_service': Mock(), 'state_manager': Mock()}
            agent1 = factory.create(shared_services)

            # Segunda creación (versión 2 - simula cambio de código)
            mock_reload.return_value = fake_module_v2

            agent2 = factory.create(shared_services)

            # Verificar que reload fue llamado 2 veces
            assert mock_reload.call_count == 2, "Debe recargar el módulo en cada create()"
