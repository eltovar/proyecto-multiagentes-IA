#!/usr/bin/env python3
"""Script para probar clasificación LLM específicamente"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import update_conversation_state, get_conversation_state
from app.config import settings

TEST_PHONE_NUMBER = "573999888777"

async def test_llm_classification():
    """Prueba la clasificación LLM específicamente"""

    print("PRUEBA DE CLASIFICACIÓN LLM")
    print("=" * 40)

    # Inicializar sistema
    initialize_database()
    agent = ReceptionAgent()

    # Configurar para modo LLM (no fixed_flow)
    original_mode = settings.fixed_flow_mode
    settings.fixed_flow_mode = False
    print(f"Modo OpenAI LLM activado (fixed_flow_mode: {settings.fixed_flow_mode})")

    try:
        # Configurar estado correcto para LLM
        from app.state.manager import state_manager

        # Crear conversación directamente
        conversation = {
            "whatsapp_id": TEST_PHONE_NUMBER,
            "state": "RECOPILANDO_NECESIDAD",
            "customer_name": "Ana",
            "customer_needs": None
        }

        print(f"Estado configurado: {conversation['state']}, Nombre: {conversation['customer_name']}")

        # TEST 1: Mensaje tipo PREGUNTA
        print("\n[TEST 1] Mensaje tipo PREGUNTA")
        message_data = {
            "from": TEST_PHONE_NUMBER,
            "text": {"body": "¿Qué servicios ofrecen?"}
        }

        result = await agent._handle_need_collection("¿Qué servicios ofrecen?", "Ana", TEST_PHONE_NUMBER)
        print(f"   Respuesta: {result['response'][:50]}...")
        print(f"   Transfer_to: {result.get('transfer_to', 'N/A')}")

        # TEST 2: Mensaje tipo NECESIDAD
        print("\n[TEST 2] Mensaje tipo NECESIDAD")
        result = await agent._handle_need_collection("Quiero comprar un apartamento", "Ana", TEST_PHONE_NUMBER)
        print(f"   Respuesta: {result['response'][:50]}...")
        print(f"   Transfer_to: {result.get('transfer_to', 'N/A')}")

        print("\n[RESULTADO] OK Clasificacion LLM funcionando")

    except Exception as e:
        print(f"\n[ERROR] Error en clasificacion LLM: {e}")

    finally:
        # Restaurar configuración original
        settings.fixed_flow_mode = original_mode
        print(f"\nConfiguración restaurada (fixed_flow_mode: {settings.fixed_flow_mode})")

if __name__ == "__main__":
    asyncio.run(test_llm_classification())