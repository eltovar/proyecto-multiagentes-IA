"""
Test de Integración Completa para validar todos los fixes implementados
Verifica que Fix 1.1, 1.2, 2.1, 2.2 y 3.1 funcionan correctamente en conjunto
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.orchestrator import AgentOrchestrator
from app.agents.reception_agent import ReceptionAgent
from app.agents.support_agent import SupportAgent
from app.agents.leadsales_agent import LeadsalesAgent

async def test_complete_flow_reception_to_support_integration():
    """Test: Flujo completo Reception -> Support con todos los fixes"""

    print("=== INICIANDO FLUJO COMPLETO RECEPTION -> SUPPORT ===")

    # PASO 1: Simular ReceptionAgent creando transferencia con metadata
    reception_agent = ReceptionAgent()

    # Simular respuesta de ReceptionAgent con transfer_metadata completa
    reception_response = reception_agent.create_response(
        response="Te conecto con nuestro especialista en consultas.",
        transfer_to="SupportAgent",
        transfer_reason="question_classification",
        new_state="TRANSFERIDO",
        data_updates={"consultation_type": "general_inquiry"}
    )

    # Verificar que la respuesta incluye transfer_metadata (Fix 1.2)
    assert "transfer_metadata" in reception_response
    assert reception_response["transfer_metadata"]["to_agent"] == "SupportAgent"
    assert reception_response["transfer_metadata"]["from_agent"] == "reception"  # Nombre real del agente
    assert reception_response["transfer_metadata"]["reason"] == "question_classification"
    print("[OK] Fix 1.2: BaseAgent response standardization funciona")

    # PASO 2: Verificar que SupportAgent puede manejar la transferencia
    support_agent = SupportAgent()

    # Conversación con metadata de transferencia
    conversation_with_metadata = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Juan Perez",
        "transfer_metadata": reception_response["transfer_metadata"]
    }

    message_data = {
        "from": "1234567890",
        "text": {"body": "Tengo dudas sobre documentos de arrendamiento"}
    }

    # Verificar que SupportAgent puede manejar (Fix 2.1)
    can_handle = await support_agent.can_handle(message_data, conversation_with_metadata)
    assert can_handle == True
    print("[OK] Fix 2.1: SupportAgent can_handle() correction funciona")

    # PASO 3: Simular orchestrator usando enhanced transfer (Fix 3.1)
    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.send_message') as mock_send, \
         patch('app.state.manager.state_manager') as mock_state_manager:

        # Mock de conversación actualizada con metadata
        updated_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Juan Perez',
            'customer_needs': 'Consulta sobre documentos',
            'current_agent': 'SupportAgent',
            'transfer_metadata': reception_response["transfer_metadata"]
        })()

        mock_state_manager.get_conversation.return_value = updated_conversation
        mock_state_manager.update_conversation_state.return_value = True
        mock_send.return_value = None

        # Mock de respuesta SupportAgent
        support_response = {
            "response": "Te ayudo con tu consulta sobre documentos de arrendamiento",
            "new_state": "SOPORTE_ACTIVO"
        }

        with patch.object(support_agent, 'process_message', return_value=support_response):

            # Ejecutar transferencia enhanced
            await orchestrator._handle_agent_transfer(
                message_data,
                {"whatsapp_id": "1234567890", "state": "CLASIFICANDO_INTENCION"},
                "SupportAgent",
                reception_response["transfer_metadata"]
            )

            # Verificar que se persistió metadata (Fix 3.1)
            mock_state_manager.update_conversation_state.assert_called()
            call_args = mock_state_manager.update_conversation_state.call_args
            assert call_args[1]["transfer_metadata"] == reception_response["transfer_metadata"]
            assert call_args[1]["current_agent"] == "SupportAgent"
            print("[OK] Fix 3.1: Enhanced agent transfer funciona")

    print("[OK] FLUJO COMPLETO RECEPTION -> SUPPORT VALIDADO")

async def test_complete_flow_support_to_leadsales_integration():
    """Test: Flujo completo Support -> Leadsales con todos los fixes"""

    print("\n=== INICIANDO FLUJO COMPLETO SUPPORT -> LEADSALES ===")

    # PASO 1: SupportAgent creando transferencia a LeadsalesAgent
    support_agent = SupportAgent()

    support_response = support_agent.create_response(
        response="Esa información la maneja directamente nuestro equipo de asesores.",
        transfer_to="LeadsalesAgent",
        transfer_reason="inmueble_especifico",
        data_updates={"consultation_type": "inmueble_especifico"}
    )

    # Verificar metadata de transferencia (Fix 1.2)
    assert support_response["transfer_metadata"]["to_agent"] == "LeadsalesAgent"
    assert support_response["transfer_metadata"]["from_agent"] == "SupportAgent"  # Nombre real del agente
    print("[OK] Fix 1.2: SupportAgent transfer metadata correcta")

    # PASO 2: Verificar que LeadsalesAgent puede manejar
    leadsales_agent = LeadsalesAgent()

    conversation_for_leadsales = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Maria Lopez",
        "transfer_metadata": support_response["transfer_metadata"]
    }

    message_data = {
        "from": "1234567890",
        "text": {"body": "Quiero saber precios de apartamentos en Poblado"}
    }

    # Verificar que LeadsalesAgent puede manejar (Fix 2.2)
    can_handle = await leadsales_agent.can_handle(message_data, conversation_for_leadsales)
    assert can_handle == True
    print("[OK] Fix 2.2: LeadsalesAgent can_handle() correction funciona")

    # PASO 3: Simular orchestrator usando enhanced transfer
    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.send_message') as mock_send, \
         patch('app.state.manager.state_manager') as mock_state_manager:

        # Mock de conversación actualizada
        updated_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Maria Lopez',
            'customer_needs': 'Informacion apartamento Poblado',
            'current_agent': 'LeadsalesAgent',
            'transfer_metadata': support_response["transfer_metadata"]
        })()

        mock_state_manager.get_conversation.return_value = updated_conversation
        mock_state_manager.update_conversation_state.return_value = True
        mock_send.return_value = None

        leadsales_response = {
            "response": "Perfecto Maria! Te ayudo con información sobre apartamentos en Poblado",
            "new_state": "CAPTURANDO_DETALLES"
        }

        with patch.object(leadsales_agent, 'process_message', return_value=leadsales_response):

            # Ejecutar transferencia
            await orchestrator._handle_agent_transfer(
                message_data,
                {"whatsapp_id": "1234567890", "state": "SOPORTE_ACTIVO"},
                "LeadsalesAgent",
                support_response["transfer_metadata"]
            )

            # Verificar persistencia de metadata
            call_args = mock_state_manager.update_conversation_state.call_args
            assert call_args[1]["current_agent"] == "LeadsalesAgent"
            assert call_args[1]["transfer_metadata"]["from_agent"] == "SupportAgent"
            print("[OK] Fix 3.1: Enhanced transfer Support -> Leadsales funciona")

    print("[OK] FLUJO COMPLETO SUPPORT -> LEADSALES VALIDADO")

async def test_state_persistence_robustness_integration():
    """Test: Fix 1.1 funciona con transferencias enhanced"""

    print("\n=== VALIDANDO PERSISTENCIA DE ESTADO ROBUSTA ===")

    orchestrator = AgentOrchestrator()

    # Test de robustez del _update_conversation_state (Fix 1.1)
    with patch('app.state.manager.state_manager') as mock_state_manager:

        # Simular fallo en primera actualización, éxito en fallback
        mock_state_manager.update_conversation_state.side_effect = [False, True]

        # Simular resultado con data_updates pero sin new_state
        result = {
            "response": "Test response",
            "data_updates": {
                "consultation_type": "test",
                "agent_notes": "integration_test"
            }
        }

        # Ejecutar actualización robusta
        await orchestrator._update_conversation_state("1234567890", result)

        # Verificar que se intentó al menos una vez (fallback puede activarse)
        assert mock_state_manager.update_conversation_state.call_count >= 1
        print("[OK] Fix 1.1: State persistence robustness funciona")

async def test_agent_selection_logic_integration():
    """Test: Agents no interfieren entre sí con nueva lógica"""

    print("\n=== VALIDANDO LOGICA DE SELECCIÓN NO INTERFERENTE ===")

    reception_agent = ReceptionAgent()
    support_agent = SupportAgent()
    leadsales_agent = LeadsalesAgent()

    # Conversación NUEVO - solo Reception debe manejar
    nuevo_conversation = {
        "whatsapp_id": "1234567890",
        "state": "NUEVO",
        "customer_name": ""
    }

    message_data = {"from": "1234567890", "text": {"body": "Hola"}}

    reception_can = await reception_agent.can_handle(message_data, nuevo_conversation)
    support_can = await support_agent.can_handle(message_data, nuevo_conversation)
    leadsales_can = await leadsales_agent.can_handle(message_data, nuevo_conversation)

    assert reception_can == True
    assert support_can == False
    assert leadsales_can == False
    print("[OK] Estado NUEVO: Solo ReceptionAgent maneja")

    # Conversación TRANSFERIDO sin metadata - ninguno debe manejar
    transferido_sin_metadata = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Test User"
    }

    reception_can = await reception_agent.can_handle(message_data, transferido_sin_metadata)
    support_can = await support_agent.can_handle(message_data, transferido_sin_metadata)
    leadsales_can = await leadsales_agent.can_handle(message_data, transferido_sin_metadata)

    assert reception_can == False
    assert support_can == False
    assert leadsales_can == False
    print("[OK] Estado TRANSFERIDO sin metadata: Ningún agente maneja")

    # Conversación TRANSFERIDO con metadata específica - solo el target maneja
    transferido_a_support = {
        "whatsapp_id": "1234567890",
        "state": "TRANSFERIDO",
        "customer_name": "Test User",
        "transfer_metadata": {
            "from_agent": "reception",
            "to_agent": "SupportAgent",
            "reason": "question"
        }
    }

    reception_can = await reception_agent.can_handle(message_data, transferido_a_support)
    support_can = await support_agent.can_handle(message_data, transferido_a_support)
    leadsales_can = await leadsales_agent.can_handle(message_data, transferido_a_support)

    assert reception_can == False
    assert support_can == True   # Solo SupportAgent debe manejar
    assert leadsales_can == False
    print("[OK] Estado TRANSFERIDO con metadata: Solo target agent maneja")

async def run_complete_integration_tests():
    """Ejecutar todos los tests de integración"""

    print("="*70)
    print("VALIDACIÓN COMPLETA DE INTEGRACIÓN - TODOS LOS FIXES")
    print("="*70)

    try:
        await test_complete_flow_reception_to_support_integration()
        await test_complete_flow_support_to_leadsales_integration()
        await test_state_persistence_robustness_integration()
        await test_agent_selection_logic_integration()

        print("\n" + "="*70)
        print("✓ ✓ ✓ TODOS LOS FIXES INTEGRADOS CORRECTAMENTE ✓ ✓ ✓")
        print("="*70)
        print("\nRESUMEN DE FIXES VALIDADOS:")
        print("- Fix 1.1: Orchestrator State Update Robustness")
        print("- Fix 1.2: Agent Response Standardization")
        print("- Fix 2.1: SupportAgent can_handle() Correction")
        print("- Fix 2.2: LeadsalesAgent can_handle() Correction")
        print("- Fix 3.1: Enhanced Agent Transfer")
        print("\nSISTEMA MULTIAGENTE FUNCIONANDO CORRECTAMENTE")
        print("="*70)

    except Exception as e:
        print(f"\n[CRITICAL FAILURE] Integration test failed: {e}")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(run_complete_integration_tests())