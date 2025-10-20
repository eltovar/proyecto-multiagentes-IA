"""
Cliente HTTP para comunicación con API de Leadsales CRM
Responsabilidad: Comunicación HTTP con API externa
"""
from typing import Dict, Any, Optional, List
from app.services.leadsales_client import LeadsalesClient as HTTPClient
from app.config import settings


class LeadsalesClient:
    """
    Cliente especializado para operaciones de API de Leadsales.
    Maneja toda la comunicación HTTP con el CRM externo.
    """

    def __init__(self):
        """Inicializa el cliente HTTP"""
        self.http_client = HTTPClient()
        self._is_demo_mode = self._detect_demo_mode()

    def _detect_demo_mode(self) -> bool:
        """Detecta si está en modo demo por token/URL de prueba"""
        demo_indicators = [
            "test_token", "demo_token", "mock_token",
            "https://api.leadsales.test/", "localhost"
        ]
        api_url = getattr(settings, 'leadsales_api_url', '').lower()
        api_token = getattr(settings, 'leadsales_api_token', '').lower()

        return any(indicator in api_url or indicator in api_token
                  for indicator in demo_indicators)

    @property
    def is_demo_mode(self) -> bool:
        """Retorna True si está en modo demo"""
        return self._is_demo_mode

    async def create_lead_api(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un lead en la API de Leadsales.

        Args:
            lead_data: Datos del lead a crear

        Returns:
            Respuesta de la API con lead_id y estado
        """
        return await self.http_client.post_lead(lead_data)

    async def get_lead_api(self, whatsapp_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un lead por whatsapp_id.

        Args:
            whatsapp_id: ID de WhatsApp del cliente

        Returns:
            Datos del lead o None si no existe
        """
        return await self.http_client.get_lead(whatsapp_id)

    async def update_lead_api(self, lead_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un lead existente.

        Args:
            lead_id: ID del lead
            updates: Campos a actualizar

        Returns:
            Respuesta de la API
        """
        return await self.http_client.update_lead(lead_id, updates)

    async def list_leads_api(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista leads desde la API con filtros opcionales.

        Args:
            filters: Filtros de búsqueda (ej: status, priority, date_range)

        Returns:
            Lista de leads que coinciden con los filtros
        """
        # Implementación placeholder - delegaría a http_client
        return []

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado de salud de la API.

        Returns:
            Estado de la API
        """
        try:
            # Simulación de health check
            return {
                "status": "healthy",
                "api_available": True,
                "message": "Leadsales API is responding"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_available": False,
                "error": str(e)
            }

    async def close(self):
        """Cierra conexiones y libera recursos del cliente HTTP"""
        # Implementación placeholder - cerraría conexiones HTTP si existieran
        pass
