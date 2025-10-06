''' Procesador de webhooks De WhatsApp. 
    Punto de entrada para mensajes de entrada de WhatsApp Business API.
    nico trabajo es pasar el control del flujo del webhook al núcleo del sistema (orchestrator).
'''
from app.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()

async def process_message(message_data: dict):
    await orchestrator.process_message(message_data)