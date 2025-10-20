"""
Handlers especializados para ReceptionAgent.
Cada handler maneja una parte específica del flujo de conversación.
"""

from .greeting import GreetingHandler, GreetingResult
from .contract import ContractHandler, ContractResult
from .lead_capture import LeadCaptureHandler, LeadCaptureResult

# Exponer solo las clases de handlers, los Results se importan directamente 
# desde los módulos específicos cuando se necesiten
__all__ = [
    "GreetingHandler",
    "ContractHandler",
    "LeadCaptureHandler"
]