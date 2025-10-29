""" Leadsales CRM Service - Modulo refactorizado. """

# Facade pattern: exportar solo la interfaz publica
from .service import LeadsalesService

__all__ = ["LeadsalesService"]
