"""
Dependency Injection Container
Elimina singletons globales y centraliza gesti�n de servicios
"""

from typing import Dict, Any, Type, Optional, Callable
from dataclasses import dataclass, field
import threading


@dataclass
class ServiceDescriptor:

    service_class: Optional[Type] = None
    factory: Optional[Callable] = None
    singleton: bool = True
    lazy: bool = True
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    initializer: Optional[str] = None  # Nombre del m�todo a llamar despu�s de crear

    def __post_init__(self):
        """Validar que al menos service_class o factory est�n definidos"""
        if not self.service_class and not self.factory:
            raise ValueError("ServiceDescriptor debe tener service_class o factory")


class DIContainer:

    def __init__(self):
        """Inicializa container vac�o"""
        self._services: Dict[str, ServiceDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def register(
        self,
        name: str,
        descriptor: ServiceDescriptor,
        override: bool = False
    ) -> None:
     
        if name in self._services and not override:
            raise ValueError(
                f"Service '{name}' already registered. "
                f"Use override=True to replace."
            )

        self._services[name] = descriptor
        print(f"[DIContainer] Registered: {name} (singleton={descriptor.singleton}, lazy={descriptor.lazy})")

        # Si no es lazy, crear instancia inmediatamente
        if not descriptor.lazy and descriptor.singleton:
            self.get(name)

    def get(self, name: str) -> Any:
   
        if name not in self._services:
            raise ValueError(
                f"Service '{name}' not registered. "
                f"Available services: {list(self._services.keys())}"
            )

        descriptor = self._services[name]

        # Singleton: retornar instancia existente o crear nueva (thread-safe)
        if descriptor.singleton:
            if name not in self._instances:
                with self._lock:
                    # Double-check locking
                    if name not in self._instances:
                        self._instances[name] = self._create_instance(name, descriptor)
            return self._instances[name]

        # Transient: siempre crear nueva instancia
        return self._create_instance(name, descriptor)

    def get_or_none(self, name: str) -> Optional[Any]:

        try:
            return self.get(name)
        except ValueError:
            return None

    def has(self, name: str) -> bool:

        return name in self._services

    def reset(self, name: Optional[str] = None) -> None:
 
        with self._lock:
            if name:
                if name in self._instances:
                    del self._instances[name]
                    print(f"[DIContainer] Reset: {name}")
            else:
                self._instances.clear()
                print("[DIContainer] Reset: all services")

    def _create_instance(self, name: str, descriptor: ServiceDescriptor) -> Any:
   
        try:
            # Usar factory function si est� definida
            if descriptor.factory:
                instance = descriptor.factory(*descriptor.args, **descriptor.kwargs)
            else:
                # Crear instancia con constructor
                instance = descriptor.service_class(*descriptor.args, **descriptor.kwargs)

            # Llamar inicializador si est� definido
            if descriptor.initializer:
                initializer_method = getattr(instance, descriptor.initializer, None)
                if initializer_method and callable(initializer_method):
                    initializer_method()
                else:
                    print(f"[DIContainer] Warning: Initializer '{descriptor.initializer}' not found on {name}")

            print(f"[DIContainer] Created: {name}")
            return instance

        except Exception as e:
            print(f"[DIContainer] Error creating {name}: {e}")
            raise

    def get_all_services(self) -> Dict[str, Any]:
     
        return {
            name: self.get(name)
            for name in self._services.keys()
            if name in self._instances or not self._services[name].lazy
        }

    def health_check(self) -> Dict[str, Any]:
        
        health = {}
        for name in self._services.keys():
            try:
                instance = self._instances.get(name)
                if instance:
                    # Intentar llamar health_check si existe
                    if hasattr(instance, 'health_check') and callable(instance.health_check):
                        health[name] = instance.health_check()
                    else:
                        health[name] = {"status": "healthy", "initialized": True}
                else:
                    health[name] = {"status": "not_initialized", "lazy": True}
            except Exception as e:
                health[name] = {"status": "unhealthy", "error": str(e)}

        return health

    def __repr__(self) -> str:
        """Representaci�n string del container"""
        return (
            f"<DIContainer: {len(self._services)} services registered, "
            f"{len(self._instances)} instances created>"
        )

def create_default_container() -> DIContainer:

    from app.services.llm_service import LLMService
    from app.rag.rag_system import RAGSystem
    from app.state.manager import StateManager
    from app.services.leadsales import LeadsalesService

    container = DIContainer()

    # LLM Service (singleton, lazy, con inicializaci�n)
    container.register("llm_service", ServiceDescriptor(
        service_class=LLMService,
        singleton=True,
        lazy=True,
        initializer="initialize"
    ))

    # RAG System (singleton, lazy, con inicializaci�n)
    container.register("rag_system", ServiceDescriptor(
        service_class=RAGSystem,
        singleton=True,
        lazy=True,
        initializer="initialize"
    ))

    # State Manager (singleton, no lazy - necesario desde inicio)
    container.register("state_manager", ServiceDescriptor(
        service_class=StateManager,
        singleton=True,
        lazy=False
    ))

    # Leadsales Service (singleton, lazy)
    container.register("leadsales_service", ServiceDescriptor(
        service_class=LeadsalesService,
        singleton=True,
        lazy=True,
        initializer="initialize"
    ))

    print("[DIContainer] Default services registered")
    return container
