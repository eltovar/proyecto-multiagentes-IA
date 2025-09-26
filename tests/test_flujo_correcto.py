#!/usr/bin/env python3
"""Test del flujo correcto según el diagrama exacto"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573123456789"

async def test_flujo_correcto():
    """Test del flujo según el diagrama exacto"""

    print("TEST: FLUJO CORRECTO SEGUN DIAGRAMA")
    print("=" * 40)

    # Inicializar sistema
    initialize_database()

    # Simular conversación existente TRANSFERIDA (problema inicial)
    print("1. Simulando conversación transferida existente...")
    update_conversation_state(TEST_PHONE_NUMBER, "TRANSFERIDO", {"customer_name": "Juan"})
    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"   Estado inicial: {conversation['state']}, Nombre: {conversation['customer_name']}")

    # Simular el proceso de chat_local.py con reset automático
    print("\n2. Aplicando reset automático...")
    if conversation.get('state') == 'TRANSFERIDO':
        print("   [RESET] Conversación transferida detectada, iniciando nueva conversación")
        update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
        conversation = get_conversation_state(TEST_PHONE_NUMBER)
        print(f"   Estado después del reset: {conversation['state']}")

    # FLUJO DESEADO:
    # 1. Usuario: "Hola" → Sofia: "¿En qué puedo ayudarte?"
    # 2. Usuario: "Busco apartamento" → Sofia: "¿Me regalas tu nombre?"
    # 3. Usuario: "Juan Pérez" → Sofia: "Perfecto, un asesor se contactará"

    agent = ReceptionAgent()

    # PASO 1: Usuario dice "Hola"
    print("\n3. PASO 1: Usuario dice 'Hola'")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Hola"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state')}")

    # Actualizar conversación
    conversation['state'] = result['new_state']

    # PASO 2: Usuario dice "Busco apartamento"
    print("\n4. PASO 2: Usuario dice 'Busco apartamento'")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Busco apartamento"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state')}")

    # Actualizar conversación
    if result.get('new_state'):
        conversation['state'] = result['new_state']
    if result.get('data_updates'):
        conversation.update(result['data_updates'])

    # PASO 3: Usuario dice "Juan Pérez"
    print("\n5. PASO 3: Usuario dice 'Juan Pérez'")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Juan Pérez"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state')}")
    print(f"   Transfer_to: {result.get('transfer_to', 'N/A')}")

    print("\n6. RESULTADO:")
    if result.get('new_state') == 'TRANSFERIDO' and 'Juan Pérez' in result.get('data_updates', {}).get('customer_name', ''):
        print("   OK: Flujo completado correctamente según diagrama")
    else:
        print("   ERROR: Flujo no coincide con diagrama")

if __name__ == "__main__":
    asyncio.run(test_flujo_correcto())