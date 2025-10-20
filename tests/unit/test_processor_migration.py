'''Test para validad migracion de processor .py'''

import pytest
import sys

def test_processor_imports_without_error():
    """Verificar que processor.py importa sin error de módulo faltante"""
    try:
        from app.core.processor import process_message, get_orchestrator
        assert process_message is not None
        assert get_orchestrator is not None
    except ImportError as e:
        pytest.fail(f"processor.py no debe tener imports rotos: {e}")

def test_processor_no_legacy_orchestrator_import():
    """Verificar que NO importa el orchestrator.py inexistente"""
    from app.core import processor
    import inspect
    
    source = inspect.getsource(processor)
    assert "from app.core.orchestrator import" not in source, \
        "processor.py no debe importar orchestrator.py legacy"
    assert "FactoryOrchestrator" in source, \
        "processor.py debe usar FactoryOrchestrator"

def test_orchestrator_singleton():
    """Verificar que get_orchestrator retorna misma instancia"""
    from app.core.processor import get_orchestrator
    
    orch1 = get_orchestrator()
    orch2 = get_orchestrator()
    
    assert orch1 is orch2, "Debe retornar misma instancia (singleton)"

@pytest.mark.asyncio
async def test_process_message_interface():
    """Verificar que process_message mantiene interfaz legacy"""
    from app.core.processor import process_message
    from unittest.mock import AsyncMock, patch
    
    # Mock del orchestrator
    with patch('app.core.processor.get_orchestrator') as mock_get_orch:
        mock_orchestrator = AsyncMock()
        mock_get_orch.return_value = mock_orchestrator
        
        message_data = {"from": "123", "text": {"body": "test"}}
        await process_message(message_data)
        
        # Verificar que delega a orchestrator
        mock_orchestrator.process_message.assert_called_once_with(message_data)