"""
Unit Tests for ResponseGenerator
Tests for all response generation methods
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.leadsales.analyzers import ResponseGenerator


class MockLLMService:
    """Mock LLM service for testing"""
    def __init__(self):
        self.api_client = MockAPIClient()
        self.llm_generator = MockLLMGenerator()

class MockAPIClient:
    def __init__(self):
        self.initialized = True

class MockLLMGenerator:
    async def generate_contextual_response(self, user_question, context, customer_name):
        return f"Mock response for {customer_name} based on: {context[:30]}..."


async def test_generate_initial_capture_response():
    """Test initial capture response generation"""
    response_gen = ResponseGenerator(None)

    response = await response_gen.generate_initial_capture_response("Maria")

    assert "Maria" in response
    assert len(response) > 50  # Should be a substantial response
    assert "inmueble" in response.lower() or "inmobiliario" in response.lower()
    print("   [OK] Initial capture response generated correctly")


async def test_generate_deepening_response_with_llm():
    """Test deepening response with mock LLM service"""
    mock_llm = MockLLMService()
    response_gen = ResponseGenerator(mock_llm)

    response = await response_gen.generate_deepening_response("Carlos", "Busco apartamento")

    assert "Mock response for Carlos" in response
    print("   [OK] Deepening response with LLM working correctly")


async def test_generate_deepening_response_fallback():
    """Test deepening response fallback when no LLM"""
    response_gen = ResponseGenerator(None)

    response = await response_gen.generate_deepening_response("Ana", "Busco casa")

    assert "Ana" in response
    assert "habitaciones" in response.lower()
    assert "presupuesto" in response.lower()
    print("   [OK] Deepening response fallback working correctly")


async def test_generate_follow_up_question():
    """Test follow up question generation"""
    response_gen = ResponseGenerator(None)

    response = await response_gen.generate_follow_up_question("apartamento 3 hab", "Luis")

    assert "Luis" in response
    assert len(response) > 30
    # Should contain motivational language
    assert any(word in response.lower() for word in ["perfecto", "excelente", "genial"])
    print("   [OK] Follow up question generated correctly")


async def test_generate_final_capture_question():
    """Test final capture question generation"""
    response_gen = ResponseGenerator(None)

    response = await response_gen.generate_final_capture_question("apartamento 3 hab poblado", "Sofia")

    assert "Sofia" in response
    assert "información" in response.lower()
    assert "asesor" in response.lower()
    print("   [OK] Final capture question generated correctly")


async def test_all_methods_are_async():
    """Test that all generation methods are properly async"""
    response_gen = ResponseGenerator(None)

    # Test all methods return coroutines
    result1 = response_gen.generate_initial_capture_response("Test")
    result2 = response_gen.generate_deepening_response("Test", "test needs")
    result3 = response_gen.generate_follow_up_question("test info", "Test")
    result4 = response_gen.generate_final_capture_question("test info", "Test")

    # All should be coroutines
    import inspect
    assert inspect.iscoroutine(result1)
    assert inspect.iscoroutine(result2)
    assert inspect.iscoroutine(result3)
    assert inspect.iscoroutine(result4)

    # Clean up coroutines
    result1.close()
    result2.close()
    result3.close()
    result4.close()

    print("   [OK] All methods are properly async")


async def test_error_handling():
    """Test error handling in ResponseGenerator"""

    class FailingLLMService:
        def __init__(self):
            self.api_client = MockAPIClient()
            self.llm_generator = FailingLLMGenerator()

    class FailingLLMGenerator:
        async def generate_contextual_response(self, user_question, context, customer_name):
            raise Exception("LLM service failed")

    failing_llm = FailingLLMService()
    response_gen = ResponseGenerator(failing_llm)

    # Should fallback gracefully when LLM fails
    response = await response_gen.generate_deepening_response("Test", "test needs")

    assert "Test" in response
    assert len(response) > 30  # Should get fallback response
    print("   [OK] Error handling working correctly")


async def test_motivational_language():
    """Test that responses contain motivational language"""
    response_gen = ResponseGenerator(None)

    responses = [
        await response_gen.generate_initial_capture_response("Cliente"),
        await response_gen.generate_follow_up_question("info", "Cliente"),
        await response_gen.generate_final_capture_question("info", "Cliente")
    ]

    motivational_words = ["excelente", "perfecto", "increíble", "genial", "emociona"]

    for response in responses:
        has_motivational = any(word in response.lower() for word in motivational_words)
        assert has_motivational, f"Response lacks motivational language: {response[:50]}..."

    print("   [OK] All responses contain motivational language")


async def run_all_tests():
    """Run all ResponseGenerator tests"""
    print("=" * 70)
    print("UNIT TESTS - RESPONSE GENERATOR")
    print("=" * 70)

    try:
        await test_generate_initial_capture_response()
        await test_generate_deepening_response_with_llm()
        await test_generate_deepening_response_fallback()
        await test_generate_follow_up_question()
        await test_generate_final_capture_question()
        await test_all_methods_are_async()
        await test_error_handling()
        await test_motivational_language()

        print("\n" + "=" * 70)
        print("[OK] ALL RESPONSE GENERATOR TESTS PASSED")
        print("=" * 70)
        print("ResponseGenerator functionality validated:")
        print("- Initial capture response generation working")
        print("- Deepening response with LLM and fallback working")
        print("- Follow up question generation working")
        print("- Final capture question generation working")
        print("- All methods properly async")
        print("- Error handling working correctly")
        print("- Motivational language present in all responses")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())