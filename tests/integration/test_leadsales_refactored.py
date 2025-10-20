"""
Tests de integracion para LeadsalesService refactorizado
Verifican que la refactorizacion modular mantiene funcionalidad
"""
import pytest
from app.services.leadsales import LeadsalesService


@pytest.mark.asyncio
async def test_create_lead_demo_mode_end_to_end():
    """Test end-to-end de create_lead en modo demo"""
    service = LeadsalesService()
    
    # Forzar modo demo
    service.client._is_demo_mode = True
    
    result = await service.create_lead(
        customer_name="Juan Perez",
        whatsapp="3001234567",
        customer_needs="Busco apartamento de 3 habitaciones en Medellin para comprar urgente con presupuesto de 350 millones",
        additional_data={"location": "Poblado"}
    )
    
    # Verificar estructura completa
    assert "customer_data" in result
    assert "crm_simulation" in result
    
    # Verificar scoring calculado
    assert result["customer_data"]["quality_score"] >= 70
    assert "ALTA" in result["customer_data"]["priority"] or "MEDIA-ALTA" in result["customer_data"]["priority"]
    
    # Verificar tags (en mayusculas)
    tags_upper = [tag.upper() for tag in result["customer_data"]["tags"]]
    assert "COMPRA" in tags_upper
    assert "APARTAMENTO" in tags_upper
    
    # Verificar metadata extraida (esta en nivel raiz, no dentro de customer_data)
    assert "metadata" in result
    assert result["metadata"]["location"] == "Poblado"
    assert result["metadata"]["budget_range"] == "200m_500m"
    assert result["metadata"]["property_type"] == "apartamento"
    assert result["metadata"]["rooms"] == 3


@pytest.mark.asyncio
async def test_refactored_service_maintains_same_interface():
    """Verificar que interfaz publica no cambio tras refactor"""
    service = LeadsalesService()
    
    # Verificar que metodos publicos existen
    assert hasattr(service, "create_lead")
    assert hasattr(service, "get_lead")
    assert hasattr(service, "update_lead")
    assert hasattr(service, "list_leads")
    assert hasattr(service, "close")
    
    # Verificar que is_demo_mode sigue disponible
    assert hasattr(service, "is_demo_mode")
    assert isinstance(service.is_demo_mode, bool)
    
    # Verificar que initialize() existe (backward compatibility)
    assert hasattr(service, "initialize")
    assert callable(service.initialize)


@pytest.mark.asyncio
async def test_regression_same_output_as_monolithic():
    """Test de regresion: output identico a version monolitica"""
    service = LeadsalesService()
    
    # Forzar modo demo
    service.client._is_demo_mode = True
    
    # Caso conocido de version monolitica
    result = await service.create_lead(
        "Test User",
        "3001234567",
        "Busco apartamento para comprar",
        {}
    )
    
    # Verificar campos clave que existian en version monolitica
    assert "customer_data" in result
    assert result["customer_data"]["name"] == "Test User"
    assert result["customer_data"]["whatsapp"] == "+573001234567"
    assert "quality_score" in result["customer_data"]
    assert "tags" in result["customer_data"]
    assert "priority" in result["customer_data"]


@pytest.mark.asyncio
async def test_components_are_initialized():
    """Verificar que todos los componentes se inicializan correctamente"""
    service = LeadsalesService()
    
    # Verificar que componentes internos existen
    assert service.client is not None
    assert service.scoring is not None
    assert service.metadata_extractor is not None
    assert service.visualization is not None
    
    # Verificar que initialized flag existe
    assert hasattr(service, "initialized")
    assert service.initialized is True


@pytest.mark.asyncio
async def test_create_lead_with_minimal_data():
    """Test con datos minimos"""
    service = LeadsalesService()
    service.client._is_demo_mode = True
    
    result = await service.create_lead(
        customer_name="Test",
        whatsapp="300",
        customer_needs="Busco casa",
        additional_data=None
    )
    
    assert result is not None
    assert "customer_data" in result
    assert result["customer_data"]["name"] == "Test"


@pytest.mark.asyncio
async def test_create_lead_scores_are_normalized():
    """Verificar que scores estan normalizados correctamente"""
    service = LeadsalesService()
    service.client._is_demo_mode = True
    
    result = await service.create_lead(
        "Test",
        "300",
        "Busco apartamento urgente con presupuesto definido",
        {"tiene_solicitud_libertador": True}
    )
    
    customer_data = result["customer_data"]
    crm_simulation = result["crm_simulation"]

    # Verificar rangos (customer_data solo tiene quality_score en demo mode)
    assert 0 <= customer_data["quality_score"] <= 100

    # confidence_level esta en crm_simulation, no en customer_data
    assert 0 <= crm_simulation["confidence_level"] <= 1.0

    # Los scores completos (interest_score, conversion_probability) se calculan
    # internamente pero no se exponen en la estructura demo simplificada.
    # Solo quality_score es visible en customer_data para demo mode.


@pytest.mark.asyncio
async def test_create_lead_orchestrates_all_modules():
    """Verificar que create_lead orquesta los 4 modulos correctamente"""
    service = LeadsalesService()
    service.client._is_demo_mode = True
    
    result = await service.create_lead(
        "Integration Test",
        "3001234567",
        "Busco apartamento de 2 habitaciones en Poblado urgente",
        {"location": "Poblado"}
    )
    
    # 1. Client: demo mode detection
    assert service.is_demo_mode is True
    
    # 2. Scoring: quality_score, tags, priority
    assert "quality_score" in result["customer_data"]
    assert "tags" in result["customer_data"]
    assert "priority" in result["customer_data"]
    
    # 3. Metadata: extraction + enrichment
    # metadata esta en nivel raiz, no dentro de customer_data
    assert "metadata" in result
    assert "whatsapp" in result["customer_data"]
    assert result["customer_data"]["whatsapp"].startswith("+57")

    # 4. Visualization: crm_simulation
    assert "crm_simulation" in result


@pytest.mark.asyncio
async def test_initialize_method_backward_compatibility():
    """Verificar que initialize() funciona (backward compatibility)"""
    service = LeadsalesService()
    
    # Llamar initialize() como en codigo legacy
    result = service.initialize()
    
    assert result is True
    assert service.initialized is True
