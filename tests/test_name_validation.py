#!/usr/bin/env python3
"""Test de validación de nombres mejorada"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.reception_agent import ReceptionAgent

async def test_name_validation():
    """Test específico para validación de nombres"""

    print("TEST: VALIDACION DE NOMBRES MEJORADA")
    print("=" * 35)

    agent = ReceptionAgent()

    # Test cases: respuestas que NO deben ser aceptadas como nombres
    invalid_inputs = ["no", "si", "nope", "ok", "hola", "bien", "qué", "como"]

    print("1. PRUEBAS DE RESPUESTAS INVALIDAS:")
    for test_input in invalid_inputs:
        result = agent._extract_name(test_input)
        status = "RECHAZADO" if result is None else f"ACEPTADO: {result}"
        print(f"   '{test_input}' → {status}")

    print("\n2. PRUEBAS DE NOMBRES VALIDOS:")
    valid_inputs = ["Juan", "Maria", "Carlos Pérez", "Ana María", "Luis Fernando"]

    for test_input in valid_inputs:
        result = agent._extract_name(test_input)
        status = f"ACEPTADO: {result}" if result else "RECHAZADO"
        print(f"   '{test_input}' → {status}")

    print("\n3. PRUEBA FLUJO COMPLETO CON 'no':")

    # Simular flujo donde usuario dice "no" cuando se le pide el nombre
    from app.state.models import initialize_database
    from app.state.manager import get_conversation_state, update_conversation_state

    TEST_PHONE_NUMBER = "573111222333"

    # Inicializar sistema
    initialize_database()

    # Crear conversación en estado RECOPILANDO_NOMBRE
    update_conversation_state(TEST_PHONE_NUMBER, "RECOPILANDO_NOMBRE", {"customer_needs": "Busco apartamento"})
    conversation = get_conversation_state(TEST_PHONE_NUMBER)

    # Usuario responde "no" cuando se le pide el nombre
    message_data = {
        "from": TEST_PHONE_NUMBER,
        "text": {"body": "no"}
    }

    result = await agent.process_message(message_data, conversation)
    print(f"   Usuario dice 'no':")
    print(f"   → Sofia: {result['response']}")
    print(f"   → Estado: {result.get('new_state', 'Sin cambio')}")

    # Verificar que siga pidiendo el nombre
    expected_stay_in_name_collection = result.get('new_state') == 'RECOPILANDO_NOMBRE'
    if expected_stay_in_name_collection:
        print("   ✅ CORRECTO: Sigue pidiendo el nombre")
    else:
        print("   ❌ ERROR: Avanzó con 'no' como nombre")

if __name__ == "__main__":
    asyncio.run(test_name_validation())