import pytest
from app.services.leadsales import LeadsalesService


@pytest.mark.asyncio
async def test_create_lead_with_classification():
    """create_lead ahora incluye clasificación de cliente"""
    service = LeadsalesService()
    service.is_demo_mode = True
    
    result = await service.create_lead(
        customer_name="Carlos Investor",
        whatsapp="3001234567",
        customer_needs="Busco apartamento para inversión en zona con alta plusvalía y buena rentabilidad",
        additional_data={"location": "Poblado"}
    )
    
    # Verificar que lead contiene clasificación
    assert "client_classification" in result["customer_data"]
    
    classification = result["customer_data"]["client_classification"]
    
    # Verificar estructura de clasificación
    assert "profile" in classification
    assert "sophistication_level" in classification
    assert "confidence" in classification
    assert "classification_method" in classification
    assert "cost_usd" in classification
    
    # Verificar clasificación correcta para inversionista
    assert classification["profile"] == "inversionista"
    assert classification["sophistication_level"] in ["alto", "medio"]
    assert classification["confidence"] >= 0.7


@pytest.mark.asyncio
async def test_classification_integrates_with_scoring():
    """Clasificación no afecta scoring (son independientes)"""
    service = LeadsalesService()
    service.is_demo_mode = True
    
    result = await service.create_lead(
        customer_name="María Arquitecta",
        whatsapp="3009876543",
        customer_needs="Soy arquitecta y busco casa para comprar urgente con buen diseño",
        additional_data={}
    )
    
    # Verificar que tanto scoring como clasificación están presentes
    customer_data = result["customer_data"]
    
    # Scoring (de PR002)
    assert "quality_score" in customer_data
    assert "priority" in customer_data
    assert "tags" in customer_data
    
    # Clasificación (de PR004)
    assert "client_classification" in customer_data
    assert customer_data["client_classification"]["profile"] == "arquitecto"
    
    # Ambos sistemas son independientes
    assert customer_data["quality_score"] >= 70  # Lead de calidad (compra + urgente)
    assert customer_data["client_classification"]["confidence"] >= 0.8


@pytest.mark.skip(reason="Requiere OpenAI API Tier 1+ (rate limits: Free=3 RPM/100k TPM, Tier1=500 RPM/200k TPM)")
@pytest.mark.asyncio
async def test_classification_performance_acceptable():
    """
    Clasificación no degrada performance significativamente.

    NOTA: Test deshabilitado temporalmente debido a rate limits de OpenAI Free tier.

    Para habilitar este test:
    1. Agregar método de pago en OpenAI (https://platform.openai.com/account/billing)
    2. Verificar que tu API key tiene Tier 1+ (500 RPM, 200k TPM)
    3. Eliminar el decorador @pytest.mark.skip de la línea 66
    4. Ejecutar: pytest tests/integration/test_hybrid_classification.py::test_classification_performance_acceptable -v

    Objetivo del test: Validar que el promedio de 10 clasificaciones es < 1000ms
    - 60% casos usan reglas (~5ms cada uno)
    - 40% casos usan LLM (~800ms cada uno)
    - Promedio esperado: ~325ms por clasificación
    """
    import time

    service = LeadsalesService()
    service.is_demo_mode = True
    
    start = time.perf_counter()
    
    for i in range(10):
        await service.create_lead(
            f"Test User {i}",
            f"30012345{i:02d}",
            "Busco apartamento para comprar" if i % 2 == 0 else "Busco apartamento para inversión",
            {}
        )
    
    end = time.perf_counter()
    avg_time_ms = ((end - start) / 10) * 1000
    
    # Promedio debe ser < 1000ms (incluyendo casos LLM)
    # 60% reglas (~5ms) + 40% LLM (~800ms) = ~325ms promedio esperado
    assert avg_time_ms < 1000, f"Performance degradada: {avg_time_ms:.0f}ms promedio"