"""
Service Container para gestión de dependencias compartidas.
Servicios costosos (LLM, RAG) se crean una vez y se inyectan.
"""

from typing import Dict, Any, Optional
from app.services.llm_service import LLMService
from app.rag.rag_system import RAGSystem
from app.state.manager import StateManager
from app.services.leadsales_service import LeadsalesService


class ServiceContainer:
    """
    Container de servicios singleton que se comparten entre agentes.
    Solo servicios COSTOSOS van aquí (no se recargan).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Servicios costosos (singleton)
        self._llm_service: Optional[LLMService] = None
        self._rag_system: Optional[RAGSystem] = None
        self._state_manager: Optional[StateManager] = None
        self._leadsales_service: Optional[LeadsalesService] = None

        self._initialized = True

    @property
    def llm_service(self) -> LLMService:
        """Lazy initialization de LLM Service"""
        if self._llm_service is None:
            print("[CONTAINER] Inicializando LLM Service...")
            self._llm_service = LLMService()
            self._llm_service.initialize()
        return self._llm_service

    @property
    def rag_system(self) -> RAGSystem:
        """Lazy initialization de RAG System"""
        if self._rag_system is None:
            print("[CONTAINER] Inicializando RAG System...")
            self._rag_system = RAGSystem()
            self._rag_system.initialize()
        return self._rag_system

    @property
    def state_manager(self) -> StateManager:
        """Lazy initialization de State Manager"""
        if self._state_manager is None:
            print("[CONTAINER] Inicializando State Manager...")
            self._state_manager = StateManager()
        return self._state_manager

    @property
    def leadsales_service(self) -> LeadsalesService:
        """Lazy initialization de Leadsales Service"""
        if self._leadsales_service is None:
            print("[CONTAINER] Inicializando Leadsales Service...")
            self._leadsales_service = LeadsalesService()
        return self._leadsales_service

    def get_all_services(self) -> Dict[str, Any]:
        """Retorna diccionario con todos los servicios disponibles"""
        return {
            'llm_service': self.llm_service,
            'rag_system': self.rag_system,
            'state_manager': self.state_manager,
            'leadsales_service': self.leadsales_service
        }

    def health_check(self) -> Dict[str, Any]:
        """Verifica salud de todos los servicios"""
        return {
            'llm_service': self._llm_service is not None and self._llm_service.api_client.initialized,
            'rag_system': self._rag_system is not None and self._rag_system.initialized,
            'state_manager': self._state_manager is not None,
            'leadsales_service': self._leadsales_service is not None
        }
