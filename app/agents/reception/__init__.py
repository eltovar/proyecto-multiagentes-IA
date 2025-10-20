"""
Reception Agent Module - Refactorizado
Maneja el flujo obligatorio de captura de datos iniciales del cliente."""

# Re-exportar solo lo necesario desde handlers
from .handlers import (
    GreetingHandler,
    ContractHandler,
    LeadCaptureHandler
)

# API pública del módulo
__all__ = [
    # Handlers disponibles (usados por nuevo agente vía factory)
    "GreetingHandler",
    "ContractHandler",
    "LeadCaptureHandler"
]

# Importar estados del sistema
from app.state.manager import (
    STATE_NUEVO,
    STATE_RECOPILANDO_NOMBRE,
    STATE_RECOPILANDO_NECESIDAD,
    STATE_LISTO_PARA_TRANSFERIR,
    STATE_TRANSFERIDO
)

__all__.extend([
    "STATE_NUEVO",
    "STATE_RECOPILANDO_NOMBRE", 
    "STATE_RECOPILANDO_NECESIDAD",
    "STATE_LISTO_PARA_TRANSFERIR",
    "STATE_TRANSFERIDO"
])
