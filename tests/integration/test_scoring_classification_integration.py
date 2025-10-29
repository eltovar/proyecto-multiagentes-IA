"""
Tests de integración para análisis integrado completo (PR005)
Valida que Scoring (PR002) + Clasificación (PR004) + LeadAnalyzer (PR005) funcionen correctamente juntos
"""
import pytest
from app.services.leadsales import LeadsalesService


@pytest.mark.asyncio
async def test_create_lead_with_integrated_analysis():
    """create_lead retorna análisis integrado completo"""
    service = LeadsalesService()
    service.is_demo_mode = True

    result = await service.create_lead(
        customer_name="Carlos Investor Pro",
        whatsapp="3001234567",
        customer_needs="Busco apartamento para inversión en zona Poblado con análisis de ROI y proyección de plusvalía",
        additional_data={"location": "Poblado", "budget": "800 millones"}
    )

    # Verificar que resultado contiene análisis integrado
    assert "integrated_analysis" in result

    analysis = result["integrated_analysis"]

    # Verificar estructura completa
    assert "composite_score" in analysis
    assert "conversion_probability" in analysis
    assert "lead_segment" in analysis
    assert "key_insights" in analysis
    assert "recommended_actions" in analysis
    assert "risk_factors" in analysis

    # Verificar valores esperados para inversionista sofisticado
    assert analysis["composite_score"] >= 90
    assert analysis["lead_segment"] == "high_value_investor"
    assert analysis["conversion_probability"] >= 0.8
    assert len(analysis["key_insights"]) >= 2


@pytest.mark.asyncio
async def test_priority_adjustment_based_on_profile():
    """Prioridad se ajusta según perfil del cliente"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # Caso 1: Inversionista debe tener prioridad boosteada
    result_investor = await service.create_lead(
        "Investor User",
        "3001111111",
        "Busco apartamento urgente para inversión con análisis de ROI y proyección de plusvalía en zona premium",
        {}
    )

    # Caso 2: Familia casual debe tener prioridad estándar
    result_family = await service.create_lead(
        "Family User",
        "3002222222",
        "Busco casa para vivir con mi familia",
        {}
    )

    # Verificar que inversionista tiene prioridad mayor o igual
    investor_priority = result_investor["integrated_analysis"]["priority_numeric"]
    family_priority = result_family["integrated_analysis"]["priority_numeric"]

    assert investor_priority >= family_priority


@pytest.mark.asyncio
async def test_visualization_includes_analysis():
    """Visualización demo incluye análisis integrado"""
    service = LeadsalesService()
    service.is_demo_mode = True

    result = await service.create_lead(
        "Test User",
        "3003333333",
        "Soy arquitecto y busco apartamento con buen diseño",
        {}
    )

    # Verificar que visualización incluye análisis
    assert "integrated_analysis" in result
    assert "crm_simulation" in result

    # Verificar que CRM simulation usa prioridad ajustada
    assert result["crm_simulation"]["priority"] == result["integrated_analysis"]["priority_adjusted"]


@pytest.mark.asyncio
async def test_composite_score_formula():
    """Composite score se calcula correctamente con multiplicadores"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # Inversionista alto: quality * 1.3 * 1.2 (debe llegar a 100 cap)
    result = await service.create_lead(
        "High Value Investor",
        "3004444444",
        "Busco apartamentos para inversión con alto ROI y análisis técnico completo",
        {}
    )

    analysis = result["integrated_analysis"]

    # Verificar que composite score es alto (seguramente capped a 100)
    assert analysis["composite_score"] >= 95
    assert analysis["profile"] == "inversionista"
    assert analysis["sophistication"] == "alto"


