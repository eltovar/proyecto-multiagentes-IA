''' Aplicacion FASTAPI para el agente IA multiagentes.
    Punto de entrada HTTP para webhooks de WhatsApp y endpoints de salud. '''

from fastapi import FastAPI, Request, Response, HTTPException
from app.config import settings
from app.state.models import initialize_database
from app.core.factory_orchestrator import FactoryOrchestrator
from app.core.di import DIContainer


container = DIContainer()
orchestrator = FactoryOrchestrator()

initialize_database()

# Verificación visual del estado LLM al iniciar servidor
print("=" * 60)
print("SERVIDOR MULTIAGENTE IA - INICIANDO")
print("=" * 60)
print(f"[LLM STATUS] {'ACTIVO' if not settings.fixed_flow_mode else 'DESACTIVADO'}")
print(f"[LLM MODEL]  {settings.llm_model_name if not settings.fixed_flow_mode else 'N/A'}")
print(f"[MODE]       {'Clasificacion Inteligente' if not settings.fixed_flow_mode else 'Flujo Fijo'}")
print("=" * 60)

app = FastAPI(title="Agente IA Multiagentes", version="2.0")

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        print("✅ Webhook verificado exitosamente!")
        return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Error de verificación")

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        if message["type"] == "text":
            await orchestrator.process_message(message)  # Directo
    except (KeyError, IndexError):
        pass
    return Response(status_code=200)
    
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "architecture": "multiagentes",
        "agents": ["ReceptionAgent", "SupportAgent", "LeadsalesAgent"],
        "llm": {
            "status": "active" if not settings.fixed_flow_mode else "disabled",
            "model": settings.llm_model_name if not settings.fixed_flow_mode else None,
            "mode": "intelligent_classification" if not settings.fixed_flow_mode else "fixed_flow"
        }
    }

@app.get("/agents/status")
def agents_status():
    return {
        "orchestrator": "active",
        "agents": {
            "ReceptionAgent": "active",
            "SupportAgent": "active",
            "LeadsalesAgent": "active"
        }
    }
    
def start_chat():
    """Función principal para iniciar el sistema de chat."""
    print("Iniciando el sistema de chat...")
    # Lógica para inicializar el sistema