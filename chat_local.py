#!/usr/bin/env python3
"""Sistema de Chat Local para Testing - Refactorizado (~80 lineas)"""

import asyncio
import sys
import os

# Imports del sistema
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tests.test_utils import simulate_whatsapp_message, print_welcome, handle_special_commands
    from app.core.orchestrator import AgentOrchestrator
    from app.state.models import initialize_database
    from app.state.manager import state_manager, get_conversation_state
    from app.agents.reception_agent import ReceptionAgent
except ImportError as e:
    print(f"ERROR: Error importando modulos del sistema: {e}")
    sys.exit(1)

TEST_PHONE_NUMBER = "573123456789"

async def process_user_message(message: str, orchestrator: AgentOrchestrator) -> None:
    """Procesa mensaje del usuario y muestra respuesta"""
    try:
        print(f"\n[Usuario] {message}")

        # Formato WhatsApp correcto para orchestrator
        message_data = {
            "from": TEST_PHONE_NUMBER,
            "text": {
                "body": message
            }
        }

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
        if await reception_agent.can_handle(message_data, conversation_before or {}):
            # Obtener respuesta del agente
            result = await reception_agent.process_message(message_data, conversation_before or {})
            print(f"[Sofia] {result.get('response', 'Sin respuesta')}")

            # Actualizar estado manualmente como hace el orchestrator
            if result.get('new_state'):
                from app.state.manager import update_conversation_state
                data_updates = result.get('data_updates', {})
                update_conversation_state(TEST_PHONE_NUMBER, result['new_state'], data_updates)
        else:
            print("[Sofia] Estado no manejable por ReceptionAgent")

        # Mostrar estado actual para debugging
        conversation_after = get_conversation_state(TEST_PHONE_NUMBER)
        if conversation_after:
            state = conversation_after.get('state', 'N/A')
            name = conversation_after.get('customer_name', 'N/A')
            print(f"[DEBUG] Estado: {state}, Nombre: {name}")

    except Exception as e:
        print(f"[ERROR] Error procesando mensaje: {e}")

async def initialize_system() -> AgentOrchestrator:
    """Inicializa el sistema multiagentes"""
    print("[SYSTEM] INFO Inicializando sistema...")

    try:
        # Inicializar base de datos
        initialize_database()
        print("[SYSTEM] EMOJI Base de datos inicializada")

        # Crear orquestador
        orchestrator = AgentOrchestrator()
        if not orchestrator.initialized:
            raise Exception("Orquestador no se inicializo correctamente")

        print("[SYSTEM] EMOJI Orquestador inicializado")
        print("[SYSTEM] EMOJI Sistema listo")
        return orchestrator

    except Exception as e:
        print(f"[SYSTEM] ERROR Error inicializando: {e}")
        raise

async def chat_loop():
    """Loop principal del chat"""
    print_welcome()

    try:
        orchestrator = await initialize_system()
        print("[SYSTEM] LAUNCH Chat iniciado. Escribe 'help' para comandos.\n")

        while True:
            user_input = input("EMOJI Usuario: ").strip()

            if not user_input:
                continue

            # Verificar comandos especiales
            if await handle_special_commands(user_input, state_manager):
                break

            # Procesar mensaje normal
            await process_user_message(user_input, orchestrator)
            print()  # Linea en blanco para separacion

    except KeyboardInterrupt:
        print("\n[SYSTEM] WARN Chat interrumpido por usuario")
    except Exception as e:
        print(f"[SYSTEM] ERROR Error inesperado: {e}")
    finally:
        print("[SYSTEM] WAVE Chat finalizado")

async def main():
    """Funcion principal"""
    if not os.path.exists("app"):
        print("ERROR: No se encuentra directorio 'app'")
        print("Ejecuta desde la raiz del proyecto")
        return

    await chat_loop()

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print("ERROR: Requiere Python 3.7+")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nChat cancelado")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)