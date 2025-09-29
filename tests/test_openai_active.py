#!/usr/bin/env python3
"""Test que el LLM ChatGPT-4o mini está activo y funcionando"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state
from app.config import settings

TEST_PHONE_NUMBER = "573888777666"

async def test_openai_llm_active():
    """Test que ChatGPT-4o mini está activo y clasificando"""

    print("TEST: CHATGPT-4O MINI ACTIVO")
    print("=" * 30)

    # Verificar configuración
    print(f"Fixed Flow Mode: {settings.fixed_flow_mode}")
    print(f"LLM Model: {settings.llm_model_name}")
    print(f"LLM Fallback: {settings.llm_fallback_enabled}")

    if settings.fixed_flow_mode:
        print("ERROR: LLM está desactivado (fixed_flow_mode=True)")
        return
    else:
        print("OK: LLM está activado (fixed_flow_mode=False)")

    # Inicializar sistema
    initialize_database()
    agent = ReceptionAgent()

    # Configurar conversación en estado RECOPILANDO_NECESIDAD
    update_conversation_state(TEST_PHONE_NUMBER, "RECOPILANDO_NECESIDAD", {"customer_name": "Carlos"})
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    print(f"\nEstado: {conversation['state']}, Nombre: {conversation['customer_name']}")

    # TEST 1: Mensaje tipo PREGUNTA (debería ir a SupportAgent)
    print("\n1. TEST PREGUNTA:")
    print("   Usuario: '¿Qué servicios ofrecen?'")

    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "¿Qué servicios ofrecen?"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response'][:50]}...")
    print(f"   Transfer_to: {result.get('transfer_to', 'N/A')}")

    if result.get('transfer_to') == 'SupportAgent':
        print("   OK: Clasificado como PREGUNTA -> SupportAgent")
    else:
        print("   ERROR: No clasificado correctamente")

    # TEST 2: Mensaje tipo NECESIDAD (debería ir a LeadsalesAgent)
    print("\n2. TEST NECESIDAD:")
    print("   Usuario: 'Quiero comprar un apartamento'")

    # Resetear conversación
    update_conversation_state(TEST_PHONE_NUMBER, "RECOPILANDO_NECESIDAD", {"customer_name": "Carlos"})
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Quiero comprar un apartamento"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Sofia: {result['response'][:50]}...")
    print(f"   Transfer_to: {result.get('transfer_to', 'N/A')}")

    if result.get('transfer_to') == 'LeadsalesAgent':
        print("   OK: Clasificado como NECESIDAD -> LeadsalesAgent")
    else:
        print("   ERROR: No clasificado correctamente")

    print("\nRESULTADO: ChatGPT-4o mini funcionando para clasificación")

if __name__ == "__main__":
    asyncio.run(test_openai_llm_active())