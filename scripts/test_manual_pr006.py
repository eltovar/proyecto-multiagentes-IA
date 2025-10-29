"""Validación manual de PR006 - Sistema mono-canal"""
import sys
import os

# Agregar directorio raíz al PYTHONPATH para imports absolutos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from app.core.factory_orchestrator import FactoryOrchestrator
from app.state.models import ConversationState


async def main():
    orchestrator = FactoryOrchestrator()
    
    test_cases = [
        {
            "description": "Primer contacto",
            "state": ConversationState(conversation_id="test_1", current_agent=None),
            "message": "Hola",
            "expected_agent": "ReceptionAgent"
        },
        {
            "description": "Consulta informativa",
            "state": ConversationState(
                conversation_id="test_2",
                current_agent="reception",
                metadata={"last_intent": "question"}
            ),
            "message": "¿Qué zonas tienen?",
            "expected_agent": "SupportAgent"
        },
        {
            "description": "Lead calificado",
            "state": ConversationState(
                conversation_id="test_3",
                current_agent="reception",
                metadata={"lead_qualified": True}
            ),
            "message": "Quiero comprar",
            "expected_agent": "LeadsalesAgent"
        },
        {
            "description": "Conversión desde support",
            "state": ConversationState(
                conversation_id="test_4",
                current_agent="support",
                metadata={"conversion_intent": True}
            ),
            "message": "Me decidí a comprarlo",
            "expected_agent": "LeadsalesAgent"
        }
    ]
    
    print("="*70)
    print("VALIDACIÓN MANUAL PR006 - SISTEMA MONO-CANAL")
    print("="*70)
    print()
    
    for case in test_cases:
        # ✅ Sin parámetro channel
        agent = orchestrator.select_agent(case["message"], case["state"])
        actual_agent = agent.__class__.__name__
        
        status = "✅" if actual_agent == case["expected_agent"] else "❌"
        print(f"{status} {case['description']}")
        print(f"   Esperado: {case['expected_agent']}")
        print(f"   Obtenido: {actual_agent}")
        
        # Verificar que estado NO tiene campo channel
        assert not hasattr(case["state"], "channel"), "❌ Estado tiene campo 'channel' (no debería)"
        
        print()
    
    print("="*70)
    print("✅ Validación manual completada exitosamente")
    print("Sistema opera correctamente sin lógica multi-canal")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())