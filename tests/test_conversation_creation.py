#!/usr/bin/env python3
"""Test que una conversación nueva se crea correctamente"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573000111222"

async def test_new_conversation():
    """Simula el flujo de chat_local.py con conversación nueva"""

    print("TEST: CREACIÓN AUTOMÁTICA DE CONVERSACIÓN")
    print("=" * 45)

    # Inicializar sistema
    initialize_database()

    # Simular primera conversación (sin estado previo)
    print(f"1. Verificando conversación existente para {TEST_PHONE_NUMBER}")
    conversation_before = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"   Conversación existente: {conversation_before}")

    # ✅ SOLUCIÓN: Crear conversación si no existe (como en chat_local.py)
    if not conversation_before:
        print("2. Creando conversación nueva con estado NUEVO")
        update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
        conversation_before = get_conversation_state(TEST_PHONE_NUMBER)
        print(f"   Conversación creada: {conversation_before}")

    # Probar can_handle del ReceptionAgent
    print("3. Probando ReceptionAgent.can_handle()")
    reception_agent = ReceptionAgent()
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Hola"}
    }

    can_handle = await reception_agent.can_handle(message_data, conversation_before or {})
    print(f"   can_handle() resultado: {can_handle}")

    if can_handle:
        print("4. Procesando mensaje con ReceptionAgent")
        result = await reception_agent.process_message(message_data, conversation_before or {})
        print(f"   Respuesta: {result['response'][:50]}...")
        print(f"   Nuevo estado: {result.get('new_state', 'N/A')}")
        print("\n✅ PROBLEMA SOLUCIONADO: Conversación nueva manejada correctamente")
    else:
        print("❌ PROBLEMA PERSISTE: can_handle() sigue retornando False")

if __name__ == "__main__":
    asyncio.run(test_new_conversation())