#!/usr/bin/env python3
"""Test del flujo correcto según especificación original"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573111000999"

async def test_correct_flow():
    """Test del flujo correcto según especificación"""

    print("TEST: FLUJO CORRECTO SEGUN ESPECIFICACION")
    print("=" * 40)

    # Inicializar sistema
    initialize_database()
    agent = ReceptionAgent()

    # PASO 1: Usuario dice "Hola"
    print("PASO 1: Usuario dice 'Hola'")

    # Crear conversación nueva
    update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Hola"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"  IA: {result['response']}")
    print(f"  Estado: {result.get('new_state')}")

    # Actualizar conversación
    conversation['state'] = result['new_state']

    # PASO 2: Usuario envía cualquier mensaje (información)
    print("\nPASO 2: Usuario dice 'Quiero informacion'")

    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Quiero informacion"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"  IA: {result['response']}")
    print(f"  Estado: {result.get('new_state')}")

    # Verificar que NO extrae "Quiero informacion" como nombre
    if "Quiero Informacion" in result.get('data_updates', {}).get('customer_name', ''):
        print("  ERROR: Extrajo mensaje como nombre incorrectamente")
    else:
        print("  OK: No extrajo mensaje como nombre")

    # Actualizar conversación
    if result.get('new_state'):
        conversation['state'] = result['new_state']
    if result.get('data_updates'):
        conversation.update(result['data_updates'])

    # PASO 3: Usuario dice su nombre
    print("\nPASO 3: Usuario dice 'Juan'")

    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Juan"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"  IA: {result['response']}")
    print(f"  Estado: {result.get('new_state')}")

    # Verificar que sí extrae "Juan" como nombre
    if "Juan" in result.get('data_updates', {}).get('customer_name', ''):
        print("  OK: Extrajo 'Juan' como nombre correctamente")
    else:
        print("  ERROR: No extrajo 'Juan' como nombre")

    print("\nRESULTADO: Flujo corregido según especificación original")

if __name__ == "__main__":
    asyncio.run(test_correct_flow())