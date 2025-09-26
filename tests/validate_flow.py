#!/usr/bin/env python3
"""Script para validar secuencia de flujo fijo"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.orchestrator import AgentOrchestrator
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573111222333"  # Nuevo número para prueba completa

async def validate_sequence():
    """Valida la secuencia completa paso a paso"""

    print("VALIDACION SECUENCIA DE FLUJO FIJO")
    print("=" * 50)

    # Inicializar sistema
    initialize_database()
    orchestrator = AgentOrchestrator()

    # LIMPIAR estado previo
    print("Limpiando estado previo...")
    try:
        update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
        print("Estado limpiado correctamente")
    except:
        print("No hay estado previo que limpiar")

    # PASO 1: "Hola" → Respuesta Sofía
    print("\n[1] PASO 1: Usuario dice 'Hola'")
    message_1 = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Hola"}
    }

    await orchestrator.process_message(message_1)
    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"   Estado: {conversation['state']}")
    print("   Esperado: RECOPILANDO_NOMBRE")

    # PASO 2: "Cualquier cosa" → Solicita nombre
    print("\n[2] PASO 2: Usuario responde 'Cualquier cosa'")
    message_2 = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Cualquier cosa"}
    }

    await orchestrator.process_message(message_2)
    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"   Estado: {conversation['state']}")
    print("   Esperado: RECOPILANDO_NECESIDAD")

    # PASO 3: "Juan" → Confirmación + Handoff
    print("\n[3] PASO 3: Usuario dice 'Juan'")
    message_3 = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "Juan"}
    }

    await orchestrator.process_message(message_3)
    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"   Estado: {conversation['state']}")
    print(f"   Nombre: {conversation.get('customer_name', 'No extraído')}")
    print("   Esperado: TRANSFERIDO + Nombre extraido")

    # VALIDACIÓN FINAL
    print("\n[RESULTADO] VALIDACION")
    print("=" * 30)

    if conversation['state'] == 'TRANSFERIDO' and conversation.get('customer_name'):
        print("[OK] SECUENCIA CORRECTA - Flujo fijo funcionando")
    else:
        print("[ERROR] Secuencia incorrecta")
        print(f"Estado final: {conversation['state']}")
        print(f"Nombre: {conversation.get('customer_name')}")

if __name__ == "__main__":
    asyncio.run(validate_sequence())