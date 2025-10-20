"""
Procesador de webhooks de WhatsApp - Bridge to Factory Pattern
LEGACY ADAPTER: Mantiene compatibilidad con main.py mientras migra a Factory
"""
from app.core.factory_orchestrator import FactoryOrchestrator

# Singleton pattern para evitar reinicializar servicios
_orchestrator_instance = None

def get_orchestrator() -> FactoryOrchestrator:
    """
    Lazy initialization del orchestrator con Factory Pattern.
    Reemplaza el AgentOrchestrator legacy que no existe.
    """
    global _orchestrator_instance

    if _orchestrator_instance is None:
        print("[Processor] Inicializando FactoryOrchestrator (migracion desde legacy)")
        _orchestrator_instance = FactoryOrchestrator()

    return _orchestrator_instance

async def process_message(message_data: dict):
    """
    Punto de entrada para webhooks de WhatsApp.

    LEGACY INTERFACE: Mantiene firma original para compatibilidad con main.py
    NUEVO BACKEND: Usa FactoryOrchestrator internamente

    Args:
        message_data: Mensaje desde WhatsApp Business API
    """
    orchestrator = get_orchestrator()
    await orchestrator.process_message(message_data)
