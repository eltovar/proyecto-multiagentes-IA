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

    # Forzar modo demo (usar atributo público)
    service.is_demo_mode = True

    result = await service.create_lead(
        customer_name="Test User",
        whatsapp="573001234567",
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

    # Forzar modo producción (usar atributo público)
    service.is_demo_mode = False

    # Mock del cliente API para capturar el payload
    captured_payload = {}

    async def mock_create_lead_api(lead_data):
        """Mock que captura payload y devuelve respuesta simulada"""
        captured_payload.update(lead_data)
        return {"lead_id": "PROD-12345", "status": "created"}

    # Mockear el método correcto en la cadena de llamadas
    service.client.create_lead_api = mock_create_lead_api

    result = await service.create_lead(
        customer_name="Test User",
        whatsapp="573001234567",
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
    """Validar que métodos duplicados fueron eliminados y arquitectura modular implementada"""
    service = LeadsalesService()

    # Verificar que los métodos antiguos NO existen (eliminados en PR002)
    assert not hasattr(service, '_calculate_demo_quality_score'), \
        "Method _calculate_demo_quality_score should be deleted"
    assert not hasattr(service, '_generate_demo_tags'), \
        "Method _generate_demo_tags should be deleted"
    assert not hasattr(service, '_determine_demo_priority'), \
        "Method _determine_demo_priority should be deleted"

    # Verificar arquitectura modular (PR003): componentes especializados
    assert hasattr(service, 'scoring'), \
        "Service should have 'scoring' component (LeadScoringIntegrator)"
    assert hasattr(service, '_score_lead'), \
        "Method _score_lead should exist as orchestrator"

    # Verificar que NO tiene componentes directos (ahora están en LeadScoringIntegrator)
    assert not hasattr(service, 'quality_scorer'), \
        "quality_scorer should NOT be in LeadsalesService (moved to LeadScoringIntegrator)"


@pytest.mark.asyncio
async def test_scoring_components_initialized():
    """Validar que componentes de scoring se inicializan correctamente en arquitectura modular"""
    service = LeadsalesService()

    # Verificar que LeadScoringIntegrator existe
    assert hasattr(service, 'scoring'), \
        "Service should have 'scoring' component (LeadScoringIntegrator)"

    # Verificar que scoring está inicializado
    assert service.scoring is not None, \
        "LeadScoringIntegrator should be initialized"

    # Verificar que metadata_extractor existe
    assert hasattr(service, 'metadata_extractor'), \
        "Service should have 'metadata_extractor' component"

    # Verificar que client_classifier existe (agregado en PR004)
    assert hasattr(service, 'client_classifier'), \
        "Service should have 'client_classifier' component"

    # Verificar que visualization existe
    assert hasattr(service, 'visualization'), \
        "Service should have 'visualization' component"

    # Verificar método orquestador
    assert hasattr(service, '_score_lead'), \
        "Service should have '_score_lead' orchestrator method"


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
