#!/usr/bin/env python3
"""Test interactivo del flujo fijo - Simulación manual"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573000111222"

async def test_interactive():
    """Test interactivo que simula la conversación"""

    print("=== TEST INTERACTIVO DEL FLUJO FIJO ===")
    print("Simulando conversación paso a paso...\n")

    # Inicializar
    initialize_database()
    agent = ReceptionAgent()

    # PASO 1: Usuario dice "Hola"
    print("[Usuario] Hola")

    message_1 = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Hola"}
    }

    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    if not conversation:
        update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
        conversation = get_conversation_state(TEST_PHONE_NUMBER)

    result_1 = await agent.process_message(message_1, conversation)
    print(f"[Sofia] {result_1['response']}")
    print(f"[Estado] {result_1.get('new_state')}")

    # Actualizar estado manualmente
    if result_1.get('new_state'):
        update_conversation_state(TEST_PHONE_NUMBER, result_1['new_state'])
        print("[DEBUG] Estado actualizado")

    # PASO 2: Usuario responde
    print("[Usuario] necesito información")

    message_2 = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "necesito información"}
    }

    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    result_2 = await agent.process_message(message_2, conversation)
    print(f"[Sofia] {result_2['response']}")
    print(f"[Estado] {result_2.get('new_state')}")

    # Actualizar estado manualmente
    if result_2.get('new_state'):
        update_conversation_state(TEST_PHONE_NUMBER, result_2['new_state'])
        print("[DEBUG] Estado actualizado")

    # PASO 3: Usuario da nombre
    print("[Usuario] Juan Pérez")

    message_3 = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Juan Pérez"}
    }

    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    result_3 = await agent.process_message(message_3, conversation)
    print(f"[Sofia] {result_3['response']}")
    print(f"[Estado] {result_3.get('new_state')}")
    print(f"[Transfer] {result_3.get('transfer_to')}")

    # Actualizar estado y datos
    if result_3.get('new_state'):
        data_updates = result_3.get('data_updates', {})
        update_conversation_state(TEST_PHONE_NUMBER, result_3['new_state'], data_updates)
        print(f"[DEBUG] Estado y datos actualizados: {data_updates}")

    # Estado final
    final_conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"\n=== ESTADO FINAL ===")
    print(f"Estado: {final_conversation['state']}")
    print(f"Nombre: {final_conversation.get('customer_name', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_interactive())