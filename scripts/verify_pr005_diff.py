"""
Verificacion del Diff Logico PR005
Valida que el flujo completo este implementado correctamente
"""
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def verify_imports():
    """Verifica que los imports estén correctos"""
    print("1️⃣  VERIFICANDO IMPORTS...")

    try:
        from app.services.lead_analyzer import LeadAnalyzer, LeadAnalysis
        print("   ✅ LeadAnalyzer importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando LeadAnalyzer: {e}")
        return False

    try:
        from app.services.leadsales.service import LeadsalesService
        print("   ✅ LeadsalesService importado correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando LeadsalesService: {e}")
        return False

    return True

def verify_lead_analyzer_structure():
    """Verifica la estructura del LeadAnalyzer"""
    print("\n2️⃣  VERIFICANDO LEAD ANALYZER...")

    from app.services.lead_analyzer import LeadAnalyzer, LeadAnalysis
    from dataclasses import fields

    # Verificar campos de LeadAnalysis
    expected_fields = {
        'quality_score', 'composite_score', 'conversion_probability',
        'estimated_value', 'profile', 'sophistication_level', 'priority',
        'priority_numeric', 'lead_segment', 'recommended_actions',
        'key_insights', 'risk_factors', 'analysis_timestamp', 'confidence'
    }

    actual_fields = {f.name for f in fields(LeadAnalysis)}

    if expected_fields == actual_fields:
        print(f"   ✅ LeadAnalysis tiene todos los campos esperados ({len(expected_fields)} campos)")
    else:
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        if missing:
            print(f"   ❌ Campos faltantes: {missing}")
        if extra:
            print(f"   ⚠️  Campos extra: {extra}")
        return False

    # Verificar constantes
    analyzer = LeadAnalyzer()

    if len(analyzer.PROFILE_MULTIPLIERS) == 8:
        print(f"   ✅ PROFILE_MULTIPLIERS: 8 perfiles definidos")
    else:
        print(f"   ❌ PROFILE_MULTIPLIERS: esperado 8, encontrado {len(analyzer.PROFILE_MULTIPLIERS)}")
        return False

    if len(analyzer.SOPHISTICATION_MULTIPLIERS) == 3:
        print(f"   ✅ SOPHISTICATION_MULTIPLIERS: 3 niveles definidos")
    else:
        print(f"   ❌ SOPHISTICATION_MULTIPLIERS: esperado 3, encontrado {len(analyzer.SOPHISTICATION_MULTIPLIERS)}")
        return False

    if len(analyzer.LEAD_SEGMENTS) == 8:
        print(f"   ✅ LEAD_SEGMENTS: 8 segmentos definidos")
    else:
        print(f"   ❌ LEAD_SEGMENTS: esperado 8, encontrado {len(analyzer.LEAD_SEGMENTS)}")
        return False

    return True

def verify_service_integration():
    """Verifica la integración en LeadsalesService"""
    print("\n3️⃣  VERIFICANDO INTEGRACIÓN EN SERVICE...")

    from app.services.leadsales.service import LeadsalesService
    import inspect

    service = LeadsalesService()

    # Verificar que lead_analyzer esté inicializado
    if hasattr(service, 'lead_analyzer'):
        print("   ✅ service.lead_analyzer instanciado")
    else:
        print("   ❌ service.lead_analyzer NO encontrado")
        return False

    # Verificar firma de create_lead
    create_lead_source = inspect.getsource(service.create_lead)

    checks = [
        ("lead_analysis = self.lead_analyzer.analyze", "Llamada a lead_analyzer.analyze()"),
        ("Lead analizado: Segment=", "Log de análisis"),
        ("lead_analysis  # ✅ NUEVO parámetro", "Parámetro lead_analysis en enrich_customer_data()"),
    ]

    for check_str, description in checks:
        if check_str in create_lead_source:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} NO encontrado")
            return False

    # Verificar _create_lead_production
    prod_source = inspect.getsource(service._create_lead_production)

    prod_checks = [
        ("lead_analysis: LeadAnalysis", "Parámetro lead_analysis tipado"),
        ("composite_score", "composite_score en payload"),
        ("priority_numeric", "priority_numeric en payload"),
        ("lead_segment", "lead_segment en payload"),
        ("conversion_probability", "conversion_probability en payload"),
        ("lead_analysis.__dict__", "lead_analysis en respuesta"),
    ]

    for check_str, description in prod_checks:
        if check_str in prod_source:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} NO encontrado")
            return False

    return True

