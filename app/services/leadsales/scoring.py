"""
Integrador de sistema scoring para leads.
Responsabilidad: Calcular quality_score, tags, priority usando estrategias refactorizadas.
"""
import logging
from typing import Dict, Any, List, Optional
from app.services.scoring.strategies import (
    DemoQualityScorer,
    InterestLevelScorer,
    ConversionProbabilityScorer,
    TransactionTypeTagger,
    PropertyTypeTagger,
    UrgencyTagger,
    MetadataTagger,
    UrgencyPriorityClassifier
)

logger = logging.getLogger(__name__)


class LeadScoringIntegrator:
    """
    Integrador del sistema scoring para leads.
    Usa Strategy Pattern para calcular scores, tags y priority.
    """

    def __init__(self):
        """Inicializa scorers, taggers y classifier"""
        self._init_components()

    def _init_components(self):
        """Inicializa componentes de scoring"""
        # Scorers
        self.quality_scorer = DemoQualityScorer()
        self.interest_scorer = InterestLevelScorer()
        self.conversion_scorer = ConversionProbabilityScorer()

        # Taggers
        self.taggers = [
            TransactionTypeTagger(),
            PropertyTypeTagger(),
            UrgencyTagger(),
            MetadataTagger()
        ]

        # Classifier
        self.priority_classifier = UrgencyPriorityClassifier()

        logger.debug("[LeadScoringIntegrator] Inicializado con 3 scorers, 4 taggers, 1 classifier")

    def score_lead(self, customer_needs: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calcula scoring completo para un lead.

        Args:
            customer_needs: Descripción de necesidades del cliente
            additional_data: Metadata adicional (location, budget, etc.)

        Returns:
            Dict con quality_score, interest_score, conversion_probability, tags, priority, confidence, reasoning
        """
        lead_data = {
            "customer_needs": customer_needs,
            "additional_data": additional_data or {}
        }

        # 1. Quality Score (keyword-based, 0-100)
        quality_result = self.quality_scorer.score(lead_data)

        # 2. Interest Score (urgency + specificity, 0-1)
        interest_result = self.interest_scorer.score(lead_data)

        # 3. Conversion Probability (metadata-based, 0-1)
        conversion_result = self.conversion_scorer.score(lead_data)

        # 4. Tags (transaction, property, urgency, location)
        all_tags = []
        for tagger in self.taggers:
            all_tags.extend(tagger.generate_tags(lead_data))

        # Eliminar duplicados manteniendo orden
        unique_tags = list(dict.fromkeys(all_tags))

        # Limitar a máximo 5 tags (las primeras son las más importantes por orden de taggers)
        unique_tags = unique_tags[:5]

        # 5. Priority Classification (ALTA, MEDIA-ALTA, MEDIA, BAJA)
        priority = self.priority_classifier.classify(lead_data)

        # 6. Combinar resultados
        scoring_result = self._combine_scoring_results(
            quality_result,
            interest_result,
            conversion_result,
            unique_tags,
            priority
        )

        # Extraer solo la parte corta del priority (antes del " - ")
        priority_short = priority.split(" - ")[0] if " - " in priority else priority

        logger.info(
            f"[LeadsalesService] Lead scored: quality={scoring_result['quality_score']}, "
            f"tags={len(unique_tags)}, priority={priority_short}"
        )

        return scoring_result

    def _combine_scoring_results(
        self,
        quality_result,
        interest_result,
        conversion_result,
        tags: List[str],
        priority: str
    ) -> Dict[str, Any]:
        """
        Combina resultados de múltiples scorers en estructura unificada.
        """
        # Calcular confianza promedio
        avg_confidence = (
            quality_result.confidence +
            interest_result.confidence +
            conversion_result.confidence
        ) / 3

        # Generar reasoning combinado
        reasoning_parts = [
            f"Quality: {quality_result.reasoning}",
            f"Interest: {interest_result.reasoning}",
            f"Conversion: {conversion_result.reasoning}"
        ]
        combined_reasoning = " | ".join(reasoning_parts)

        return {
            "quality_score": int(quality_result.score),
            "interest_score": round(float(interest_result.score) / 100.0, 2),  # Normalizar 0-100 a 0-1
            "conversion_probability": round(float(conversion_result.score) / 100.0, 2),  # Normalizar 0-100 a 0-1
            "tags": tags,
            "priority": priority,
            "confidence": round(avg_confidence, 2),
            "reasoning": combined_reasoning,
            "scoring_metadata": {
                "quality": {
                    "score": int(quality_result.score),
                    "confidence": round(quality_result.confidence, 2),
                    "reasoning": quality_result.reasoning,
                    "factors": quality_result.factors
                },
                "interest": {
                    "score": round(float(interest_result.score) / 100.0, 2),
                    "confidence": round(interest_result.confidence, 2),
                    "reasoning": interest_result.reasoning,
                    "factors": interest_result.factors
                },
                "conversion": {
                    "score": round(float(conversion_result.score) / 100.0, 2),
                    "confidence": round(conversion_result.confidence, 2),
                    "reasoning": conversion_result.reasoning,
                    "factors": conversion_result.factors
                },
                # Aliases para backward compatibility con tests antiguos
                "quality_factors": quality_result.factors,
                "quality_confidence": round(quality_result.confidence, 2),
                "quality_reasoning": quality_result.reasoning,
                "tags_count": len(tags),
                "priority": priority
            }
        }
