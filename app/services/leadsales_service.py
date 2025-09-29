"""Servicio de Leadsales CRM.
    Creacion de leads y trasferencia a asesores humanos
"""

from typing import Dict, Any, Optional, List
from app.services.leadsales_client import LeadsalesClient
from app.config import settings

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

        # DEMO MODE DETECTION
        if self._is_demo_mode():
            return await self._create_mock_lead(customer_name, whatsapp_id, customer_needs, additional_data)

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

    def _is_demo_mode(self) -> bool:
        """Detecta si está en modo demo por token de prueba"""
        demo_indicators = [
            "test_token", "demo_token", "mock_token",
            "https://api.leadsales.test/", "localhost"
        ]
        api_url = settings.leadsales_api_url.lower()
        api_token = settings.leadsales_api_token.lower()

        return any(indicator in api_url or indicator in api_token
                  for indicator in demo_indicators)

    async def _create_mock_lead(self, customer_name: str, whatsapp_id: str,
                               customer_needs: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula creación exitosa de lead con data estructurada"""
        import uuid
        import time

        mock_lead_id = f"DEMO-{uuid.uuid4().hex[:8]}"

        return {
            "success": True,
            "lead_id": mock_lead_id,
            "demo_mode": True,
            "customer_data": {
                "name": customer_name,
                "whatsapp": whatsapp_id,
                "needs": customer_needs,
                "quality_score": self._calculate_demo_quality_score(customer_needs),
                "tags": self._generate_demo_tags(customer_needs, additional_data),
                "priority": self._determine_demo_priority(customer_needs),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "crm_simulation": self._generate_crm_preview(customer_name, customer_needs)
        }

    def _calculate_demo_quality_score(self, needs: str) -> int:
        """Calcula score de calidad basado en keywords"""
        quality_keywords = {
            "high": ["comprar", "vender", "presupuesto", "millones", "urgente", "casa", "apartamento"],
            "medium": ["arrendar", "alquilar", "busco", "necesito", "zona"],
            "low": ["información", "consulta", "pregunta"]
        }

        needs_lower = needs.lower()
        high_score = sum(2 for keyword in quality_keywords["high"] if keyword in needs_lower)
        medium_score = sum(1 for keyword in quality_keywords["medium"] if keyword in needs_lower)

        total_score = min(100, max(30, (high_score * 20) + (medium_score * 10) + 40))
        return total_score

    def _generate_demo_tags(self, needs: str, additional_data: Dict) -> List[str]:
        """Genera tags automáticas para el CRM"""
        tags = []
        needs_lower = needs.lower()

        # Tags por tipo transacción
        if any(word in needs_lower for word in ["comprar", "compra"]):
            tags.append("COMPRA")
        if any(word in needs_lower for word in ["vender", "venta"]):
            tags.append("VENTA")
        if any(word in needs_lower for word in ["arrendar", "arriendo"]):
            tags.append("ARRIENDO")

        # Tags por tipo propiedad
        if "casa" in needs_lower:
            tags.append("CASA")
        if any(word in needs_lower for word in ["apartamento", "apto"]):
            tags.append("APARTAMENTO")

        # Tags por urgencia/presupuesto
        if any(word in needs_lower for word in ["urgente", "rápido", "pronto"]):
            tags.append("URGENTE")
        if any(word in needs_lower for word in ["millones", "presupuesto"]):
            tags.append("PRESUPUESTO_DEFINIDO")

        # Tags por información adicional
        if additional_data and additional_data.get("tiene_solicitud_libertador"):
            tags.append("LIBERTADOR_APROBADO")

        return tags[:5]  # Máximo 5 tags

    def _determine_demo_priority(self, needs: str) -> str:
        """Determina prioridad del lead para demo"""
        needs_lower = needs.lower()

        if any(word in needs_lower for word in ["urgente", "rápido", "ya", "inmediato"]):
            return "ALTA - Contacto inmediato"
        elif any(word in needs_lower for word in ["presupuesto", "millones", "definido"]):
            return "MEDIA-ALTA - Contacto 24h"
        elif any(word in needs_lower for word in ["información", "consulta"]):
            return "MEDIA - Contacto 48h"
        else:
            return "MEDIA - Contacto 24-48h"

    def _generate_crm_preview(self, customer_name: str, needs: str) -> Dict[str, str]:
        """Genera preview de cómo se vería en el CRM real"""
        return {
            "Pipeline": "Leads Entrantes > Contacto Inicial",
            "Asesor Asignado": "Por asignar automáticamente",
            "Fuente": "WhatsApp Business - Bot Sofia",
            "Estado": "Nuevo - Requiere contacto 24h",
            "Seguimiento": "Llamada + WhatsApp oficial",
            "Notas": f"Lead capturado por IA. Cliente: {customer_name}. Interés: {needs[:50]}...",
            "Próxima Acción": f"Contactar {customer_name} en próximas 2 horas"
        }

# Singleton para uso global
leadsales_service = LeadsalesService()