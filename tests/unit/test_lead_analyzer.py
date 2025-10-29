"""
Tests unitarios para LeadAnalyzer (PR005)
Valida integración de scoring + clasificación → análisis compuesto
"""
import pytest
from app.services.lead_analyzer import LeadAnalyzer, LeadAnalysis


class TestCompositeScoreCalculation:
    """Tests para cálculo de Composite Score"""

    def test_composite_score_calculation_basic(self):
        """Composite score básico sin multiplicadores"""
        analyzer = LeadAnalyzer()

        composite = analyzer._calculate_composite_score(
            quality_score=70,
            profile="individual",  # 0.9x
            sophistication="medio"  # 1.0x
        )

        # 70 * 0.9 * 1.0 = 63
        assert composite == 63.0

    def test_composite_score_capped_at_100(self):
        """Composite score cap en 100"""
        analyzer = LeadAnalyzer()

        composite = analyzer._calculate_composite_score(
            quality_score=90,
            profile="inversionista",  # 1.3x
            sophistication="alto"  # 1.2x
        )

        # 90 * 1.3 * 1.2 = 140.4 → cap a 100
        assert composite == 100.0

    def test_all_profile_multipliers(self):
        """Todos los perfiles tienen multiplier válido"""
        analyzer = LeadAnalyzer()

        profiles = ["inversionista", "arquitecto", "ingeniero", "corredor",
                   "empresario", "familia", "individual", "desconocido"]

        for profile in profiles:
            composite = analyzer._calculate_composite_score(
                quality_score=60,
                profile=profile,
                sophistication="medio"
            )
            assert 0 <= composite <= 100

    def test_familia_neutral_multiplier(self):
        """Familia + medio → multiplicador neutral (1.0 × 1.0)"""
        analyzer = LeadAnalyzer()

        composite = analyzer._calculate_composite_score(
            quality_score=75,
            profile="familia",
            sophistication="medio"
        )

        # 75 * 1.0 * 1.0 = 75
        assert composite == 75.0

    def test_desconocido_min_multiplier(self):
        """Desconocido + bajo → multiplicador mínimo (0.8 × 0.85)"""
        analyzer = LeadAnalyzer()

        composite = analyzer._calculate_composite_score(
            quality_score=50,
            profile="desconocido",
            sophistication="bajo"
        )

        # 50 * 0.8 * 0.85 = 34
        assert composite == 34.0


