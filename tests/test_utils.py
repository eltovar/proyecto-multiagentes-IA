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
    """Maneja comandos especiales - True si es comando"""
    cmd = user_input.lower().strip()

    if cmd in ['quit', 'salir', 'exit']:
        print("WAVE Saliendo del chat local...")
        return True

    elif cmd == 'reset':
        try:
            # Reset conversation state
            phone = "573123456789"
            conversation = state_manager.get_conversation(phone)
            if conversation:
                state_manager.update_conversation_state(
                    whatsapp_id=phone,
                    new_state="NUEVO",
                    customer_name=None,
                    customer_needs=None
                )
                print("EMOJI Conversacion reiniciada")
            else:
                print("WARN No hay conversacion para reiniciar")
        except Exception as e:
            print(f"ERROR Error reiniciando: {e}")
        return True

    elif cmd == 'status':
        try:
            phone = "573123456789"
            conversation = state_manager.get_conversation(phone)
            if conversation:
                print(f"\nEMOJI ESTADO DE CONVERSACION:")
                print(f"  Estado: {conversation.state}")
                print(f"  Nombre: {conversation.customer_name or 'No recopilado'}")
                print(f"  Necesidades: {conversation.customer_needs or 'No recopiladas'}")
            else:
                print("WARN No hay conversacion activa")
        except Exception as e:
            print(f"ERROR Error obteniendo estado: {e}")
        return True

    elif cmd == 'help':
        print("\nLIST COMANDOS DISPONIBLES:")
        print("  quit/salir  → Salir del chat")
        print("  reset       → Reiniciar conversacion")
        print("  status      → Estado actual")
        print("  help        → Esta ayuda")
        print("\nTIP FLUJO SUGERIDO:")
        print("  1. 'Hola' → Saludo")
        print("  2. Tu nombre → Recopilacion")
        print("  3. 'Necesito...' → Transferencia")
        return True

    return False