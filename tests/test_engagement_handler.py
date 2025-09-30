"""
Unit Tests for EngagementHandler
Tests for initial engagement and conversation initiation
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.leadsales.handlers import EngagementHandler


class MockResponseGenerator:
    """Mock ResponseGenerator for testing"""
    async def generate_initial_capture_response(self, customer_name):
        return f"Mock initial response for {customer_name}"

    async def generate_deepening_response(self, customer_name, existing_needs):
        return f"Mock deepening response for {customer_name} about {existing_needs[:20]}..."


async def test_initial_engagement_no_existing_needs():
    """Test initial engagement when no existing needs"""
    mock_response_gen = MockResponseGenerator()
    handler = EngagementHandler(mock_response_gen)

    conversation = {"customer_needs": ""}

    result = await handler.handle_initial_engagement("Maria", conversation)

    assert "Mock initial response for Maria" in result["response"]
    assert result["new_state"] == "CAPTURANDO_DETALLES"
    assert result["data_updates"]["conversion_stage"] == "initial_engagement"
    print("   [OK] Initial engagement with no existing needs working correctly")


async def test_initial_engagement_with_existing_needs():
    """Test initial engagement when existing needs are present"""
    mock_response_gen = MockResponseGenerator()
    handler = EngagementHandler(mock_response_gen)

    conversation = {"customer_needs": "Busco apartamento en el poblado"}

    result = await handler.handle_initial_engagement("Carlos", conversation)

    assert "Mock deepening response for Carlos" in result["response"]
    assert result["new_state"] == "PROFUNDIZANDO_NECESIDAD"
    assert result["data_updates"]["conversion_stage"] == "initial_engagement"
    print("   [OK] Initial engagement with existing needs working correctly")


async def test_initial_engagement_short_needs():
    """Test initial engagement when existing needs are too short"""
    mock_response_gen = MockResponseGenerator()
    handler = EngagementHandler(mock_response_gen)

    conversation = {"customer_needs": "Casa"}  # Only 4 characters, less than 10

    result = await handler.handle_initial_engagement("Ana", conversation)

    assert "Mock initial response for Ana" in result["response"]
    assert result["new_state"] == "CAPTURANDO_DETALLES"
    print("   [OK] Initial engagement with short needs working correctly")


async def test_engagement_handler_with_logger():
    """Test EngagementHandler with logger"""

    class MockLogger:
        def __init__(self):
            self.logs = []

        def log_action(self, message, metadata):
            self.logs.append({"message": message, "metadata": metadata})

    mock_response_gen = MockResponseGenerator()
    mock_logger = MockLogger()
    handler = EngagementHandler(mock_response_gen, mock_logger)

    conversation = {"customer_needs": ""}

    result = await handler.handle_initial_engagement("TestUser", conversation)

    # Check that logging occurred
    assert len(mock_logger.logs) == 1
    assert mock_logger.logs[0]["message"] == "Initial engagement completed"
    assert mock_logger.logs[0]["metadata"]["customer"] == "TestUser"
    print("   [OK] EngagementHandler logging working correctly")


async def test_engagement_handler_no_logger():
    """Test EngagementHandler without logger (should not crash)"""
    mock_response_gen = MockResponseGenerator()
    handler = EngagementHandler(mock_response_gen, None)

    conversation = {"customer_needs": ""}

    result = await handler.handle_initial_engagement("TestUser", conversation)

    # Should work without crashing
    assert "response" in result
    assert "new_state" in result
    print("   [OK] EngagementHandler working correctly without logger")


async def run_all_tests():
    """Run all EngagementHandler tests"""
    print("=" * 70)
    print("UNIT TESTS - ENGAGEMENT HANDLER")
    print("=" * 70)

    try:
        await test_initial_engagement_no_existing_needs()
        await test_initial_engagement_with_existing_needs()
        await test_initial_engagement_short_needs()
        await test_engagement_handler_with_logger()
        await test_engagement_handler_no_logger()

        print("\n" + "=" * 70)
        print("[OK] ALL ENGAGEMENT HANDLER TESTS PASSED")
        print("=" * 70)
        print("EngagementHandler functionality validated:")
        print("- Initial engagement with/without existing needs working")
        print("- State transitions working correctly")
        print("- Logging functionality working")
        print("- Error handling for missing logger working")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())