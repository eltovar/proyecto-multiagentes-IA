"""
Test para validar Fix 3.1: Enhanced Agent Transfer
Verifica que el orchestrator maneja correctamente las transferencias con metadata
"""

import asyncio
import sys
import os
import time
from unittest.mock import AsyncMock, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.orchestrator import AgentOrchestrator

async def test_enhanced_agent_transfer_with_metadata():
    """Test: Transferencia con metadata se persiste correctamente"""

    orchestrator = AgentOrchestrator()

    # Mock del state manager y whatsapp service
    with patch('app.core.orchestrator.send_message') as mock_send, \
         patch('app.state.manager.state_manager') as mock_state_manager:

        # Configurar mock de conversación actualizada
        mock_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Juan Perez',
            'customer_needs': 'Apartamento en Poblado',
            'current_agent': 'SupportAgent',
            'transfer_metadata': {
                'from_agent': 'ReceptionAgent',
                'to_agent': 'SupportAgent',
                'reason': 'question_classification'
            }
        })()

        mock_state_manager.get_conversation.return_value = mock_conversation
        mock_state_manager.update_conversation_state.return_value = True
        mock_send.return_value = None

        # Mock del agent process_message
        mock_agent_response = {
            "response": "Te ayudo con tu consulta sobre apartamentos",
            "new_state": "CONSULTA_RAG_ACTIVA"
        }

        with patch.object(orchestrator.agents["SupportAgent"], 'process_message',
                         return_value=mock_agent_response) as mock_process:

            message_data = {
                "from": "1234567890",
                "text": {"body": "Tengo dudas sobre contratos"}
            }

            conversation = {
                "whatsapp_id": "1234567890",
                "state": "NUEVO",
                "customer_name": "Juan Perez"
            }

            transfer_metadata = {
                "from_agent": "ReceptionAgent",
                "to_agent": "SupportAgent",
                "reason": "question_classification"
            }

            # Ejecutar transferencia
            await orchestrator._handle_agent_transfer(
                message_data, conversation, "SupportAgent", transfer_metadata
            )

            # Verificar que se persistió la metadata ANTES de procesar
            mock_state_manager.update_conversation_state.assert_called_once()
            call_args = mock_state_manager.update_conversation_state.call_args

            assert call_args[0][0] == "1234567890"  # sender_id
            assert call_args[1]["current_agent"] == "SupportAgent"
            assert call_args[1]["transfer_metadata"] == transfer_metadata
            assert "last_transfer_time" in call_args[1]

            # Verificar que se llamó al agente con conversación actualizada
            mock_process.assert_called_once()
            process_call_args = mock_process.call_args
            conversation_dict = process_call_args[0][1]

            assert conversation_dict["current_agent"] == "SupportAgent"
            assert conversation_dict["transfer_metadata"]["to_agent"] == "SupportAgent"

            # Verificar que se envió la respuesta
            mock_send.assert_called_once_with("1234567890", "Te ayudo con tu consulta sobre apartamentos")

async def test_enhanced_transfer_sequence_reception_to_support():
    """Test: Secuencia completa ReceptionAgent -> SupportAgent"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.send_message') as mock_send, \
         patch('app.state.manager.state_manager') as mock_state_manager:

        # Configurar conversación inicial
        initial_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'CLASIFICANDO_INTENCION',
            'customer_name': 'Maria Lopez',
            'customer_needs': '',
            'current_agent': 'ReceptionAgent'
        })()

        # Conversación después de transferencia
        transferred_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Maria Lopez',
            'customer_needs': 'Consulta general',
            'current_agent': 'SupportAgent',
            'transfer_metadata': {
                'from_agent': 'ReceptionAgent',
                'to_agent': 'SupportAgent',
                'reason': 'question_classification'
            }
        })()

        mock_state_manager.get_conversation.return_value = transferred_conversation
        mock_state_manager.update_conversation_state.return_value = True
        mock_send.return_value = None

        # Mock de respuesta del SupportAgent
        support_response = {
            "response": "Hola Maria! Estoy aqui para ayudarte con tu consulta",
            "new_state": "SOPORTE_ACTIVO"
        }

        with patch.object(orchestrator.agents["SupportAgent"], 'process_message',
                         return_value=support_response) as mock_support:

            message_data = {
                "from": "1234567890",
                "text": {"body": "Tengo preguntas sobre arrendamiento"}
            }

            conversation = {
                "whatsapp_id": "1234567890",
                "state": "CLASIFICANDO_INTENCION",
                "customer_name": "Maria Lopez"
            }

            transfer_metadata = {
                "from_agent": "ReceptionAgent",
                "to_agent": "SupportAgent",
                "reason": "question_classification"
            }

            # Ejecutar transferencia
            await orchestrator._handle_agent_transfer(
                message_data, conversation, "SupportAgent", transfer_metadata
            )

            # Verificar persistencia de metadata
            mock_state_manager.update_conversation_state.assert_called_once()

            # Verificar que SupportAgent recibió conversación con metadata correcta
            mock_support.assert_called_once()
            conv_dict = mock_support.call_args[0][1]
            assert conv_dict["transfer_metadata"]["to_agent"] == "SupportAgent"
            assert conv_dict["current_agent"] == "SupportAgent"

async def test_enhanced_transfer_sequence_support_to_leadsales():
    """Test: Secuencia completa SupportAgent -> LeadsalesAgent"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.send_message') as mock_send, \
         patch('app.state.manager.state_manager') as mock_state_manager:

        # Conversación después de transferencia a ventas
        transferred_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Carlos Ruiz',
            'customer_needs': 'Informacion apartamento especifico',
            'current_agent': 'LeadsalesAgent',
            'transfer_metadata': {
                'from_agent': 'SupportAgent',
                'to_agent': 'LeadsalesAgent',
                'reason': 'inmueble_especifico'
            }
        })()

        mock_state_manager.get_conversation.return_value = transferred_conversation
        mock_state_manager.update_conversation_state.return_value = True
        mock_send.return_value = None

        # Mock de respuesta del LeadsalesAgent
        leadsales_response = {
            "response": "Perfecto Carlos! Te ayudo con la informacion del apartamento",
            "new_state": "CAPTURANDO_DETALLES"
        }

        with patch.object(orchestrator.agents["LeadsalesAgent"], 'process_message',
                         return_value=leadsales_response) as mock_leadsales:

            message_data = {
                "from": "1234567890",
                "text": {"body": "Quiero saber precios de apartamentos en Poblado"}
            }

            conversation = {
                "whatsapp_id": "1234567890",
                "state": "SOPORTE_ACTIVO",
                "customer_name": "Carlos Ruiz"
            }

            transfer_metadata = {
                "from_agent": "SupportAgent",
                "to_agent": "LeadsalesAgent",
                "reason": "inmueble_especifico"
            }

            # Ejecutar transferencia
            await orchestrator._handle_agent_transfer(
                message_data, conversation, "LeadsalesAgent", transfer_metadata
            )

            # Verificar que LeadsalesAgent recibió metadata correcta
            mock_leadsales.assert_called_once()
            conv_dict = mock_leadsales.call_args[0][1]
            assert conv_dict["transfer_metadata"]["to_agent"] == "LeadsalesAgent"
            assert conv_dict["transfer_metadata"]["from_agent"] == "SupportAgent"
            assert conv_dict["current_agent"] == "LeadsalesAgent"

