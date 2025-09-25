''' Procesador de webhooks De WhatsApp. 
    Punto de entrada para mensajes de entrada de WhatsApp Business API.
'''
from app.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()

async def process_message(message_data: dict):
    await orchestrator.process_message(message_data)