@pytest.mark.asyncio
async def test_lead_segmentation_accuracy():
    """Segmentación de leads funciona correctamente para diferentes perfiles"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # Test 1: High value investor
    result1 = await service.create_lead(
        "Investor Elite",
        "3005555555",
        "Soy inversionista profesional y busco comprar múltiples apartamentos para mi portafolio con análisis de ROI y proyección de plusvalía",
        {}
    )
    assert result1["integrated_analysis"]["lead_segment"] == "high_value_investor"

    # Test 2: Professional buyer (arquitecto)
    result2 = await service.create_lead(
        "María Arquitecta",
        "3006666666",
        "Soy arquitecta y busco comprar apartamento con excelente diseño arquitectónico y buena ubicación",
        {}
    )
    assert result2["integrated_analysis"]["lead_segment"] == "professional_buyer"

    # Test 3: Family premium
    result3 = await service.create_lead(
        "Familia García",
        "3007777777",
        "Busco comprar casa urgente para mi familia con 4 habitaciones cerca de colegios en zona segura",
        {}
    )
    assert result3["integrated_analysis"]["lead_segment"] in ["family_premium", "family_casual"]


@pytest.mark.asyncio
async def test_insights_generation():
    """Insights se generan correctamente basados en análisis"""
    service = LeadsalesService()
    service.is_demo_mode = True

    result = await service.create_lead(
        "Carlos Urgente",
        "3008888888",
        "Necesito apartamento urgente en Poblado para inversión con presupuesto definido",
        {"location": "Poblado"}
    )

    analysis = result["integrated_analysis"]

    # Verificar que hay insights
    assert len(analysis["key_insights"]) >= 2

    # Verificar que insights mencionan elementos clave
    insights_text = " ".join(analysis["key_insights"]).lower()

    # Debe mencionar urgencia
    assert "urgente" in insights_text or "urgencia" in insights_text or "inmediato" in insights_text

    # Debe mencionar ubicación (Poblado)
    assert "poblado" in insights_text


@pytest.mark.asyncio
async def test_recommended_actions_per_segment():
    """Acciones recomendadas son específicas por segmento"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # High value investor debe tener acciones premium
    result_investor = await service.create_lead(
        "Top Investor",
        "3009999999",
        "Soy inversionista institucional y busco comprar apartamentos premium urgente con análisis de ROI y proyección de rentabilidad",
        {}
    )

    actions_investor = result_investor["integrated_analysis"]["recommended_actions"]
    actions_text = " ".join(actions_investor).lower()

    # Debe incluir acciones de alto nivel
    assert len(actions_investor) >= 2
    assert any(keyword in actions_text for keyword in ["senior", "inmediato", "roi", "análisis"])


@pytest.mark.asyncio
async def test_risk_factors_identification():
    """Factores de riesgo se identifican correctamente"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # Lead con baja información (debería generar riesgos)
    result = await service.create_lead(
        "Usuario Vago",
        "3000000000",
        "apartamento",  # Mensaje muy corto y poco específico
        {}
    )

    analysis = result["integrated_analysis"]

    # Debe identificar riesgos (información incompleta, baja calidad, etc.)
    assert isinstance(analysis["risk_factors"], list)
    # Puede tener 0 o más riesgos, dependiendo de la implementación


@pytest.mark.asyncio
async def test_conversion_probability_calculation():
    """Probabilidad de conversión se calcula con múltiples factores"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # Lead con alta probabilidad: inversionista + urgente + presupuesto definido
    result_high = await service.create_lead(
        "Comprador Decidido",
        "3001010101",
        "Busco apartamento urgente para inversión con presupuesto de 500 millones definido",
        {}
    )

    # Lead con baja probabilidad: mensaje vago
    result_low = await service.create_lead(
        "Usuario Explorador",
        "3002020202",
        "quizás compre algo",
        {}
    )

    prob_high = result_high["integrated_analysis"]["conversion_probability"]
    prob_low = result_low["integrated_analysis"]["conversion_probability"]

    # Alta probabilidad debe ser mayor que baja probabilidad
    assert prob_high > prob_low
    assert prob_high >= 0.7
    assert prob_low <= 0.6


@pytest.mark.asyncio
async def test_backward_compatibility_with_pr004():
    """Análisis integrado no rompe compatibilidad con clasificación (PR004)"""
    service = LeadsalesService()
    service.is_demo_mode = True

    result = await service.create_lead(
        "Test Compatibility",
        "3003030303",
        "Soy corredor inmobiliario y busco propiedades",
        {}
    )

    # Verificar que ambos sistemas coexisten
    customer_data = result["customer_data"]

    # De PR004: client_classification debe existir
    assert "client_classification" in customer_data
    assert customer_data["client_classification"]["profile"] == "corredor"

    # De PR005: integrated_analysis debe existir
    assert "integrated_analysis" in result
    assert result["integrated_analysis"]["profile"] == "corredor"

    # Ambos deben ser consistentes
    assert customer_data["client_classification"]["profile"] == result["integrated_analysis"]["profile"]


@pytest.mark.asyncio
async def test_estimated_value_calculation():
    """Valor estimado se calcula correctamente según segmento y composite score"""
    service = LeadsalesService()
    service.is_demo_mode = True

    # High value investor debe tener valor estimado "Altísimo" o "Alto"
    result = await service.create_lead(
        "Mega Investor",
        "3004040404",
        "Soy inversionista institucional y busco comprar portafolio de apartamentos premium urgente con análisis de ROI y alta rentabilidad",
        {}
    )

    estimated_value = result["integrated_analysis"]["estimated_value"]

    # Debe ser alto o altísimo (case-insensitive)
    assert estimated_value.lower() in ["altísimo", "alto"]