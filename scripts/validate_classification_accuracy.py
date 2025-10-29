"""
Script para validar precisión del sistema de clasificación híbrido.
Objetivo: 92% de precisión en dataset de prueba.
"""
import asyncio
import json
import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar encoding UTF-8 para output (Windows compatibility)
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.services.client_classifier import ClientClassifier


async def validate_accuracy():
    """Valida precisión contra dataset de test cases"""
    
    # Cargar test cases
    dataset_path = Path("datasets/classification_test_cases.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    
    classifier = ClientClassifier()
    
    results = {
        "total": len(test_cases),
        "correct_profile": 0,
        "correct_sophistication": 0,
        "correct_method": 0,
        "details": []
    }
    
    print("="*70)
    print("VALIDACIÓN DE PRECISIÓN - SISTEMA HÍBRIDO CLASIFICACIÓN")
    print("="*70)
    print(f"\nTotal casos: {len(test_cases)}\n")
    
    for case in test_cases:
        result = await classifier.classify(case["message"])
        
        # Verificar profile
        expected_profiles = case["expected_profile"].split("|")
        profile_correct = result.profile in expected_profiles
        
        # Verificar sophistication
        expected_soph = case["expected_sophistication"].split("|")
        soph_correct = result.sophistication_level in expected_soph
        
        # Verificar método
        expected_methods = case["expected_method"].split("|")
        method_correct = result.classification_method in expected_methods
        
        # Actualizar contadores
        if profile_correct:
            results["correct_profile"] += 1
        if soph_correct:
            results["correct_sophistication"] += 1
        if method_correct:
            results["correct_method"] += 1
        
        # Status
        status = "✅" if (profile_correct and soph_correct) else "❌"
        
        print(f"{status} Caso {case['id']}: {case['message'][:50]}...")
        print(f"   Esperado: {case['expected_profile']} | {case['expected_sophistication']}")
        print(f"   Obtenido: {result.profile} | {result.sophistication_level}")
        print(f"   Método: {result.classification_method} (esperado: {case['expected_method']})")
        print(f"   Confianza: {result.confidence:.2f}")
        
        if not profile_correct:
            print(f"   ⚠️  FALLO: Profile incorrecto")
        if not soph_correct:
            print(f"   ⚠️  FALLO: Sophistication incorrecto")
        
        print()
        
        results["details"].append({
            "case_id": case["id"],
            "profile_correct": profile_correct,
            "sophistication_correct": soph_correct,
            "method_correct": method_correct,
            "confidence": result.confidence
        })
    
    # Calcular métricas
    profile_accuracy = (results["correct_profile"] / results["total"]) * 100
    sophistication_accuracy = (results["correct_sophistication"] / results["total"]) * 100
    method_accuracy = (results["correct_method"] / results["total"]) * 100
    
    # Overall accuracy (profile + sophistication)
    overall_correct = sum(
        1 for detail in results["details"]
        if detail["profile_correct"] and detail["sophistication_correct"]
    )
    overall_accuracy = (overall_correct / results["total"]) * 100
    
    print("="*70)
    print("RESULTADOS")
    print("="*70)
    print(f"Precisión Profile: {profile_accuracy:.1f}% ({results['correct_profile']}/{results['total']})")
    print(f"Precisión Sophistication: {sophistication_accuracy:.1f}% ({results['correct_sophistication']}/{results['total']})")
    print(f"Precisión Método: {method_accuracy:.1f}% ({results['correct_method']}/{results['total']})")
    print(f"\n🎯 PRECISIÓN OVERALL: {overall_accuracy:.1f}%")
    
    # Estadísticas del clasificador
    stats = classifier.get_statistics()
    print(f"\nEstadísticas de uso:")
    print(f"  - Reglas: {stats['rule_based_percentage']:.1f}%")
    print(f"  - LLM: {stats['llm_based_percentage']:.1f}%")
    print(f"  - Costo promedio: ${stats['avg_cost_per_classification']:.6f}")
    
    # Verificar objetivo del PR
    print("\n" + "="*70)
    if overall_accuracy >= 92:
        print("✅ OBJETIVO CUMPLIDO: Precisión >= 92%")
    else:
        print(f"❌ OBJETIVO NO CUMPLIDO: Precisión {overall_accuracy:.1f}% < 92%")
    
    if stats['avg_cost_per_classification'] <= 0.00008:
        print(f"✅ COSTO ÓPTIMO: ${stats['avg_cost_per_classification']:.6f} <= $0.00008")
    else:
        print(f"⚠️  COSTO ELEVADO: ${stats['avg_cost_per_classification']:.6f} > $0.00008")
    
    print("="*70)
    
    return overall_accuracy >= 92


if __name__ == "__main__":
    success = asyncio.run(validate_accuracy())
    exit(0 if success else 1)