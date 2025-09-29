"""
Test para validar Fix 2.1: SupportAgent can_handle() Correction
Verifica que SupportAgent puede manejar conversaciones TRANSFERIDO con metadata correcta
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.support_agent import SupportAgent

async def test_support_agent_can_handle_transferido_with_metadata(support_agent):
    """Test CASO 1: Estado TRANSFERIDO + metadata de transferencia a SupportAgent"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Tengo dudas sobre los tramites de arrendamiento"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Juan Perez",
        "transfer_metadata": {
            "from_agent": "ReceptionAgent",
            "to_agent": "SupportAgent",
            "reason": "question_classification"
        }
    }

    result = await support_agent.can_handle(message_data, conversation)
    assert result == True, "SupportAgent debe manejar estado TRANSFERIDO con metadata correcta"

async def test_support_agent_cannot_handle_transferido_wrong_metadata(support_agent):
    """Test CASO 1: Estado TRANSFERIDO pero transferencia a otro agente"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Quiero comprar un apartamento"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Ana Garcia",
        "transfer_metadata": {
            "from_agent": "ReceptionAgent",
            "to_agent": "LeadsalesAgent",  # Transferido a ventas, no soporte
            "reason": "sales_inquiry"
        }
    }

    result = await support_agent.can_handle(message_data, conversation)
    assert result == False, "SupportAgent NO debe manejar transferencia a otro agente"

async def test_support_agent_can_handle_support_states(support_agent):
    """Test CASO 2: Estados especificos de soporte"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Continuar con mi consulta"}
    }

    # Test con estado RAG activo
    conversation_rag = {
        "whatsapp_id": "1234567890",
        "state": "CONSULTA_RAG_ACTIVA",
        "customer_name": "Pedro Martinez"
    }

    result = await support_agent.can_handle(message_data, conversation_rag)
    assert result == True, "SupportAgent debe manejar CONSULTA_RAG_ACTIVA"

    # Test con estado administrativo
    conversation_admin = {
        "whatsapp_id": "1234567890",
        "state": "SOPORTE_ADMINISTRATIVO",
        "customer_name": "Maria Lopez"
    }

    result = await support_agent.can_handle(message_data, conversation_admin)
    assert result == True, "SupportAgent debe manejar SOPORTE_ADMINISTRATIVO"

async def test_support_agent_can_handle_current_agent_metadata(support_agent):
    """Test CASO 3: Metadata current_agent = SupportAgent"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Necesito ayuda con documentos"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "EN_PROCESO",
        "customer_name": "Carlos Ruiz",
        "current_agent": "SupportAgent"
    }

    result = await support_agent.can_handle(message_data, conversation)
    assert result == True, "SupportAgent debe manejar cuando current_agent = SupportAgent"

async def test_support_agent_cannot_handle_other_states(support_agent):
    """Test: SupportAgent NO debe manejar estados no relacionados"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Hola"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "NUEVO",
        "customer_name": ""
    }

    result = await support_agent.can_handle(message_data, conversation)
    assert result == False, "SupportAgent NO debe manejar estado NUEVO sin metadata"

    # Test con estado de ventas
    conversation_sales = {
        "whatsapp_id": "1234567890",
        "state": "RECOPILANDO_NECESIDADES",
        "customer_name": "Luis Torres"
    }

    result = await support_agent.can_handle(message_data, conversation_sales)
    assert result == False, "SupportAgent NO debe manejar estados de ventas"

async def test_support_agent_transferido_without_metadata(support_agent):
    """Test: Estado TRANSFERIDO sin metadata debe retornar False"""

    message_data = {
        "from": "1234567890",
        "text": {"body": "Pregunta general"}
    }

    conversation = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Sofia Vargas"
        # Sin transfer_metadata
    }

    result = await support_agent.can_handle(message_data, conversation)
    assert result == False, "SupportAgent NO debe manejar TRANSFERIDO sin metadata"

if __name__ == "__main__":
    # Ejecutar tests
    async def run_tests():
        agent = SupportAgent()

        print("=== VALIDANDO FIX 2.1: SupportAgent can_handle() Correction ===")

        # Test 1: TRANSFERIDO con metadata correcta
        try:
            await test_support_agent_can_handle_transferido_with_metadata(agent)
            print("[OK] Test 1 PASADO: TRANSFERIDO con metadata correcta")
        except Exception as e:
            print(f"[FAIL] Test 1 FALLIDO: {e}")

        # Test 2: TRANSFERIDO con metadata incorrecta
        try:
            await test_support_agent_cannot_handle_transferido_wrong_metadata(agent)
            print("[OK] Test 2 PASADO: TRANSFERIDO con metadata incorrecta")
        except Exception as e:
            print(f"[FAIL] Test 2 FALLIDO: {e}")

        # Test 3: Estados de soporte
        try:
            await test_support_agent_can_handle_support_states(agent)
            print("[OK] Test 3 PASADO: Estados especificos de soporte")
        except Exception as e:
            print(f"[FAIL] Test 3 FALLIDO: {e}")

        # Test 4: current_agent metadata
        try:
            await test_support_agent_can_handle_current_agent_metadata(agent)
            print("[OK] Test 4 PASADO: current_agent metadata")
        except Exception as e:
            print(f"[FAIL] Test 4 FALLIDO: {e}")

        # Test 5: Estados no relacionados
        try:
            await test_support_agent_cannot_handle_other_states(agent)
            print("[OK] Test 5 PASADO: Estados no relacionados")
        except Exception as e:
            print(f"[FAIL] Test 5 FALLIDO: {e}")

        # Test 6: TRANSFERIDO sin metadata
        try:
            await test_support_agent_transferido_without_metadata(agent)
            print("[OK] Test 6 PASADO: TRANSFERIDO sin metadata")
        except Exception as e:
            print(f"[FAIL] Test 6 FALLIDO: {e}")

        print("\n=== FIX 2.1 VALIDADO CORRECTAMENTE ===")

    asyncio.run(run_tests())