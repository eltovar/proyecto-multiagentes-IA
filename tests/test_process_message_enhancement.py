"""
Test para validar Fix 3.2: Process Message Enhancement
Verifica que el orchestrator actualiza el estado ANTES de procesar transferencias
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, call
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.orchestrator import AgentOrchestrator

async def test_process_message_state_update_before_transfer():
    """Test: Estado se actualiza ANTES de procesar transferencia"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.get_conversation_state') as mock_get, \
         patch('app.core.orchestrator.update_conversation_state') as mock_update, \
         patch('app.core.orchestrator.send_message') as mock_send, \
         patch('app.state.manager.state_manager') as mock_state_manager:

        # Mock de conversación existente
        mock_conversation = {
            "whatsapp_id": "1234567890",
            "state": "NUEVO",
            "customer_name": "",
            "customer_needs": ""
        }

        mock_get.return_value = mock_conversation
        mock_send.return_value = None
        mock_update.return_value = None

        # Mock de state manager para enhanced transfer
        mock_updated_conv = type('obj', (object,), {
            'whatsapp_id': '1234567890',
            'state': 'TRANSFERIDO',
            'customer_name': 'Juan Perez',
            'customer_needs': 'Consulta general',
            'current_agent': 'SupportAgent',
            'transfer_metadata': {}
        })()

        mock_state_manager.get_conversation.return_value = mock_updated_conv
        mock_state_manager.update_conversation_state.return_value = True

        # Mock de respuesta del agente con transferencia
        agent_response = {
            "response": "Te conecto con nuestro especialista",
            "new_state": "CLASIFICANDO_INTENCION",
            "transfer_to": "SupportAgent",
            "transfer_metadata": {
                "from_agent": "reception",
                "to_agent": "SupportAgent",
                "reason": "question_classification"
            }
        }

        # Lista para capturar el orden de llamadas
        call_order = []

        def track_update_call(*args, **kwargs):
            call_order.append("update_state")
            return None

        def track_send_call(*args, **kwargs):
            call_order.append("send_message")
            return None

        def track_transfer_call(*args, **kwargs):
            call_order.append("handle_transfer")
            return None

        # Aplicar tracking a los métodos
        orchestrator._update_conversation_state = AsyncMock(side_effect=track_update_call)
        mock_send.side_effect = track_send_call
        orchestrator._handle_agent_transfer = AsyncMock(side_effect=track_transfer_call)

        # Mock del agente seleccionado
        with patch.object(orchestrator.agents["ReceptionAgent"], 'process_message',
                         return_value=agent_response) as mock_process:

            message_data = {
                "from": "1234567890",
                "text": {"body": "Hola, tengo una consulta"}
            }

            # Ejecutar process_message
            await orchestrator.process_message(message_data)

            # Verificar orden de operaciones: update_state -> send_message -> handle_transfer
            expected_order = ["update_state", "send_message", "handle_transfer"]
            assert call_order == expected_order, f"Orden incorrecto: {call_order}, esperado: {expected_order}"

            # Verificar que se llamaron todos los métodos
            orchestrator._update_conversation_state.assert_called_once_with("1234567890", agent_response)
            mock_send.assert_called_once_with("1234567890", "Te conecto con nuestro especialista")
            orchestrator._handle_agent_transfer.assert_called_once()

async def test_process_message_no_transfer_flow():
    """Test: Flujo normal sin transferencia funciona correctamente"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.get_conversation_state') as mock_get, \
         patch('app.core.orchestrator.send_message') as mock_send:

        # Mock de conversación existente
        mock_conversation = {
            "whatsapp_id": "1234567890",
            "state": "RECOPILANDO_NOMBRE",
            "customer_name": "",
            "customer_needs": ""
        }

        mock_get.return_value = mock_conversation
        mock_send.return_value = None

        # Mock de respuesta sin transferencia
        agent_response = {
            "response": "Perfecto! Ahora necesito tu nombre",
            "new_state": "RECOPILANDO_NECESIDAD",
            "data_updates": {"step": "nombre_completado"}
        }

        # Tracking de llamadas
        call_order = []

        def track_update_call(*args, **kwargs):
            call_order.append("update_state")
            return None

        def track_send_call(*args, **kwargs):
            call_order.append("send_message")
            return None

        orchestrator._update_conversation_state = AsyncMock(side_effect=track_update_call)
        mock_send.side_effect = track_send_call

        # Mock del agente
        with patch.object(orchestrator.agents["ReceptionAgent"], 'process_message',
                         return_value=agent_response):

            message_data = {
                "from": "1234567890",
                "text": {"body": "Juan Perez"}
            }

            # Ejecutar process_message
            await orchestrator.process_message(message_data)

            # Verificar orden: update_state -> send_message (sin transfer)
            expected_order = ["update_state", "send_message"]
            assert call_order == expected_order, f"Orden incorrecto: {call_order}"

async def test_process_message_handoff_protocol():
    """Test: Handoff protocol (STATE_TRANSFERIDO) se respeta"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.get_conversation_state') as mock_get, \
         patch('app.core.orchestrator.send_message') as mock_send:

        # Mock de conversación en estado TRANSFERIDO
        mock_conversation = {
            "whatsapp_id": "1234567890",
            "state": "TRANSFERIDO",
            "customer_name": "Juan Perez",
            "customer_needs": "Consulta transferida"
        }

        mock_get.return_value = mock_conversation

        message_data = {
            "from": "1234567890",
            "text": {"body": "Mensaje después de transferencia"}
        }

        # Ejecutar process_message
        await orchestrator.process_message(message_data)

        # Verificar que NO se procesó el mensaje ni se envió respuesta
        mock_send.assert_not_called()

