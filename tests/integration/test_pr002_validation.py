"""
Tests de Validación del PR002 - Integración de Sistema Scoring
Estos tests validan los requisitos específicos del PR002
"""
import pytest
from app.services.leadsales import LeadsalesService


@pytest.mark.asyncio
async def test_demo_mode_uses_refactored_scoring():
    """Verifica que modo demo usa estrategias refactorizadas"""
    service = LeadsalesService()
    service.initialize()

    # Forzar modo demo
    def force_demo_mode():
        return True

    service._is_demo_mode = force_demo_mode

    result = await service.create_lead(
        customer_name="Test User",
        whatsapp_id="573001234567",
        customer_needs="Busco apartamento urgente para comprar en Medellín con presupuesto de 300 millones",
        additional_data={"location": "Medellín"}
    )

    # Verificar scoring calculado correctamente
    customer_data = result["customer_data"]

    assert customer_data["quality_score"] >= 70, \
        f"Expected quality_score >= 70, got {customer_data['quality_score']}"  # Keywords: comprar, urgente, apartamento

    tags = customer_data["tags"]
    assert "COMPRA" in tags, f"Expected 'COMPRA' in tags, got {tags}"
    assert "APARTAMENTO" in tags, f"Expected 'APARTAMENTO' in tags, got {tags}"
    assert "URGENTE" in tags, f"Expected 'URGENTE' in tags, got {tags}"

    priority = customer_data["priority"]
    assert "ALTA" in priority or "MEDIA-ALTA" in priority, \
        f"Expected priority to be ALTA or MEDIA-ALTA, got {priority}"


@pytest.mark.asyncio
async def test_production_mode_includes_scoring():
    """Verifica que producción ahora envía scoring al CRM"""
    service = LeadsalesService()
    service.initialize()

    # Mock para simular producción sin modo demo
    def force_production_mode():
        return False

    service._is_demo_mode = force_production_mode

    # Mock del cliente HTTP para capturar el payload
    from unittest.mock import AsyncMock, MagicMock

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"lead_id": "12345", "status": "created"}

    captured_payload = {}

    async def mock_post_lead(lead_data):
        captured_payload.update(lead_data)
        return {"success": True, "lead_id": "PROD-12345"}

    service.client.post_lead = mock_post_lead

    result = await service.create_lead(
        customer_name="Test User",
        whatsapp_id="573001234567",
        customer_needs="Necesito local comercial para arrendar",
        additional_data={}
    )

    # Verificar que payload incluye scoring
    assert "quality_score" in captured_payload, \
        f"Expected 'quality_score' in payload, got {captured_payload.keys()}"
    assert "tags" in captured_payload, \
        f"Expected 'tags' in payload, got {captured_payload.keys()}"
    assert "priority" in captured_payload, \
        f"Expected 'priority' in payload, got {captured_payload.keys()}"

    # Verificar que priority no es valor fijo "normal"
    assert captured_payload["priority"] != "normal", \
        f"Priority should not be 'normal', got {captured_payload['priority']}"

    # Verificar tags específicos
    tags = captured_payload["tags"]
    assert "ARRIENDO" in tags, f"Expected 'ARRIENDO' in tags, got {tags}"
    assert "LOCAL_COMERCIAL" in tags, f"Expected 'LOCAL_COMERCIAL' in tags, got {tags}"


@pytest.mark.asyncio
async def test_regression_scoring_consistency():
    """Test de regresión: comparar scoring con valores conocidos"""
    service = LeadsalesService()
    service.initialize()

    # Caso 1: Lead de alta calidad
    scoring_high = service._score_lead(
        "Busco casa urgente para comprar con presupuesto de 500 millones",
        {"location": "Poblado"}
    )
    assert scoring_high["quality_score"] >= 80, \
        f"High quality lead should have score >= 80, got {scoring_high['quality_score']}"
    assert "ALTA" in scoring_high["priority"], \
        f"High quality urgent lead should have ALTA priority, got {scoring_high['priority']}"

    # Caso 2: Lead de calidad media
    scoring_medium = service._score_lead(
        "Me interesa arrendar apartamento",
        {}
    )
    assert 50 <= scoring_medium["quality_score"] < 100, \
        f"Medium quality lead should have score 50-100, got {scoring_medium['quality_score']}"
    assert "MEDIA" in scoring_medium["priority"], \
        f"Medium quality lead should have MEDIA priority, got {scoring_medium['priority']}"

    # Caso 3: Lead de baja calidad
    scoring_low = service._score_lead(
        "Solo pregunta por información general",
        {}
    )
    assert scoring_low["quality_score"] < 50, \
        f"Low quality lead should have score < 50, got {scoring_low['quality_score']}"


@pytest.mark.asyncio
async def test_no_duplicate_methods_exist():
    """Validar que métodos duplicados fueron eliminados"""
    service = LeadsalesService()

    # Verificar que los métodos antiguos NO existen
    assert not hasattr(service, '_calculate_demo_quality_score'), \
        "Method _calculate_demo_quality_score should be deleted"
    assert not hasattr(service, '_generate_demo_tags'), \
        "Method _generate_demo_tags should be deleted"
    assert not hasattr(service, '_determine_demo_priority'), \
        "Method _determine_demo_priority should be deleted"

    # Verificar que los nuevos métodos SÍ existen
    assert hasattr(service, '_init_scoring_components'), \
        "Method _init_scoring_components should exist"
    assert hasattr(service, '_score_lead'), \
        "Method _score_lead should exist"


@pytest.mark.asyncio
async def test_scoring_components_initialized():
    """Validar que componentes de scoring se inicializan correctamente"""
    service = LeadsalesService()

    # Verificar que componentes existen
    assert hasattr(service, 'quality_scorer'), \
        "Service should have quality_scorer"
    assert hasattr(service, 'interest_scorer'), \
        "Service should have interest_scorer"
    assert hasattr(service, 'taggers'), \
        "Service should have taggers"
    assert hasattr(service, 'priority_classifier'), \
        "Service should have priority_classifier"

    # Verificar tipos correctos
    assert len(service.taggers) == 4, \
        f"Expected 4 taggers, got {len(service.taggers)}"

    # Verificar que son instancias correctas
    from app.services.scoring.strategies import (
        DemoQualityScorer,
        InterestLevelScorer,
        UrgencyPriorityClassifier
    )

    assert isinstance(service.quality_scorer, DemoQualityScorer), \
        "quality_scorer should be DemoQualityScorer instance"
    assert isinstance(service.interest_scorer, InterestLevelScorer), \
        "interest_scorer should be InterestLevelScorer instance"
    assert isinstance(service.priority_classifier, UrgencyPriorityClassifier), \
        "priority_classifier should be UrgencyPriorityClassifier instance"


@pytest.mark.asyncio
async def test_scoring_performance():
    """Verifica que scoring no degrada rendimiento"""
    import time

    service = LeadsalesService()
    service.initialize()

    start = time.perf_counter()
    for _ in range(100):
        service._score_lead("Busco apartamento en Medellín", {})
    end = time.perf_counter()

    avg_time_ms = ((end - start) / 100) * 1000
    assert avg_time_ms < 1.0, f"Scoring demasiado lento: {avg_time_ms:.2f}ms (límite: 1ms)"

    print(f"\nOK: Performance OK: {avg_time_ms:.3f}ms promedio por scoring (límite: 1ms)")
