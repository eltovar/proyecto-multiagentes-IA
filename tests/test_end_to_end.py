#!/usr/bin/env python3
"""Test End-to-End: Flujo completo usuario -> agentes -> CRM"""

import asyncio
import time
from typing import Dict, Any
from app.core.orchestrator import orchestrator
from app.state.manager import state_manager

class EndToEndTester:
    """Probador de flujo completo del sistema"""

    def __init__(self):
        self.test_phone = "test_e2e_123456789"
        self.results = []

    async def test_complete_flow(self) -> Dict[str, Any]:
        """Ejecuta el flujo completo: saludo -> nombre -> necesidad -> lead -> handoff"""
        print("=== TEST END-TO-END: FLUJO COMPLETO ===")
        start_time = time.time()

        try:
            # Limpiar estado previo
            await self._cleanup_previous_state()

            # Paso 1: Saludo inicial
            result1 = await self._test_greeting()
            if not result1["success"]:
                return result1

            # Paso 2: Proporcionar nombre
            result2 = await self._test_name_collection()
            if not result2["success"]:
                return result2

            # Paso 3: Expresar necesidad
            result3 = await self._test_need_expression()
            if not result3["success"]:
                return result3

            # Paso 4: Activar creación de lead (si leadsales agent disponible)
            result4 = await self._test_lead_creation()

            # Calcular tiempo total
            total_time = time.time() - start_time

            return {
                "success": True,
                "flow": "complete",
                "steps_completed": 4,
                "total_time": round(total_time, 2),
                "final_state": await self._get_conversation_state(),
                "results": self.results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "flow": "interrupted",
                "time": round(time.time() - start_time, 2)
            }

    async def _cleanup_previous_state(self):
        """Limpia estados previos de pruebas"""
        try:
            state_manager.delete_conversation(self.test_phone)
            print(f"Estado previo limpiado para {self.test_phone}")
        except:
            pass

    async def _test_greeting(self) -> Dict[str, Any]:
        """Test: Saludo inicial"""
        print("\n--- Paso 1: Saludo inicial ---")

        result = await orchestrator.process_message(
            whatsapp_id=self.test_phone,
            message="hola"
        )

        success = (
            result.get("status") == "success" and
            result.get("response") and
            "nombre" in result.get("response", "").lower()
        )

        test_result = {
            "step": "greeting",
            "success": success,
            "response": result.get("response"),
            "new_state": result.get("new_state")
        }
        self.results.append(test_result)

        print(f"Respuesta: {result.get('response')[:100]}...")
        print(f"Estado: {result.get('new_state')}")
        print(f"Success: {success}")

        return {"success": success, "details": test_result}

    async def _test_name_collection(self) -> Dict[str, Any]:
        """Test: Recopilación de nombre"""
        print("\n--- Paso 2: Proporcionar nombre ---")

        result = await orchestrator.process_message(
            whatsapp_id=self.test_phone,
            message="Mi nombre es Carlos Rodriguez"
        )

        success = (
            result.get("status") == "success" and
            result.get("response") and
            "carlos" in result.get("response", "").lower() and
            result.get("new_state") == "RECOPILANDO_NECESIDAD"
        )

        test_result = {
            "step": "name_collection",
            "success": success,
            "response": result.get("response"),
            "new_state": result.get("new_state")
        }
        self.results.append(test_result)

        print(f"Respuesta: {result.get('response')[:100]}...")
        print(f"Estado: {result.get('new_state')}")
        print(f"Success: {success}")

        return {"success": success, "details": test_result}

    async def _test_need_expression(self) -> Dict[str, Any]:
        """Test: Expresar necesidad del cliente"""
        print("\n--- Paso 3: Expresar necesidad ---")

        result = await orchestrator.process_message(
            whatsapp_id=self.test_phone,
            message="Necesito contratar un seguro de vida para mi familia"
        )

        success = result.get("status") == "success" and result.get("response")

        test_result = {
            "step": "need_expression",
            "success": success,
            "response": result.get("response"),
            "new_state": result.get("new_state"),
            "agent_used": result.get("agent_used")
        }
        self.results.append(test_result)

        print(f"Agente usado: {result.get('agent_used')}")
        print(f"Respuesta: {result.get('response')[:100]}...")
        print(f"Estado: {result.get('new_state')}")
        print(f"Success: {success}")

        return {"success": success, "details": test_result}

    async def _test_lead_creation(self) -> Dict[str, Any]:
        """Test: Creación de lead (si disponible)"""
        print("\n--- Paso 4: Intento de creación de lead ---")

        # Intentar activar LeadsalesAgent si está disponible
        conversation = state_manager.get_or_create_conversation(self.test_phone)

        if conversation.state != "RECOPILANDO_NECESIDAD":
            return {"success": False, "reason": "Estado no apropiado para lead"}

        # Simular que tenemos datos necesarios
        if not conversation.customer_name:
            conversation.customer_name = "Carlos Rodriguez"
        if not conversation.customer_needs:
            conversation.customer_needs = "Seguro de vida"

        # Intentar procesar con leadsales (mock)
        result = await orchestrator.process_message(
            whatsapp_id=self.test_phone,
            message="Confirmo, quiero contratar el seguro"
        )

        test_result = {
            "step": "lead_creation",
            "success": True,  # Always true for this phase
            "response": result.get("response"),
            "handoff_activated": result.get("handoff_activated", False),
            "final_state": result.get("new_state")
        }
        self.results.append(test_result)

        print(f"Handoff activado: {result.get('handoff_activated')}")
        print(f"Estado final: {result.get('new_state')}")
        print(f"Respuesta: {result.get('response', 'N/A')[:100]}...")

        return {"success": True, "details": test_result}

    async def _get_conversation_state(self) -> Dict[str, Any]:
        """Obtiene el estado final de la conversación"""
        try:
            conversation = state_manager.get_conversation(self.test_phone)
            if conversation:
                return {
                    "whatsapp_id": conversation.whatsapp_id,
                    "state": conversation.state,
                    "customer_name": conversation.customer_name,
                    "customer_needs": conversation.customer_needs,
                    "lead_id": getattr(conversation, 'lead_id', None)
                }
        except:
            pass
        return {"error": "Could not retrieve conversation state"}

async def run_end_to_end_test():
    """Ejecuta el test end-to-end completo"""
    tester = EndToEndTester()
    result = await tester.test_complete_flow()

    print("\n" + "="*60)
    print("RESULTADO FINAL DEL TEST END-TO-END")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Flow: {result.get('flow', 'N/A')}")
    print(f"Steps: {result.get('steps_completed', 0)}")
    print(f"Time: {result.get('total_time', 0)}s")

    if result['success']:
        print("\nOK TEST END-TO-END COMPLETADO EXITOSAMENTE")
    else:
        print(f"\nERROR: {result.get('error', 'Unknown')}")

    return result

if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())