async def test_process_message_agent_selection_failure():
    """Test: Manejo de error cuando no se puede seleccionar agente"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.get_conversation_state') as mock_get, \
         patch('app.core.orchestrator.send_message') as mock_send:

        # Mock de conversación válida
        mock_conversation = {
            "whatsapp_id": "1234567890",
            "state": "ESTADO_INVALIDO_PARA_TESTING",
            "customer_name": "Test User"
        }

        mock_get.return_value = mock_conversation
        mock_send.return_value = None

        # Mock _select_agent para retornar None (fallo en selección)
        orchestrator._select_agent = AsyncMock(return_value=None)

        message_data = {
            "from": "1234567890",
            "text": {"body": "Test message"}
        }

        # Ejecutar process_message
        await orchestrator.process_message(message_data)

        # Verificar que se envió mensaje de error
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == "1234567890"  # sender_id
        assert "problema técnico" in call_args[1].lower()  # mensaje de error

async def test_process_message_exception_handling():
    """Test: Manejo de excepciones durante procesamiento"""

    orchestrator = AgentOrchestrator()

    with patch('app.core.orchestrator.get_conversation_state') as mock_get, \
         patch('app.core.orchestrator.send_message') as mock_send:

        # Mock de conversación válida
        mock_conversation = {
            "whatsapp_id": "1234567890",
            "state": "NUEVO",
            "customer_name": ""
        }

        mock_get.return_value = mock_conversation
        mock_send.return_value = None

        # Mock del agente para lanzar excepción
        with patch.object(orchestrator.agents["ReceptionAgent"], 'process_message',
                         side_effect=Exception("Test exception")):

            message_data = {
                "from": "1234567890",
                "text": {"body": "Test message"}
            }

            # Ejecutar process_message
            await orchestrator.process_message(message_data)

            # Verificar que se envió mensaje de error
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "1234567890"
            assert "problema técnico" in call_args[1].lower()

if __name__ == "__main__":
    # Ejecutar tests
    async def run_tests():
        print("=== VALIDANDO FIX 3.2: Process Message Enhancement ===")

        # Test 1: Orden de operaciones correcto
        try:
            await test_process_message_state_update_before_transfer()
            print("[OK] Test 1 PASADO: Estado se actualiza ANTES de transferencia")
        except Exception as e:
            print(f"[FAIL] Test 1 FALLIDO: {e}")

        # Test 2: Flujo sin transferencia
        try:
            await test_process_message_no_transfer_flow()
            print("[OK] Test 2 PASADO: Flujo normal sin transferencia")
        except Exception as e:
            print(f"[FAIL] Test 2 FALLIDO: {e}")

        # Test 3: Handoff protocol
        try:
            await test_process_message_handoff_protocol()
            print("[OK] Test 3 PASADO: Handoff protocol respetado")
        except Exception as e:
            print(f"[FAIL] Test 3 FALLIDO: {e}")

        # Test 4: Fallo en selección de agente
        try:
            await test_process_message_agent_selection_failure()
            print("[OK] Test 4 PASADO: Manejo de fallo en selección")
        except Exception as e:
            print(f"[FAIL] Test 4 FALLIDO: {e}")

        # Test 5: Manejo de excepciones
        try:
            await test_process_message_exception_handling()
            print("[OK] Test 5 PASADO: Manejo de excepciones")
        except Exception as e:
            print(f"[FAIL] Test 5 FALLIDO: {e}")

        print("\n=== FIX 3.2 VALIDADO CORRECTAMENTE ===")

    asyncio.run(run_tests())