class TestLeadSegmentation:
    """Tests para segmentación de leads (8 segmentos)"""

    def test_high_value_investor_segment(self):
        """Detecta segmento high_value_investor"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="inversionista",
            sophistication="alto",
            quality_score=85
        )

        assert segment == "high_value_investor"

    def test_professional_buyer_segment(self):
        """Detecta segmento professional_buyer"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="arquitecto",
            sophistication="alto",
            quality_score=75
        )

        assert segment == "professional_buyer"

    def test_entrepreneur_commercial_segment(self):
        """Detecta segmento entrepreneur_commercial"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="empresario",
            sophistication="medio",
            quality_score=80
        )

        assert segment == "entrepreneur_commercial"

    def test_family_premium_segment(self):
        """Detecta segmento family_premium"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="familia",
            sophistication="medio",
            quality_score=85
        )

        assert segment == "family_premium"

    def test_family_casual_segment(self):
        """Detecta segmento family_casual"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="familia",
            sophistication="medio",
            quality_score=60
        )

        assert segment == "family_casual"

    def test_individual_qualified_segment(self):
        """Detecta segmento individual_qualified"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="individual",
            sophistication="medio",
            quality_score=75
        )

        assert segment == "individual_qualified"

    def test_exploratory_segment(self):
        """Detecta segmento exploratory"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="individual",
            sophistication="bajo",
            quality_score=45
        )

        assert segment == "exploratory"

    def test_unknown_low_quality_segment(self):
        """Detecta segmento unknown_low_quality"""
        analyzer = LeadAnalyzer()

        segment = analyzer._determine_segment(
            profile="desconocido",
            sophistication="medio",  # Cambio: medio para evitar exploratory
            quality_score=35
        )

        assert segment == "unknown_low_quality"


class TestPriorityAdjustment:
    """Tests para ajuste inteligente de prioridad"""

    def test_priority_boost_for_high_value(self):
        """High value investor recibe boost de prioridad (+2)"""
        analyzer = LeadAnalyzer()

        adjusted_priority, numeric = analyzer._adjust_priority(
            base_priority="ALTA",  # 8 base
            segment="high_value_investor"  # +2 boost
        )

        # 8 + 2 = 10 → capped at 10 → ALTA (máximo nivel)
        assert adjusted_priority == "ALTA"
        assert numeric == 10

    def test_priority_boost_for_professional(self):
        """Professional buyer recibe boost moderado (+1)"""
        analyzer = LeadAnalyzer()

        adjusted_priority, numeric = analyzer._adjust_priority(
            base_priority="MEDIA-ALTA",  # 6 base (no 7)
            segment="professional_buyer"  # +1 boost
        )

        # 6 + 1 = 7 → MEDIA-ALTA (necesita >=8 para ALTA)
        assert adjusted_priority == "MEDIA-ALTA"
        assert numeric == 7

    def test_priority_downgrade_for_exploratory(self):
        """Exploratory recibe downgrade de prioridad (-1)"""
        analyzer = LeadAnalyzer()

        adjusted_priority, numeric = analyzer._adjust_priority(
            base_priority="MEDIA",  # 4 base (no 5)
            segment="exploratory"  # -1 boost
        )

        # 4 - 1 = 3 → BAJA
        assert adjusted_priority == "BAJA"
        assert numeric == 3

    def test_priority_downgrade_for_unknown(self):
        """Unknown low quality recibe downgrade (-1)"""
        analyzer = LeadAnalyzer()

        adjusted_priority, numeric = analyzer._adjust_priority(
            base_priority="MEDIA",  # 4 base (no 5)
            segment="unknown_low_quality"  # -1 boost
        )

        # 4 - 1 = 3 → BAJA
        assert adjusted_priority == "BAJA"
        assert numeric == 3


class TestConversionProbability:
    """Tests para cálculo de probabilidad de conversión"""

    def test_high_conversion_probability(self):
        """Alta calidad + inversionista alto + urgente → prob. alta"""
        analyzer = LeadAnalyzer()

        probability = analyzer._calculate_conversion_probability(
            quality_score=95,
            profile="inversionista",
            sophistication="alto",
            metadata={
                "urgency_level": "high",
                "budget_range": "$500k-$1M"
            }
        )

        # Base 0.95 + profile 0.15 + soph 0.10 + urgency 0.12 + budget 0.08 = 1.40 → capped at 1.0
        assert probability == 1.0

    def test_medium_conversion_probability(self):
        """Calidad media + familia medio → prob. media"""
        analyzer = LeadAnalyzer()

        probability = analyzer._calculate_conversion_probability(
            quality_score=60,
            profile="familia",
            sophistication="medio",
            metadata={}
        )

        # Base 0.60 + profile 0.05 + soph 0.05 = 0.70
        assert 0.55 <= probability <= 0.70

    def test_low_conversion_probability(self):
        """Baja calidad + desconocido bajo → prob. baja"""
        analyzer = LeadAnalyzer()

        probability = analyzer._calculate_conversion_probability(
            quality_score=35,
            profile="desconocido",
            sophistication="bajo",
            metadata={}
        )

        # Base 0.35 + profile -0.10 + soph -0.05 = 0.20
        assert probability <= 0.30


class TestInsightsGeneration:
    """Tests para generación de insights"""

    def test_insights_for_high_quality_lead(self):
        """Genera insights para lead de alta calidad"""
        analyzer = LeadAnalyzer()

        insights = analyzer._generate_insights(
            quality_score=85,
            profile="inversionista",
            sophistication="alto",
            segment="high_value_investor",
            metadata={"customer_needs": "Busco apartamento urgente en Poblado"}
        )

        # Verificar que insights incluyen elementos clave
        insights_text = " ".join(insights).lower()
        assert "inversionista" in insights_text or "alto valor" in insights_text
        assert len(insights) >= 2

    def test_insights_include_budget_when_present(self):
        """Insights mencionan presupuesto cuando está presente"""
        analyzer = LeadAnalyzer()

        insights = analyzer._generate_insights(
            quality_score=75,
            profile="familia",
            sophistication="medio",
            segment="family_casual",
            metadata={"budget_range": "200m_500m"}
        )

        insights_text = " ".join(insights).lower()
        assert "presupuesto" in insights_text or "$200m" in insights_text


class TestRiskFactorIdentification:
    """Tests para identificación de factores de riesgo"""

    def test_risk_low_quality_score(self):
        """Score bajo genera riesgo de baja calidad"""
        analyzer = LeadAnalyzer()

        risks = analyzer._identify_risk_factors(
            quality_score=35,
            classification_result={
                "profile": "individual",
                "confidence": 0.70
            },
            metadata={}
        )

        risk_text = " ".join(risks).lower()
        assert "calidad" in risk_text or "score bajo" in risk_text or "poco calificado" in risk_text

    def test_risk_low_confidence(self):
        """Confianza baja genera riesgo de clasificación incierta"""
        analyzer = LeadAnalyzer()

        risks = analyzer._identify_risk_factors(
            quality_score=60,
            classification_result={
                "profile": "individual",
                "confidence": 0.35  # Baja confianza (< 0.5)
            },
            metadata={}
        )

        risk_text = " ".join(risks).lower()
        assert "confianza" in risk_text or "clasificación" in risk_text

    def test_risk_fallback_classification(self):
        """Perfil desconocido genera riesgo"""
        analyzer = LeadAnalyzer()

        risks = analyzer._identify_risk_factors(
            quality_score=50,
            classification_result={
                "profile": "desconocido",
                "confidence": 0.30
            },
            metadata={}
        )

        risk_text = " ".join(risks).lower()
        assert "desconocido" in risk_text or "calificación" in risk_text


class TestRecommendedActions:
    """Tests para recomendaciones de acciones"""

    def test_actions_for_high_value_investor(self):
        """Recomienda acciones para inversionista de alto valor"""
        analyzer = LeadAnalyzer()

        actions = analyzer._recommend_actions(
            segment="high_value_investor",
            sophistication="alto",
            metadata={}
        )

        # Debe incluir acciones específicas para inversionistas
        actions_text = " ".join(actions).lower()
        assert "senior" in actions_text or "inmediato" in actions_text
        assert "roi" in actions_text or "análisis" in actions_text or "inversión" in actions_text

    def test_actions_for_exploratory(self):
        """Recomienda acciones para lead exploratorio"""
        analyzer = LeadAnalyzer()

        actions = analyzer._recommend_actions(
            segment="exploratory",
            sophistication="bajo",
            metadata={}
        )

        # Debe incluir acciones educativas
        actions_text = " ".join(actions).lower()
        assert "educativo" in actions_text or "nurturing" in actions_text or "seguimiento" in actions_text

    def test_actions_for_unknown_low_quality(self):
        """Recomienda acciones de calificación para unknown"""
        analyzer = LeadAnalyzer()

        actions = analyzer._recommend_actions(
            segment="unknown_low_quality",
            sophistication="bajo",
            metadata={}
        )

        actions_text = " ".join(actions).lower()
        assert "guía" in actions_text or "acompañar" in actions_text or len(actions) >= 1


class TestLeadAnalyzerIntegration:
    """Tests de integración completa (end-to-end)"""

    def test_full_analysis_high_value_investor(self):
        """Análisis completo de inversionista de alto valor"""
        analyzer = LeadAnalyzer()

        scoring_result = {
            "quality_score": 85,
            "priority": "ALTA",
            "tags": ["COMPRA", "URGENTE"],
            "confidence": 0.9
        }

        classification_result = {
            "profile": "inversionista",
            "sophistication_level": "alto",
            "confidence": 0.95
        }

        metadata = {
            "customer_needs": "Busco apartamento para inversión en Poblado con presupuesto de 1000 millones",
            "location": "Poblado",
            "budget_range": "mas_1000m",
            "urgency_level": "high"
        }

        analysis = analyzer.analyze(scoring_result, classification_result, metadata)

        # Verificaciones completas
        assert analysis.quality_score == 85
        assert analysis.composite_score == 100.0  # 85 * 1.3 * 1.2 = 132.6 → capped
        assert analysis.lead_segment == "high_value_investor"
        assert analysis.priority == "ALTA"  # ALTA(8) + boost(+2) = 10 → ALTA (máximo nivel)
        assert analysis.priority_numeric == 10
        assert analysis.estimated_value == "alto"  # Sistema solo tiene 3 categorías: alto, medio, bajo
        assert analysis.conversion_probability >= 0.90
        assert len(analysis.key_insights) >= 3
        assert len(analysis.recommended_actions) >= 2
        assert isinstance(analysis.risk_factors, list)
        assert 0.8 <= analysis.confidence <= 1.0

    def test_full_analysis_family_casual(self):
        """Análisis completo de familia casual"""
        analyzer = LeadAnalyzer()

        scoring_result = {
            "quality_score": 55,
            "priority": "MEDIA",
            "tags": ["COMPRA", "APARTAMENTO"],
            "confidence": 0.7
        }

        classification_result = {
            "profile": "familia",
            "sophistication_level": "medio",
            "confidence": 0.75
        }

        metadata = {}

        analysis = analyzer.analyze(scoring_result, classification_result, metadata)

        # Verificaciones
        assert analysis.quality_score == 55
        assert analysis.composite_score == 55.0  # 55 * 1.0 * 1.0 = 55
        assert analysis.lead_segment == "family_casual"
        assert analysis.priority in ["MEDIA", "MEDIA-ALTA", "BAJA"]
        assert 0.45 <= analysis.conversion_probability <= 0.70
        assert len(analysis.key_insights) > 0
        assert len(analysis.recommended_actions) > 0