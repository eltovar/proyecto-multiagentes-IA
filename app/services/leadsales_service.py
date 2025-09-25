"""Servicio de Leadsales CRM.
    Creacion de leads y trasferencia a asesores humanos
"""

from typing import Dict, Any, Optional
from app.services.leadsales_client import LeadsalesClient

class LeadsalesService:
    """
    Usa LeadsalesClient para toda la logica HTTP.
    """

    def __init__(self):
        self.client = LeadsalesClient()
        self.initialized = False

    def initialize(self) -> bool:
        """Inicializa el servicio verificando configuracion"""
        try:
            # Verificar que el cliente tenga configuracion
            if not self.client.api_url or not self.client.api_token:
                print("[LeadsalesService] Configuracion incompleta")
                return False

            self.initialized = True
            print("[LeadsalesService] Servicio inicializado correctamente")
            return True

        except Exception as e:
            print(f"[LeadsalesService] Error inicializando: {e}")
            return False

    async def create_lead(
        self,
        customer_name: str,
        whatsapp_id: str,
        customer_needs: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crea lead usando cliente HTTP"""
        if not self.initialized:
            print("[LeadsalesService] Servicio no inicializado")
            return {"success": False, "error": "Servicio no inicializado"}

        # Preparar datos del lead
        lead_data = {
            "name": customer_name,
            "whatsapp_id": whatsapp_id,
            "phone": whatsapp_id,
            "needs": customer_needs,
            "source": "WhatsApp_Multiagent_Bot",
            "status": "nuevo",
            "priority": "normal",
            "created_by": "sistema_multiagente"
        }

        # Agregar datos adicionales
        if additional_data:
            lead_data.update(additional_data)

        # Enviar via cliente
        result = await self.client.post_lead(lead_data)

        # Manejar lead duplicado
        if not result["success"] and result.get("code") == "DUPLICATE":
            existing_lead = await self.client.get_lead(whatsapp_id)
            if existing_lead:
                return {
                    "success": True,
                    "lead_id": existing_lead.get("id"),
                    "data": existing_lead,
                    "already_exists": True
                }

        return result

    async def update_lead_status(self, lead_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        """Actualiza estado del lead"""
        if not self.initialized:
            return False

        update_data = {"status": new_status}
        if notes:
            update_data["notes"] = notes

        return await self.client.update_lead(lead_id, update_data)

    async def assign_advisor(self, lead_id: str, advisor_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Asigna asesor especializado al lead"""
        if not self.initialized:
            return {"success": False, "error": "Servicio no inicializado"}

        return await self.client.assign_advisor(lead_id, advisor_criteria)

    async def health_check(self) -> Dict[str, Any]:
        """Verifica salud del servicio"""
        if not self.initialized:
            return {"status": "unhealthy", "reason": "Servicio no inicializado"}

        return await self.client.health_check()

# Singleton para uso global
leadsales_service = LeadsalesService()