"""Cliente HTTP para Leadsales API 
    Puente de comunicación entre tu aplicación (el agente de IA) y el sistema de gestión de Leadsales.
"""

import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.error_logger import log_error, log_info

class LeadsalesClient:
    """Cliente HTTP simplificado para API de Leadsales"""

    def __init__(self):
        self.api_url = settings.leadsales_api_url
        self.api_token = settings.leadsales_api_token
        self.timeout = settings.leadsales_timeout

    async def post_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.api_url}/leads", json=lead_data, headers=self._get_headers())

                return self._validate_response(response)

        except httpx.TimeoutException:
            log_error("LeadsalesClient", "Timeout conectando con API")
            return {"success": False, "error": "Timeout en API de Leadsales"}
        except Exception as e:
            log_error("LeadsalesClient", "Error inesperado", e)
            return {"success": False, "error": f"Error inesperado: {str(e)}"}

    async def get_lead(self, whatsapp_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_url}/leads", params={"whatsapp_id": whatsapp_id}, headers=self._get_headers())

                if response.status_code == 200:
                    leads_data = response.json()
                    if leads_data and len(leads_data) > 0:
                        return leads_data[0]

        except Exception as e:
            log_error("LeadsalesClient", "Error buscando lead", e)

        return None

    async def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(f"{self.api_url}/leads/{lead_id}", json=update_data, headers=self._get_headers())

                if response.status_code == 200:
                    log_info("LeadsalesClient", f"Lead {lead_id} actualizado")
                    return True
                else:
                    log_error("LeadsalesClient", f"Error actualizando lead: {response.status_code}")
                    return False

        except Exception as e:
            log_error("LeadsalesClient", f"Error actualizando lead {lead_id}", e)
            return False

    async def assign_advisor(self, lead_id: str, criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        assignment_data = {"lead_id": lead_id, "auto_assign": True, "criteria": criteria or {}}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.api_url}/leads/{lead_id}/assign", json=assignment_data, headers=self._get_headers())
                if response.status_code == 200:
                    assignment_result = response.json()
                    advisor_info = assignment_result.get("advisor", {})
                    log_info("LeadsalesClient", f"Asesor asignado: {advisor_info.get('name')}")
                    return {"success": True, "advisor": advisor_info}
                else:
                    log_error("LeadsalesClient", f"Error asignando asesor: {response.status_code}")
                    return {"success": False, "error": f"Error HTTP {response.status_code}"}

        except Exception as e:
            log_error("LeadsalesClient", "Error asignando asesor", e)
            return {"success": False, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.api_url}/health", headers=self._get_headers())
                if response.status_code == 200:
                    return {"status": "healthy", "api_url": self.api_url, "response_time": response.elapsed.total_seconds()}
                else:
                    return {"status": "unhealthy", "reason": f"API retorno codigo {response.status_code}"}

        except Exception as e:
            return {"status": "unhealthy", "reason": f"Error conectando: {str(e)}"}

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    def _validate_response(self, response) -> Dict[str, Any]:
        if response.status_code == 201:
            result_data = response.json()
            lead_id = result_data.get("id", "unknown")
            log_info("LeadsalesClient", f"Lead creado: {lead_id}")
            return {"success": True, "lead_id": lead_id, "data": result_data}
        elif response.status_code == 409:
            log_info("LeadsalesClient", "Lead ya existe")
            return {"success": False, "error": "Lead ya existe", "code": "DUPLICATE"}
        else:
            error_detail = response.text
            log_error("LeadsalesClient", f"Error API: {response.status_code} - {error_detail}")
            return {"success": False, "error": f"Error HTTP {response.status_code}: {error_detail}"}