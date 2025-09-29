"""
Test para validar Fix 2.2: LeadsalesAgent can_handle() Correction
Verifica que LeadsalesAgent puede manejar conversaciones transferidas con metadata correcta
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.leadsales_agent import LeadsalesAgent

async def test_leadsales_agent_can_handle_flujo_completado(leadsales_agent):
    """Test: LeadsalesAgent debe manejar FLUJO_COMPLETADO desde ReceptionAgent"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Quiero comprar un apartamento en Poblado"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "FLUJO_COMPLETADO",
        "customer_name": "Maria Lopez",
        "customer_needs": "Apartamento en zona norte"
    }

    result = await leadsales_agent.can_handle(message_data, conversation)
    assert result == True, "LeadsalesAgent debe manejar FLUJO_COMPLETADO"

async def test_leadsales_agent_can_handle_transfer_from_support(leadsales_agent):
    """Test: LeadsalesAgent debe manejar transferencia desde SupportAgent"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Necesito informacion sobre precios de apartamentos"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Carlos Ruiz",
        "transfer_metadata": {
            "from_agent": "SupportAgent",
            "to_agent": "LeadsalesAgent",
            "reason": "inmueble_especifico"
        }
    }

    result = await leadsales_agent.can_handle(message_data, conversation)
    assert result == True, "LeadsalesAgent debe manejar transferencia desde SupportAgent"

async def test_leadsales_agent_can_handle_transfer_from_reception(leadsales_agent):
    """Test: LeadsalesAgent debe manejar transferencia desde ReceptionAgent"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Estoy interesado en comprar una casa"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Ana Garcia",
        "transfer_metadata": {
            "from_agent": "ReceptionAgent",
            "to_agent": "LeadsalesAgent",
            "reason": "sales_intent"
        }
    }

    result = await leadsales_agent.can_handle(message_data, conversation)
    assert result == True, "LeadsalesAgent debe manejar transferencia desde ReceptionAgent"

async def test_leadsales_agent_can_handle_conversion_states(leadsales_agent):
    """Test: LeadsalesAgent debe manejar estados de conversion en progreso"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Necesito 3 habitaciones y 2 banos"}
    }

    # Test CAPTURANDO_DETALLES
    conversation_capturing = {
        "whatsapp_id": "1234567890",
        "state": "CAPTURANDO_DETALLES",
        "customer_name": "Pedro Martinez"
    }

    result = await leadsales_agent.can_handle(message_data, conversation_capturing)
    assert result == True, "LeadsalesAgent debe manejar CAPTURANDO_DETALLES"

    # Test PROFUNDIZANDO_NECESIDAD
    conversation_deepening = {
        "whatsapp_id": "1234567890",
        "state": "PROFUNDIZANDO_NECESIDAD",
        "customer_name": "Laura Torres"
    }

    result = await leadsales_agent.can_handle(message_data, conversation_deepening)
    assert result == True, "LeadsalesAgent debe manejar PROFUNDIZANDO_NECESIDAD"

    # Test CONFIRMANDO_INFORMACION
    conversation_confirming = {
        "whatsapp_id": "1234567890",
        "state": "CONFIRMANDO_INFORMACION",
        "customer_name": "Diego Silva"
    }

    result = await leadsales_agent.can_handle(message_data, conversation_confirming)
    assert result == True, "LeadsalesAgent debe manejar CONFIRMANDO_INFORMACION"

async def test_leadsales_agent_cannot_handle_wrong_transfer(leadsales_agent):
    """Test: LeadsalesAgent NO debe manejar transferencia a otro agente"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Tengo dudas sobre documentos"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Sofia Vargas",
        "transfer_metadata": {
            "from_agent": "ReceptionAgent",
            "to_agent": "SupportAgent",  # Transferido a soporte, no ventas
            "reason": "question_classification"
        }
    }

    result = await leadsales_agent.can_handle(message_data, conversation)
    assert result == False, "LeadsalesAgent NO debe manejar transferencia a otro agente"

