''' Scoring Strategies '''

from typing import Dict, Any, List
from .base import LeadScorer, LeadTagger, PriorityClassifier, ScoringResult

class DemoQualityScorer(LeadScorer):
    """Estrategia que calcula puntaje del 0 al 100"""
    def __init__(self):
        super().__init__("DemoQualityScorer")
        self.quality_keywords = {
            "high": ["comprar", "vender", "presupuesto", "millones", "urgente", "casa", "apartamento"],
            "medium": ["arrendar", "alquilar", "busco", "necesito", "zona"],
            "low": ["informacion", "consulta", "pregunta"]
        }

    def score(self, lead_data: Dict[str, Any]) -> ScoringResult:
        """Calcula quality score del lead"""
        needs = lead_data.get("customer_needs", "")
        needs_lower = needs.lower()

        # Calcular score por nivel de keywords
        high_score = sum(2 for kw in self.quality_keywords["high"] if kw in needs_lower)
        medium_score = sum(1 for kw in self.quality_keywords["medium"] if kw in needs_lower)

        # Score total: base 40, max 100
        total_score = min(100, max(30, (high_score * 20) + (medium_score * 10) + 40))

        # Factores que contribuyeron
        factors = {
            "high_keywords": high_score,
            "medium_keywords": medium_score,
            "base_score": 40
        }

        return ScoringResult(
            score=float(total_score),
            confidence=0.8 if high_score > 0 else 0.6,
            factors=factors,
            tags=[],
            reasoning=f"Score basado en {high_score} keywords high-value y {medium_score} medium-value"
        )


class InterestLevelScorer(LeadScorer):
    def __init__(self):
        super().__init__("InterestLevelScorer")
        self.urgency_words = ["urgente", "rapido", "ya", "inmediato", "pronto"]
        self.specificity_words = ["habitaciones", "banos", "metros", "zona", "presupuesto"]

    def score(self, lead_data: Dict[str, Any]) -> ScoringResult:
        """Calcula interest level score"""
        needs = lead_data.get("customer_needs", "").lower()

        urgency_count = sum(1 for word in self.urgency_words if word in needs)
        specificity_count = sum(1 for word in self.specificity_words if word in needs)

        # Score: urgencia vale mas (60%), especificidad (40%)
        score = (urgency_count * 30) + (specificity_count * 10)
        score = min(100, max(20, score))

        return ScoringResult(
            score=float(score),
            confidence=0.75,
            factors={
                "urgency_indicators": urgency_count,
                "specificity_indicators": specificity_count
            },
            tags=[],
            reasoning=f"Interes alto por urgencia ({urgency_count}) y especificidad ({specificity_count})"
        )


class ConversionProbabilityScorer(LeadScorer):
    def __init__(self):
        super().__init__("ConversionProbabilityScorer")

    def score(self, lead_data: Dict[str, Any]) -> ScoringResult:
        """Calcula conversion probability"""
        additional_data = lead_data.get("additional_data", {})

        score = 50.0  # Base score

        # Factores positivos
        if additional_data.get("tiene_solicitud_libertador"):
            score += 20
        if additional_data.get("fecha_necesidad"):
            score += 15
        if not additional_data.get("tiene_contrato_inmobiliaria"):
            score += 15

        score = min(100, score)

        return ScoringResult(
            score=score,
            confidence=0.85,
            factors={
                "libertador_approved": additional_data.get("tiene_solicitud_libertador", False),
                "date_defined": bool(additional_data.get("fecha_necesidad")),
                "no_current_contract": not additional_data.get("tiene_contrato_inmobiliaria", False)
            },
            tags=[],
            reasoning="Probabilidad basada en datos estructurados del flujo"
        )

