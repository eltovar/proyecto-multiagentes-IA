#!/usr/bin/env python3
"""Test de Stress - Múltiples usuarios simultáneos"""

import asyncio
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from app.core.orchestrator import orchestrator
from app.state.manager import state_manager

class StressTester:
    """Tester para carga de múltiples usuarios simultáneos"""

    def __init__(self, max_users: int = 10):
        self.max_users = max_users
        self.results = []

    async def simulate_user_session(self, user_id: int) -> Dict[str, Any]:
        """Simula una sesión completa de usuario"""
        phone = f"stress_test_{user_id:04d}"
        start_time = time.time()

        try:
            # Limpiar estado previo
            try:
                state_manager.delete_conversation(phone)
            except:
                pass

            # Paso 1: Saludo
            result1 = await orchestrator.process_message(
                whatsapp_id=phone,
                message=f"hola, soy el usuario {user_id}"
            )

            await asyncio.sleep(0.1)  # Simular tiempo de pensamiento

            # Paso 2: Nombre
            result2 = await orchestrator.process_message(
                whatsapp_id=phone,
                message=f"Mi nombre es Usuario{user_id} Test"
            )

            await asyncio.sleep(0.1)

            # Paso 3: Necesidad
            needs = [
                "Necesito un seguro de vida",
                "¿Qué tipos de seguros tienen?",
                "Quiero información sobre seguros de auto",
                "Necesito ayuda con un reclamo",
                "¿Cuánto cuesta un seguro médico?"
            ]
            need = needs[user_id % len(needs)]

            result3 = await orchestrator.process_message(
                whatsapp_id=phone,
                message=need
            )

            session_time = time.time() - start_time
            success = all(r.get("status") == "success" for r in [result1, result2, result3])

            return {
                "user_id": user_id,
                "phone": phone,
                "success": success,
                "session_time": round(session_time, 3),
                "steps_completed": 3,
                "final_response": result3.get("response", "")[:50] + "..."
            }

        except Exception as e:
            return {
                "user_id": user_id,
                "phone": phone,
                "success": False,
                "error": str(e),
                "session_time": round(time.time() - start_time, 3)
            }

    async def run_concurrent_users(self, num_users: int) -> Dict[str, Any]:
        """Ejecuta múltiples usuarios de forma concurrente"""
        print(f"=== TEST DE STRESS: {num_users} USUARIOS SIMULTÁNEOS ===")
        start_time = time.time()

        # Crear tasks para todos los usuarios
        tasks = [
            self.simulate_user_session(i)
            for i in range(1, num_users + 1)
        ]

        # Ejecutar todos los usuarios concurrentemente
        user_results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Procesar resultados
        successful_users = sum(1 for r in user_results if isinstance(r, dict) and r.get("success"))
        failed_users = num_users - successful_users
        avg_session_time = sum(
            r.get("session_time", 0) for r in user_results
            if isinstance(r, dict)
        ) / len(user_results) if user_results else 0

        # Calcular throughput
        throughput = num_users / total_time if total_time > 0 else 0

        return {
            "total_users": num_users,
            "successful_users": successful_users,
            "failed_users": failed_users,
            "success_rate": round((successful_users / num_users) * 100, 2),
            "total_time": round(total_time, 2),
            "avg_session_time": round(avg_session_time, 3),
            "throughput": round(throughput, 2),  # usuarios por segundo
            "user_results": user_results
        }

    async def run_stress_test_suite(self) -> Dict[str, Any]:
        """Ejecuta suite completo de tests de stress"""
        print("INICIANDO TESTS DE STRESS - MÚLTIPLES USUARIOS")
        print("="*60)

        test_scenarios = [
            {"users": 5, "name": "Carga ligera"},
            {"users": 10, "name": "Carga media"},
            {"users": 20, "name": "Carga alta"}
        ]

        all_results = {}

        for scenario in test_scenarios:
            print(f"\n--- {scenario['name']}: {scenario['users']} usuarios ---")

            result = await self.run_concurrent_users(scenario['users'])
            all_results[scenario['name']] = result

            print(f"Success Rate: {result['success_rate']}%")
            print(f"Total Time: {result['total_time']}s")
            print(f"Throughput: {result['throughput']} users/s")
            print(f"Avg Session Time: {result['avg_session_time']}s")

            # Pequeña pausa entre tests
            await asyncio.sleep(1)

        return self._generate_stress_report(all_results)

    def _generate_stress_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera reporte final de tests de stress"""
        total_users_tested = sum(r['total_users'] for r in results.values())
        total_successful = sum(r['successful_users'] for r in results.values())
        overall_success_rate = (total_successful / total_users_tested * 100) if total_users_tested > 0 else 0

        max_throughput = max(r['throughput'] for r in results.values())
        min_response_time = min(r['avg_session_time'] for r in results.values())

        return {
            "summary": {
                "total_users_tested": total_users_tested,
                "total_successful": total_successful,
                "overall_success_rate": round(overall_success_rate, 2),
                "max_throughput": round(max_throughput, 2),
                "min_response_time": round(min_response_time, 3)
            },
            "scenarios": results,
            "recommendations": self._get_performance_recommendations(results)
        }

    def _get_performance_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en resultados"""
        recommendations = []

        for name, result in results.items():
            if result['success_rate'] < 95:
                recommendations.append(f"Baja tasa de éxito en {name}: {result['success_rate']}%")

            if result['avg_session_time'] > 2.0:
                recommendations.append(f"Tiempo de respuesta alto en {name}: {result['avg_session_time']}s")

            if result['throughput'] < 5:
                recommendations.append(f"Bajo throughput en {name}: {result['throughput']} users/s")

        if not recommendations:
            recommendations.append("Sistema funcionando dentro de parámetros aceptables")

        return recommendations

async def run_stress_tests():
    """Punto de entrada para tests de stress"""
    tester = StressTester()
    result = await tester.run_stress_test_suite()

    print(f"\n{'='*60}")
    print("REPORTE FINAL DE STRESS TESTING")
    print(f"{'='*60}")
    print(f"Usuarios totales: {result['summary']['total_users_tested']}")
    print(f"Tasa de éxito: {result['summary']['overall_success_rate']}%")
    print(f"Max throughput: {result['summary']['max_throughput']} users/s")
    print(f"Min response time: {result['summary']['min_response_time']}s")

    print(f"\nRecomendaciones:")
    for rec in result['recommendations']:
        print(f"- {rec}")

    return result

if __name__ == "__main__":
    asyncio.run(run_stress_tests())