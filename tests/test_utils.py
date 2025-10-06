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
    print("DEBUG Comandos: /reset, /estado, /help, /quit")
    print("TOOLS Extra: help, status, nuevo, restart, salir")
    print("="*60 + "\n")

async def handle_special_commands(user_input: str, state_manager) -> bool:
    """Maneja comandos especiales - True si es comando de salida, False si continúa chat"""
    cmd = user_input.lower().strip()

    # Support both /command and command formats
    if cmd.startswith('/'):
        cmd = cmd[1:]

    if cmd in ["reset", "nuevo", "restart"]:
        try:
            from app.state.crud_operations import ConversationCRUD
            phone = "573123456789"  # TEST_PHONE_NUMBER
            crud = ConversationCRUD()
            crud.delete_conversation(phone)
            print("[RESET] Conversación eliminada. Estado limpio para nuevo flujo.")
            print("[DEBUG] /reset ejecutado correctamente - FASE II Action 4.1")
        except Exception as e:
            print(f"[ERROR] Error en reset: {e}")
        return False  # Continúa en chat, no sale

    elif cmd in ["quit", "exit", "salir"]:
        print("[EXIT] Saliendo del chat local...")
        return True  # Sale del chat

    elif cmd == "estado":
        try:
            from app.state.manager import get_conversation_state
            phone = "573123456789"  # TEST_PHONE_NUMBER
            conversation = get_conversation_state(phone)
            print(f"[DEBUG] /estado ejecutado - FASE II Action 4.2")
            print(f"[DEBUG] Estado actual: {conversation}")

            # Enhanced estado output
            if conversation:
                print(f"[DEBUG] Estado: {conversation.get('state', 'N/A')}")
                print(f"[DEBUG] Cliente: {conversation.get('customer_name', 'N/A')}")
                print(f"[DEBUG] Agente actual: {conversation.get('current_agent', 'N/A')}")
                if 'lead_id' in conversation:
                    print(f"[DEBUG] Lead ID: {conversation.get('lead_id', 'N/A')}")
            else:
                print("[DEBUG] No hay conversación activa")
        except Exception as e:
            print(f"[ERROR] Error obteniendo estado: {e}")
        return False

    elif cmd == 'help':
        print("\n[DEBUG] Comandos disponibles - FASE II Action 4.4:")
        print("  /reset, reset, nuevo, restart → Eliminar conversación y reiniciar")
        print("  /estado, estado → Estado actual de conversación")
        print("  /quit, quit, salir, exit → Salir del chat")
        print("  /help, help → Esta ayuda")
        print("\n[DEBUG] Flujo sugerido:")
        print("  1. 'Hola' → Saludo inicial")
        print("  2. Tu nombre → Fase recopilación")
        print("  3. 'Necesito apartamento' → Transferencia a LeadsalesAgent")
        print("  4. Detalles específicos → Captura y conversión CRM")
        return False

    return False