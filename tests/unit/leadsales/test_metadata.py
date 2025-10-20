"""
Tests unitarios para LeadMetadataExtractor
"""
import pytest
from app.services.leadsales.metadata import LeadMetadataExtractor


@pytest.fixture
def metadata_extractor():
    """Fixture que crea un LeadMetadataExtractor para tests"""
    return LeadMetadataExtractor()


class TestLeadMetadataExtractor:
    """Tests para LeadMetadataExtractor"""

    def test_extract_location_from_text(self):
        """Extrae ubicacion desde texto"""
        extractor = LeadMetadataExtractor()
        metadata = extractor.extract_metadata("Busco apartamento en Medellin, zona Poblado", {})
        assert "location" in metadata

    def test_extract_location_from_additional_data(self):
        """Prioriza additional_data para ubicacion"""
        extractor = LeadMetadataExtractor()
        metadata = extractor.extract_metadata("Busco apartamento", {"location": "Envigado"})
        assert metadata["location"] == "Envigado"

    def test_extract_budget_range_200_500m(self):
        """Extrae presupuesto entre 200-500 millones"""
        extractor = LeadMetadataExtractor()
        metadata = extractor.extract_metadata("Presupuesto de 400 millones", {})
        assert metadata["budget_range"] == "200m_500m"

    def test_extract_property_type_casa(self):
        """Extrae tipo de propiedad: casa"""
        extractor = LeadMetadataExtractor()
        metadata = extractor.extract_metadata("Necesito una casa de 3 habitaciones", {})
        assert metadata["property_type"] == "casa"

    def test_extract_rooms_count_3(self):
        """Extrae numero de habitaciones: 3"""
        extractor = LeadMetadataExtractor()
        metadata = extractor.extract_metadata("Apartamento de 3 habitaciones", {})
        assert metadata["rooms"] == 3

    def test_detect_urgency_high_urgente(self):
        """Detecta urgencia alta con urgente"""
        extractor = LeadMetadataExtractor()
        metadata = extractor.extract_metadata("Necesito apartamento urgente", {})
        assert metadata["urgency_level"] == "high"

    def test_normalize_phone_adds_country_code(self):
        """Normaliza telefono agregando codigo pais"""
        extractor = LeadMetadataExtractor()
        normalized = extractor._normalize_phone("3001234567")
        assert normalized == "+573001234567"

    def test_enrich_customer_data_complete_structure(self):
        """enrich_customer_data() retorna estructura completa"""
        extractor = LeadMetadataExtractor()
        scoring_result = {"quality_score": 85, "priority": "ALTA", "tags": ["compra"], "confidence": 0.88}
        metadata = {"location": "Medellin", "rooms": 3}
        enriched = extractor.enrich_customer_data("Juan Perez", "3001234567", "Busco apartamento", scoring_result, metadata)
        assert enriched["name"] == "Juan Perez"
        assert enriched["whatsapp"] == "+573001234567"
        assert enriched["quality_score"] == 85
