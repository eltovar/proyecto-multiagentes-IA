"""
Factory para creación dinámica de agentes sin singletons globales.
Permite recrear agentes con código actualizado en cada request.
"""

import importlib
from typing import Dict, Any
from abc import ABC, abstractmethod

from app.agents.reception.handlers.greeting import GreetingHandler
from app.agents.reception.handlers.contract import ContractHandler
from app.agents.reception.handlers.lead_capture import LeadCaptureHandler
from app.agents.reception.states.conversation import ConversationStateMachine

# Imports para la nueva estructura de SupportAgent con pipeline
from app.agents.support import SupportAgent


class AgentFactory(ABC):
    """Factory base para creación de agentes"""

    @abstractmethod
    def create(self, shared_services: Dict[str, Any]) -> Any:
        """Crea una instancia del agente con servicios compartidos"""
        pass


class ReceptionAgentFactory(AgentFactory):
    """Factory para ReceptionAgent con nuevo diseño modular"""

    def create(self, shared_services: Dict[str, Any]):
        # Obtener servicios compartidos
        llm_service = shared_services.get('llm_service')
        state_manager = shared_services.get('state_manager')
        config = shared_services.get('config', {})

        # Crear componentes
        state_machine = ConversationStateMachine()
        greeting_handler = GreetingHandler(llm_service, state_manager, config)
        contract_handler = ContractHandler(llm_service, state_manager, config)
        lead_handler = LeadCaptureHandler(llm_service, state_manager, config)

        # Recargar módulo para hot-reload
        module = importlib.import_module('app.agents.reception.agent')
        importlib.reload(module)
        agent_class = getattr(module, 'ReceptionAgent')

        # Crear agente con todos sus componentes
        agent = agent_class(
            llm_service=llm_service,
            state_manager=state_manager,
            state_machine=state_machine,
            handlers={
                'greeting': greeting_handler,
                'contract': contract_handler,
                'lead': lead_handler
            }
        )

        return agent


class SupportAgentFactory(AgentFactory):
    """Factory para SupportAgent con pipeline pattern"""

    def create(self, shared_services: Dict[str, Any]):
        # Obtener servicios compartidos
        llm_service = shared_services.get('llm_service')
        state_manager = shared_services.get('state_manager')
        rag_system = shared_services.get('rag_system')

        # Recargar módulo para hot-reload (pipeline pattern con nueva estructura)
        module = importlib.import_module('app.agents.support.agent')
        importlib.reload(module)
        agent_class = getattr(module, 'SupportAgent')

        # Crear agente con pipeline pattern
        agent = agent_class(
            llm_service=llm_service,
            state_manager=state_manager,
            rag_system=rag_system
        )

        return agent


class LeadsalesAgentFactory(AgentFactory):
    """Factory para LeadsalesAgent (ya refactorizado)"""

    def create(self, shared_services: Dict[str, Any]):
        # Obtener servicios compartidos
        llm_service = shared_services.get('llm_service')
        state_manager = shared_services.get('state_manager')
        leadsales_service = shared_services.get('leadsales_service')

        # Recargar módulo para hot-reload
        module = importlib.import_module('app.agents.leadsales_agent')
        importlib.reload(module)
        agent_class = getattr(module, 'LeadsalesAgent')

        # Crear agente con servicios inyectados
        agent = agent_class(
            llm_service=llm_service,
            state_manager=state_manager,
            leadsales_service=leadsales_service
        )

        return agent


class AgentFactoryRegistry:
    """
    Registro centralizado de factories de agentes.
    Permite agregar nuevos agentes sin modificar código existente.
    """

    def __init__(self):
        self._factories: Dict[str, AgentFactory] = {}
        self._register_default_factories()

    def _register_default_factories(self):
        """Registra factories por defecto"""
        self.register('ReceptionAgent', ReceptionAgentFactory())
        self.register('SupportAgent', SupportAgentFactory())
        self.register('LeadsalesAgent', LeadsalesAgentFactory())

    def register(self, agent_name: str, factory: AgentFactory):
        """Registra una factory para un tipo de agente"""
        self._factories[agent_name] = factory
        print(f"[FACTORY] Registrada factory: {agent_name}")

    def create_agent(self, agent_name: str, shared_services: Dict[str, Any]):
        """Crea una instancia fresh del agente especificado"""
        if agent_name not in self._factories:
            raise ValueError(f"No hay factory registrada para: {agent_name}")

        factory = self._factories[agent_name]
        agent = factory.create(shared_services)

        print(f"[FACTORY] Creado agente fresh: {agent_name}")
        return agent

    def reload_agent(self, agent_name: str, shared_services: Dict[str, Any]):
        """Alias de create_agent (en factory pattern, create siempre da instancia fresh)"""
        return self.create_agent(agent_name, shared_services)
