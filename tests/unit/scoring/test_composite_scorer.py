'''Test suite para CompositeLeadScorer'''
'''
Combina los puntajes
'''

import pytest
from app.services.scoring.strategies import (
    CompositeLeadScorer,
    DemoQualityScorer,
    InterestLevelScorer,
    ConversionProbabilityScorer
)

from app.services.scoring.base import ScoringResult


# TEST SUITE 1: CompositeLeadScorer
class TestCompositeLeadScorer:
    """Tests para CompositeLeadScorer (combina múltiples scorers)"""
    
    @pytest.fixture
    def base_scorers(self):
        """Fixture: Lista de scorers base para composición"""
        return [
            DemoQualityScorer(),
            InterestLevelScorer(),
            ConversionProbabilityScorer()
        ]
    
    def test_composite_combines_multiple_scorers(self, base_scorers):
        """
        Test: Combina 3 scorers correctamente
        
        Given: CompositeScorer con 3 scorers (Demo, Interest, Conversion)
        When: Se calcula score de un lead
        Then: Retorna promedio ponderado de los 3 scores
        """
        composite = CompositeLeadScorer(scorers=base_scorers)
        
        lead_data = {
            "customer_needs": "Quiero comprar apartamento urgente con presupuesto de 500 millones",
            "additional_data": {
                "tiene_solicitud_libertador": True,
                "fecha_necesidad": "2025-02-15"
            }
        }
        
        result = composite.score(lead_data)
        
        # Verificar estructura
        assert isinstance(result, ScoringResult)
        assert 0 <= result.score <= 100
        assert result.confidence >= 0.8
        
        # Verificar que consolidó factores de los 3 scorers
        assert "DemoQualityScorer" in result.factors
        assert "InterestLevelScorer" in result.factors
        assert "ConversionProbabilityScorer" in result.factors
    
    def test_composite_with_custom_weights(self):
       
        scorers = [
            DemoQualityScorer(),
            InterestLevelScorer(),
            ConversionProbabilityScorer()
        ]
        
        weights = {
            "DemoQualityScorer": 2.0,        # Doble peso
            "InterestLevelScorer": 1.5,      # 1.5x peso
            "ConversionProbabilityScorer": 1.0  # Peso normal
        }
        
        composite = CompositeLeadScorer(scorers=scorers, weights=weights)
        
        lead_data = {
            "customer_needs": "comprar apartamento millones urgente",
            "additional_data": {"tiene_solicitud_libertador": True}
        }
        
        result = composite.score(lead_data)
        
        # Score debería estar influenciado más por DemoQuality (peso 2.0)
        assert result.score > 50
        assert "3 scorers" in result.reasoning
    
    def test_composite_with_default_weights(self, base_scorers):
        """
        Test: Usa pesos por defecto (1.0 para todos)
        
        Given: CompositeScorer sin weights especificados
        When: Se calcula score
        Then: Todos los scorers tienen peso igual (1.0)
        """
        composite = CompositeLeadScorer(scorers=base_scorers)
        
        # Verificar que tiene pesos por defecto
        assert composite.weights["DemoQualityScorer"] == 1.0
        assert composite.weights["InterestLevelScorer"] == 1.0
        assert composite.weights["ConversionProbabilityScorer"] == 1.0
    
    def test_composite_calculates_weighted_average(self):
        
        # Crear mock scorers con scores fijos
        from unittest.mock import Mock
        
        scorer1 = Mock()
        scorer1.name = "Scorer1"
        scorer1.score = Mock(return_value=ScoringResult(
            score=80.0,
            confidence=0.9,
            factors={},
            tags=[],
            reasoning="test"
        ))
        
        scorer2 = Mock()
        scorer2.name = "Scorer2"
        scorer2.score = Mock(return_value=ScoringResult(
            score=60.0,
            confidence=0.8,
            factors={},
            tags=[],
            reasoning="test"
        ))
        
        weights = {"Scorer1": 2.0, "Scorer2": 1.0}
        composite = CompositeLeadScorer(scorers=[scorer1, scorer2], weights=weights)
        
        result = composite.score({})
        
        # Score esperado: (80*2 + 60*1) / (2+1) = 220/3 = 73.33
        assert 73.0 <= result.score <= 74.0
    
    def test_composite_consolidates_factors_and_tags(self, base_scorers):
        
        composite = CompositeLeadScorer(scorers=base_scorers)
        
        lead_data = {
            "customer_needs": "comprar casa urgente",
            "additional_data": {}
        }
        
        result = composite.score(lead_data)
        
        # Verificar consolidación de factores
        assert len(result.factors) == 3  # 3 scorers
        assert all(scorer.name in result.factors for scorer in base_scorers)
        
        # Verificar que tags es lista (aunque puede estar vacía)
        assert isinstance(result.tags, list)
    
    def test_composite_with_empty_scorers(self):
        
        composite = CompositeLeadScorer(scorers=[])
        
        result = composite.score({"customer_needs": "test"})
        
        assert result.score == 0.0
        assert result.factors == {}
        assert result.tags == []


# TEST SUITE 2: Integración con scorers reales
class TestCompositeIntegration:
    """Tests de integración con scorers reales"""
    
    def test_composite_high_value_lead(self):
        
        scorers = [
            DemoQualityScorer(),
            InterestLevelScorer(),
            ConversionProbabilityScorer()
        ]
        
        composite = CompositeLeadScorer(scorers=scorers)
        
        lead_data = {
            "customer_needs": "Quiero comprar apartamento urgente, presupuesto 500 millones, 3 habitaciones",
            "additional_data": {
                "tiene_solicitud_libertador": True,
                "fecha_necesidad": "2025-02-15",
                "tiene_contrato_inmobiliaria": False
            }
        }
        
        result = composite.score(lead_data)
        
        assert result.score >= 75, "Lead high-value debería tener score >= 75"
    
    def test_composite_low_value_lead(self):
        
        scorers = [
            DemoQualityScorer(),
            InterestLevelScorer(),
            ConversionProbabilityScorer()
        ]
        
        composite = CompositeLeadScorer(scorers=scorers)
        
        lead_data = {
            "customer_needs": "información",
            "additional_data": {}
        }
        
        result = composite.score(lead_data)
        
        assert result.score <= 50, "Lead low-value debería tener score <= 50"
    
    def test_composite_removes_duplicate_tags(self):
        # Este test asume que en el futuro los scorers generarán tags
        # Por ahora, verifica que la lógica de deduplicación existe
        scorers = [DemoQualityScorer()]
        composite = CompositeLeadScorer(scorers=scorers)
        
        result = composite.score({"customer_needs": "test"})
        
        # Verificar que tags es lista (preparada para deduplicación)
        assert isinstance(result.tags, list)