"""
Extractor y enriquecedor de metadata para leads.
Responsabilidad: Normalizar datos, extraer información estructurada, enriquecer con contexto.
"""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LeadMetadataExtractor:
    """Extrae y enriquece metadata de leads"""

    def extract_metadata(self, customer_needs: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae metadata estructurada desde texto no estructurado.

        Args:
            customer_needs: Texto con necesidades del cliente
            additional_data: Datos adicionales (location, budget, etc.)

        Returns:
            Dict con metadata extraída (location, budget_range, property_type, etc.)
        """
        metadata = {}

        # 1. Extraer ubicación
        location = self._extract_location(customer_needs, additional_data)
        if location:
            metadata["location"] = location

        # 2. Extraer rango de presupuesto
        budget_range = self._extract_budget_range(customer_needs)
        if budget_range:
            metadata["budget_range"] = budget_range

        # 3. Extraer tipo de propiedad
        property_type = self._extract_property_type(customer_needs)
        if property_type:
            metadata["property_type"] = property_type

        # 4. Extraer número de habitaciones
        rooms = self._extract_rooms(customer_needs)
        if rooms:
            metadata["rooms"] = rooms

        # 5. Detectar urgencia temporal
        urgency = self._detect_urgency(customer_needs)
        metadata["urgency_level"] = urgency

        # 6. Timestamp de extracción
        metadata["extracted_at"] = datetime.now().isoformat()

        logger.debug(f"Metadata extraida: {len(metadata)} campos")

        return metadata

    def enrich_customer_data(
        self,
        customer_name: str,
        whatsapp: str,
        customer_needs: str,
        scoring_result: Dict[str, Any],
        metadata: Dict[str, Any],
        classification_result: Optional[Any] = None,
        lead_analysis: Optional[Any] = None  # ✅ NUEVO (PR005)
    ) -> Dict[str, Any]:
        """
        Enriquece datos del cliente con scoring, metadata, clasificación y análisis.

        Args:
            customer_name: Nombre del cliente
            whatsapp: Número de WhatsApp
            customer_needs: Necesidades descritas
            scoring_result: Resultado de scoring
            metadata: Metadata extraída
            classification_result: Clasificación de cliente (opcional)
            lead_analysis: Análisis integrado del lead (opcional) ✅ NUEVO

        Returns:
            Dict con datos enriquecidos listos para CRM
        """
        # Normalizar teléfono
        normalized_phone = self._normalize_phone(whatsapp)

        # Construir estructura enriquecida
        enriched_data = {
            "name": customer_name,
            "whatsapp": normalized_phone,
            "needs": customer_needs,
            "source": "whatsapp_bot",

            # Scoring
            "quality_score": scoring_result["quality_score"],
            "priority": scoring_result["priority"],
            "tags": scoring_result["tags"],
            "confidence": scoring_result["confidence"],

            # Metadata
            "metadata": metadata,

            # Timestamps
            "created_at": datetime.now().isoformat(),
        }

        # Agregar scoring_metadata si existe (para backward compatibility con tests)
        if "scoring_metadata" in scoring_result:
            # Agregar campos de metadata anidados al nivel raíz para tests antiguos
            enriched_data["quality_confidence"] = scoring_result["scoring_metadata"]["quality"]["confidence"]
            enriched_data["quality_factors"] = scoring_result["scoring_metadata"]["quality_factors"]
            enriched_data["quality_reasoning"] = scoring_result["scoring_metadata"]["quality_reasoning"]

        # Agregar clasificación de cliente si está disponible
        if classification_result:
            enriched_data["client_classification"] = {
                "profile": classification_result.profile,
                "sophistication_level": classification_result.sophistication_level,
                "confidence": classification_result.confidence,
                "reasoning": classification_result.reasoning,
                "detected_keywords": classification_result.detected_keywords,
                "profession_explicit": classification_result.profession_explicit,
                "classification_method": classification_result.classification_method,
                "cost_usd": classification_result.cost_usd,
                "latency_ms": classification_result.latency_ms
            }

        # Agregar análisis integrado si está disponible ✅ NUEVO (PR005)
        if lead_analysis:
            enriched_data["lead_analysis"] = {
                "composite_score": lead_analysis.composite_score,
                "conversion_probability": lead_analysis.conversion_probability,
                "estimated_value": lead_analysis.estimated_value,
                "priority": lead_analysis.priority,
                "priority_numeric": lead_analysis.priority_numeric,
                "lead_segment": lead_analysis.lead_segment,
                "key_insights": lead_analysis.key_insights,
                "recommended_actions": lead_analysis.recommended_actions,
                "risk_factors": lead_analysis.risk_factors,
                "confidence": lead_analysis.confidence
            }

            logger.info(
                f"✅ Datos enriquecidos para: {customer_name} "
                f"(Composite Score: {lead_analysis.composite_score:.1f}/100, "
                f"Segment: {lead_analysis.lead_segment})"
            )
        else:
            logger.info(
                f"✅ Datos enriquecidos para: {customer_name} "
                f"(Quality: {scoring_result['quality_score']}/100, sin análisis integrado)"
            )

        return enriched_data

    def _extract_location(self, text: str, additional_data: Dict[str, Any]) -> Optional[str]:
        """Extrae ubicación desde texto o additional_data"""
        # Prioridad 1: additional_data
        if "location" in additional_data:
            return additional_data["location"]

        # Prioridad 2: Detectar ciudades colombianas en texto
        cities = ["medellin", "bogota", "cali", "barranquilla", "cartagena", "bucaramanga", "poblado", "envigado"]
        text_lower = text.lower()

        for city in cities:
            if city in text_lower:
                return city.capitalize()

        return None

    def _extract_budget_range(self, text: str) -> Optional[str]:
        """Extrae rango de presupuesto desde texto"""
        # Buscar menciones de millones
        pattern = r'(\d+)\s*millones?'
        match = re.search(pattern, text.lower())

        if match:
            amount = int(match.group(1))

            if amount < 200:
                return "bajo_200m"
            elif amount < 500:
                return "200m_500m"
            elif amount < 1000:
                return "500m_1000m"
            else:
                return "mas_1000m"

        return None

    def _extract_property_type(self, text: str) -> Optional[str]:
        """Extrae tipo de propiedad desde texto"""
        text_lower = text.lower()

        if "apartamento" in text_lower or "apto" in text_lower:
            return "apartamento"
        elif "casa" in text_lower:
            return "casa"
        elif "local" in text_lower:
            return "local_comercial"
        elif "oficina" in text_lower:
            return "oficina"
        elif "lote" in text_lower or "terreno" in text_lower:
            return "lote"

        return None

    def _extract_rooms(self, text: str) -> Optional[int]:
        """Extrae número de habitaciones"""
        patterns = [
            r'(\d+)\s*habitacion',
            r'(\d+)\s*cuartos?',
            r'(\d+)\s*hab',
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))

        return None

    def _detect_urgency(self, text: str) -> str:
        """Detecta nivel de urgencia desde texto"""
        text_lower = text.lower()

        high_urgency_keywords = ["urgente", "ya", "inmediato", "rapido", "pronto", "hoy"]
        medium_urgency_keywords = ["esta semana", "pronto", "necesito"]

        for keyword in high_urgency_keywords:
            if keyword in text_lower:
                return "high"

        for keyword in medium_urgency_keywords:
            if keyword in text_lower:
                return "medium"

        return "low"

    def _normalize_phone(self, whatsapp: str) -> str:
        """
        Normaliza número de WhatsApp a formato internacional.

        Args:
            whatsapp: Número en cualquier formato

        Returns:
            Número normalizado (ej: +573001234567)
        """
        # Eliminar caracteres no numéricos
        digits = re.sub(r'\D', '', whatsapp)

        # Agregar código país Colombia si no existe
        if not digits.startswith("57") and len(digits) == 10:
            digits = "57" + digits

        # Agregar + si no existe
        if not digits.startswith("+"):
            digits = "+" + digits

        return digits
