"""
Constructor de visualizaciones para CRM.
Responsabilidad: Generar estructuras de preview, simulaciones demo, formatos de display.
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CRMVisualizationBuilder:
    """Constructor de visualizaciones para CRM"""

    def build_crm_preview(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye preview visual para CRM (modo producción).

        Args:
            enriched_data: Datos enriquecidos del lead

        Returns:
            Dict con estructura de preview para CRM
        """
        preview = {
            "customer_info": {
                "name": enriched_data["name"],
                "whatsapp": enriched_data["whatsapp"],
                "source": "WhatsApp Bot"
            },
            "lead_quality": {
                "score": enriched_data["quality_score"],
                "priority": self._format_priority_label(enriched_data["priority"]),
                "confidence": f"{int(enriched_data['confidence'] * 100)}%"
            },
            "classification": {
                "tags": enriched_data["tags"],
                "property_type": enriched_data["metadata"].get("property_type", "No especificado"),
                "location": enriched_data["metadata"].get("location", "No especificada")
            },
            "customer_needs": {
                "description": enriched_data["needs"][:200] + "..." if len(enriched_data["needs"]) > 200 else enriched_data["needs"],
                "urgency": enriched_data["metadata"].get("urgency_level", "low")
            },
            "timestamp": enriched_data["created_at"]
        }

        logger.debug("CRM preview construido")

        return preview

    def build_demo_simulation(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye simulación de CRM para modo demo.

        Args:
            enriched_data: Datos enriquecidos del lead

        Returns:
            Dict con simulación completa de CRM
        """
        simulation = {
            "customer_data": {
                "name": enriched_data["name"],
                "whatsapp": enriched_data["whatsapp"],
                "needs": enriched_data["needs"],
                "quality_score": enriched_data["quality_score"],
                "tags": enriched_data["tags"],
                "priority": enriched_data["priority"],
                "source": "whatsapp_bot"
            },
            "crm_simulation": {
                "lead_id": f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "nuevo",
                "assigned_to": "Sin asignar",
                "created_at": enriched_data["created_at"],
                "next_followup": self._calculate_next_followup(enriched_data["priority"]),
                "estimated_value": self._estimate_lead_value(enriched_data),
                "confidence_level": enriched_data["confidence"]
            },
            "metadata": enriched_data["metadata"],
            "visualization_type": "demo_preview"
        }

        logger.info("Simulacion CRM demo construida")

        return simulation

    def _format_priority_label(self, priority: str) -> str:
        """
        Formatea label de prioridad con emoji/color.

        Args:
            priority: Prioridad (ALTA, MEDIA-ALTA, MEDIA, BAJA)

        Returns:
            Label formateado
        """
        priority_labels = {
            "ALTA": "ROJO ALTA",
            "MEDIA-ALTA": "NARANJA MEDIA-ALTA",
            "MEDIA": "AMARILLO MEDIA",
            "BAJA": "VERDE BAJA"
        }

        return priority_labels.get(priority, f"BLANCO {priority}")

    def _calculate_next_followup(self, priority: str) -> str:
        """Calcula fecha de próximo seguimiento según prioridad"""
        from datetime import timedelta

        days_map = {
            "ALTA": 1,
            "MEDIA-ALTA": 2,
            "MEDIA": 3,
            "BAJA": 7
        }

        days = days_map.get(priority, 3)
        next_date = datetime.now() + timedelta(days=days)

        return next_date.strftime("%Y-%m-%d")

    def _estimate_lead_value(self, enriched_data: Dict[str, Any]) -> str:
        """Estima valor del lead según metadata"""
        budget_range = enriched_data["metadata"].get("budget_range")

        value_map = {
            "mas_1000m": "$1.000.000.000+",
            "500m_1000m": "$500.000.000 - $1.000.000.000",
            "200m_500m": "$200.000.000 - $500.000.000",
            "bajo_200m": "< $200.000.000"
        }

        return value_map.get(budget_range, "No estimado")