def verify_metadata_enrichment():
    """Verifica el enriquecimiento de datos"""
    print("\n4️⃣  VERIFICANDO METADATA ENRICHMENT...")

    from app.services.leadsales.metadata import LeadMetadataExtractor
    import inspect

    extractor = LeadMetadataExtractor()
    enrich_source = inspect.getsource(extractor.enrich_customer_data)

    checks = [
        ("lead_analysis: Optional[Any] = None", "Parámetro lead_analysis"),
        ("enriched_data[\"lead_analysis\"]", "Agregar lead_analysis a enriched_data"),
        ("composite_score", "composite_score en lead_analysis"),
        ("key_insights", "key_insights en lead_analysis"),
        ("recommended_actions", "recommended_actions en lead_analysis"),
        ("risk_factors", "risk_factors en lead_analysis"),
    ]

    for check_str, description in checks:
        if check_str in enrich_source:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} NO encontrado")
            return False

    return True

def verify_visualization():
    """Verifica las visualizaciones enriquecidas"""
    print("\n5️⃣  VERIFICANDO VISUALIZACIONES...")

    from app.services.leadsales.visualization import CRMVisualizationBuilder
    import inspect

    builder = CRMVisualizationBuilder()

    # Verificar build_crm_preview
    preview_source = inspect.getsource(builder.build_crm_preview)

    preview_checks = [
        ("lead_analysis: Optional[Any] = None", "Parámetro lead_analysis"),
        ("integrated_analysis", "Sección integrated_analysis"),
        ("composite_score", "composite_score en preview"),
        ("lead_segment", "lead_segment en preview"),
    ]

    for check_str, description in preview_checks:
        if check_str in preview_source:
            print(f"   ✅ build_crm_preview: {description}")
        else:
            print(f"   ❌ build_crm_preview: {description} NO encontrado")
            return False

    # Verificar build_demo_simulation
    demo_source = inspect.getsource(builder.build_demo_simulation)

    demo_checks = [
        ("lead_analysis: Optional[Any] = None", "Parámetro lead_analysis"),
        ("integrated_analysis", "Sección integrated_analysis completa"),
        ("segment_description", "segment_description"),
        ("key_insights", "key_insights"),
        ("recommended_actions", "recommended_actions"),
    ]

    for check_str, description in demo_checks:
        if check_str in demo_source:
            print(f"   ✅ build_demo_simulation: {description}")
        else:
            print(f"   ❌ build_demo_simulation: {description} NO encontrado")
            return False

    # Verificar _get_segment_description
    if hasattr(builder, '_get_segment_description'):
        print("   ✅ _get_segment_description() existe")
    else:
        print("   ❌ _get_segment_description() NO encontrado")
        return False

    return True

def verify_demo_visualizer():
    """Verifica el demo visualizer"""
    print("\n6️⃣  VERIFICANDO DEMO VISUALIZER...")

    from app.agents.leadsales.demo.demo_visualizer import DemoVisualizer
    import inspect

    display_source = inspect.getsource(DemoVisualizer.display_crm_preview)

    checks = [
        ("integrated_analysis", "Extracción de integrated_analysis"),
        ("🎯 ANÁLISIS INTEGRADO", "Sección de análisis integrado"),
        ("Composite Score", "Mostrar composite score"),
        ("Prob. Conversión", "Mostrar probabilidad conversión"),
        ("💡 INSIGHTS CLAVE", "Sección de insights"),
        ("✅ ACCIONES RECOMENDADAS", "Sección de acciones"),
        ("⚠️  FACTORES DE RIESGO", "Sección de riesgos"),
    ]

    for check_str, description in checks:
        if check_str in display_source:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} NO encontrado")
            return False

    return True

