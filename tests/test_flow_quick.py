#!/usr/bin/env python3
"""Test rápido del flujo principal sin emojis"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573000999888"

async def test_main_flow():
    """Test del flujo principal paso a paso"""

    print("=== TEST FLUJO PRINCIPAL ===")

    # Inicializar
    initialize_database()
    agent = ReceptionAgent()

    # Función helper
    def update_state_from_result(result):
        if result.get('new_state'):
            data_updates = result.get('data_updates', {})
            update_conversation_state(TEST_PHONE_NUMBER, result['new_state'], data_updates)

    # PASO 1: Usuario: "Hola"
    print("\n[Usuario] Hola")

    # Crear conversación nueva
    update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    message_1 = {"from": TEST_PHONE_NUMBER, "text": {"body": "Hola"}}
    result_1 = await agent.process_message(message_1, conversation)
    update_state_from_result(result_1)

    print(f"[Sofia] {result_1['response']}")
    print(f"[Estado] {result_1.get('new_state')}")

    # PASO 2: Usuario responde cualquier cosa
    print("\n[Usuario] necesito información")

    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    message_2 = {"from": TEST_PHONE_NUMBER, "text": {"body": "necesito información"}}
    result_2 = await agent.process_message(message_2, conversation)
    update_state_from_result(result_2)

    print(f"[Sofia] {result_2['response']}")
    print(f"[Estado] {result_2.get('new_state')}")

    # PASO 3: Usuario da nombre
    print("\n[Usuario] Juan Carlos")

    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    message_3 = {"from": TEST_PHONE_NUMBER, "text": {"body": "Juan Carlos"}}
    result_3 = await agent.process_message(message_3, conversation)
    update_state_from_result(result_3)

    print(f"[Sofia] {result_3['response']}")
    print(f"[Estado] {result_3.get('new_state')}")
    print(f"[Transfer] {result_3.get('transfer_to')}")

    # Estado final
    final_conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"\n=== RESULTADO FINAL ===")
    print(f"Estado: {final_conversation['state']}")
    print(f"Nombre: {final_conversation.get('customer_name')}")

    # Validación
    if (final_conversation['state'] == 'TRANSFERIDO' and
        final_conversation.get('customer_name') == 'Juan Carlos'):
        print("[OK] FLUJO PRINCIPAL FUNCIONANDO CORRECTAMENTE")
        return True
    else:
        print("[ERROR] Flujo principal con problemas")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_main_flow())
    if result:
        print("\n*** FLUJO PRINCIPAL LISTO ***")
    else:
        print("\n*** FLUJO PRINCIPAL REQUIERE CORRECCIÓN ***")