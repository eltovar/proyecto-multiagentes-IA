import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_llm():
    mock = Mock()
    mock.generate_response = AsyncMock(return_value={"response": "Hola! ¿Cómo puedo ayudarte?"})
    return mock

@pytest.fixture
def mock_state():
    mock = Mock()
    mock.update_state = AsyncMock()
    return mock