def verify_data_flow():
    """Verifica el flujo completo de datos"""
    print("\n7️⃣  VERIFICANDO FLUJO DE DATOS...")

    # Simular scoring_result
    scoring_result = {
        "quality_score": 85,
        "priority": "ALTA",
        "tags": ["COMPRA", "APARTAMENTO"],
        "confidence": 0.85
    }

    # Simular classification_result
    class MockClassification:
        profile = "inversionista"
        sophistication_level = "alto"
        confidence = 0.90
        reasoning = "Palabras clave de inversión detectadas"
        detected_keywords = ["inversión", "ROI"]
        profession_explicit = True
        classification_method = "hybrid"
        cost_usd = 0.0
        latency_ms = 50

    classification_result = MockClassification()

    # Simular metadata
    metadata = {
        "location": "Poblado",
        "budget_range": "500m_1000m",
        "property_type": "apartamento",
        "urgency_level": "high"
    }

    # Ejecutar análisis
    from app.services.lead_analyzer import LeadAnalyzer

    analyzer = LeadAnalyzer()

    try:
        lead_analysis = analyzer.analyze(
            scoring_result=scoring_result,
            classification_result=classification_result,  # Pasar el objeto directamente
            metadata={"customer_needs": "Busco apartamento urgente en Poblado"}
        )

        print(f"   ✅ Análisis ejecutado correctamente")
        print(f"      • Quality Score: {lead_analysis.quality_score}/100")
        print(f"      • Composite Score: {lead_analysis.composite_score:.1f}/100")
        print(f"      • Conversion Probability: {lead_analysis.conversion_probability:.2%}")
        print(f"      • Lead Segment: {lead_analysis.lead_segment}")
        print(f"      • Priority: {lead_analysis.priority} (Numérico: {lead_analysis.priority_numeric}/10)")
        print(f"      • Insights: {len(lead_analysis.key_insights)} generados")
        print(f"      • Actions: {len(lead_analysis.recommended_actions)} recomendadas")
        print(f"      • Risks: {len(lead_analysis.risk_factors)} identificados")

        # Verificar fórmula de composite score
        expected_composite = min(85 * 1.3 * 1.2, 100)  # inversionista (1.3) * alto (1.2)

        if abs(lead_analysis.composite_score - expected_composite) < 0.1:
            print(f"   ✅ Fórmula composite score correcta: {expected_composite:.1f}")
        else:
            print(f"   ❌ Fórmula composite score incorrecta: esperado {expected_composite:.1f}, obtenido {lead_analysis.composite_score:.1f}")
            return False

        # Verificar que sea high_value_investor
        if lead_analysis.lead_segment == "high_value_investor":
            print(f"   ✅ Segmento correcto: high_value_investor")
        else:
            print(f"   ⚠️  Segmento: {lead_analysis.lead_segment} (esperado: high_value_investor)")

        return True

    except Exception as e:
        print(f"   ❌ Error ejecutando análisis: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("="*80)
    print("VERIFICACIÓN DIFF LÓGICO PR005")
    print("="*80)

    results = {
        "Imports": verify_imports(),
        "LeadAnalyzer Structure": verify_lead_analyzer_structure(),
        "Service Integration": verify_service_integration(),
        "Metadata Enrichment": verify_metadata_enrichment(),
        "Visualization": verify_visualization(),
        "Demo Visualizer": verify_demo_visualizer(),
        "Data Flow": verify_data_flow(),
    }

    print("\n" + "="*80)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*80)

    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {check_name}")

    all_passed = all(results.values())

    print("="*80)
    if all_passed:
        print("🎉 TODAS LAS VERIFICACIONES PASARON")
        print("✅ El Diff Lógico de PR005 está COMPLETO")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("⚠️  El Diff Lógico de PR005 está INCOMPLETO")
    print("="*80)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())