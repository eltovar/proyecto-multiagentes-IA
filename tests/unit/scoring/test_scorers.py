'''Para LeadScorer, estrategias de puntuación'''
''' 
"Vale la pena este cliente?" Estrategia que calcula puntaje del
0 al 100
'''

import pytest
from app.services.scoring.strategies import (
    DemoQualityScorer,
    InterestLevelScorer,
    ConversionProbabilityScorer
)

from app.services.scoring.base import ScoringResult

#Test 1 DemoQualityScorer
class TestDemoQualityScorer:
    """Tests para DemoQualityScorer (score basado en keywords)"""
    
    @pytest.fixture
    def scorer(self):
        """Fixture: Instancia de DemoQualityScorer"""
        return DemoQualityScorer()
    
    def test_score_high_value_keywords(self, scorer):
        """
        Test: Score alto con keywords high-value
        
        Given: Lead con keywords "comprar", "apartamento", "millones"
        When: Se calcula el score
        Then: Score >= 80 (high-value keywords valen 20pts c/u)
        """
        lead_data = {
            "customer_needs": "Quiero comprar un apartamento con presupuesto de 500 millones"
        }
        
        result = scorer.score(lead_data)
        
        # Assertions
        assert isinstance(result, ScoringResult)
        assert result.score >= 80, "Score debería ser >= 80 con 3+ keywords high-value"
        assert result.confidence >= 0.8, "Confidence alta con keywords high-value"
        assert result.factors["high_keywords"] >= 3
        assert "high-value" in result.reasoning
    
    def test_score_medium_value_keywords(self, scorer):
        """
        Test: Score medio con keywords medium-value
        
        Given: Lead con keywords "arrendar", "busco", "zona"
        When: Se calcula el score
        Then: Score entre 50-70 (medium-value keywords valen 10pts c/u)
        """
        lead_data = {
            "customer_needs": "Busco arrendar en zona norte"
        }
        
        result = scorer.score(lead_data)
        
        assert 50 <= result.score <= 70
        assert result.factors["medium_keywords"] >= 2
        assert result.confidence >= 0.6
    
    def test_score_low_value_keywords(self, scorer):
        """
        Test: Score bajo sin keywords de valor

        Given: Lead con solo keywords low-value o genericas
        When: Se calcula el score
        Then: Score minimo (base 40, sin bonus)
        """
        lead_data = {
            "customer_needs": "Solo quiero informacion general"
        }
        
        result = scorer.score(lead_data)
        
        assert result.score <= 50, "Score bajo sin keywords valiosas"
        assert result.factors["high_keywords"] == 0
    
    def test_score_mixed_keywords(self, scorer):
        """
        Test: Score con mezcla de keywords high + medium
        
        Given: Lead con mix de keywords
        When: Se calcula el score
        Then: Score refleja combinación (high*20 + medium*10 + base)
        """
        lead_data = {
            "customer_needs": "Necesito comprar casa, busco en zona sur"
            # high: "comprar", "casa" (2*20=40)
            # medium: "busco", "zona" (2*10=20)
            # base: 40
            # total esperado: min(100, 40+20+40) = 100
        }
        
        result = scorer.score(lead_data)
        
        assert result.score >= 80
        assert result.factors["high_keywords"] >= 2
        assert result.factors["medium_keywords"] >= 2
    
    def test_score_empty_needs(self, scorer):
        """
        Test: Score mínimo con customer_needs vacío
        
        Given: Lead sin customer_needs
        When: Se calcula el score
        Then: Score base (30-40) sin bonus
        """
        lead_data = {
            "customer_needs": ""
        }
        
        result = scorer.score(lead_data)
        
        assert 30 <= result.score <= 50
        assert result.factors["high_keywords"] == 0
        assert result.factors["medium_keywords"] == 0


