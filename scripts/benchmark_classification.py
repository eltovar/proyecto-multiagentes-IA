"""
Benchmark de performance del sistema híbrido de clasificación
"""

import asyncio
import time
import sys
from pathlib import Path

# Agregar raíz del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.client_classifier import ClientClassifier


async def benchmark():
    classifier = ClientClassifier()

    # Casos de prueba mixtos (reglas + LLM)
    test_cases = [
        "Busco apartamento para inversión con buena rentabilidad",  # Reglas
        "Soy arquitecto y busco casa para remodelar",  # Reglas
        "Me interesa una propiedad con potencial comercial y diseño",  # LLM
        "Necesito local comercial para mi empresa",  # Reglas
        "Busco casa para mi familia cerca de colegios",  # Reglas
        "Quiero una propiedad con buen ROI y ubicación estratégica",  # LLM
        "Es mi primera vez comprando, necesito ayuda",  # Reglas
        "Trabajo en construcción y busco apartamento con buena estructura",  # LLM
        "Busco apartamento de 2 habitaciones",  # Reglas
        "Soy corredor y busco propiedades para mi cartera"  # Reglas
    ] * 10  # 100 clasificaciones

    print("="*70)
    print("BENCHMARK - SISTEMA HÍBRIDO CLASIFICACIÓN")
    print("="*70)
    print(f"Casos de prueba: {len(test_cases)}")
    print()

    start = time.perf_counter()

    for i, case in enumerate(test_cases, 1):
        result = await classifier.classify(case)

        if i % 10 == 0:
            print(f"Progreso: {i}/{len(test_cases)} clasificaciones completadas...")

    end = time.perf_counter()

    total_time_ms = (end - start) * 1000
    avg_time_ms = total_time_ms / len(test_cases)

    stats = classifier.get_statistics()

    print("\n" + "="*70)
    print("RESULTADOS")
    print("="*70)
    print(f"Tiempo total: {total_time_ms:.0f}ms")
    print(f"Tiempo promedio: {avg_time_ms:.1f}ms/clasificación")
    print(f"Throughput: {len(test_cases) / (total_time_ms / 1000):.1f} clasificaciones/segundo")
    print()
    print(f"Clasificaciones por reglas: {stats['rule_based_percentage']:.1f}%")
    print(f"Clasificaciones por LLM: {stats['llm_based_percentage']:.1f}%")
    print(f"Costo total: ${stats['total_cost_usd']:.6f}")
    print(f"Costo promedio: ${stats['avg_cost_per_classification']:.6f}/clasificación")
    print()

    # Verificar objetivos
    print("="*70)
    print("OBJETIVOS")
    print("="*70)

    objectives = {
        "Latencia promedio < 500ms": avg_time_ms < 500,
        "Reglas >= 60%": stats['rule_based_percentage'] >= 60,
        "Costo promedio <= $0.00008": stats['avg_cost_per_classification'] <= 0.00008
    }

    for objective, met in objectives.items():
        status = "✅" if met else "❌"
        print(f"{status} {objective}")

    print("="*70)


if __name__ == "__main__":
    asyncio.run(benchmark())