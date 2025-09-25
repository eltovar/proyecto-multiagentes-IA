#!/usr/bin/env python3
"""Sistema de Chat Local para Testing - Refactorizado (~80 lineas)"""

import asyncio
import sys
import os

# Imports del sistema
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from test_utils import simulate_whatsapp_message, print_welcome, handle_special_commands
    from app.core.orchestrator import AgentOrchestrator
    from app.state.models import initialize_database
    from app.state.manager import state_manager
except ImportError as e:
    print(f"ERROR: Error importando modulos del sistema: {e}")
    sys.exit(1)

TEST_PHONE_NUMBER = "573123456789"

async def process_user_message(message: str, orchestrator: AgentOrchestrator) -> None:
    """Procesa mensaje del usuario a traves del orquestador"""
    try:
        print(f"[BOT] Procesando: {message[:30]}{'...' if len(message) > 30 else ''}")

        result = await orchestrator.process_message(
            whatsapp_id=TEST_PHONE_NUMBER,
            message=message,
            message_type="text"
        )

        # Mostrar respuesta
        status = result.get("status", "unknown")
        response = result.get("response", "")

        if status == "success" and response:
            print(f"[AGENT] {response}")
        elif status == "handoff_active":
            print("[SYSTEM] PAUSE Conversacion transferida - Humano al control")
        elif status == "error":
            print(f"[ERROR] {result.get('message', 'Error desconocido')}")
        else:
            print(f"[SYSTEM] Estado: {status}")

    except Exception as e:
        print(f"ERROR Error procesando mensaje: {e}")

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