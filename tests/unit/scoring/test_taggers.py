'''Tests unitarios para LeadTagger strategies'''
'''Etiqueta de los clientes?

 Detecta "comprar" → genera tag COMPRA
Detecta "casa" → genera tag CASA
Detecta "urgente" → genera tag URGENTE
Sin keywords → no genera tags
'''

import pytest
from app.services.scoring.strategies import (
    TransactionTypeTagger,
    PropertyTypeTagger,
    UrgencyTagger,
    MetadataTagger
)

#Test 1 TransactionTypeTagger
class TestTransactionTypeTagger:
    """Tests para TransactionTypeTagger (COMPRA/VENTA/ARRIENDO)"""
    
    @pytest.fixture
    def tagger(self):
        """Fixture: Instancia de TransactionTypeTagger"""
        return TransactionTypeTagger()
    
    def test_tag_compra(self, tagger):
       
        lead_data = {
            "customer_needs": "Quiero comprar un apartamento"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "COMPRA" in tags
        assert isinstance(tags, list)
    
    def test_tag_venta(self, tagger):
    
        lead_data = {
            "customer_needs": "Necesito vender mi casa"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "VENTA" in tags
    
    def test_tag_arriendo(self, tagger):
        """
        Test: Detecta tag ARRIENDO
        
        Given: Lead con palabra "arrendar" o "arriendo"
        When: Se generan tags
        Then: Retorna ["ARRIENDO"]
        """
        lead_data = {
            "customer_needs": "Busco arrendar apartamento"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "ARRIENDO" in tags
    
    def test_tag_multiple_transaction_types(self, tagger):
        """
        Test: Detecta múltiples tags simultáneos
        
        Given: Lead con "comprar" Y "vender"
        When: Se generan tags
        Then: Retorna ["COMPRA", "VENTA"]
        """
        lead_data = {
            "customer_needs": "Quiero vender mi casa y comprar un apartamento"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "COMPRA" in tags
        assert "VENTA" in tags
        assert len(tags) == 2
    
    def test_tag_no_transaction_keywords(self, tagger):
       
        lead_data = {
            "customer_needs": "Solo quiero información"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert tags == []


#Test 2 PropertyTypeTagger
class TestPropertyTypeTagger:
    """Tests para PropertyTypeTagger (CASA/APARTAMENTO/LOCAL_COMERCIAL)"""
    
    @pytest.fixture
    def tagger(self):
        """Fixture: Instancia de PropertyTypeTagger"""
        return PropertyTypeTagger()
    
    def test_tag_casa(self, tagger):
        
        lead_data = {
            "customer_needs": "Busco casa en el norte"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "CASA" in tags
    
    def test_tag_apartamento(self, tagger):
        
        lead_data = {
            "customer_needs": "Necesito un apto de 3 habitaciones"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "APARTAMENTO" in tags
    
    def test_tag_local_comercial(self, tagger):
        
        lead_data = {
            "customer_needs": "Busco local para negocio"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "LOCAL_COMERCIAL" in tags
    
    def test_tag_multiple_property_types(self, tagger):
        
        lead_data = {
            "customer_needs": "Me interesa casa o apartamento en el sur"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "CASA" in tags
        assert "APARTAMENTO" in tags
    
    def test_tag_no_property_keywords(self, tagger):
        
        lead_data = {
            "customer_needs": "Quiero comprar algo"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert tags == []


# TEST SUITE 3: UrgencyTagger
class TestUrgencyTagger:
    """Tests para UrgencyTagger (URGENTE/PRESUPUESTO_DEFINIDO)"""
    
    @pytest.fixture
    def tagger(self):
        """Fixture: Instancia de UrgencyTagger"""
        return UrgencyTagger()
    
    def test_tag_urgente(self, tagger):
        """
        Test: Detecta tag URGENTE
        
        Given: Lead con palabras de urgencia
        When: Se generan tags
        Then: Retorna ["URGENTE"]
        """
        lead_data = {
            "customer_needs": "Necesito algo urgente, lo más rápido posible"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "URGENTE" in tags
    
    def test_tag_presupuesto_definido(self, tagger):
        
        lead_data = {
            "customer_needs": "Tengo presupuesto de 500 millones"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "PRESUPUESTO_DEFINIDO" in tags
    
    def test_tag_both_urgency_and_budget(self, tagger):
      
        lead_data = {
            "customer_needs": "Urgente! Tengo presupuesto de 300 millones"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "URGENTE" in tags
        assert "PRESUPUESTO_DEFINIDO" in tags
        assert len(tags) == 2
    
    def test_tag_no_urgency_indicators(self, tagger):
       
        lead_data = {
            "customer_needs": "Solo quiero información"
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert tags == []


# TEST SUITE 4: MetadataTagger
class TestMetadataTagger:
    """Tests para MetadataTagger (LIBERTADOR_APROBADO/CONTRATO_VIGENTE)"""
    
    @pytest.fixture
    def tagger(self):
        """Fixture: Instancia de MetadataTagger"""
        return MetadataTagger()
    
    def test_tag_libertador_aprobado(self, tagger):
        
        lead_data = {
            "additional_data": {
                "tiene_solicitud_libertador": True
            }
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "LIBERTADOR_APROBADO" in tags
    
    def test_tag_contrato_vigente(self, tagger):
       
        lead_data = {
            "additional_data": {
                "tiene_contrato_inmobiliaria": True
            }
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "CONTRATO_VIGENTE" in tags
    
    def test_tag_both_metadata_tags(self, tagger):
        
        lead_data = {
            "additional_data": {
                "tiene_solicitud_libertador": True,
                "tiene_contrato_inmobiliaria": True
            }
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert "LIBERTADOR_APROBADO" in tags
        assert "CONTRATO_VIGENTE" in tags
        assert len(tags) == 2
    
    def test_tag_no_metadata(self, tagger):
       
        lead_data = {
            "additional_data": {}
        }
        
        tags = tagger.generate_tags(lead_data)
        
        assert tags == []
    
    def test_tag_missing_additional_data_key(self, tagger):
       
        lead_data = {}
        
        tags = tagger.generate_tags(lead_data)
        
        assert tags == []
        assert isinstance(tags, list)
