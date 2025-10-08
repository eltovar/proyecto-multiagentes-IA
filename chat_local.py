#!/usr/bin/env python3
"""Sistema de Chat Local para Testing - Refactorizado (~80 lineas)"""

import asyncio
import sys
import os

# Imports del sistema
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tests.test_utils import simulate_whatsapp_message, print_welcome, handle_special_commands
    from app.core.factory_orchestrator import FactoryOrchestrator  # ← NUEVO: Factory Pattern
    from app.state.models import initialize_database
    from app.state.manager import state_manager, get_conversation_state
    from app.config import settings

    # ❌ REMOVIDO: from app.agents.reception_agent import ReceptionAgent
    # ❌ REMOVIDO: from app.core.orchestrator import AgentOrchestrator

    # PASO 1: Activar LLM temporalmente
    settings.fixed_flow_mode = False

    print(f"[SYSTEM] LLM Status: {'ACTIVO' if not settings.fixed_flow_mode else 'DESACTIVADO'}")
    print(f"[SYSTEM] Modelo: {settings.llm_model_name if not settings.fixed_flow_mode else 'N/A'}")
    

except ImportError as e:
    print(f"ERROR: Error importando modulos del sistema: {e}")
    sys.exit(1)

TEST_PHONE_NUMBER = "573123456789"

async def process_user_message(message: str, orchestrator: FactoryOrchestrator) -> None:
    """Procesa mensaje del usuario usando FactoryOrchestrator"""
    try:
        print(f"\n[Usuario] {message}")

        # Formato WhatsApp correcto
        message_data = {
            "from": TEST_PHONE_NUMBER,
            "text": {
                "body": message
            }
        }

        # IMPORTANTE: Capturar conversación antes de procesar
        conversation_before = get_conversation_state(TEST_PHONE_NUMBER)

        # ✅ SOLUCIÓN: Crear conversación si no existe O resetear si está transferida
        if not conversation_before:
            from app.state.manager import update_conversation_state
            update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
            conversation_before = get_conversation_state(TEST_PHONE_NUMBER)
        elif conversation_before.get('state') == 'TRANSFERIDO':
            print(f"[RESET] Conversación transferida detectada, eliminando y creando nueva")
            from app.state.crud_operations import ConversationCRUD
            crud = ConversationCRUD()
            crud.delete_conversation(TEST_PHONE_NUMBER)
            from app.state.manager import update_conversation_state
            update_conversation_state(TEST_PHONE_NUMBER, "NUEVO")
            conversation_before = get_conversation_state(TEST_PHONE_NUMBER)

        # 🔥 INTERCEPTAR send_message para capturar respuesta
        captured_responses = []

        # Importar send_message original
        from app.services.whatsapp_service import send_message as original_send_message

        async def mock_send_message(to: str, text: str) -> bool:
            """Mock que captura respuestas"""
            captured_responses.append(text)
            return True

        # Monkey-patch temporal
        import app.services.whatsapp_service
        import app.core.factory_orchestrator
        app.services.whatsapp_service.send_message = mock_send_message
        app.core.factory_orchestrator.send_message = mock_send_message

        try:
            # 🔥 USAR FACTORY ORCHESTRATOR - Hot Reload automático
            await orchestrator.process_message(message_data)

            # Mostrar respuestas capturadas
            if captured_responses:
                for response in captured_responses:
                    print(f"[Sofia] {response}")
            else:
                print("[Sofia] (Sin respuesta)")

        finally:
            # Restaurar send_message original
            app.services.whatsapp_service.send_message = original_send_message
            app.core.factory_orchestrator.send_message = original_send_message

        # Mostrar estado actual para debugging
        conversation_after = get_conversation_state(TEST_PHONE_NUMBER)
        if conversation_after:
            state = conversation_after.get('state', 'N/A')
            name = conversation_after.get('customer_name', 'N/A')
            current_agent = conversation_after.get('current_agent', 'N/A')
            print(f"[DEBUG] Estado: {state}, Nombre: {name}, Agente: {current_agent}")

    except Exception as e:
        print(f"[ERROR] Error procesando mensaje: {e}")
        import traceback
        traceback.print_exc()

async def initialize_system() -> FactoryOrchestrator:
    """Inicializa el sistema con FactoryOrchestrator (Hot Reload enabled)"""
    print("[SYSTEM] INFO Inicializando sistema con Hot Reload...")

    try:
        # AUTO-RESET: Limpiar conversaciones transferidas
        try:
            from app.state.crud_operations import ConversationCRUD
            crud = ConversationCRUD()
            conversation = crud.get_conversation(TEST_PHONE_NUMBER)
            if conversation and conversation.state == "TRANSFERIDO":
                crud.delete_conversation(TEST_PHONE_NUMBER)
                print("[AUTO-RESET] Conversación transferida limpiada")
        except:
            pass

        # Inicializar base de datos
        initialize_database()
        print("[SYSTEM] OK Base de datos inicializada")

        # Crear FactoryOrchestrator (con Hot Reload)
        orchestrator = FactoryOrchestrator()
        if not orchestrator.initialized:
            raise Exception("FactoryOrchestrator no se inicializo correctamente")

        print("[SYSTEM] OK FactoryOrchestrator inicializado")
        print("[SYSTEM] OK Hot Reload ACTIVO")
        print("[SYSTEM] OK Sistema listo")
        return orchestrator

    except Exception as e:
        print(f"[SYSTEM] ERROR Error inicializando: {e}")
        import traceback
        traceback.print_exc()
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