#Test 2 InterestLevelScorer
class TestInterestLevelScorer:
    """Tests para InterestLevelScorer (urgencia + especificidad)"""
    
    @pytest.fixture
    def scorer(self):
        """Fixture: Instancia de InterestLevelScorer"""
        return InterestLevelScorer()
    
    def test_score_high_urgency(self, scorer):
        """
        Test: Score alto por urgencia

        Given: Lead con palabras de urgencia ("urgente", "rapido", "ya")
        When: Se calcula el score
        Then: Score alto (urgencia vale 30pts c/u)
        """
        lead_data = {
            "customer_needs": "Necesito algo urgente, ya, lo mas rapido posible"
        }

        result = scorer.score(lead_data)

        assert result.score >= 70, "Urgencia alta deberia dar score >= 70"
        assert result.factors["urgency_indicators"] >= 2
        assert "urgencia" in result.reasoning.lower()
    
    def test_score_high_specificity(self, scorer):
        """
        Test: Score por especificidad

        Given: Lead con detalles especificos ("3 habitaciones", "2 banos", "presupuesto")
        When: Se calcula el score
        Then: Score medio-alto (especificidad vale 10pts c/u)
        """
        lead_data = {
            "customer_needs": "Busco apartamento de 3 habitaciones, 2 banos, presupuesto 300M, zona norte"
        }

        result = scorer.score(lead_data)

        assert result.score >= 40
        assert result.factors["specificity_indicators"] >= 3
        assert "especificidad" in result.reasoning.lower()
    
    def test_score_combined_urgency_and_specificity(self, scorer):
        """
        Test: Score combinado (urgencia 60% + especificidad 40%)
        
        Given: Lead con urgencia Y especificidad
        When: Se calcula el score
        Then: Score refleja ambos factores
        """
        lead_data = {
            "customer_needs": "Urgente! Necesito apartamento 3 habitaciones con presupuesto de 400M"
            # urgency: 1 * 30 = 30
            # specificity: 2 * 10 = 20
            # total: 50
        }
        
        result = scorer.score(lead_data)
        
        assert result.score >= 40
        assert result.factors["urgency_indicators"] >= 1
        assert result.factors["specificity_indicators"] >= 2
    
    def test_score_no_indicators(self, scorer):
        """
        Test: Score minimo sin indicadores

        Given: Lead generico sin urgencia ni especificidad
        When: Se calcula el score
        Then: Score base (20-30)
        """
        lead_data = {
            "customer_needs": "Hola, quiero informacion"
        }
        
        result = scorer.score(lead_data)
        
        assert result.score <= 30
        assert result.factors["urgency_indicators"] == 0
        assert result.factors["specificity_indicators"] == 0


#Test 3 ConversionProbabilityScorer

class TestConversionProbabilityScorer:
    """Tests para ConversionProbabilityScorer (metadata del flujo)"""
    
    @pytest.fixture
    def scorer(self):
        """Fixture: Instancia de ConversionProbabilityScorer"""
        return ConversionProbabilityScorer()
    
    def test_score_all_positive_factors(self, scorer):
        """
        Test: Score maximo con todos los factores positivos

        Given: Lead con solicitud Libertador, fecha definida, sin contrato
        When: Se calcula el score
        Then: Score alto (50 base + 20 + 15 + 15 = 100)
        """
        lead_data = {
            "additional_data": {
                "tiene_solicitud_libertador": True,      # +20
                "fecha_necesidad": "2025-02-15",          # +15
                "tiene_contrato_inmobiliaria": False      # +15
            }
        }
        
        result = scorer.score(lead_data)
        
        assert result.score == 100, "Todos los factores positivos = 100pts"
        assert result.confidence >= 0.85
        assert result.factors["libertador_approved"] is True
        assert result.factors["date_defined"] is True
        assert result.factors["no_current_contract"] is True
    
    def test_score_no_positive_factors(self, scorer):
        """
        Test: Score base sin factores positivos
        
        Given: Lead sin metadata positiva
        When: Se calcula el score
        Then: Score base (50)
        """
        lead_data = {
            "additional_data": {
                "tiene_solicitud_libertador": False,
                "fecha_necesidad": None,
                "tiene_contrato_inmobiliaria": True
            }
        }
        
        result = scorer.score(lead_data)
        
        assert result.score == 50, "Sin factores positivos = score base"
        assert result.factors["libertador_approved"] is False
        assert result.factors["date_defined"] is False
        assert result.factors["no_current_contract"] is False
    
    def test_score_partial_factors(self, scorer):
        """
        Test: Score parcial con algunos factores
        
        Given: Lead con 2 de 3 factores positivos
        When: Se calcula el score
        Then: Score = 50 + suma de bonos aplicables
        """
        lead_data = {
            "additional_data": {
                "tiene_solicitud_libertador": True,   # +20
                "fecha_necesidad": "2025-03-01",       # +15
                "tiene_contrato_inmobiliaria": True    # +0
            }
        }
        
        result = scorer.score(lead_data)
        
        assert result.score == 85, "Base 50 + 20 + 15 = 85"
        assert result.factors["libertador_approved"] is True
        assert result.factors["date_defined"] is True
        assert result.factors["no_current_contract"] is False


#Test 4 Integration de scoringResults
class TestScoringResultStructure:
    """Tests para validar estructura de ScoringResult"""
    
    def test_scoring_result_structure(self):
        """
        Test: ScoringResult tiene estructura correcta
        
        Given: Cualquier scorer
        When: Se ejecuta score()
        Then: Retorna ScoringResult con todos los campos
        """
        scorer = DemoQualityScorer()
        lead_data = {"customer_needs": "test"}
        
        result = scorer.score(lead_data)
        
        # Verificar campos requeridos
        assert hasattr(result, 'score')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'factors')
        assert hasattr(result, 'tags')
        assert hasattr(result, 'reasoning')
        
        # Verificar tipos
        assert isinstance(result.score, float)
        assert isinstance(result.confidence, float)
        assert isinstance(result.factors, dict)
        assert isinstance(result.tags, list)
        assert isinstance(result.reasoning, str)
        
        # Verificar rangos
        assert 0 <= result.score <= 100
        assert 0 <= result.confidence <= 1.0
