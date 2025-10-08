"""
Factory para creación dinámica de agentes sin singletons globales.
Permite recrear agentes con código actualizado en cada request.
"""

import importlib
from typing import Dict, Any
from abc import ABC, abstractmethod


class AgentFactory(ABC):
    """Factory base para creación de agentes"""

    @abstractmethod
    def create(self, shared_services: Dict[str, Any]) -> Any:
        """Crea una instancia del agente con servicios compartidos"""
        pass


class ReceptionAgentFactory(AgentFactory):
    """Factory para ReceptionAgent"""

    def create(self, shared_services: Dict[str, Any]):
        # Recargar módulo para obtener última versión del código
        module = importlib.import_module('app.agents.reception_agent')
        importlib.reload(module)

        # Crear instancia fresh
        agent_class = getattr(module, 'ReceptionAgent')

        # ✅ Inyectar servicios en constructor
        agent = agent_class(
            llm_service=shared_services.get('llm_service'),
            state_manager=shared_services.get('state_manager')
        )

        return agent


class SupportAgentFactory(AgentFactory):
    """Factory para SupportAgent"""

    def create(self, shared_services: Dict[str, Any]):
        module = importlib.import_module('app.agents.support_agent')
        importlib.reload(module)

        agent_class = getattr(module, 'SupportAgent')

        # ✅ Inyectar servicios en constructor
        agent = agent_class(
            llm_service=shared_services.get('llm_service'),
            state_manager=shared_services.get('state_manager'),
            rag_system=shared_services.get('rag_system')
        )

        return agent


class LeadsalesAgentFactory(AgentFactory):
    """Factory para LeadsalesAgent"""

    def create(self, shared_services: Dict[str, Any]):
        module = importlib.import_module('app.agents.leadsales_agent')
        importlib.reload(module)

        agent_class = getattr(module, 'LeadsalesAgent')

        # ✅ Inyectar servicios en constructor
        # Nota: leadsales_service NO se comparte (cada agente tiene el suyo)
        agent = agent_class(
            llm_service=shared_services.get('llm_service'),
            state_manager=shared_services.get('state_manager')
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
