"""
Tests unitarios para LeadScoringIntegrator
"""
import pytest
from app.services.leadsales.scoring import LeadScoringIntegrator


@pytest.fixture
def scoring_integrator():
    """Fixture que crea un LeadScoringIntegrator para tests"""
    return LeadScoringIntegrator()


class TestLeadScoringIntegrator:
    """Tests para LeadScoringIntegrator"""

    def test_initialization_loads_components(self):
        """__init__() inicializa scorers, taggers y classifier"""
        integrator = LeadScoringIntegrator()

        assert integrator.quality_scorer is not None
        assert integrator.interest_scorer is not None
        assert integrator.conversion_scorer is not None
        assert len(integrator.taggers) == 4
        assert integrator.priority_classifier is not None

    def test_score_lead_returns_complete_structure(self):
        """score_lead() retorna estructura completa"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento urgente para comprar en Medellin",
            {"location": "Medellin"}
        )

        # Verificar campos obligatorios
        assert "quality_score" in result
        assert "interest_score" in result
        assert "conversion_probability" in result
        assert "tags" in result
        assert "priority" in result
        assert "confidence" in result
        assert "reasoning" in result

        # Verificar tipos
        assert isinstance(result["quality_score"], int)
        assert 0 <= result["quality_score"] <= 100
        assert isinstance(result["tags"], list)

    def test_score_high_quality_lead(self):
        """Score para lead de alta calidad"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Necesito comprar casa urgente con presupuesto de 500 millones en Poblado",
            {}
        )

        assert result["quality_score"] >= 70
        assert "ALTA" in result["priority"] or "MEDIA-ALTA" in result["priority"]
        # Tags en mayusculas
        tags_upper = [tag.upper() for tag in result["tags"]]
        assert "COMPRA" in tags_upper or "CASA" in tags_upper

    def test_score_low_quality_lead(self):
        """Score para lead de baja calidad"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Solo quiero informacion general",
            {}
        )

        assert result["quality_score"] < 60
        # Prioridad es MEDIA cuando solo tiene palabra "informacion"
        assert "MEDIA" in result["priority"] or "BAJA" in result["priority"]

    def test_score_lead_with_urgency_keywords(self):
        """Detecta keywords de urgencia"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Necesito urgente apartamento ya",
            {}
        )

        assert result["interest_score"] > 0.3
        tags_upper = [tag.upper() for tag in result["tags"]]
        assert "URGENTE" in tags_upper or "APARTAMENTO" in tags_upper

    def test_score_lead_normalizes_interest_score(self):
        """interest_score esta normalizado entre 0-1"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento urgente con 3 habitaciones y presupuesto definido",
            {}
        )

        assert 0 <= result["interest_score"] <= 1.0
        assert isinstance(result["interest_score"], float)

    def test_score_lead_normalizes_conversion_probability(self):
        """conversion_probability esta normalizado entre 0-1"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento",
            {"tiene_solicitud_libertador": True}
        )

        assert 0 <= result["conversion_probability"] <= 1.0
        assert isinstance(result["conversion_probability"], float)

    def test_score_lead_tags_not_empty_for_valid_lead(self):
        """Tags no vacio para lead valido"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento para comprar",
            {}
        )

        assert len(result["tags"]) > 0

    def test_score_lead_confidence_in_valid_range(self):
        """Confidence esta en rango valido"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento",
            {}
        )

        assert 0 <= result["confidence"] <= 1.0

    def test_score_lead_reasoning_not_empty(self):
        """Reasoning no esta vacio"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento",
            {}
        )

        assert len(result["reasoning"]) > 0
        assert "Quality:" in result["reasoning"]
        assert "Interest:" in result["reasoning"]
        assert "Conversion:" in result["reasoning"]

    def test_score_lead_with_budget_increases_quality(self):
        """Mencion de presupuesto aumenta quality score"""
        integrator = LeadScoringIntegrator()

        result_without_budget = integrator.score_lead("Busco apartamento", {})
        result_with_budget = integrator.score_lead(
            "Busco apartamento con presupuesto de 300 millones",
            {}
        )

        assert result_with_budget["quality_score"] >= result_without_budget["quality_score"]

    def test_score_lead_with_none_additional_data(self):
        """Funciona con additional_data None"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead("Busco apartamento", None)

        assert result is not None
        assert "quality_score" in result

    def test_score_lead_with_empty_string(self):
        """Maneja string vacio correctamente"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead("", {})

        assert result is not None
        # DemoQualityScorer tiene base_score de 40
        assert result["quality_score"] >= 30

    def test_score_lead_priority_classification(self):
        """Prioridad se clasifica correctamente"""
        integrator = LeadScoringIntegrator()

        # Lead con urgencia -> ALTA
        result_urgent = integrator.score_lead("Busco casa urgente ya", {})
        assert "ALTA" in result_urgent["priority"]

        # Lead con presupuesto -> MEDIA-ALTA
        result_budget = integrator.score_lead("Busco casa con 500 millones", {})
        assert "MEDIA" in result_budget["priority"]

        # Lead con informacion -> MEDIA
        result_info = integrator.score_lead("Quiero informacion sobre casas", {})
        assert "MEDIA" in result_info["priority"]

    def test_score_lead_combines_multiple_scorers(self):
        """Combina resultados de multiple scorers"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento urgente",
            {"tiene_solicitud_libertador": True}
        )

        # Debe tener resultados de los 3 scorers
        assert result["quality_score"] > 0  # DemoQualityScorer
        assert result["interest_score"] > 0  # InterestLevelScorer
        assert result["conversion_probability"] > 0.5  # ConversionProbabilityScorer (base 0.5 + solicitud)

    def test_score_lead_metadata_influences_conversion(self):
        """Metadata adicional influye en conversion probability"""
        integrator = LeadScoringIntegrator()

        result_without = integrator.score_lead("Busco apartamento", {})
        result_with = integrator.score_lead(
            "Busco apartamento",
            {
                "tiene_solicitud_libertador": True,
                "fecha_necesidad": "2025-02-01"
            }
        )

        # Metadata debe incrementar conversion probability
        assert result_with["conversion_probability"] > result_without["conversion_probability"]


class TestScoringIntegratorEdgeCases:
    """Tests de casos borde"""

    def test_score_very_long_text(self):
        """Maneja texto muy largo"""
        integrator = LeadScoringIntegrator()

        long_text = "Busco apartamento " * 100

        result = integrator.score_lead(long_text, {})

        assert result is not None
        assert result["quality_score"] > 0

    def test_score_special_characters(self):
        """Maneja caracteres especiales"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "Busco apartamento!!! @#$% con 3 habitaciones???",
            {}
        )

        assert result is not None
        assert "quality_score" in result

    def test_score_mixed_case_text(self):
        """Maneja texto con mayusculas/minusculas mezcladas"""
        integrator = LeadScoringIntegrator()

        result = integrator.score_lead(
            "BUSCO ApaRtAmeNTo ParA ComPRaR",
            {}
        )

        assert result is not None
        tags_upper = [tag.upper() for tag in result["tags"]]
        assert "APARTAMENTO" in tags_upper or "COMPRA" in tags_upper
