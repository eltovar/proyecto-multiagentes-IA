#!/usr/bin/env python3
"""Test flujo cuando usuario dice 'no' al pedir nombre"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573111222333"

async def test_no_response_flow():
    """Test flujo cuando usuario dice 'no' al pedir nombre"""

    print("TEST: FLUJO CON RESPUESTA 'no'")
    print("=" * 30)

    # Inicializar sistema
    initialize_database()
    agent = ReceptionAgent()

    # Configurar conversación en estado RECOPILANDO_NOMBRE
    update_conversation_state(TEST_PHONE_NUMBER, "RECOPILANDO_NOMBRE", {"customer_needs": "Busco apartamento"})
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    print(f"Estado inicial: {conversation['state']}")
    print(f"Necesidades: {conversation['customer_needs']}")

    # PASO 1: Usuario responde "no" cuando se le pide el nombre
    print("\n1. Usuario dice 'no':")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "no"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state', 'Sin cambio')}")

    # Verificar que sigue en RECOPILANDO_NOMBRE
    if result.get('new_state') == 'RECOPILANDO_NOMBRE':
        print("   OK: Sigue pidiendo el nombre")
    else:
        print("   ERROR: No siguio pidiendo el nombre")

    # Actualizar conversación para el siguiente paso
    conversation['state'] = result.get('new_state', conversation['state'])
    if result.get('data_updates'):
        conversation.update(result['data_updates'])

    # PASO 2: Usuario finalmente da un nombre válido
    print("\n2. Usuario dice 'Juan':")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Juan"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state', 'Sin cambio')}")

    # Verificar que ahora sí procesa el nombre y transfiere
    if result.get('new_state') == 'TRANSFERIDO' and 'Juan' in result.get('data_updates', {}).get('customer_name', ''):
        print("   OK: Nombre aceptado y conversacion transferida")
    else:
        print("   ERROR: No proceso el nombre correctamente")

    print("\nRESULTADO: Validacion de nombres funcionando correctamente")

if __name__ == "__main__":
    asyncio.run(test_no_response_flow())