#!/usr/bin/env python3
"""Test del chat real simulando conversación transferida"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent
from app.state.models import initialize_database
from app.state.manager import get_conversation_state, update_conversation_state

TEST_PHONE_NUMBER = "573123456789"

async def simulate_real_chat():
    """Simula el chat real con reset automático"""

    print("SIMULACION CHAT REAL CON RESET AUTOMATICO")
    print("=" * 45)

    # Inicializar sistema
    initialize_database()

    # Crear conversación transferida (estado problemático)
    print("1. Creando conversación transferida (problema inicial)...")
    update_conversation_state(TEST_PHONE_NUMBER, "TRANSFERIDO", {"customer_name": "Juan Anterior"})
    conversation = get_conversation_state(TEST_PHONE_NUMBER)
    print(f"   Estado problemático: {conversation['state']}, Nombre: {conversation['customer_name']}")

    # Simular proceso de chat_local.py
    async def process_message_like_chat_local(message):
        print(f"\n[Usuario] {message}")

        # IMPORTANTE: Capturar respuesta antes que el orchestrator la envíe
        conversation_before = get_conversation_state(TEST_PHONE_NUMBER)

        # ✅ SOLUCIÓN: Crear conversación si no existe O resetear si está transferida
        if not conversation_before:
            from app.state.manager import update_conversation_state
            update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
            conversation_before = get_conversation_state(TEST_PHONE_NUMBER)
        elif conversation_before.get('state') == 'TRANSFERIDO':
            print(f"[RESET] Conversación transferida detectada, eliminando y creando nueva")
            # Eliminar conversación transferida completamente
            from app.state.crud_operations import ConversationCRUD
            crud = ConversationCRUD()
            crud.delete_conversation(TEST_PHONE_NUMBER)
            # Crear nueva conversación
            from app.state.manager import update_conversation_state
            update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
            conversation_before = get_conversation_state(TEST_PHONE_NUMBER)

        # Usar ReceptionAgent directamente para obtener la respuesta
        reception_agent = ReceptionAgent()
        message_data = {
            "from": TEST_PHONE_NUMBER,
            "text": {"body": message}
        }

        if await reception_agent.can_handle(message_data, conversation_before or {}):
            # Obtener respuesta del agente
            result = await reception_agent.process_message(message_data, conversation_before or {})
            print(f"[Sofia] {result.get('response', 'Sin respuesta')}")

            # Actualizar estado manualmente como hace el orchestrator
            if result.get('new_state'):
                from app.state.manager import update_conversation_state
                data_updates = result.get('data_updates', {})
                update_conversation_state(TEST_PHONE_NUMBER, result['new_state'], data_updates)

            # Mostrar estado actual para debugging
            conversation_after = get_conversation_state(TEST_PHONE_NUMBER)
            if conversation_after:
                state = conversation_after.get('state', 'N/A')
                name = conversation_after.get('customer_name', 'N/A')
                needs = conversation_after.get('customer_needs', 'N/A')
                print(f"[DEBUG] Estado: {state}, Nombre: {name}, Necesidades: {needs}")
        else:
            print("[Sofia] Estado no manejable por ReceptionAgent")

    # Flujo completo
    await process_message_like_chat_local("Hola")
    await process_message_like_chat_local("Busco apartamento")
    await process_message_like_chat_local("Maria Gonzalez")

    print("\nCHAT REAL COMPLETADO")

if __name__ == "__main__":
    asyncio.run(simulate_real_chat())