async def test_enhanced_transfer_nonexistent_agent():
    """Test: Transferencia a agente inexistente se maneja correctamente"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.send_message') as mock_send:

        message_data = {
            "from": "1234567890",
            "text": {"body": "Test message"}
        }

        conversation = {
            "whatsapp_id": "1234567890",
            "state": "NUEVO",
            "customer_name": "Test User"
        }

        # Intentar transferir a agente que no existe
        await orchestrator._handle_agent_transfer(
            message_data, conversation, "NonExistentAgent", {}
        )

        # No debe enviar mensaje ni hacer actualizaciones
        mock_send.assert_not_called()

async def test_enhanced_transfer_timing_metadata():
    """Test: Metadata de timing se agrega correctamente"""

    orchestrator = AgentOrchestrator()

    with patch('app.state.manager.state_manager') as mock_state_manager, \
         patch('app.core.orchestrator.send_message') as mock_send:

        # Mock básico de conversación
        mock_conversation = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Test User',
            'customer_needs': '',
            'current_agent': 'SupportAgent',
            'transfer_metadata': {}
        })()

        mock_state_manager.get_conversation.return_value = mock_conversation
        mock_state_manager.update_conversation_state.return_value = True
        mock_send.return_value = None

        with patch.object(orchestrator.agents["SupportAgent"], 'process_message',
                         return_value={"response": "test", "new_state": "TEST"}):

            # Capturar tiempo antes de transferencia
            start_time = time.time()

            await orchestrator._handle_agent_transfer(
                {"from": "1234567890", "text": {"body": "test"}},
                {"whatsapp_id": "1234567890", "state": "NUEVO"},
                "SupportAgent",
                {"test": "metadata"}
            )

            end_time = time.time()

            # Verificar que se agregó timestamp
            call_args = mock_state_manager.update_conversation_state.call_args
            transfer_time = call_args[1]["last_transfer_time"]

            assert start_time <= transfer_time <= end_time

if __name__ == "__main__":
    # Ejecutar tests
    async def run_tests():
        print("=== VALIDANDO FIX 3.1: Enhanced Agent Transfer ===")

        # Test 1: Transferencia con metadata
        try:
            await test_enhanced_agent_transfer_with_metadata()
            print("[OK] Test 1 PASADO: Transferencia con metadata")
        except Exception as e:
            print(f"[FAIL] Test 1 FALLIDO: {e}")

        # Test 2: Secuencia Reception -> Support
        try:
            await test_enhanced_transfer_sequence_reception_to_support()
            print("[OK] Test 2 PASADO: Secuencia Reception -> Support")
        except Exception as e:
            print(f"[FAIL] Test 2 FALLIDO: {e}")

        # Test 3: Secuencia Support -> Leadsales
        try:
            await test_enhanced_transfer_sequence_support_to_leadsales()
            print("[OK] Test 3 PASADO: Secuencia Support -> Leadsales")
        except Exception as e:
            print(f"[FAIL] Test 3 FALLIDO: {e}")

        # Test 4: Agente inexistente
        try:
            await test_enhanced_transfer_nonexistent_agent()
            print("[OK] Test 4 PASADO: Agente inexistente")
        except Exception as e:
            print(f"[FAIL] Test 4 FALLIDO: {e}")

        # Test 5: Metadata de timing
        try:
            await test_enhanced_transfer_timing_metadata()
            print("[OK] Test 5 PASADO: Metadata de timing")
        except Exception as e:
            print(f"[FAIL] Test 5 FALLIDO: {e}")

        print("\n=== FIX 3.1 VALIDADO CORRECTAMENTE ===")

    asyncio.run(run_tests())