# Tagger Strategies
class TransactionTypeTagger(LeadTagger):
    
    def __init__(self):
        super().__init__("TransactionTypeTagger")

    def generate_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """Genera tags de tipo de transaccion"""
        tags = []
        needs = lead_data.get("customer_needs", "").lower()

        if any(word in needs for word in ["comprar", "compra"]):
            tags.append("COMPRA")
        if any(word in needs for word in ["vender", "venta"]):
            tags.append("VENTA")
        if any(word in needs for word in ["arrendar", "arriendo"]):
            tags.append("ARRIENDO")

        return tags

class PropertyTypeTagger(LeadTagger):
    """Genera tags por tipo de propiedad (CASA, APARTAMENTO)"""
    def __init__(self):
        super().__init__("PropertyTypeTagger")

    def generate_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """Genera tags de tipo de propiedad"""
        tags = []
        needs = lead_data.get("customer_needs", "").lower()

        if "casa" in needs:
            tags.append("CASA")
        if any(word in needs for word in ["apartamento", "apto"]):
            tags.append("APARTAMENTO")
        if "local" in needs:
            tags.append("LOCAL_COMERCIAL")

        return tags


class UrgencyTagger(LeadTagger):
    """Genera tags por urgencia y presupuesto"""
    def __init__(self):
        super().__init__("UrgencyTagger")

    def generate_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """Genera tags de urgencia"""
        tags = []
        needs = lead_data.get("customer_needs", "").lower()

        if any(word in needs for word in ["urgente", "rapido", "pronto"]):
            tags.append("URGENTE")
        if any(word in needs for word in ["millones", "presupuesto"]):
            tags.append("PRESUPUESTO_DEFINIDO")

        return tags

class MetadataTagger(LeadTagger):
    """Genera tags basadas en metadata del flujo"""
    def __init__(self):
        super().__init__("MetadataTagger")

    def generate_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """Genera tags de metadata"""
        tags = []
        additional_data = lead_data.get("additional_data", {})

        if additional_data.get("tiene_solicitud_libertador"):
            tags.append("LIBERTADOR_APROBADO")
        if additional_data.get("tiene_contrato_inmobiliaria"):
            tags.append("CONTRATO_VIGENTE")

        return tags


# Priority Classifier Strategies
class UrgencyPriorityClassifier(PriorityClassifier):
    """Clasifica prioridad basada en urgencia y presupuesto"""
    def __init__(self):
        super().__init__("UrgencyPriorityClassifier")

    def classify(self, lead_data: Dict[str, Any]) -> str:
        """Clasifica prioridad del lead"""
        needs = lead_data.get("customer_needs", "").lower()

        if any(word in needs for word in ["urgente", "rapido", "ya", "inmediato"]):
            return "ALTA - Contacto inmediato"
        elif any(word in needs for word in ["presupuesto", "millones", "definido"]):
            return "MEDIA-ALTA - Contacto 24h"
        elif any(word in needs for word in ["informacion", "consulta"]):
            return "MEDIA - Contacto 48h"
        else:
            return "MEDIA - Contacto 24-48h"


# Composite Strategy (usa multiples estrategias)
class CompositeLeadScorer(LeadScorer):
    def __init__(self, scorers: List[LeadScorer], weights: Dict[str, float] = None):
        """Combina multiples scorers para score final"""
        super().__init__("CompositeScorer")
        self.scorers = scorers
        self.weights = weights or {scorer.name: 1.0 for scorer in scorers}

    def score(self, lead_data: Dict[str, Any]) -> ScoringResult:
        """Calcula score combinado de todos los scorers"""
        total_score = 0.0
        total_weight = 0.0
        all_factors = {}
        all_tags = []

        for scorer in self.scorers:
            result = scorer.score(lead_data)
            weight = self.weights.get(scorer.name, 1.0)

            total_score += result.score * weight
            total_weight += weight
            all_factors[scorer.name] = result.factors
            all_tags.extend(result.tags)

        final_score = total_score / total_weight if total_weight > 0 else 0.0

        return ScoringResult(
            score=final_score,
            confidence=0.9,
            factors=all_factors,
            tags=list(set(all_tags)),  # Eliminar duplicados
            reasoning=f"Score combinado de {len(self.scorers)} scorers"
        )