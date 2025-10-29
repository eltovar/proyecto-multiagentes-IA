"""
Analizador integrado de leads.
Responsabilidad: Combinar scoring + clasificación para generar insights y métricas compuestas.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LeadAnalysis:
    """Análisis completo de lead (scoring + clasificación + insights)"""
    # Scores
    quality_score: int  # 0-100 (de scoring)
    composite_score: float  # 0-100 (scoring + clasificación + sofisticación)
    conversion_probability: float  # 0-1
    estimated_value: str  # "alto|medio|bajo"

    # Classification
    profile: str
    sophistication_level: str

    # Priority
    priority: str  # ALTA, MEDIA-ALTA, MEDIA, BAJA
    priority_numeric: int  # 1-10 para ordenamiento

    # Insights
    lead_segment: str  # "high_value_investor", "family_casual", etc.
    recommended_actions: List[str]
    key_insights: List[str]
    risk_factors: List[str]

    # Metadata
    analysis_timestamp: str
    confidence: float  # 0-1


class LeadAnalyzer:
    """
    Analizador integrado de leads.
    Combina scoring + clasificación para generar insights accionables.
    """

    # Matriz de Lead Composite Score
    # Formula: base_quality * profile_multiplier * sophistication_multiplier
    PROFILE_MULTIPLIERS = {
        "inversionista": 1.3,      # Mayor valor comercial
        "arquitecto": 1.25,        # Profesional con red de contactos
        "corredor": 1.2,           # Puede traer múltiples clientes
        "ingeniero": 1.15,         # Profesional con capacidad económica
        "empresario": 1.3,         # Alto valor, propiedades comerciales
        "familia": 1.0,            # Valor estándar
        "individual": 0.9,         # Menor valor promedio
        "desconocido": 0.8         # Sin información suficiente
    }

    SOPHISTICATION_MULTIPLIERS = {
        "alto": 1.2,    # Conoce el mercado, decisión más rápida
        "medio": 1.0,   # Estándar
        "bajo": 0.85    # Requiere más educación, proceso más largo
    }

    # Segmentos de leads
    LEAD_SEGMENTS = {
        "high_value_investor": {
            "conditions": lambda p, s, q: p == "inversionista" and s == "alto" and q >= 70,
            "description": "Inversionista profesional de alto valor",
            "estimated_ltv": "$50,000+",
            "priority_boost": 2
        },
        "professional_buyer": {
            "conditions": lambda p, s, q: p in ["arquitecto", "ingeniero", "corredor"] and q >= 60,
            "description": "Comprador profesional con red de contactos",
            "estimated_ltv": "$30,000+",
            "priority_boost": 1
        },
        "entrepreneur_commercial": {
            "conditions": lambda p, s, q: p == "empresario" and q >= 65,
            "description": "Empresario buscando propiedad comercial",
            "estimated_ltv": "$40,000+",
            "priority_boost": 1
        },
        "family_premium": {
            "conditions": lambda p, s, q: p == "familia" and s in ["alto", "medio"] and q >= 70,
            "description": "Familia con alta intención de compra",
            "estimated_ltv": "$25,000+",
            "priority_boost": 1
        },
        "family_casual": {
            "conditions": lambda p, s, q: p == "familia" and q < 70,
            "description": "Familia en etapa exploratoria",
            "estimated_ltv": "$15,000",
            "priority_boost": 0
        },
        "individual_qualified": {
            "conditions": lambda p, s, q: p == "individual" and q >= 65,
            "description": "Comprador individual calificado",
            "estimated_ltv": "$20,000",
            "priority_boost": 0
        },
        "exploratory": {
            "conditions": lambda p, s, q: s == "bajo" and q < 50,
            "description": "Lead en etapa muy temprana",
            "estimated_ltv": "$5,000",
            "priority_boost": -1
        },
        "unknown_low_quality": {
            "conditions": lambda p, s, q: p == "desconocido" or q < 40,
            "description": "Lead con información insuficiente",
            "estimated_ltv": "$3,000",
            "priority_boost": -1
        }
    }

    def analyze(
        self,
        scoring_result: Dict[str, Any],
        classification_result: Any,
        metadata: Dict[str, Any]
    ) -> LeadAnalysis:
        """
        Analiza lead combinando scoring + clasificación.

        Args:
            scoring_result: Output de LeadScoringIntegrator
            classification_result: Output de ClientClassifier (puede ser dict o objeto)
            metadata: Metadata extraída del lead

        Returns:
            LeadAnalysis con scoring compuesto e insights
        """
        # Normalizar classification_result (puede ser objeto o dict)
        if hasattr(classification_result, 'profile'):
            # Es un objeto ClientClassificationResult
            classification_dict = {
                "profile": classification_result.profile,
                "sophistication_level": classification_result.sophistication_level,
                "confidence": classification_result.confidence,
                "classification_method": classification_result.classification_method
            }
        else:
            # Ya es un dict
            classification_dict = classification_result

        # Extraer valores base
        quality_score = scoring_result["quality_score"]
        profile = classification_dict["profile"]
        sophistication = classification_dict["sophistication_level"]
        base_priority = scoring_result["priority"]

        # 1. Calcular Composite Score
        composite_score = self._calculate_composite_score(
            quality_score,
            profile,
            sophistication
        )

        # 2. Calcular probabilidad de conversión mejorada
        conversion_probability = self._calculate_conversion_probability(
            quality_score,
            profile,
            sophistication,
            metadata
        )

        # 3. Determinar segmento de lead
        segment = self._determine_segment(profile, sophistication, quality_score)

        # 4. Ajustar prioridad según perfil
        adjusted_priority, priority_numeric = self._adjust_priority(
            base_priority,
            segment
        )

        # 5. Estimar valor del lead
        estimated_value = self._estimate_lead_value(segment, composite_score)

        # 6. Generar insights accionables
        insights = self._generate_insights(
            quality_score,
            profile,
            sophistication,
            segment,
            metadata
        )

        # 7. Recomendar acciones
        recommended_actions = self._recommend_actions(segment, sophistication, metadata)

        # 8. Identificar factores de riesgo
        risk_factors = self._identify_risk_factors(
            quality_score,
            classification_dict,
            metadata
        )

        # 9. Calcular confianza del análisis
        analysis_confidence = self._calculate_analysis_confidence(
            scoring_result,
            classification_dict
        )

        logger.info(
            f"✅ Lead analizado: Segment={segment}, Composite Score={composite_score:.1f}, "
            f"Priority={adjusted_priority}, Conversion Prob={conversion_probability:.2f}"
        )

        return LeadAnalysis(
            quality_score=quality_score,
            composite_score=composite_score,
            conversion_probability=conversion_probability,
            estimated_value=estimated_value,
            profile=profile,
            sophistication_level=sophistication,
            priority=adjusted_priority,
            priority_numeric=priority_numeric,
            lead_segment=segment,
            recommended_actions=recommended_actions,
            key_insights=insights,
            risk_factors=risk_factors,
            analysis_timestamp=datetime.now().isoformat(),
            confidence=analysis_confidence
        )

    def _calculate_composite_score(
        self,
        quality_score: int,
        profile: str,
        sophistication: str
    ) -> float:
        """
        Calcula Lead Composite Score.

        Formula:
        composite = quality_score * profile_multiplier * sophistication_multiplier

        Ejemplo:
        - Quality: 80/100
        - Profile: inversionista (1.3x)
        - Sophistication: alto (1.2x)
        - Composite: 80 * 1.3 * 1.2 = 124.8 → cap a 100 → 100
        """
        profile_mult = self.PROFILE_MULTIPLIERS.get(profile, 1.0)
        soph_mult = self.SOPHISTICATION_MULTIPLIERS.get(sophistication, 1.0)

        composite = quality_score * profile_mult * soph_mult

        # Cap a 100
        composite = min(100, composite)

        return round(composite, 1)

    def _calculate_conversion_probability(
        self,
        quality_score: int,
        profile: str,
        sophistication: str,
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calcula probabilidad de conversión mejorada.

        Factores:
        - Quality score base
        - Profile (inversionistas convierten más)
        - Sophistication (altos deciden más rápido)
        - Urgency (urgentes convierten más)
        - Budget defined (presupuesto claro = más probable)
        """
        # Base: quality_score / 100
        base_prob = quality_score / 100

        # Ajuste por profile
        profile_boost = {
            "inversionista": 0.15,
            "arquitecto": 0.10,
            "empresario": 0.12,
            "corredor": 0.08,
            "ingeniero": 0.08,
            "familia": 0.05,
            "individual": 0.0,
            "desconocido": -0.1
        }.get(profile, 0)

        # Ajuste por sophistication
        soph_boost = {
            "alto": 0.10,
            "medio": 0.05,
            "bajo": -0.05
        }.get(sophistication, 0)

        # Ajuste por urgencia
        urgency_boost = 0.0
        if metadata.get("urgency_level") == "high":
            urgency_boost = 0.12
        elif metadata.get("urgency_level") == "medium":
            urgency_boost = 0.06

        # Ajuste por presupuesto definido
        budget_boost = 0.08 if metadata.get("budget_range") else 0.0

        # Calcular probabilidad final
        conversion_prob = base_prob + profile_boost + soph_boost + urgency_boost + budget_boost

        # Cap entre 0 y 1
        conversion_prob = max(0.0, min(1.0, conversion_prob))

        return round(conversion_prob, 2)

    def _determine_segment(
        self,
        profile: str,
        sophistication: str,
        quality_score: int
    ) -> str:
        """Determina segmento de lead según condiciones"""
        for segment_name, segment_config in self.LEAD_SEGMENTS.items():
            if segment_config["conditions"](profile, sophistication, quality_score):
                return segment_name

        # Default
        return "unknown_low_quality"

    def _adjust_priority(
        self,
        base_priority: str,
        segment: str
    ) -> tuple:
        """
        Ajusta prioridad según segmento.

        Returns:
            Tuple (priority_str, priority_numeric)
        """
        # Mapeo de prioridad a numérico
        priority_map = {
            "ALTA": 8,
            "MEDIA-ALTA": 6,
            "MEDIA": 4,
            "BAJA": 2
        }

        # Extraer solo la parte antes del " - " si existe
        base_priority_clean = base_priority.split(" - ")[0] if " - " in base_priority else base_priority

        base_numeric = priority_map.get(base_priority_clean, 4)

        # Aplicar boost del segmento
        segment_config = self.LEAD_SEGMENTS.get(segment, {})
        priority_boost = segment_config.get("priority_boost", 0)

        adjusted_numeric = base_numeric + priority_boost
        adjusted_numeric = max(1, min(10, adjusted_numeric))  # Cap entre 1-10

        # Convertir de vuelta a string
        if adjusted_numeric >= 8:
            adjusted_str = "ALTA"
        elif adjusted_numeric >= 6:
            adjusted_str = "MEDIA-ALTA"
        elif adjusted_numeric >= 4:
            adjusted_str = "MEDIA"
        else:
            adjusted_str = "BAJA"

        return adjusted_str, adjusted_numeric

    def _estimate_lead_value(self, segment: str, composite_score: float) -> str:
        """Estima valor del lead (alto, medio, bajo)"""
        segment_config = self.LEAD_SEGMENTS.get(segment, {})
        estimated_ltv = segment_config.get("estimated_ltv", "$10,000")

        # Categorizar por LTV
        if "$40,000" in estimated_ltv or "$50,000" in estimated_ltv:
            return "alto"
        elif "$20,000" in estimated_ltv or "$25,000" in estimated_ltv or "$30,000" in estimated_ltv:
            return "medio"
        else:
            return "bajo"

    def _generate_insights(
        self,
        quality_score: int,
        profile: str,
        sophistication: str,
        segment: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Genera insights clave sobre el lead"""
        insights = []

        # Insight de segmento
        segment_config = self.LEAD_SEGMENTS.get(segment, {})
        insights.append(f"📊 {segment_config.get('description', 'Lead estándar')}")

        # Insight de calidad
        if quality_score >= 80:
            insights.append("⭐ Lead de calidad excepcional")
        elif quality_score >= 60:
            insights.append("✅ Lead de buena calidad")
        elif quality_score < 40:
            insights.append("⚠️ Lead de baja calidad, requiere calificación")

        # Insight de perfil
        if profile == "inversionista" and sophistication == "alto":
            insights.append("💰 Inversionista profesional: Priorizar respuesta técnica y ROI")
        elif profile == "arquitecto":
            insights.append("🏗️ Profesional de diseño: Enfatizar espacios y acabados")
        elif profile == "familia" and metadata.get("rooms"):
            insights.append(f"👨‍👩‍👧‍👦 Familia buscando {metadata['rooms']} habitaciones")

        # Insight de urgencia
        if metadata.get("urgency_level") == "high":
            insights.append("🔥 Alta urgencia: Contactar en menos de 24h")

        # Insight de ubicación
        if metadata.get("location"):
            insights.append(f"📍 Interesado en zona: {metadata['location']}")

        # Insight de presupuesto
        if metadata.get("budget_range"):
            budget_labels = {
                "bajo_200m": "< $200M",
                "200m_500m": "$200M - $500M",
                "500m_1000m": "$500M - $1.000M",
                "mas_1000m": "> $1.000M"
            }
            budget_label = budget_labels.get(metadata["budget_range"], "No especificado")
            insights.append(f"💵 Presupuesto estimado: {budget_label}")

        return insights

    def _recommend_actions(
        self,
        segment: str,
        sophistication: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Recomienda acciones específicas para el lead"""
        actions = []

        # Acciones por segmento
        if segment == "high_value_investor":
            actions.append("Asignar a agente senior especializado en inversión")
            actions.append("Preparar análisis de ROI y comparables de mercado")
            actions.append("Agendar reunión presencial en menos de 48h")

        elif segment == "professional_buyer":
            actions.append("Responder con información técnica detallada")
            actions.append("Incluir planos y especificaciones en comunicación")
            actions.append("Ofrecer tour personalizado de propiedades")

        elif segment == "family_casual":
            actions.append("Enviar opciones variadas según presupuesto")
            actions.append("Explicar proceso de compra paso a paso")
            actions.append("Seguimiento en 3-5 días")

        elif segment == "exploratory":
            actions.append("Enviar contenido educativo sobre proceso de compra")
            actions.append("Incluir en campaña de nurturing automatizada")
            actions.append("Seguimiento en 7-10 días")

        # Acción por sofisticación
        if sophistication == "bajo":
            actions.append("Acompañar con guía de compra para principiantes")

        # Acción por urgencia
        if metadata.get("urgency_level") == "high":
            actions.append("⚡ URGENTE: Responder dentro de las próximas 2 horas")

        return actions

    def _identify_risk_factors(
        self,
        quality_score: int,
        classification_result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Identifica factores de riesgo del lead"""
        risks = []

        # Riesgo por baja calidad
        if quality_score < 40:
            risks.append("⚠️ Quality score bajo: Lead poco calificado")

        # Riesgo por baja confianza en clasificación
        if classification_result.get("confidence", 1.0) < 0.5:
            risks.append("⚠️ Baja confianza en clasificación de perfil")

        # Riesgo por falta de información
        if not metadata.get("location"):
            risks.append("📍 Sin ubicación especificada")

        if not metadata.get("budget_range"):
            risks.append("💵 Sin presupuesto definido")

        # Riesgo por perfil desconocido
        if classification_result.get("profile") == "desconocido":
            risks.append("❓ Perfil de cliente desconocido: Requiere más calificación")

        # Riesgo por método de clasificación (si fue fallback)
        if classification_result.get("classification_method") == "rules_fallback":
            risks.append("⚠️ Clasificación por fallback: Verificar manualmente")

        return risks

    def _calculate_analysis_confidence(
        self,
        scoring_result: Dict[str, Any],
        classification_result: Dict[str, Any]
    ) -> float:
        """Calcula confianza general del análisis"""
        scoring_confidence = scoring_result.get("confidence", 0.8)
        classification_confidence = classification_result.get("confidence", 0.8)

        # Promedio ponderado (scoring 60%, clasificación 40%)
        overall_confidence = (scoring_confidence * 0.6) + (classification_confidence * 0.4)

        return round(overall_confidence, 2)