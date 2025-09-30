"""
Unit Tests for CRMHandler
Tests for CRM operations, lead creation, and success/error handling
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.leadsales.handlers import CRMHandler


class MockLeadsalesService:
    """Mock LeadsalesService for testing"""
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed

    async def create_lead(self, customer_name, whatsapp_id, customer_needs, additional_data):
        if self.should_succeed:
            return {
                "success": True,
                "lead_id": "LEAD_12345",
                "demo_mode": True,
                "customer_data": {
                    "name": customer_name,
                    "whatsapp": whatsapp_id or "123456789",
                    "needs": customer_needs,
                    "quality_score": 95,
                    "tags": ["hot_lead", "high_intent"],
                    "priority": "Alta",
                    "created_at": "2025-01-01 10:30:00"
                },
                "crm_simulation": {"status": "created", "id": "LEAD_12345", "pipeline": "ventas"}
            }
        else:
            return {
                "success": False,
                "error": "CRM connection failed"
            }


async def test_successful_lead_creation():
    """Test successful lead creation flow"""
    mock_service = MockLeadsalesService(should_succeed=True)
    handler = CRMHandler(mock_service)

    # Set conversation context
    conversation = {
        "whatsapp_id": "1234567890",
        "tiene_contrato_inmobiliaria": "No",
        "fecha_necesidad": "Pronto"
    }
    handler.set_conversation_context(conversation, "1234567890")

    result = await handler.proceed_to_crm_creation("Apartamento 3 hab poblado", "Maria")

    assert "Excelente Maria!" in result["response"]
    assert result["new_state"] == "LEAD_CREADO"
    assert result["data_updates"]["lead_created"] == True
    assert result["data_updates"]["lead_id"] == "LEAD_12345"
    print("   [OK] Successful lead creation working correctly")


async def test_failed_lead_creation():
    """Test failed lead creation flow"""
    mock_service = MockLeadsalesService(should_succeed=False)
    handler = CRMHandler(mock_service)

    conversation = {"whatsapp_id": "1234567890"}
    handler.set_conversation_context(conversation, "1234567890")

    result = await handler.proceed_to_crm_creation("Apartamento 3 hab poblado", "Carlos")

    assert "No te preocupes Carlos!" in result["response"]
    assert result["new_state"] == "LEAD_ERROR"
    assert result["data_updates"]["lead_error"] == True
    print("   [OK] Failed lead creation handling working correctly")


async def test_lead_creation_exception():
    """Test lead creation with exception"""

    class FailingLeadsalesService:
        async def create_lead(self, customer_name, whatsapp_id, customer_needs, additional_data):
            raise Exception("Service unavailable")

    failing_service = FailingLeadsalesService()
    handler = CRMHandler(failing_service)

    conversation = {"whatsapp_id": "1234567890"}
    handler.set_conversation_context(conversation, "1234567890")

    result = await handler.proceed_to_crm_creation("Apartamento 3 hab poblado", "Ana")

    assert "Tranquilo Ana!" in result["response"]
    assert result["new_state"] == "ERROR_FALLBACK"
    assert result["data_updates"]["fallback_activated"] == True
    print("   [OK] Lead creation exception handling working correctly")


async def test_handle_successful_lead_creation_with_demo():
    """Test successful lead creation with demo visualization"""
    mock_service = MockLeadsalesService(should_succeed=True)
    handler = CRMHandler(mock_service)

    lead_result = {
        "success": True,
        "lead_id": "LEAD_67890",
        "demo_mode": True,
        "customer_data": {
            "name": "Luis",
            "whatsapp": "9876543210",
            "needs": "Casa 4 hab",
            "quality_score": 90,
            "tags": ["family_home", "urgent"],
            "priority": "Media",
            "created_at": "2025-01-01 11:00:00"
        },
        "crm_simulation": {"status": "created", "id": "LEAD_67890", "pipeline": "ventas"}
    }

    result = await handler.handle_successful_lead_creation("Luis", lead_result)

    assert "Excelente Luis!" in result["response"]
    assert "324 551 6105" in result["response"]  # WhatsApp oficial
    assert result["data_updates"]["lead_id"] == "LEAD_67890"
    print("   [OK] Successful lead creation with demo working correctly")


async def test_handle_lead_creation_error():
    """Test lead creation error handling"""
    mock_service = MockLeadsalesService()
    handler = CRMHandler(mock_service)

    lead_result = {
        "success": False,
        "error": "Database connection timeout"
    }

    result = await handler.handle_lead_creation_error("Sofia", lead_result)

    assert "No te preocupes Sofia!" in result["response"]
    assert result["data_updates"]["error_details"] == "Database connection timeout"
    assert result["data_updates"]["manual_follow_up_required"] == True
    print("   [OK] Lead creation error handling working correctly")


async def test_handle_error_fallback():
    """Test general error fallback"""
    mock_service = MockLeadsalesService()
    handler = CRMHandler(mock_service)

    result = await handler.handle_error_fallback("TestUser")

    assert "Tranquilo TestUser!" in result["response"]
    assert result["data_updates"]["fallback_activated"] == True
    print("   [OK] Error fallback working correctly")


async def test_conversation_context_setting():
    """Test conversation context setting"""
    mock_service = MockLeadsalesService()
    handler = CRMHandler(mock_service)

    conversation = {
        "whatsapp_id": "9876543210",
        "customer_name": "TestUser"
    }

    handler.set_conversation_context(conversation, "9876543210")

    assert handler._current_conversation == conversation
    assert handler._current_whatsapp_id == "9876543210"
    print("   [OK] Conversation context setting working correctly")


async def test_crm_handler_with_logger():
    """Test CRMHandler with logger"""

    class MockLogger:
        def __init__(self):
            self.logs = []
            self.errors = []

        def log_action(self, message, metadata):
            self.logs.append({"message": message, "metadata": metadata})

        def log_error(self, message, exception):
            self.errors.append({"message": message, "exception": exception})

    mock_service = MockLeadsalesService(should_succeed=True)
    mock_logger = MockLogger()
    handler = CRMHandler(mock_service, "324 551 6105", mock_logger)

    conversation = {"whatsapp_id": "1234567890"}
    handler.set_conversation_context(conversation, "1234567890")

    result = await handler.proceed_to_crm_creation("Test needs", "TestUser")

    # Check that logging occurred
    assert len(mock_logger.logs) >= 1
    assert any("Starting CRM lead creation" in log["message"] for log in mock_logger.logs)
    print("   [OK] CRMHandler logging working correctly")


async def test_custom_whatsapp_number():
    """Test CRMHandler with custom WhatsApp number"""
    mock_service = MockLeadsalesService()
    custom_whatsapp = "555 123 4567"
    handler = CRMHandler(mock_service, custom_whatsapp)

    result = await handler.handle_error_fallback("TestUser")

    assert custom_whatsapp in result["response"]
    print("   [OK] Custom WhatsApp number working correctly")


async def run_all_tests():
    """Run all CRMHandler tests"""
    print("=" * 70)
    print("UNIT TESTS - CRM HANDLER")
    print("=" * 70)

    try:
        await test_successful_lead_creation()
        await test_failed_lead_creation()
        await test_lead_creation_exception()
        await test_handle_successful_lead_creation_with_demo()
        await test_handle_lead_creation_error()
        await test_handle_error_fallback()
        await test_conversation_context_setting()
        await test_crm_handler_with_logger()
        await test_custom_whatsapp_number()

        print("\n" + "=" * 70)
        print("[OK] ALL CRM HANDLER TESTS PASSED")
        print("=" * 70)
        print("CRMHandler functionality validated:")
        print("- Successful lead creation working")
        print("- Failed lead creation handling working")
        print("- Exception handling working")
        print("- Demo visualization integration working")
        print("- Error fallback working")
        print("- Conversation context management working")
        print("- Logging functionality working")
        print("- Custom WhatsApp number support working")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())