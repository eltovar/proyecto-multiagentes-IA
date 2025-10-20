'''Test para PriorityClassifier'''

'''
Que tan rapido hay que contactar al cliente?
'''

import pytest

from app.services.scoring.strategies import UrgencyPriorityClassifier

# TEST SUITE 1: UrgencyPriorityClassifier
class TestUrgencyPriorityClassifier:
    """Tests para UrgencyPriorityClassifier (ALTA/MEDIA-ALTA/MEDIA)"""
    
    @pytest.fixture
    def classifier(self):
        """Fixture: Instancia de UrgencyPriorityClassifier"""
        return UrgencyPriorityClassifier()
    
    def test_classify_alta_priority(self, classifier):
        
        lead_data = {
            "customer_needs": "Necesito esto urgente, ya, es inmediato"
        }
        
        priority = classifier.classify(lead_data)
        
        assert "ALTA" in priority
        assert "inmediato" in priority.lower()
    
    def test_classify_media_alta_priority(self, classifier):
       
        lead_data = {
            "customer_needs": "Tengo presupuesto de 400 millones definido"
        }
        
        priority = classifier.classify(lead_data)
        
        assert "MEDIA-ALTA" in priority
        assert "24h" in priority
    
    def test_classify_media_priority_informacion(self, classifier):
        
        lead_data = {
            "customer_needs": "Quiero información sobre sus servicios"
        }
        
        priority = classifier.classify(lead_data)
        
        assert "MEDIA" in priority
        assert "48h" in priority
    
    def test_classify_media_priority_default(self, classifier):
        
        lead_data = {
            "customer_needs": "Estoy buscando opciones"
        }
        
        priority = classifier.classify(lead_data)
        
        assert "MEDIA" in priority
        assert "24-48h" in priority or "24h" in priority
    
    def test_classify_empty_needs(self, classifier):
        """
        Test: Maneja customer_needs vacío
        
        Given: Lead sin customer_needs
        When: Se clasifica prioridad
        Then: Retorna MEDIA por default sin error
        """
        lead_data = {
            "customer_needs": ""
        }
        
        priority = classifier.classify(lead_data)
        
        assert isinstance(priority, str)
        assert len(priority) > 0
        assert "MEDIA" in priority
    
    def test_classify_case_insensitive(self, classifier):
        """
        Test: Clasificación es case-insensitive
        
        Given: Keywords en diferentes casos (URGENTE, Urgente, urgente)
        When: Se clasifica prioridad
        Then: Detecta correctamente en todos los casos
        """
        test_cases = [
            {"customer_needs": "URGENTE necesito esto"},
            {"customer_needs": "Urgente por favor"},
            {"customer_needs": "urgente!"}
        ]
        
        for lead_data in test_cases:
            priority = classifier.classify(lead_data)
            assert "ALTA" in priority, f"Debería detectar urgencia en: {lead_data}"


# TEST SUITE 2: Validación de output
class TestPriorityClassifierOutput:
    """Tests para validar formato de output"""
    
    def test_priority_format_is_string(self):
        
        classifier = UrgencyPriorityClassifier()
        lead_data = {"customer_needs": "test"}
        
        priority = classifier.classify(lead_data)
        
        assert isinstance(priority, str)
        assert len(priority) > 0
    
    def test_priority_contains_level_and_action(self):
        
        classifier = UrgencyPriorityClassifier()
        lead_data = {"customer_needs": "urgente"}
        
        priority = classifier.classify(lead_data)
        
        # Debe tener nivel
        assert any(level in priority for level in ["ALTA", "MEDIA"])
        # Debe tener acción de contacto
        assert "Contacto" in priority or "contacto" in priority
