"""
Tests unitarios para CRMVisualizationBuilder
"""
import pytest
from app.services.leadsales.visualization import CRMVisualizationBuilder


class TestCRMVisualizationBuilder:
    def test_build_crm_preview_structure(self):
        builder = CRMVisualizationBuilder()
        enriched_data = {
            "name": "Test User",
            "whatsapp": "+573001234567",
            "needs": "Busco apartamento",
            "quality_score": 82,
            "priority": "ALTA",
            "tags": ["compra"],
            "confidence": 0.85,
            "metadata": {"location": "Medellin"},
            "created_at": "2025-10-17T10:30:00"
        }
        preview = builder.build_crm_preview(enriched_data)
        assert "customer_info" in preview
        assert preview["customer_info"]["name"] == "Test User"

    def test_build_demo_simulation_complete(self):
        builder = CRMVisualizationBuilder()
        enriched_data = {
            "name": "Test User",
            "whatsapp": "+573001234567",
            "needs": "Busco apartamento",
            "quality_score": 82,
            "priority": "ALTA",
            "tags": ["compra"],
            "confidence": 0.85,
            "metadata": {},
            "created_at": "2025-10-17T10:30:00"
        }
        simulation = builder.build_demo_simulation(enriched_data)
        assert "customer_data" in simulation
        assert simulation["crm_simulation"]["lead_id"].startswith("DEMO_")

    def test_format_priority_label(self):
        builder = CRMVisualizationBuilder()
        assert "ALTA" in builder._format_priority_label("ALTA")

    def test_calculate_next_followup(self):
        builder = CRMVisualizationBuilder()
        followup = builder._calculate_next_followup("ALTA")
        assert followup is not None
        assert len(followup) == 10

    def test_estimate_lead_value(self):
        builder = CRMVisualizationBuilder()
        enriched_data = {"metadata": {"budget_range": "mas_1000m"}}
        value = builder._estimate_lead_value(enriched_data)
        assert ".000.000.000+" in value
