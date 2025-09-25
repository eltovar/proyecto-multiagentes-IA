import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.core.orchestrator import AgentOrchestrator
from app.state.models import ConversationState
from app.config import STATE_NUEVO, STATE_TRANSFERIDO, STATE_RECOPILANDO_NOMBRE

class TestAgentOrchestrator:
    """
    Tests unitarios para el Orquestador Central del sistema multiagentes.

    Verifica:
    - Inicializacion correcta
    - Seleccion de agentes
    - Procesamiento de mensajes
    - Handoff Protocol
    - Manejo de errores
    """

    @pytest.fixture
    def orchestrator(self):
        """Fixture que retorna una instancia del orquestador."""
        with patch('app.core.orchestrator.state_manager'):
            # Mock del agente de recepción para evitar dependencias
            with patch('app.agents.reception_agent.ReceptionAgent') as mock_reception:
                mock_reception_instance = Mock()
                mock_reception_instance.process_message = AsyncMock()
                mock_reception.return_value = mock_reception_instance

                orchestrator = AgentOrchestrator()
                return orchestrator

    @pytest.fixture
    def sample_conversation(self):
        """Fixture que retorna una conversación de ejemplo."""
        return ConversationState(
            whatsapp_id="57312345678",
            state=STATE_NUEVO,
            customer_name=None,
            customer_needs=None
        )

    def test_orchestrator_initialization(self, orchestrator):
        """Verifica que el orquestador se inicializa correctamente."""
        assert orchestrator.initialized is True
        assert "reception" in orchestrator.agents
        assert len(orchestrator.agents) == 1  # Solo reception en FASE 1A

    def test_select_agent_new_conversation(self, orchestrator, sample_conversation):
        """Verifica seleccion de agente para conversacion nueva."""
        selected_agent = orchestrator.select_agent("Hola", sample_conversation)
        assert selected_agent == "reception"

    def test_select_agent_handoff_protocol(self, orchestrator):
        """Verifica que el Handoff Protocol bloquea la selección de agentes."""
        transferred_conversation = ConversationState(
            whatsapp_id="57312345678",
            state=STATE_TRANSFERIDO
        )

        selected_agent = orchestrator.select_agent("Mensaje", transferred_conversation)
        assert selected_agent is None

    @pytest.mark.asyncio
    async def test_process_message_new_user(self, orchestrator):
        """Verifica procesamiento de mensaje para usuario nuevo."""
        # Mock del state_manager
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            # Configurar mock para retornar conversación nueva
            mock_conversation = ConversationState(
                whatsapp_id="57312345678",
                state=STATE_NUEVO
            )
            mock_state_manager.get_or_create_conversation.return_value = mock_conversation
            mock_state_manager.update_conversation_state.return_value = True

            # Mock respuesta del agente
            mock_agent_response = {
                "response": "¡Hola! ¿Cuál es tu nombre?",
                "new_state": STATE_RECOPILANDO_NOMBRE
            }
            orchestrator.agents["reception"].process_message.return_value = mock_agent_response

            # Ejecutar
            result = await orchestrator.process_message(
                whatsapp_id="57312345678",
                message="Hola"
            )

            # Verificar
            assert result["status"] == "success"
            assert result["agent_used"] == "reception"
            assert result["response"] == "¡Hola! ¿Cuál es tu nombre?"
            assert result["new_state"] == STATE_RECOPILANDO_NOMBRE

    @pytest.mark.asyncio
    async def test_process_message_handoff_active(self, orchestrator):
        """Verifica que mensajes se ignoran cuando Handoff Protocol está activo."""
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            # Conversación transferida
            transferred_conversation = ConversationState(
                whatsapp_id="57312345678",
                state=STATE_TRANSFERIDO
            )
            mock_state_manager.get_or_create_conversation.return_value = transferred_conversation

            # Ejecutar
            result = await orchestrator.process_message(
                whatsapp_id="57312345678",
                message="Necesito ayuda"
            )

            # Verificar que se ignora el mensaje
            assert result["status"] == "handoff_active"
            assert result["response"] is None

            # Verificar que NO se llamó al agente
            orchestrator.agents["reception"].process_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_agent_error(self, orchestrator):
        """Verifica manejo de errores cuando un agente falla."""
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            mock_conversation = ConversationState(
                whatsapp_id="57312345678",
                state=STATE_NUEVO
            )
            mock_state_manager.get_or_create_conversation.return_value = mock_conversation

            # Configurar agente para lanzar excepción
            orchestrator.agents["reception"].process_message.side_effect = Exception("Error en agente")

            # Ejecutar
            result = await orchestrator.process_message(
                whatsapp_id="57312345678",
                message="Hola"
            )

            # Verificar manejo del error
            assert result["status"] == "error"
            assert "Error interno" in result["message"]
            assert "Error en agente" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_agent_transfer_unavailable(self, orchestrator):
        """Verifica manejo de transferencias a agentes no disponibles en FASE 1A."""
        mock_conversation = ConversationState(whatsapp_id="57312345678", state=STATE_NUEVO)

        agent_response = {
            "transfer_to": "support",  # No disponible en FASE 1A
            "response": "Transfiriendo a soporte"
        }

        result = await orchestrator._handle_agent_transfer(
            agent_response,
            mock_conversation,
            "57312345678"
        )

        assert result["status"] == "transfer_deferred"
        assert "será implementada en fases posteriores" in result["message"]

    def test_get_system_status(self, orchestrator):
        """Verifica que el estado del sistema se retorna correctamente."""
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            mock_state_manager.get_stats.return_value = {
                "total_conversations": 5,
                "active_handoffs": 2
            }

            status = orchestrator.get_system_status()

            assert status["orchestrator_initialized"] is True
            assert status["available_agents"] == ["reception"]
            assert status["phase"] == "1A"
            assert status["agents_implemented"] == ["reception"]
            assert status["agents_pending"] == ["support", "leadsales"]

    def test_health_check_healthy(self, orchestrator):
        """Verifica health check cuando el sistema está saludable."""
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            mock_state_manager.get_stats.return_value = {"total_conversations": 10}

            health = orchestrator.health_check()

            assert health["status"] == "healthy"
            assert health["phase"] == "1A"
            assert health["agents_count"] == 1

    def test_health_check_unhealthy_not_initialized(self):
        """Verifica health check cuando el orquestador no está inicializado."""
        # Crear orquestador sin inicializar
        orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
        orchestrator.initialized = False

        health = orchestrator.health_check()

        assert health["status"] == "unhealthy"
        assert "not initialized" in health["reason"]

    def test_health_check_database_error(self, orchestrator):
        """Verifica health check cuando hay error en la base de datos."""
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            mock_state_manager.get_stats.side_effect = Exception("Database connection failed")

            health = orchestrator.health_check()

            assert health["status"] == "unhealthy"
            assert "Database error" in health["reason"]

    @pytest.mark.asyncio
    async def test_state_update_failure(self, orchestrator):
        """Verifica manejo cuando falla la actualización del estado."""
        with patch('app.core.orchestrator.state_manager') as mock_state_manager:
            mock_conversation = ConversationState(
                whatsapp_id="57312345678",
                state=STATE_NUEVO
            )
            mock_state_manager.get_or_create_conversation.return_value = mock_conversation
            # Simular fallo en actualización de estado
            mock_state_manager.update_conversation_state.return_value = False

            # Mock respuesta del agente que requiere actualización de estado
            mock_agent_response = {
                "response": "Perfecto",
                "new_state": STATE_RECOPILANDO_NOMBRE,
                "customer_name": "Juan"
            }
            orchestrator.agents["reception"].process_message.return_value = mock_agent_response

            # Ejecutar
            result = await orchestrator.process_message(
                whatsapp_id="57312345678",
                message="Mi nombre es Juan"
            )

            # Debe retornar éxito aunque falle la actualización de estado
            assert result["status"] == "success"
            assert result["agent_used"] == "reception"

    def test_select_agent_unknown_state(self, orchestrator):
        """Verifica selección de agente para estado desconocido."""
        unknown_state_conversation = ConversationState(
            whatsapp_id="57312345678",
            state="ESTADO_INEXISTENTE"
        )

        selected_agent = orchestrator.select_agent("Mensaje", unknown_state_conversation)
        assert selected_agent == "reception"  # Debe hacer fallback a reception

# Fixture para ejecutar tests asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Fixture para manejar el event loop en tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])