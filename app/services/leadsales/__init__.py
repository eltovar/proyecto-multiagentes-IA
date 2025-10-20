"""
Leadsales CRM Service - Modulo refactorizado.

Arquitectura modular:
- client.py: Cliente HTTP para API Leadsales
- scoring.py: Integracion con sistema scoring
- metadata.py: Extraccion y enriquecimiento de metadata
- visualization.py: Construccion de visualizaciones CRM
- service.py: Orquestador principal

Uso:
    from app.services.leadsales import LeadsalesService

    service = LeadsalesService()
    result = await service.create_lead("Juan Perez", "+573001234567", "Busco apartamento")
"""

# Facade pattern: exportar solo la interfaz publica
from .service import LeadsalesService

__all__ = ["LeadsalesService"]
