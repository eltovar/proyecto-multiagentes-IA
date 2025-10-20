'''Test para validacion de integracion del webhook de main.py'''

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_webhook_endpoint_uses_migrated_processor():
    """Verificar que endpoint /webhook usa processor migrado"""
    from app.main import app

    client = TestClient(app)

    # Mock orchestrator.process_message (patchea el método del orchestrator)
    with patch('app.main.orchestrator.process_message', new_callable=AsyncMock) as mock_process:
        # Payload típico de WhatsApp
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "573001234567",
                            "type": "text",
                            "text": {"body": "Hola"}
                        }]
                    }
                }]
            }]
        }
        
        response = client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        mock_process.assert_called_once()

@pytest.mark.asyncio
async def test_processor_creates_factory_orchestrator():
    """Verificar que processor crea FactoryOrchestrator correctamente"""
    from app.core.processor import get_orchestrator
    from app.core.factory_orchestrator import FactoryOrchestrator
    
    orchestrator = get_orchestrator()

    assert isinstance(orchestrator, FactoryOrchestrator)
    assert hasattr(orchestrator, 'service_container')  # Nombre correcto del atributo
    assert hasattr(orchestrator, 'process_message')