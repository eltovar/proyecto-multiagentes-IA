#!/usr/bin/env python3
"""Test del sistema de monitoreo"""

import asyncio
import time
from app.monitoring.metrics import performance_monitor
from app.monitoring.dashboard import dashboard
from app.core.orchestrator import orchestrator

async def test_monitoring_system():
    """Prueba el sistema de monitoreo completo"""
    print("=== TEST SISTEMA DE MONITOREO ===")

    # Simular algunas operaciones monitoreadas
    print("\n1. Simulando operaciones monitoreadas...")

    # Operación 1
    timer1 = performance_monitor.start_operation("reception", "process_message")
    await asyncio.sleep(0.1)  # Simular trabajo
    performance_monitor.end_operation("reception", "process_message", timer1, success=True)

    # Operación 2
    timer2 = performance_monitor.start_operation("reception", "extract_name")
    await asyncio.sleep(0.05)  # Simular trabajo
    performance_monitor.end_operation("reception", "extract_name", timer2, success=True)

    # Registrar algunas métricas adicionales
    performance_monitor.record_message_processed("reception", 0.15)
    performance_monitor.record_message_processed("reception", 0.12)
    performance_monitor.record_transfer("reception", "support", True)

    print("OK Operaciones simuladas")

    # Test de métricas
    print("\n2. Verificando métricas...")
    reception_metrics = performance_monitor.collector.get_agent_metrics("reception")
    print(f"Métricas de reception: {len(reception_metrics['metrics'])} tipos")

    system_overview = performance_monitor.collector.get_system_overview()
    print(f"Agentes activos: {system_overview['active_agents']}")

    # Test de dashboard
    print("\n3. Generando dashboard...")
    dashboard.print_dashboard()

    # Exportar reporte
    print("\n4. Exportando reporte...")
    dashboard.export_json("test_monitoring_report.json")

    return True

if __name__ == "__main__":
    asyncio.run(test_monitoring_system())