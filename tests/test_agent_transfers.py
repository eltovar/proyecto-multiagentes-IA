#!/usr/bin/env python3
"""Test de transferencias entre agentes"""

import asyncio
from typing import Dict, Any
from app.core.orchestrator import orchestrator
from app.state.manager import state_manager

class AgentTransferTester:
    """Tester especializado en transferencias entre agentes"""

    def __init__(self):
        self.test_phone = "test_transfer_987654321"

    async def test_reception_to_support(self) -> Dict[str, Any]:
        """Test transferencia: Reception -> Support"""
        print("=== TEST: TRANSFERENCIA RECEPTION -> SUPPORT ===")

        # Limpiar estado previo
        try:
            state_manager.delete_conversation(self.test_phone)
        except:
            pass

        try:
            # Simular flujo hasta pregunta
            await self._setup_customer_with_question()

            # Hacer una pregunta que debería ir a support
            result = await orchestrator.process_message(
                whatsapp_id=self.test_phone,
                message="¿Qué tipos de seguros ofrecen y cuáles son las diferencias?"
            )

            return {
                "success": True,
                "transfer_attempted": result.get("agent_used") != "reception",
                "response": result.get("response"),
                "agent_used": result.get("agent_used"),
                "transfer_to": result.get("transfer_to"),
                "details": result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_reception_to_leadsales(self) -> Dict[str, Any]:
        """Test transferencia: Reception -> Leadsales"""
        print("\n=== TEST: TRANSFERENCIA RECEPTION -> LEADSALES ===")

        # Limpiar estado previo
        try:
            state_manager.delete_conversation(self.test_phone + "_lead")
        except:
            pass

        try:
            # Configurar cliente con necesidad de lead
            await self._setup_customer_with_need()

            # Expresar intención de compra
            result = await orchestrator.process_message(
                whatsapp_id=self.test_phone + "_lead",
                message="Quiero contratar un seguro de vida ahora"
            )

            return {
                "success": True,
                "transfer_attempted": result.get("transfer_to") == "leadsales",
                "response": result.get("response"),
                "transfer_to": result.get("transfer_to"),
                "handoff_activated": result.get("handoff_activated"),
                "details": result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_handoff_protocol(self) -> Dict[str, Any]:
        """Test del Handoff Protocol - transferencia a humano"""
        print("\n=== TEST: HANDOFF PROTOCOL ===")

        # Crear conversación en estado TRANSFERIDO
        conversation = state_manager.get_or_create_conversation(self.test_phone + "_handoff")
        conversation.state = "TRANSFERIDO"
        conversation.customer_name = "Test User"

        try:
            # Intentar enviar mensaje cuando está en handoff
            result = await orchestrator.process_message(
                whatsapp_id=self.test_phone + "_handoff",
                message="¿Sigues ahí?"
            )

            return {
                "success": True,
                "handoff_respected": result.get("status") == "handoff_active",
                "message_blocked": result.get("response") is None,
                "status": result.get("status"),
                "details": result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _setup_customer_with_question(self):
        """Configura un cliente que hará preguntas"""
        # Saludo inicial
        await orchestrator.process_message(
            whatsapp_id=self.test_phone,
            message="hola"
        )

        # Dar nombre
        await orchestrator.process_message(
            whatsapp_id=self.test_phone,
            message="Mi nombre es Ana Lopez"
        )

    async def _setup_customer_with_need(self):
        """Configura un cliente con necesidad de compra"""
        # Saludo inicial
        await orchestrator.process_message(
            whatsapp_id=self.test_phone + "_lead",
            message="hola"
        )

        # Dar nombre
        await orchestrator.process_message(
            whatsapp_id=self.test_phone + "_lead",
            message="Mi nombre es Roberto Martinez"
        )

        # Expresar necesidad inicial
        await orchestrator.process_message(
            whatsapp_id=self.test_phone + "_lead",
            message="Estoy interesado en un seguro"
        )

    async def run_all_transfer_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de transferencia"""
        print("INICIANDO TESTS DE TRANSFERENCIAS ENTRE AGENTES")
        print("="*60)

        results = {}

        # Test 1: Reception to Support
        results["reception_to_support"] = await self.test_reception_to_support()

        # Test 2: Reception to Leadsales
        results["reception_to_leadsales"] = await self.test_reception_to_leadsales()

        # Test 3: Handoff Protocol
        results["handoff_protocol"] = await self.test_handoff_protocol()

        # Resumen
        successful_tests = sum(1 for r in results.values() if r.get("success"))
        total_tests = len(results)

        print(f"\n{'='*60}")
        print(f"RESUMEN DE TESTS DE TRANSFERENCIA")
        print(f"{'='*60}")
        print(f"Tests exitosos: {successful_tests}/{total_tests}")

        for test_name, result in results.items():
            status = "OK" if result.get("success") else "ERROR"
            print(f"- {test_name}: {status}")
            if not result.get("success"):
                print(f"  Error: {result.get('error')}")

        return {
            "success": successful_tests == total_tests,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "results": results
        }

async def run_transfer_tests():
    """Punto de entrada para tests de transferencia"""
    tester = AgentTransferTester()
    return await tester.run_all_transfer_tests()

if __name__ == "__main__":
    asyncio.run(run_transfer_tests())