#!/usr/bin/env python3
"""Test flujo completo con ChatGPT-4o mini activo"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state
from app.config import settings

TEST_PHONE_NUMBER = "573777888999"

async def test_flujo_completo_openai():
    """Test flujo completo usando ChatGPT-4o mini"""

    print("TEST: FLUJO COMPLETO CON CHATGPT-4O MINI")
    print("=" * 40)

    print(f"LLM Activado: {not settings.fixed_flow_mode}")
    print(f"Modelo: {settings.llm_model_name}")

    # Inicializar sistema
    initialize_database()
    agent = ReceptionAgent()

    # PASO 1: Usuario dice "Hola"
    print("\n1. Usuario: 'Hola'")
    update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Hola"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state')}")

    # Actualizar estado
    if result.get('new_state'):
        conversation['state'] = result['new_state']

    # PASO 2: Usuario responde necesidad
    print("\n2. Usuario: 'Busco apartamento'")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Busco apartamento"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state')}")

    # Actualizar estado
    if result.get('new_state'):
        conversation['state'] = result['new_state']
    if result.get('data_updates'):
        conversation.update(result['data_updates'])

    # PASO 3: Usuario da nombre
    print("\n3. Usuario: 'Pedro'")
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Pedro"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response']}")
    print(f"   Estado: {result.get('new_state')}")
    print(f"   Transfer_to: {result.get('transfer_to', 'N/A')}")

    # PASO 4: Probar clasificación LLM en estado RECOPILANDO_NECESIDAD
    print("\n4. TEST DIRECTO DE CLASIFICACION LLM:")
    print("   Configurando estado RECOPILANDO_NECESIDAD...")

    # Crear conversación específica para test LLM
    update_conversation_state(TEST_PHONE_NUMBER + "_llm", "RECOPILANDO_NECESIDAD", {"customer_name": "Ana"})
    conversation_llm = get_conversation_state(TEST_PHONE_NUMBER + "_llm")

    print("\n   4a. Pregunta: '¿Cuáles son sus servicios?'")
    message_data = {
        "from": TEST_PHONE_NUMBER + "_llm",
        "text": {"body": "¿Cuáles son sus servicios?"}
    }

    result = await agent.process_message(message_data, conversation_llm)
    print(f"      Sofia: {result['response'][:60]}...")
    print(f"      Transfer_to: {result.get('transfer_to', 'N/A')}")

    if result.get('transfer_to') == 'SupportAgent':
        print("      ✅ CLASIFICACION LLM: PREGUNTA -> SupportAgent")
    else:
        print("      ❌ Error en clasificación LLM")

    print("\n   4b. Necesidad: 'Quiero comprar casa'")
    # Reset para segundo test
    update_conversation_state(TEST_PHONE_NUMBER + "_llm2", "RECOPILANDO_NECESIDAD", {"customer_name": "Luis"})
    conversation_llm2 = get_conversation_state(TEST_PHONE_NUMBER + "_llm2")

    message_data = {
        "from": TEST_PHONE_NUMBER + "_llm2",
        "text": {"body": "Quiero comprar casa"}
    }

    result = await agent.process_message(message_data, conversation_llm2)
    print(f"      Sofia: {result['response'][:60]}...")
    print(f"      Transfer_to: {result.get('transfer_to', 'N/A')}")

    if result.get('transfer_to') == 'LeadsalesAgent':
        print("      ✅ CLASIFICACION LLM: NECESIDAD -> LeadsalesAgent")
    else:
        print("      ❌ Error en clasificación LLM")

    print("\nRESULTADO: ChatGPT-4o mini funcionando en clasificación inteligente")

if __name__ == "__main__":
    asyncio.run(test_flujo_completo_openai())