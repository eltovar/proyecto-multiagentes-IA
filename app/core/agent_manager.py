"""
Agent Manager - Factory Pattern Adapter
Deprecation Notice: Este módulo será eliminado en futuras versiones.
Usar directamente FactoryOrchestrator para gestión de agentes.
"""
from typing import Dict, Any, Optional
from app.monitoring.logger import get_logger
from app.core.factory_orchestrator import FactoryOrchestrator

logger = get_logger(__name__)

class AgentManager:
    """
    LEGACY ADAPTER: Mantiene compatibilidad con código que usa AgentManager.

    Internamente delega a FactoryOrchestrator (nuevo sistema).
    Este patrón permite migración gradual sin romper dependencias.
    """

    def __init__(self, orchestrator: Optional[FactoryOrchestrator] = None):
        """
        Args:
            orchestrator: FactoryOrchestrator opcional (crea uno si no se provee)
        """
        # Si no se provee orchestrator, crear uno nuevo
        if orchestrator is None:
            self.orchestrator = FactoryOrchestrator()
        else:
            self.orchestrator = orchestrator

        # Mantener interfaz legacy
        self.agents = {}
        self.agent_priority = ["reception", "support", "leadsales"]
        self.initialized = False

        logger.info("[AgentManager] Inicializado con Factory Pattern")

    def register_agent(self, name: str, agent) -> None:
        """
        LEGACY METHOD: Registra un agente manualmente.

        Deprecado: Los agentes ahora se crean dinámicamente via Factory.
        Este método se mantiene por compatibilidad.
        """
        self.agents[name] = agent
        logger.info(f"Agente '{name}' registrado (legacy mode)")

    async def select_agent(self, message: str, conversation) -> Optional[str]:
        """
        Selecciona agente apropiado basado en estado y mensaje.

        MIGRADO: Usa lógica de FactoryOrchestrator en vez de hardcoded.
        """
        # HANDOFF PROTOCOL: Si está transferido, ningún agente IA puede actuar
        if conversation.state == "TRANSFERIDO":
            logger.info("HANDOFF activo - conversación bloqueada")
            return None

        # Delegar selección a orchestrator
        state = conversation.state

        # Mapeo de estados a agentes (puede venir del orchestrator en el futuro)
        if state in ["NUEVO", "RECOPILANDO_NOMBRE", "RECOPILANDO_NECESIDAD"]:
            return "reception"
        elif state == "CONSULTA_RAG":
            # Support agent disponible via factory
            return "support"
        elif state == "CREANDO_LEAD":
            # Leadsales disponible via factory
            return "leadsales"
        else:
            logger.warning(f"Estado desconocido: {state}, usando reception")
            return "reception"

    def get_agent(self, name: str):
        """
        Obtiene agente por nombre.

        MIGRADO: Usa Factory para crear agentes on-demand.
        """
        # Si ya existe en cache legacy, retornarlo
        if name in self.agents:
            return self.agents[name]

        # Sino, crear agente via factory registry
        try:
            # Mapeo de nombres legacy a nombres Factory
            factory_name_map = {
                "reception": "ReceptionAgent",
                "support": "SupportAgent",
                "leadsales": "LeadsalesAgent"
            }

            factory_name = factory_name_map.get(name, name)
            shared_services = self.orchestrator.service_container.get_all_services()
            agent = self.orchestrator.factory_registry.create_agent(factory_name, shared_services)

            # Cachear para compatibilidad legacy
            self.agents[name] = agent
            return agent
        except Exception as e:
            logger.error(f"Error obteniendo agente '{name}': {e}")
            return None

    def get_available_agents(self) -> list:
        """Lista de agentes disponibles (nombres legacy para compatibilidad)"""
        # Combinar agentes legacy + factory
        factory_agents = list(self.orchestrator.factory_registry._factories.keys())
        legacy_agents = list(self.agents.keys())

        # Mapeo inverso: Factory names → legacy names
        factory_to_legacy = {
            "ReceptionAgent": "reception",
            "SupportAgent": "support",
            "LeadsalesAgent": "leadsales"
        }

        # Convertir nombres de factories a nombres legacy
        factory_legacy_names = [factory_to_legacy.get(name, name.lower()) for name in factory_agents]

        return list(set(factory_legacy_names + legacy_agents))

    def initialize_agents(self) -> bool:
        """
        Inicializa todos los agentes especializados.

        MIGRADO: Delega a FactoryOrchestrator en vez de imports manuales.
        """
        try:
            # Los agentes se crean lazy via Factory
            # No necesitamos importar ReceptionAgent legacy
            logger.info("Agentes disponibles via Factory Pattern (lazy loading)")

            available = self.get_available_agents()
            logger.info(f"{len(available)} factories disponibles: {available}")

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Error inicializando agentes: {e}", exc_info=True)
            return False

    def health_check(self) -> Dict[str, Any]:
        """Verifica salud de los agentes"""
        if not self.initialized:
            return {"status": "unhealthy", "reason": "AgentManager no inicializado"}

        # Verificar salud del orchestrator
        try:
            available_agents = self.get_available_agents()

            return {
                "status": "healthy",
                "agent_count": len(available_agents),
                "available_agents": available_agents,
                "factory_pattern": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Error en health check: {e}"
            }
