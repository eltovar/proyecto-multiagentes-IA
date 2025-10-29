"""
Pipeline Pattern - Anti-Spaghetti Architecture
Elimina God Objects mediante procesamiento secuencial de pasos
"""

from typing import Callable, List, Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time

@dataclass
class PipelineContext:
    
    message: Dict[str, Any]
    conversation: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    def set_result(self, step_name: str, result: Any) -> None:
        """Almacena resultado de un paso"""
        self.results[step_name] = result

    def get_result(self, step_name: str) -> Optional[Any]:
        """Obtiene resultado de un paso previo"""
        return self.results.get(step_name)

    def has_error(self) -> bool:
        """Verifica si hay error en el contexto"""
        return self.error is not None


# Pipeline Steps

class PipelineStep(ABC):

    def __init__(self, name: str):
        
        self.name = name

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        pass

    def should_execute(self, context: PipelineContext) -> bool:
        
        return True

    def on_error(self, context: PipelineContext, error: Exception) -> PipelineContext:
        
        context.error = error
        print(f"[Pipeline] Error en paso '{self.name}': {error}")
        return context


# Pipeline Implementation
class MessagePipeline:
    
    def __init__(self, name: str = "DefaultPipeline"):
        """ Nombre del pipeline """
        self.name = name
        self.steps: List[PipelineStep] = []
        self.middlewares: List[Callable] = []

    def add_step(self, step: PipelineStep) -> 'MessagePipeline':
       
        self.steps.append(step)
        print(f"[Pipeline:{self.name}] Added step: {step.name}")
        return self

    def add_middleware(self, middleware: Callable) -> 'MessagePipeline':
        
        self.middlewares.append(middleware)
        return self

    async def process(
        self,
        message: Dict[str, Any],
        conversation: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> PipelineContext:
        
        # Crear contexto inicial
        context = PipelineContext(
            message=message,
            conversation=conversation,
            metadata=metadata or {}
        )

        # Metadata de timing
        start_time = time.time()
        context.metadata["pipeline_name"] = self.name
        context.metadata["start_time"] = start_time

        print(f"[Pipeline:{self.name}] Starting with {len(self.steps)} steps")

        # Ejecutar pasos secuencialmente
        for i, step in enumerate(self.steps, 1):
            try:
                # Verificar si debe ejecutarse (conditional step)
                if not step.should_execute(context):
                    print(f"[Pipeline:{self.name}] Step {i}/{len(self.steps)} '{step.name}' - SKIPPED")
                    continue

                step_start = time.time()

                # Ejecutar middlewares
                for middleware in self.middlewares:
                    context = await middleware(context, step)

                # Ejecutar paso
                print(f"[Pipeline:{self.name}] Step {i}/{len(self.steps)} '{step.name}' - EXECUTING")
                context = await step.execute(context)

                step_duration = int((time.time() - step_start) * 1000)
                print(f"[Pipeline:{self.name}] Step {i}/{len(self.steps)} '{step.name}' - COMPLETED ({step_duration}ms)")

                # Si hay error, detener pipeline
                if context.has_error():
                    print(f"[Pipeline:{self.name}] STOPPED due to error in step '{step.name}'")
                    break

            except Exception as e:
                # Manejar error con handler del paso
                context = step.on_error(context, e)

                # Detener pipeline si el paso no maneja el error
                if context.has_error():
                    print(f"[Pipeline:{self.name}] FAILED at step '{step.name}': {e}")
                    break

        # Metadata final
        total_duration = int((time.time() - start_time) * 1000)
        context.metadata["duration_ms"] = total_duration
        context.metadata["steps_executed"] = len([s for s in self.steps if s.name in context.results])

        print(f"[Pipeline:{self.name}] FINISHED ({total_duration}ms)")

        return context

    def clear(self) -> None:
        """Limpia todos los pasos del pipeline"""
        self.steps.clear()
        print(f"[Pipeline:{self.name}] Cleared all steps")

    def get_step(self, name: str) -> Optional[PipelineStep]:
    
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def __repr__(self) -> str:
        """Representacion string del pipeline"""
        step_names = [s.name for s in self.steps]
        return f"<Pipeline:{self.name} steps={step_names}>"


# Utility Middleware

async def logging_middleware(context: PipelineContext, step: PipelineStep) -> PipelineContext:
    """
    Middleware de logging para debugging."""
    print(f"[Middleware:Logging] Before step '{step.name}' - Results: {list(context.results.keys())}")
    return context


async def validation_middleware(context: PipelineContext, step: PipelineStep) -> PipelineContext:
    """
    Middleware de validaci�n.
"""
    if not context.message:
        raise ValueError("Context message is empty")
    if not context.conversation:
        raise ValueError("Context conversation is empty")
    return context


# Builder Pattern Helper

class PipelineBuilder:
    def __init__(self, name: str):
        """ Nombre del pipeline """
        self.pipeline = MessagePipeline(name)

    def add(self, step: PipelineStep) -> 'PipelineBuilder':
        """Agrega paso al pipeline"""
        self.pipeline.add_step(step)
        return self

    def with_logging(self) -> 'PipelineBuilder':
        """Agrega middleware de logging"""
        self.pipeline.add_middleware(logging_middleware)
        return self

    def with_validation(self) -> 'PipelineBuilder':
        """Agrega middleware de validaci�n"""
        self.pipeline.add_middleware(validation_middleware)
        return self

    def build(self) -> MessagePipeline:
        """Retorna pipeline construido"""
        return self.pipeline
