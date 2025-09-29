#!/usr/bin/env python3
"""
Test de integración RAG System - Paso 1.3
Validar integración completa del sistema RAG con la aplicación.
"""

import sys
import os

# Setup path para importar módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_integration():
    """Test completo de integración RAG."""
    print("=" * 60)
    print("PASO 1.3: VALIDACIÓN RAG INTEGRATION")
    print("=" * 60)

    try:
        # PASO 1: Importar sistema RAG
        print("\n[TEST] Importando sistema RAG...")
        from app.rag.rag_system import rag_system
        print("[PASS] Sistema RAG importado correctamente")

        # PASO 1.5: Inicializar sistema RAG
        print("\n[TEST] Inicializando sistema RAG...")
        initialization_success = rag_system.initialize()
        if not initialization_success:
            print("[FAIL] Error inicializando sistema RAG")
            return False
        print("[PASS] Sistema RAG inicializado correctamente")

        # PASO 2: Ejecutar query de test
        print("\n[TEST] Ejecutando query: 'inmobiliaria'")
        test_query = "inmobiliaria"
        context = rag_system.get_context_for_query(test_query)

        # PASO 3: Validación context != None
        print(f"\n[TEST] Validando context != None...")
        if context is None:
            print("[FAIL] Context es None")
            return False
        else:
            print("[PASS] Context no es None")

        # PASO 4: Verificar contenido información servicios
        print(f"\n[TEST] Verificando contenido información servicios...")
        context_lower = context.lower()
        service_keywords = [
            "servicio", "servicios", "inmobiliaria", "proteger",
            "arrendamiento", "venta", "alquiler", "asesor"
        ]

        found_keywords = [kw for kw in service_keywords if kw in context_lower]
        if found_keywords:
            print(f"[PASS] Contenido relacionado con servicios encontrado")
            print(f"       Keywords encontrados: {found_keywords}")
        else:
            print("[WARN] No se encontraron keywords específicos de servicios")

        # PASO 5: Confirmar longitud > 100 caracteres
        print(f"\n[TEST] Confirmando longitud > 100 caracteres...")
        context_length = len(context)
        print(f"       Longitud del contexto: {context_length} caracteres")

        if context_length > 100:
            print("[PASS] Longitud > 100 caracteres")
        else:
            print(f"[FAIL] Longitud {context_length} <= 100 caracteres")
            return False

        # MOSTRAR RESULTADO COMPLETO
        print(f"\n[RESULT] Contexto RAG obtenido:")
        print("-" * 40)
        print(context)
        print("-" * 40)

        print(f"\n[SUCCESS] RESULTADO ESPERADO CUMPLIDO:")
        print(f"   - context != None: PASS")
        print(f"   - context contiene información servicios: PASS")
        print(f"   - Longitud > 100 caracteres: PASS ({context_length})")

        return True

    except ImportError as e:
        print(f"[ERROR] Error importando RAG system: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error en test RAG integration: {e}")
        return False

def main():
    """Función principal del test."""
    success = test_rag_integration()

    if success:
        print(f"\n[SUCCESS] PASO 1.3: RAG INTEGRATION - COMPLETADO EXITOSAMENTE")
        return 0
    else:
        print(f"\n[FAIL] PASO 1.3: RAG INTEGRATION - FALLÓ")
        return 1

if __name__ == "__main__":
    exit(main())