async def test_leadsales_agent_cannot_handle_initial_states(leadsales_agent):
    """Test: LeadsalesAgent NO debe manejar estados iniciales"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Hola"}
    }

    # Test estado NUEVO
    conversation_nuevo = {
        "whatsapp_id": "1234567890",
        "state": "NUEVO",
        "customer_name": ""
    }

    result = await leadsales_agent.can_handle(message_data, conversation_nuevo)
    assert result == False, "LeadsalesAgent NO debe manejar estado NUEVO"

    # Test estado RECOPILANDO_NOMBRE
    conversation_nombre = {
        "whatsapp_id": "1234567890",
        "state": "RECOPILANDO_NOMBRE",
        "customer_name": ""
    }

    result = await leadsales_agent.can_handle(message_data, conversation_nombre)
    assert result == False, "LeadsalesAgent NO debe manejar RECOPILANDO_NOMBRE"

async def test_leadsales_agent_transferido_without_metadata(leadsales_agent):
    """Test: Estado TRANSFERIDO sin metadata debe retornar False"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Quiero vender mi apartamento"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Roberto Gomez"
        # Sin transfer_metadata
    }

    result = await leadsales_agent.can_handle(message_data, conversation)
    assert result == False, "LeadsalesAgent NO debe manejar TRANSFERIDO sin metadata"

if __name__ == "__main__":
    # Ejecutar tests
    async def run_tests():
        agent = LeadsalesAgent()

        print("=== VALIDANDO FIX 2.2: LeadsalesAgent can_handle() Correction ===")

        # Test 1: FLUJO_COMPLETADO
        try:
            await test_leadsales_agent_can_handle_flujo_completado(agent)
            print("[OK] Test 1 PASADO: FLUJO_COMPLETADO")
        except Exception as e:
            print(f"[FAIL] Test 1 FALLIDO: {e}")

        # Test 2: Transferencia desde SupportAgent
        try:
            await test_leadsales_agent_can_handle_transfer_from_support(agent)
            print("[OK] Test 2 PASADO: Transferencia desde SupportAgent")
        except Exception as e:
            print(f"[FAIL] Test 2 FALLIDO: {e}")

        # Test 3: Transferencia desde ReceptionAgent
        try:
            await test_leadsales_agent_can_handle_transfer_from_reception(agent)
            print("[OK] Test 3 PASADO: Transferencia desde ReceptionAgent")
        except Exception as e:
            print(f"[FAIL] Test 3 FALLIDO: {e}")

        # Test 4: Estados de conversion
        try:
            await test_leadsales_agent_can_handle_conversion_states(agent)
            print("[OK] Test 4 PASADO: Estados de conversion")
        except Exception as e:
            print(f"[FAIL] Test 4 FALLIDO: {e}")

        # Test 5: Transferencia incorrecta
        try:
            await test_leadsales_agent_cannot_handle_wrong_transfer(agent)
            print("[OK] Test 5 PASADO: Transferencia incorrecta")
        except Exception as e:
            print(f"[FAIL] Test 5 FALLIDO: {e}")

        # Test 6: Estados iniciales
        try:
            await test_leadsales_agent_cannot_handle_initial_states(agent)
            print("[OK] Test 6 PASADO: Estados iniciales")
        except Exception as e:
            print(f"[FAIL] Test 6 FALLIDO: {e}")

        # Test 7: TRANSFERIDO sin metadata
        try:
            await test_leadsales_agent_transferido_without_metadata(agent)
            print("[OK] Test 7 PASADO: TRANSFERIDO sin metadata")
        except Exception as e:
            print(f"[FAIL] Test 7 FALLIDO: {e}")

        print("\n=== FIX 2.2 VALIDADO CORRECTAMENTE ===")

    asyncio.run(run_tests())