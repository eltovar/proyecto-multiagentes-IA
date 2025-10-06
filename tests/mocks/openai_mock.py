"""
OpenAI Mock - Simulador de API de OpenAI para Testing
====================================================

Mock inteligente que permite tests sin llamadas API reales.
Reduce costos y tiempo de ejecución de tests dramáticamente.

VERSION: 1.0.0
AUTHOR: PR #1 - Fundamentos
USAGE: Ver tests/unit/test_llm_extraction.py
"""

import json
import os
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, AsyncMock


class MockOpenAIResponse:
    """Simula la estructura de respuesta de OpenAI."""

    def __init__(self, content: str):
        self.choices = [MagicMock()]
        self.choices[0].message = MagicMock()
        self.choices[0].message.content = content


class MockOpenAIClient:
    """
    Mock completo del cliente AsyncOpenAI.

    Simula el comportamiento de OpenAI API usando fixtures predefinidas.
    Permite tests determinísticos, rápidos y sin costo.

    Example:
        >>> fixtures_path = "tests/fixtures/llm_responses.json"
        >>> mock_client = MockOpenAIClient(fixtures_path)
        >>> client = mock_client.get_mock_client()
        >>>
        >>> # Usar en tests
        >>> llm_service.api_client.client = client
        >>> result = await llm_service.classify_intent_and_extract_entities("Hola, soy Carlos")
    """

    def __init__(self, fixtures_path: Optional[str] = None):
        """
        Inicializa el mock con fixtures.

        Args:
            fixtures_path: Ruta al archivo JSON de fixtures.
                          Por defecto: tests/fixtures/llm_responses.json
        """
        if fixtures_path is None:
            # Path relativo desde raíz del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            fixtures_path = os.path.join(base_dir, "tests", "fixtures", "llm_responses.json")

        self.fixtures_path = fixtures_path
        self.fixtures = self._load_fixtures()
        self.call_count = 0
        self.last_call_params = None

    def _load_fixtures(self) -> Dict[str, Any]:
        """Carga fixtures desde archivo JSON."""
        try:
            with open(self.fixtures_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[MockOpenAI] WARNING: Fixtures file not found: {self.fixtures_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[MockOpenAI] ERROR: Invalid JSON in fixtures: {e}")
            return {}

    def get_mock_client(self):
        """
        Retorna un cliente AsyncOpenAI mockeado.

        Returns:
            MagicMock configurado para simular AsyncOpenAI
        """
        client = MagicMock()
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=self._mock_completion)

        return client

    async def _mock_completion(self, **kwargs) -> MockOpenAIResponse:
        """
        Simula una llamada a chat.completions.create.

        Analiza el mensaje del usuario y retorna la fixture apropiada.

        Args:
            **kwargs: Parámetros de la llamada (model, messages, temperature, etc.)

        Returns:
            MockOpenAIResponse con contenido JSON apropiado
        """
        self.call_count += 1
        self.last_call_params = kwargs

        # Extraer mensaje del usuario
        messages = kwargs.get("messages", [])
        user_message = ""

        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break

        # Mapear mensaje a fixture apropiada
        fixture_key = self._map_message_to_fixture(user_message)

        # Obtener fixture
        fixture_data = self.fixtures.get(
            fixture_key,
            self._get_default_fixture()
        )

        # Retornar respuesta mockeada
        return MockOpenAIResponse(json.dumps(fixture_data))

    def _map_message_to_fixture(self, user_message: str) -> str:
        """
        Mapea el contenido del mensaje a la fixture apropiada.

        Args:
            user_message: Mensaje del usuario (lowercase)

        Returns:
            Key de la fixture a usar
        """
        # Búsqueda por keywords específicos

        # Nombres específicos
        if "carlos" in user_message and ("apartamento" in user_message or "chapinero" in user_message):
            return "extraction_with_name_and_property"

        if "maría fernanda" in user_message or "maria fernanda" in user_message:
            return "extraction_name_only_greeting"

        if "andrés" in user_message or "andres" in user_message:
            return "extraction_property_detailed"

        if "laura" in user_message:
            return "extraction_job_search"

        if "roberto" in user_message:
            return "extraction_with_current_contract"

        # Intenciones
        if any(kw in user_message for kw in ["problema", "error", "ayuda", "soporte"]):
            if "pago" in user_message or "factura" in user_message:
                return "extraction_payment_support"
            elif "reparacion" in user_message or "arreglar" in user_message or "dañado" in user_message:
                return "extraction_maintenance_support"
            else:
                return "extraction_support_intent"

        if any(kw in user_message for kw in ["trabajo", "empleo", "vacante", "aplicar"]):
            return "extraction_job_search"

        if any(kw in user_message for kw in ["llamar", "telefono", "hablar"]):
            return "extraction_call_request"

        # Búsqueda de propiedad
        if "urgente" in user_message:
            return "extraction_urgent_search"

        if any(kw in user_message for kw in ["busco", "apartamento", "casa", "arriendo", "comprar"]):
            return "extraction_with_name_and_property"

        # Saludo simple
        if any(kw in user_message for kw in ["hola", "buenos dias", "buenas tardes"]):
            if "soy" in user_message or "llamo" in user_message:
                return "extraction_name_only_greeting"

        # Mensajes ambiguos
        if len(user_message.split()) <= 2:
            return "extraction_unclear"

        # Default: búsqueda de propiedad genérica
        return "extraction_with_name_and_property"

    def _get_default_fixture(self) -> Dict[str, Any]:
        """Fixture por defecto para mensajes no mapeados."""
        return {
            "nombre": None,
            "intent": "unclear",
            "confidence": 0.5,
            "entities": {
                "property_type": None,
                "location": None,
                "budget": None,
                "rooms": None,
                "bathrooms": None,
                "urgency": None,
                "current_situation": None
            },
            "reasoning": "Mensaje no mapeado a fixture específica (mock default)"
        }

    def reset_call_count(self):
        """Resetea el contador de llamadas (útil entre tests)."""
        self.call_count = 0
        self.last_call_params = None


# Instancia global para uso conveniente
_mock_client_instance = None


def get_mock_openai_client(fixtures_path: Optional[str] = None):
    """
    Factory function para obtener instancia del mock.

    Args:
        fixtures_path: Path opcional a fixtures custom

    Returns:
        MockOpenAIClient instance
    """
    global _mock_client_instance

    if _mock_client_instance is None or fixtures_path is not None:
        _mock_client_instance = MockOpenAIClient(fixtures_path)

    return _mock_client_instance
