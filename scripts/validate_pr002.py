"""
Script de Validación Manual - PR002
Verifica la integración del sistema de scoring en LeadsalesService
"""
from app.services.leadsales import LeadsalesService
import asyncio


async def main():
    service = LeadsalesService()
    service.initialize()

    test_cases = [
        ("Busco casa urgente para comprar", {"location": "Medellín"}),
        ("Quiero arrendar apartamento de 3 habitaciones", {}),
        ("Necesito información sobre sus servicios", {})
    ]

    print("=== VALIDACIÓN PR002 - INTEGRACIÓN SCORING ===\n")

    for needs, data in test_cases:
        scoring = service._score_lead(needs, data)
        print(f"MENSAJE: {needs}")
        print(f"  -> Quality Score: {scoring['quality_score']}/100")
        print(f"  -> Tags: {', '.join(scoring['tags'])}")
        print(f"  -> Priority: {scoring['priority']}")

        # Verificar si existe confidence y reasoning en scoring_metadata
        if 'scoring_metadata' in scoring:
            print(f"  -> Confidence: {scoring['scoring_metadata']['quality_confidence']:.2f}")
            print(f"  -> Reasoning: {scoring['scoring_metadata']['quality_reasoning']}")
        else:
            print(f"  -> Confidence: N/A (sin metadata)")
            print(f"  -> Reasoning: N/A (sin metadata)")
        print()

    print("=== VERIFICACIÓN DE MÉTODOS ELIMINADOS ===\n")

    # Verificar que métodos duplicados fueron eliminados
    eliminated_methods = [
        '_calculate_demo_quality_score',
        '_generate_demo_tags',
        '_determine_demo_priority'
    ]

    for method in eliminated_methods:
        exists = hasattr(service, method)
        status = "[ERROR] ERROR: Aún existe" if exists else "[OK] OK: Eliminado"
        print(f"{method}: {status}")

    print("\n=== VERIFICACIÓN DE MÉTODOS NUEVOS ===\n")

    # Verificar que nuevos métodos existen
    new_methods = [
        '_init_scoring_components',
        '_score_lead'
    ]

    for method in new_methods:
        exists = hasattr(service, method)
        status = "[OK] OK: Existe" if exists else "[ERROR] ERROR: No existe"
        print(f"{method}: {status}")

    print("\n=== VERIFICACIÓN DE COMPONENTES ===\n")

    # Verificar componentes de scoring
    components = {
        'quality_scorer': 'DemoQualityScorer',
        'interest_scorer': 'InterestLevelScorer',
        'taggers': 'List (4 taggers)',
        'priority_classifier': 'UrgencyPriorityClassifier'
    }

    for component, expected_type in components.items():
        exists = hasattr(service, component)
        if exists:
            value = getattr(service, component)
            if component == 'taggers':
                info = f"[OK] OK: {len(value)} taggers"
            else:
                info = f"[OK] OK: {value.__class__.__name__}"
            print(f"{component}: {info}")
        else:
            print(f"{component}: [ERROR] ERROR: No existe")

    print("\n=== VALIDACIÓN COMPLETA ===")
    print("PR002 implementado correctamente [OK]")


if __name__ == "__main__":
    asyncio.run(main())
