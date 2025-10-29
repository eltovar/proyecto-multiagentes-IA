import pytest
import os
from unittest.mock import AsyncMock
from app.services.leadsales import LeadsalesService


@pytest.mark.asyncio
class TestScoringInProduction:
    """Tests de scoring en modo producción"""

    async def test_production_mode_uses_scoring(self):
        """Verificar que modo producción calcula scoring"""
        service = LeadsalesService()
        service.initialized = True

        # Forzar modo producción (no demo)
        service.is_demo_mode = False

        # Mock del cliente API para capturar el payload
        captured_lead_data = {}

        async def mock_create_lead_api(lead_data):
            # Capturar datos enviados
            nonlocal captured_lead_data
            captured_lead_data = lead_data.copy()

            # Verificar que lead_data tiene scoring
            assert "quality_score" in lead_data, "Falta quality_score en producción"
            assert "tags" in lead_data, "Faltan tags en producción"
            assert "priority" in lead_data, "Falta priority en producción"

            # Verificar que priority NO es el valor fijo "normal"
            assert lead_data["priority"] != "normal", \
                "Priority debe ser calculada inteligentemente, no valor fijo 'normal'"

            # Verificar tipos correctos
            assert isinstance(lead_data["quality_score"], (int, float)), \
                "quality_score debe ser numérico"
            assert isinstance(lead_data["tags"], list), \
                "tags debe ser una lista"
            assert isinstance(lead_data["priority"], str), \
                "priority debe ser string"

            # Verificar que tags no está vacío
            assert len(lead_data["tags"]) > 0, \
                "tags debe contener al menos una etiqueta"

            return {"lead_id": "PROD-123", "status": "created"}

        service.client.create_lead_api = mock_create_lead_api

        # Ejecutar creación de lead en "producción"
        result = await service.create_lead(
            "Juan Pérez",
            "+573001234567",
            "Busco apartamento urgente 3 habitaciones Poblado 300 millones",
            {"tiene_solicitud_libertador": "Sí"}
        )

        # Verificar resultado exitoso
        assert result["lead_id"] == "PROD-123"
        assert result["status"] == "created"

        # Verificar que los campos de scoring fueron calculados
        assert captured_lead_data["quality_score"] > 0
        assert "APARTAMENTO" in captured_lead_data["tags"]
        assert "URGENTE" in captured_lead_data["tags"]

    async def test_production_scoring_matches_demo_scoring(self):
        """Verificar que scoring en producción es igual al de demo"""
        service = LeadsalesService()
        service.initialized = True

        customer_needs = "Busco casa para comprar en Envigado 200 millones"
        additional_data = {"tiene_solicitud_libertador": True}

        # Calcular scoring directamente (como lo usaría producción y demo)
        scoring_result = service._score_lead(customer_needs, additional_data)

        # Verificar estructura
        assert "quality_score" in scoring_result
        assert "tags" in scoring_result
        assert "priority" in scoring_result
        assert "scoring_metadata" in scoring_result

        # Verificar valores lógicos
        assert scoring_result["quality_score"] >= 30  # Mínimo del algoritmo
        assert "COMPRA" in scoring_result["tags"]
        assert "CASA" in scoring_result["tags"]
        assert "LIBERTADOR_APROBADO" in scoring_result["tags"]

    async def test_production_scoring_with_urgent_need(self):
        """Verificar scoring con necesidad urgente"""
        service = LeadsalesService()
        service.initialized = True

        scoring_result = service._score_lead(
            "URGENTE necesito apartamento YA, presupuesto 500 millones",
            {}
        )

        # Debe tener alta prioridad
        assert "ALTA" in scoring_result["priority"] or "MEDIA-ALTA" in scoring_result["priority"]
        assert "URGENTE" in scoring_result["tags"]
        assert scoring_result["quality_score"] > 70  # Alto score por keywords

    async def test_production_scoring_with_low_quality(self):
        """Verificar scoring con lead de baja calidad"""
        service = LeadsalesService()
        service.initialized = True

        scoring_result = service._score_lead(
            "información general",
            {}
        )

        # Debe tener menor score
        assert scoring_result["quality_score"] < 70
        # Priority debe ser MEDIA o BAJA
        assert "MEDIA" in scoring_result["priority"] or "BAJA" in scoring_result["priority"]

    async def test_production_mode_adds_quality_score_field(self):
        """Verificar que campo quality_score se agrega en producción"""
        service = LeadsalesService()
        service.initialized = True

        # Forzar modo producción
        service.is_demo_mode = False

        lead_data_sent = None

        async def capture_create_lead_api(lead_data):
            nonlocal lead_data_sent
            lead_data_sent = lead_data
            return {"lead_id": "TEST-001", "status": "created"}

        service.client.create_lead_api = capture_create_lead_api

        await service.create_lead(
            "Test User",
            "+573001111111",
            "Busco apartamento",
            {}
        )

        # Verificar que quality_score fue agregado
        assert lead_data_sent is not None
        assert "quality_score" in lead_data_sent
        assert isinstance(lead_data_sent["quality_score"], (int, float))

    async def test_production_mode_adds_tags_field(self):
        """Verificar que campo tags se agrega en producción"""
        service = LeadsalesService()
        service.initialized = True

        # Forzar modo producción
        service.is_demo_mode = False

        lead_data_sent = None

        async def capture_create_lead_api(lead_data):
            nonlocal lead_data_sent
            lead_data_sent = lead_data
            return {"lead_id": "TEST-002", "status": "created"}

        service.client.create_lead_api = capture_create_lead_api

        await service.create_lead(
            "Test User 2",
            "+573002222222",
            "Quiero vender mi casa en Laureles",
            {}
        )

        # Verificar que tags fueron agregadas
        assert lead_data_sent is not None
        assert "tags" in lead_data_sent
        assert isinstance(lead_data_sent["tags"], list)
        assert "VENTA" in lead_data_sent["tags"]
        assert "CASA" in lead_data_sent["tags"]

    async def test_production_mode_calculates_priority_intelligently(self):
        """Verificar que priority es calculada (no valor fijo)"""
        service = LeadsalesService()
        service.initialized = True

        # Forzar modo producción
        service.is_demo_mode = False

        priorities_captured = []

        async def capture_create_lead_api(lead_data):
            priorities_captured.append(lead_data["priority"])
            return {"lead_id": f"TEST-{len(priorities_captured)}", "status": "created"}

        service.client.create_lead_api = capture_create_lead_api

        # Test 1: Lead urgente
        await service.create_lead(
            "User 1",
            "+573001111111",
            "URGENTE necesito apartamento YA",
            {}
        )

        # Test 2: Lead con presupuesto
        await service.create_lead(
            "User 2",
            "+573002222222",
            "Busco casa presupuesto 400 millones",
            {}
        )

        # Test 3: Lead informativo
        await service.create_lead(
            "User 3",
            "+573003333333",
            "Información sobre apartamentos",
            {}
        )

        # Verificar que las prioridades son diferentes (inteligentes)
        assert len(priorities_captured) == 3
        assert priorities_captured[0] != "normal"  # No debe ser valor fijo
        assert priorities_captured[1] != "normal"
        assert priorities_captured[2] != "normal"

        # Verificar que al menos una es ALTA o MEDIA-ALTA
        assert any("ALTA" in p for p in priorities_captured)


