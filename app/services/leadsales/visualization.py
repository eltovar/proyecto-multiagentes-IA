"""
Constructor de visualizaciones para CRM.
Responsabilidad: Generar estructuras de preview, simulaciones demo, formatos de display.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CRMVisualizationBuilder:
    """Constructor de visualizaciones para CRM"""

    def build_crm_preview(
        self,
        enriched_data: Dict[str, Any],
        lead_analysis: Optional[Any] = None  # ✅ NUEVO parámetro (PR005)
    ) -> Dict[str, Any]:
        """
        Construye preview visual para CRM (modo producción) con análisis enriquecido.

        Args:
            enriched_data: Datos enriquecidos del lead
            lead_analysis: Análisis integrado del lead (opcional) ✅ NUEVO

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
                "quality_score": enriched_data["quality_score"],
                "priority": self._format_priority_label(enriched_data["priority"]),
                "confidence": f"{int(enriched_data['confidence'] * 100)}%"
            },
            "classification": {
                "tags": enriched_data["tags"],
                "property_type": enriched_data["metadata"].get("property_type", "No especificado"),
                "location": enriched_data["metadata"].get("location", "No especificada")
            },
            "customer_needs": {
                "description": (
                    enriched_data["needs"][:200] + "..."
                    if len(enriched_data["needs"]) > 200
                    else enriched_data["needs"]
                ),
                "urgency": enriched_data["metadata"].get("urgency_level", "low")
            },
            "timestamp": enriched_data["created_at"]
        }

        # Agregar sección de análisis integrado si está disponible ✅ NUEVO (PR005)
        if lead_analysis:
            preview["integrated_analysis"] = {
                "composite_score": lead_analysis.composite_score,
                "conversion_probability": f"{int(lead_analysis.conversion_probability * 100)}%",
                "estimated_value": lead_analysis.estimated_value.upper(),
                "lead_segment": lead_analysis.lead_segment.replace("_", " ").title(),
                "profile": lead_analysis.profile.capitalize(),
                "sophistication": lead_analysis.sophistication_level.capitalize(),
                "priority_numeric": lead_analysis.priority_numeric,
                "key_insights": lead_analysis.key_insights[:3],  # Top 3 insights
                "recommended_actions": lead_analysis.recommended_actions[:3],  # Top 3 actions
                "risk_factors": lead_analysis.risk_factors,
                "analysis_confidence": f"{int(lead_analysis.confidence * 100)}%"
            }

        logger.debug("✅ CRM preview construido (enriquecido)")

        return preview

    def build_demo_simulation(
        self,
        enriched_data: Dict[str, Any],
        lead_analysis: Optional[Any] = None  # ✅ NUEVO parámetro (PR005)
    ) -> Dict[str, Any]:
        """
        Construye simulación de CRM para modo demo con análisis enriquecido.

        Args:
            enriched_data: Datos enriquecidos del lead
            lead_analysis: Análisis integrado del lead (opcional) ✅ NUEVO

        Returns:
            Dict con simulación completa de CRM
        """
        customer_data = {
            "name": enriched_data["name"],
            "whatsapp": enriched_data["whatsapp"],
            "needs": enriched_data["needs"],
            "quality_score": enriched_data["quality_score"],
            "tags": enriched_data["tags"],
            "priority": enriched_data["priority"],
            "source": "whatsapp_bot"
        }

        # Agregar scoring metadata si existe (backward compatibility)
        if "quality_confidence" in enriched_data:
            customer_data["quality_confidence"] = enriched_data["quality_confidence"]
        if "quality_factors" in enriched_data:
            customer_data["quality_factors"] = enriched_data["quality_factors"]
        if "quality_reasoning" in enriched_data:
            customer_data["quality_reasoning"] = enriched_data["quality_reasoning"]

        # Agregar clasificación de cliente si existe
        if "client_classification" in enriched_data:
            customer_data["client_classification"] = enriched_data["client_classification"]

        simulation = {
            "customer_data": customer_data,
            "crm_simulation": {
                "lead_id": f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "nuevo",
                "assigned_to": "Sin asignar",
                "created_at": enriched_data["created_at"],
                "next_followup": self._calculate_next_followup(enriched_data["priority"]),
                "estimated_value": (
                    self._estimate_lead_value(enriched_data)
                    if not lead_analysis
                    else lead_analysis.estimated_value
                ),
                "confidence_level": enriched_data["confidence"]
            },
            "metadata": enriched_data["metadata"],
            "visualization_type": "demo_preview"
        }

        # Agregar análisis integrado completo si está disponible ✅ NUEVO (PR005)
        if lead_analysis:
            simulation["integrated_analysis"] = {
                "composite_score": lead_analysis.composite_score,
                "conversion_probability": lead_analysis.conversion_probability,
                "estimated_value": lead_analysis.estimated_value,
                "priority_adjusted": lead_analysis.priority,
                "priority_numeric": lead_analysis.priority_numeric,
                "lead_segment": lead_analysis.lead_segment,
                "segment_description": self._get_segment_description(lead_analysis.lead_segment),
                "key_insights": lead_analysis.key_insights,
                "recommended_actions": lead_analysis.recommended_actions,
                "risk_factors": lead_analysis.risk_factors,
                "profile": lead_analysis.profile,
                "sophistication": lead_analysis.sophistication_level,
                "analysis_confidence": lead_analysis.confidence,
                "analysis_timestamp": lead_analysis.analysis_timestamp
            }

            # Actualizar prioridad y valor estimado con análisis
            simulation["crm_simulation"]["priority"] = lead_analysis.priority
            simulation["crm_simulation"]["estimated_value"] = lead_analysis.estimated_value
            simulation["customer_data"]["priority"] = lead_analysis.priority

        logger.info("✅ Simulación CRM demo construida (con análisis integrado)")

        return simulation

    def _format_priority_label(self, priority: str) -> str:
        """ Formatea label de prioridad con emoji/color. """
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

    def _get_segment_description(self, segment: str) -> str:
        """Retorna descripción legible del segmento (PR005)"""
        descriptions = {
            "high_value_investor": "Inversionista de Alto Valor",
            "professional_buyer": "Comprador Profesional",
            "entrepreneur_commercial": "Empresario Comercial",
            "family_premium": "Familia Premium",
            "family_casual": "Familia Casual",
            "individual_qualified": "Individual Calificado",
            "exploratory": "Exploratorio",
            "unknown_low_quality": "Desconocido/Baja Calidad"
        }
        return descriptions.get(segment, segment.replace("_", " ").title())
