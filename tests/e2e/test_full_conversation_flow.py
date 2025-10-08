"""
tests/e2e/test_full_conversation_flow.py
=========================================
Test end-to-end de flujos de conversación completos con FactoryOrchestrator.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.factory_orchestrator import FactoryOrchestrator
from app.state.manager import state_manager


@pytest.fixture
def cleanup_conversation_user(request):
    """Fixture de usuario de conversación - genera ID único por test"""
    import uuid
    # Generar ID único para cada test para evitar colisiones
    test_user = f"e2e_user_{uuid.uuid4().hex[:8]}"
    yield test_user


class TestFullConversationFlow:
    """Test E2E de flujos completos de conversación"""

    @pytest.mark.asyncio
    async def test_complete_inmuebles_flow(self, cleanup_conversation_user):
        """
        Test de flujo completo de consulta de inmuebles.

        Escenario:
        1. Saludo inicial
        2. Consulta sobre departamento
        3. Preguntas específicas (precio, ubicación, características)
        4. Cierre de conversación
        """
        user_id = cleanup_conversation_user
        orchestrator = FactoryOrchestrator()

        with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            # Secuencia de mensajes
            messages = [
                {'from': user_id, 'text': {'body': 'Hola, buenos días' }, 'timestamp': 1234567890},
                {'from': user_id, 'text': {'body': 'Quiero información sobre departamentos' }, 'timestamp': 1234567891},
                {'from': user_id, 'text': {'body': '¿Cuánto cuesta el departamento en Miraflores?' }, 'timestamp': 1234567892},
                {'from': user_id, 'text': {'body': '¿Tiene estacionamiento?' }, 'timestamp': 1234567893},
                {'from': user_id, 'text': {'body': 'Gracias, me interesa' }, 'timestamp': 1234567894}
            ]

            # Procesar todos los mensajes
            for message in messages:
                await orchestrator.process_message(message)

            # Verificar que todos los mensajes fueron procesados
            assert mock_send.call_count >= len(messages), \
                f"Debe haber procesado todos los {len(messages)} mensajes"

            # Verificar que hay estado final
            final_conv = state_manager.get_conversation(user_id)
            assert final_conv is not None, "Debe existir estado de conversación al final"

    @pytest.mark.asyncio
    async def test_complete_general_inquiry_flow(self, cleanup_conversation_user):
        """
        Test de flujo completo de consulta general.

        Escenario:
        1. Saludo
        2. Pregunta sobre horarios
        3. Pregunta sobre servicios
        4. Despedida
        """
        user_id = cleanup_conversation_user
        orchestrator = FactoryOrchestrator()

        with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            messages = [
                {'from': user_id, 'text': {'body': 'Hola' }, 'timestamp': 1234567890},
                {'from': user_id, 'text': {'body': '¿Cuál es su horario de atención?' }, 'timestamp': 1234567891},
                {'from': user_id, 'text': {'body': '¿Qué servicios ofrecen?' }, 'timestamp': 1234567892},
                {'from': user_id, 'text': {'body': 'Gracias, hasta luego' }, 'timestamp': 1234567893}
            ]

            for message in messages:
                await orchestrator.process_message(message)

            # Nota: El mensaje "¿Qué servicios ofrecen?" puede activar transferencia a departamento
            # lo que causa que mensajes posteriores sean ignorados (comportamiento correcto)
            # Por eso verificamos >= 3 en lugar de >= 4
            assert mock_send.call_count >= 3, \
                f"Debe haber procesado al menos 3 mensajes (procesó {mock_send.call_count})"

            final_state = state_manager.get_conversation(user_id)
            assert final_state is not None, "Debe existir estado final"

    @pytest.mark.asyncio
    async def test_conversation_with_context_switching(self, cleanup_conversation_user):
        """
        Test de conversación con cambio de contexto entre temas.

        Escenario:
        1. Consulta sobre departamentos
        2. Cambio a pregunta general
        3. Vuelta a departamentos
        4. Verificar que el estado se maneja correctamente
        """
        user_id = cleanup_conversation_user
        orchestrator = FactoryOrchestrator()

        with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            messages = [
                {'from': user_id, 'text': {'body': 'Quiero comprar un departamento' }, 'timestamp': 1234567890},
                {'from': user_id, 'text': {'body': '¿Cuál es su horario?' }, 'timestamp': 1234567891},
                {'from': user_id, 'text': {'body': 'Volviendo al departamento, ¿tiene fotos?' }, 'timestamp': 1234567892}
            ]

            for message in messages:
                await orchestrator.process_message(message)

            assert mock_send.call_count >= len(messages), \
                "Debe procesar todos los mensajes incluyendo cambios de contexto"

            final_state = state_manager.get_conversation(user_id)
            assert final_state is not None, "Debe mantener estado a pesar de cambios de contexto"

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_state_persistence(self, cleanup_conversation_user):
        """
        Test de persistencia de estado en conversación multi-turno.

        Escenario:
        1. 10 mensajes consecutivos
        2. Verificar que el estado evoluciona correctamente
        3. Verificar que no se pierde información entre turnos
        """
        user_id = cleanup_conversation_user
        orchestrator = FactoryOrchestrator()

        with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            # Simular 10 turnos de conversación
            for i in range(10):
                message = {
                    'from': user_id,
                    'text': {'body': f'Mensaje número {i+1}'},
                    'timestamp': 1234567890 + i
                }
                await orchestrator.process_message(message)

                # Verificar que el estado existe después de cada mensaje
                state = state_manager.get_conversation(user_id)
                assert state is not None, f"Estado debe existir después del mensaje {i+1}"

            # Verificar que se procesaron todos los mensajes
            assert mock_send.call_count >= 10, "Debe haber procesado los 10 mensajes"

            # Estado final debe existir
            final_state = state_manager.get_conversation(user_id)
            assert final_state is not None, "Estado final debe existir"

    @pytest.mark.asyncio
    async def test_conversation_flow_with_errors(self, cleanup_conversation_user):
        """
        Test de flujo de conversación con manejo de errores.

        Escenario:
        1. Mensaje normal
        2. Simular error en procesamiento
        3. Mensaje de recuperación
        4. Verificar que el sistema se recupera y continúa
        """
        user_id = cleanup_conversation_user
        orchestrator = FactoryOrchestrator()

        with patch('app.core.factory_orchestrator.send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            # Mensaje 1: Normal
            message_1 = {
                'from': user_id,
                'text': {'body': 'Hola'},
                'timestamp': 1234567890
            }
            await orchestrator.process_message(message_1)

            assert mock_send.called, "Primer mensaje debe procesarse"

            # Mensaje 2: Simular error temporal
            with patch.object(orchestrator, '_select_agent', side_effect=Exception("Simulated error")):
                message_2 = {
                    'from': user_id,
                    'text': {'body': 'Mensaje con error'},
                    'timestamp': 1234567891
                }

                try:
                    await orchestrator.process_message(message_2)
                except Exception:
                    # Error esperado, continuamos
                    pass

            # Mensaje 3: Recuperación (sin mock de error)
            message_3 = {
                'from': user_id,
                'text': {'body': 'Mensaje de recuperación'},
                'timestamp': 1234567892
            }

            # No debe lanzar excepción, debe funcionar normalmente
            await orchestrator.process_message(message_3)

            # El sistema debe haberse recuperado
            # Al menos el primer y tercer mensaje deben haber sido procesados
            assert mock_send.call_count >= 2, "Sistema debe procesarse del error y continuar"