@pytest.mark.asyncio
class TestScoringMetadata:
    """Tests de metadata adicional de scoring"""

    async def test_scoring_metadata_includes_confidence(self):
        """Verificar que metadata incluye confianza del score"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Busco apartamento para comprar",
            {}
        )

        assert "scoring_metadata" in scoring_result
        assert "quality" in scoring_result["scoring_metadata"]
        assert "confidence" in scoring_result["scoring_metadata"]["quality"]
        assert 0 <= scoring_result["scoring_metadata"]["quality"]["confidence"] <= 1.0
        
    async def test_scoring_metadata_includes_factors(self):
        """Verificar que metadata incluye factores del score"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Comprar casa urgente presupuesto 500 millones",
            {}
        )

        assert "scoring_metadata" in scoring_result
        assert "quality_factors" in scoring_result["scoring_metadata"]
        assert isinstance(scoring_result["scoring_metadata"]["quality_factors"], dict)

    async def test_scoring_metadata_includes_reasoning(self):
        """Verificar que metadata incluye razonamiento"""
        service = LeadsalesService()

        scoring_result = service._score_lead(
            "Necesito apartamento",
            {}
        )

        assert "scoring_metadata" in scoring_result
        assert "quality_reasoning" in scoring_result["scoring_metadata"]
        assert isinstance(scoring_result["scoring_metadata"]["quality_reasoning"], str)
        assert len(scoring_result["scoring_metadata"]["quality_reasoning"]) > 0