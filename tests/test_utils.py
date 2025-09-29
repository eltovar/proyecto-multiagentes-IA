#!/usr/bin/env python3
"""Utilidades para testing - Maximo 80 lineas"""

from datetime import datetime
from typing import Dict, Any

def simulate_whatsapp_message(phone: str, text: str) -> Dict[str, Any]:
    """Simula formato WhatsApp webhook"""
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": phone,
                        "type": "text",
                        "text": {"body": text},
                        "timestamp": str(int(datetime.now().timestamp()))
                    }]
                }
            }]
        }]
    }

def print_welcome():
    """Banner de bienvenida"""
    print("\n" + "="*60)
    print("BOT CHAT LOCAL - AGENTE MULTIAGENTES")
    print("="*60)
    print("PHONE Simulando WhatsApp: 573123456789")
    print("TOOLS Comandos: 'quit', 'reset', 'status', 'help'")
    print("="*60 + "\n")

async def handle_special_commands(user_input: str, state_manager) -> bool:
    """Maneja comandos especiales - True si es comando de salida, False si continúa chat"""
    cmd = user_input.lower().strip()

    if cmd in ["reset", "nuevo", "restart"]:
        try:
            from app.state.crud_operations import ConversationCRUD
            phone = "573123456789"  # TEST_PHONE_NUMBER
            crud = ConversationCRUD()
            crud.delete_conversation(phone)
            print("[RESET] Conversación eliminada. Estado limpio para nuevo flujo.")
        except Exception as e:
            print(f"[ERROR] Error en reset: {e}")
        return False  # Continúa en chat, no sale

    elif cmd in ["quit", "exit", "salir"]:
        print("WAVE Saliendo del chat local...")
        return True  # Sale del chat

    elif cmd == "estado":
        try:
            from app.state.manager import get_conversation_state
            phone = "573123456789"  # TEST_PHONE_NUMBER
            conversation = get_conversation_state(phone)
            print(f"[DEBUG] Estado actual: {conversation}")
        except Exception as e:
            print(f"[ERROR] Error obteniendo estado: {e}")
        return False

    elif cmd == 'help':
        print("\nLIST COMANDOS DISPONIBLES:")
        print("  quit/salir/exit → Salir del chat")
        print("  reset/nuevo/restart → Eliminar conversación y reiniciar")
        print("  estado → Estado actual de conversación")
        print("  help → Esta ayuda")
        print("\nTIP FLUJO SUGERIDO:")
        print("  1. 'Hola' → Saludo")
        print("  2. Tu nombre → Recopilacion")
        print("  3. 'Necesito...' → Transferencia")
        return False

    return False