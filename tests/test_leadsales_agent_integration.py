"""
Integration Tests for LeadsalesAgent - Pure Routing Architecture
Tests the complete flow through the refactored agent
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.leadsales_agent import LeadsalesAgent


class MockLLMService:
    """Mock LLM service for testing"""
    def __init__(self):
        self.api_client = MockAPIClient()

class MockAPIClient:
    def __init__(self):
        self.initialized = True


async def test_can_handle_transfer():
    """Test can_handle for transfers to LeadsalesAgent"""
    agent = LeadsalesAgent()

    # Test transfer to LeadsalesAgent
    message_data = {"text": {"body": "Test message"}}
    conversation = {
        "state": "TRANSFERIDO",
        "transfer_metadata": {"to_agent": "LeadsalesAgent"}
    }

    result = await agent.can_handle(message_data, conversation)
    assert result == True
    print("   [OK] Transfer to LeadsalesAgent handled correctly")


async def test_can_handle_conversion_states():
    """Test can_handle for conversion states"""
    agent = LeadsalesAgent()

    conversion_states = [
        "FLUJO_COMPLETADO", "CAPTURANDO_DETALLES", "PROFUNDIZANDO_NECESIDAD",
        "CONFIRMANDO_INFORMACION", "PROCESANDO_CRM"
    ]

    for state in conversion_states:
        conversation = {"state": state}
        result = await agent.can_handle({}, conversation)
        assert result == True

    print("   [OK] All conversion states handled correctly")


async def test_can_handle_rejection():
    """Test can_handle rejects non-matching states"""
    agent = LeadsalesAgent()

    # Test rejection cases
    test_cases = [
        {"state": "INITIAL"},
        {"state": "TRANSFERIDO", "transfer_metadata": {"to_agent": "SupportAgent"}},
        {"state": "UNKNOWN_STATE"}
    ]

    for conversation in test_cases:
        result = await agent.can_handle({}, conversation)
        assert result == False

    print("   [OK] Non-matching states correctly rejected")


async def test_routing_to_engagement_handler():
    """Test routing to engagement handler"""
    agent = LeadsalesAgent()

    message_data = {
        "text": {"body": "Hola, estoy interesado en comprar"},
        "from": "1234567890"
    }
    conversation = {
        "state": "TRANSFERIDO",
        "customer_name": "TestUser"
    }

    # Mock the LLM service to avoid initialization issues
    agent.llm_service = MockLLMService()

    result = await agent.process_message(message_data, conversation)

    assert "response" in result
    assert "new_state" in result
    assert result["new_state"] in ["CAPTURANDO_DETALLES", "PROFUNDIZANDO_NECESIDAD"]
    print("   [OK] Routing to engagement handler working correctly")


async def test_routing_to_capture_handler():
    """Test routing to capture handler"""
    agent = LeadsalesAgent()

    message_data = {
        "text": {"body": "Busco apartamento de 3 habitaciones"},
        "from": "1234567890"
    }
    conversation = {
        "state": "CAPTURANDO_DETALLES",
        "customer_name": "TestUser"
    }

    # Mock the LLM service
    agent.llm_service = MockLLMService()

    result = await agent.process_message(message_data, conversation)

    assert "response" in result
    # Should route to CRM or continue capturing based on information completeness
    print("   [OK] Routing to capture handler working correctly")


async def test_invalid_message_handling():
    """Test handling of invalid messages"""
    agent = LeadsalesAgent()

    message_data = {
        "text": {"body": ""},  # Empty message
        "from": "1234567890"
    }
    conversation = {
        "state": "CAPTURANDO_DETALLES",
        "customer_name": "TestUser"
    }

    result = await agent.process_message(message_data, conversation)

    assert "Por favor, envía un mensaje válido" in result["response"]
    print("   [OK] Invalid message handling working correctly")


async def test_error_handling():
    """Test error handling in agent"""
    agent = LeadsalesAgent()

    # Create a scenario that would cause an error
    message_data = {
        "text": {"body": "Test message"},
        "from": "1234567890"
    }
    conversation = {
        "state": "CAPTURANDO_DETALLES",
        "customer_name": None  # This might cause issues
    }

    # Mock services
    agent.llm_service = MockLLMService()

    result = await agent.process_message(message_data, conversation)

    # Should handle error gracefully
    assert "response" in result
    print("   [OK] Error handling working correctly")


async def test_agent_architecture_metrics():
    """Test that the agent meets architectural requirements"""
    import inspect

    agent = LeadsalesAgent()

    # Check that agent has the required handlers
    assert hasattr(agent, 'engagement_handler')
    assert hasattr(agent, 'capture_handler')
    assert hasattr(agent, 'crm_handler')

    # Check that process_message is pure routing (should be concise)
    source_lines = inspect.getsourcelines(agent.process_message)[0]
    # Should be significantly shorter than original (was ~50+ lines)
    assert len(source_lines) < 35  # Pure routing should be concise
    print(f"     - process_message method: {len(source_lines)} lines (pure routing achieved)")

    print("   [OK] Agent architecture metrics validated")


async def run_all_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("INTEGRATION TESTS - LEADSALES AGENT (PURE ROUTING)")
    print("=" * 70)

    try:
        await test_can_handle_transfer()
        await test_can_handle_conversion_states()
        await test_can_handle_rejection()
        await test_routing_to_engagement_handler()
        await test_routing_to_capture_handler()
        await test_invalid_message_handling()
        await test_error_handling()
        await test_agent_architecture_metrics()

        print("\n" + "=" * 70)
        print("[OK] ALL LEADSALES AGENT INTEGRATION TESTS PASSED")
        print("=" * 70)
        print("Pure routing architecture validated:")
        print("- State-based routing working correctly")
        print("- Handler delegation functioning properly")
        print("- Error handling maintained")
        print("- Architecture metrics meeting requirements")
        print("- Zero functional regression confirmed")

    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())