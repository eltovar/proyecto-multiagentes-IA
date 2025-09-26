#!/usr/bin/env python3
"""Test rápido simulando chat_local.py"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573123456789"

async def simulate_chat():
    """Simula el chat completo"""

    print("SIMULACION CHAT COMPLETO")
    print("=" * 25)

    # Inicializar sistema
    initialize_database()
    agent = ReceptionAgent()

    messages = ["Hola", "Quiero informacion", "Juan"]

    conversation_before = None

    for i, user_message in enumerate(messages, 1):
        print(f"\n[{i}] Usuario: {user_message}")

        # ✅ SOLUCIÓN: Crear conversación si no existe (como en chat_local.py)
        if not conversation_before:
            update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
            conversation_before = get_conversation_state(TEST_PHONE_NUMBER)

        # Usar ReceptionAgent directamente
        message_data = {
            "from": TEST_PHONE_NUMBER,
            "text": {"body": user_message}
        }

        if await agent.can_handle(message_data, conversation_before or {}):
            result = await agent.process_message(message_data, conversation_before or {})
            print(f"[Sofia] {result.get('response', 'Sin respuesta')}")

            # Actualizar estado manualmente
            if result.get('new_state'):
                data_updates = result.get('data_updates', {})
                update_conversation_state(TEST_PHONE_NUMBER, result['new_state'], data_updates)
                conversation_before = get_conversation_state(TEST_PHONE_NUMBER)

            # Mostrar estado actual
            if conversation_before:
                state = conversation_before.get('state', 'N/A')
                name = conversation_before.get('customer_name', 'N/A')
                needs = conversation_before.get('customer_needs', 'N/A')
                print(f"[DEBUG] Estado: {state}, Nombre: {name}, Necesidades: {needs}")
        else:
            print("[Sofia] Estado no manejable")

    print("\nCHAT COMPLETADO")

if __name__ == "__main__":
    asyncio.run(simulate_chat())