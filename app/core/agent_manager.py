"""Gestion y registro de agentes - Maximo 80 lineas"""

from typing import Dict, Any, Optional

class AgentManager:
    """Maneja registro y seleccion de agentes"""

    def __init__(self):
        self.agents = {}
        self.agent_priority = ["reception", "support", "leadsales"]
        self.initialized = False

    def register_agent(self, name: str, agent) -> None:
        """Registra un agente en el sistema"""
        self.agents[name] = agent
        print(f"[AgentManager] Agente '{name}' registrado")

    async def select_agent(self, message: str, conversation) -> Optional[str]:
        """Selecciona agente apropiado basado en estado y mensaje"""

        # HANDOFF PROTOCOL: Si esta transferido, ningun agente IA puede actuar
        if conversation.state == "TRANSFERIDO":
            print("[AgentManager] HANDOFF activo - conversacion bloqueada")
            return None

        # Logica de seleccion para FASE 1A (solo reception disponible)
        state = conversation.state

        if state in ["NUEVO", "RECOPILANDO_NOMBRE", "RECOPILANDO_NECESIDAD"]:
            return "reception"
        elif state == "CONSULTA_RAG":
            print("[AgentManager] Support agent no disponible en FASE 1A")
            return "reception"  # Fallback
        elif state == "CREANDO_LEAD":
            print("[AgentManager] Leadsales agent no disponible en FASE 1A")
            return "reception"  # Fallback
        else:
            print(f"[AgentManager] Estado desconocido: {state}, usando reception")
            return "reception"

    def get_agent(self, name: str):
        """Obtiene agente por nombre"""
        agent = self.agents.get(name)
        if not agent:
            print(f"[AgentManager] Agente '{name}' no encontrado")
        return agent

    def get_available_agents(self) -> list:
        """Lista de agentes disponibles"""
        return list(self.agents.keys())

    def initialize_agents(self) -> bool:
        """Inicializa todos los agentes especializados"""
        try:
            # Importar y registrar agentes (solo reception en FASE 1A)
            from app.agents.reception_agent import ReceptionAgent

            reception_agent = ReceptionAgent()
            self.register_agent("reception", reception_agent)

            # En fases futuras:
            # from app.agents.support_agent import SupportAgent
            # from app.agents.leadsales_agent import LeadsalesAgent
            # self.register_agent("support", SupportAgent())
            # self.register_agent("leadsales", LeadsalesAgent())

            self.initialized = True
            print(f"[AgentManager] {len(self.agents)} agentes inicializados")
            return True

        except ImportError as e:
            print(f"[AgentManager] Error importando agentes: {e}")
            if "ReceptionAgent" in str(e):
                raise  # Reception es critico
            else:
                print("[AgentManager] Algunos agentes no estan disponibles aun")
                self.initialized = True
                return True
        except Exception as e:
            print(f"[AgentManager] Error inicializando agentes: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Verifica salud de los agentes"""
        if not self.initialized:
            return {"status": "unhealthy", "reason": "AgentManager no inicializado"}

        # Verificar que cada agente tenga el metodo process_message
        for name, agent in self.agents.items():
            if not hasattr(agent, 'process_message'):
                return {
                    "status": "unhealthy",
                    "reason": f"Agente {name} sin metodo process_message"
                }

        return {
            "status": "healthy",
            "agent_count": len(self.agents),
            "available_agents": self.get_available_agents()
        }