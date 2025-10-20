"""
Tests unitarios para LeadsalesClient
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.leadsales.client import LeadsalesClient


class TestLeadsalesClient:
    """Tests para LeadsalesClient (HTTP client)"""

    def test_detect_demo_mode_with_test_token(self):
        """Detecta modo demo con test_token"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "test_token_123"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"
            client = LeadsalesClient()
            assert client.is_demo_mode is True

    def test_detect_demo_mode_with_demo_token(self):
        """Detecta modo demo con demo_token"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "demo_token_xyz"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"
            client = LeadsalesClient()
            assert client.is_demo_mode is True

    def test_detect_demo_mode_with_localhost_url(self):
        """Detecta modo demo con localhost URL"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "any_token"
            mock_settings.leadsales_api_url = "http://localhost:8000"
            client = LeadsalesClient()
            assert client.is_demo_mode is True

    def test_detect_production_mode_with_real_token(self):
        """Detecta modo produccion con token real"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_ldsls_xyz789"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"
            client = LeadsalesClient()
            assert client.is_demo_mode is False

    @pytest.mark.asyncio
    async def test_create_lead_api_success(self):
        """create_lead_api() envia payload correcto"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # Mock http_client.post_lead
            mock_response = {
                "success": True,
                "lead_id": "12345",
                "status": "created"
            }
            client.http_client.post_lead = AsyncMock(return_value=mock_response)

            payload = {
                "customer_name": "Test User",
                "whatsapp": "+573001234567",
                "customer_needs": "Busco apartamento",
                "priority": "ALTA"
            }

            result = await client.create_lead_api(payload)

            # Verificar que se llamo con payload correcto
            client.http_client.post_lead.assert_called_once_with(payload)

            # Verificar resultado
            assert result["success"] is True
            assert result["lead_id"] == "12345"

    @pytest.mark.asyncio
    async def test_get_lead_api_success(self):
        """get_lead_api() obtiene lead correctamente"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # Mock http_client.get_lead
            mock_lead = {
                "id": "12345",
                "name": "Juan Perez",
                "whatsapp": "+573001234567"
            }
            client.http_client.get_lead = AsyncMock(return_value=mock_lead)

            result = await client.get_lead_api("+573001234567")

            # Verificar llamada
            client.http_client.get_lead.assert_called_once_with("+573001234567")

            # Verificar resultado
            assert result["id"] == "12345"
            assert result["name"] == "Juan Perez"

    @pytest.mark.asyncio
    async def test_get_lead_api_not_found(self):
        """get_lead_api() retorna None cuando lead no existe"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()
            client.http_client.get_lead = AsyncMock(return_value=None)

            result = await client.get_lead_api("+573001234567")

            assert result is None

    @pytest.mark.asyncio
    async def test_update_lead_api_success(self):
        """update_lead_api() actualiza lead correctamente"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # Mock http_client.update_lead
            mock_response = {
                "success": True,
                "lead_id": "12345",
                "updated_fields": ["status"]
            }
            client.http_client.update_lead = AsyncMock(return_value=mock_response)

            updates = {"status": "contactado"}

            result = await client.update_lead_api("12345", updates)

            # Verificar llamada
            client.http_client.update_lead.assert_called_once_with("12345", updates)

            # Verificar resultado
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_leads_api_returns_empty_list(self):
        """list_leads_api() retorna lista vacia (placeholder)"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            result = await client.list_leads_api()

            # Placeholder retorna lista vacia
            assert result == []

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self):
        """health_check() retorna estado healthy"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            result = await client.health_check()

            assert result["status"] == "healthy"
            assert result["api_available"] is True

    @pytest.mark.asyncio
    async def test_close_completes_successfully(self):
        """close() completa sin errores"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # No debe lanzar excepciones
            await client.close()

    def test_is_demo_mode_property(self):
        """Propiedad is_demo_mode es accesible"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "test_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # Propiedad es accesible y retorna bool
            assert isinstance(client.is_demo_mode, bool)
            assert client.is_demo_mode is True


class TestLeadsalesClientEdgeCases:
    """Tests de casos borde"""

    @pytest.mark.asyncio
    async def test_create_lead_with_empty_payload(self):
        """Crear lead con payload vacio"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "prod_token"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # Mock error response
            client.http_client.post_lead = AsyncMock(
                return_value={"success": False, "error": "Empty payload"}
            )

            result = await client.create_lead_api({})

            assert result["success"] is False

    def test_detect_demo_mode_case_insensitive(self):
        """Deteccion de modo demo es case-insensitive"""
        with patch("app.services.leadsales.client.settings") as mock_settings:
            mock_settings.leadsales_api_token = "TEST_TOKEN_ABC"
            mock_settings.leadsales_api_url = "https://api.leadsales.io"

            client = LeadsalesClient()

            # Debe detectar modo demo incluso con mayusculas
            assert client.is_demo_mode is True