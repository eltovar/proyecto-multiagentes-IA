#!/usr/bin/env python3
"""Dashboard de monitoreo básico """

import json
import time
from datetime import datetime
from typing import Dict, Any
from app.monitoring.metrics import performance_monitor
from app.core.orchestrator import orchestrator

class MonitoringDashboard:
    """Dashboard básico de monitoreo del sistema"""

    def __init__(self):
        self.monitor = performance_monitor

    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte completo del sistema"""
        return {
            "report_time": datetime.now().isoformat(),
            "system_health": self._get_system_health(),
            "agent_performance": self._get_agent_performance(),
            "recent_activity": self._get_recent_activity(),
            "recommendations": self._get_recommendations()
        }

    def _get_system_health(self) -> Dict[str, Any]:
        """Obtiene salud general del sistema"""
        orchestrator_health = orchestrator.health_check()
        dashboard_data = self.monitor.get_dashboard_data()

        return {
            "orchestrator_status": orchestrator_health.get("status"),
            "active_agents": dashboard_data["system"]["active_agents"],
            "total_agents": dashboard_data["system"]["total_agents"],
            "uptime": "Running"  # Simplificado
        }

    def _get_agent_performance(self) -> Dict[str, Any]:
        """Obtiene performance de todos los agentes"""
        dashboard_data = self.monitor.get_dashboard_data()
        agent_performance = {}

        for agent_name, agent_data in dashboard_data["agents"].items():
            metrics = agent_data.get("metrics", {})
            counters = agent_data.get("counters", {})

            # Calcular estadísticas clave
            avg_response_time = metrics.get("response_time", {}).get("avg", 0)
            total_messages = counters.get("messages_processed", 0)
            success_rate = self._calculate_success_rate(counters)

            agent_performance[agent_name] = {
                "avg_response_time": avg_response_time,
                "total_messages": total_messages,
                "success_rate": success_rate,
                "status": "healthy" if success_rate > 0.9 else "warning"
            }

        return agent_performance

    def _get_recent_activity(self) -> Dict[str, Any]:
        """Obtiene actividad reciente del sistema"""
        dashboard_data = self.monitor.get_dashboard_data()
        system_data = dashboard_data["system"]

        return {
            "total_metrics_collected": system_data["total_metrics"],
            "total_counters": system_data["total_counters"],
            "last_update": datetime.now().isoformat()
        }

    def _get_recommendations(self) -> list:
        """Genera recomendaciones basadas en métricas"""
        recommendations = []
        dashboard_data = self.monitor.get_dashboard_data()

        for agent_name, agent_data in dashboard_data["agents"].items():
            metrics = agent_data.get("metrics", {})
            counters = agent_data.get("counters", {})

            # Verificar tiempo de respuesta alto
            response_time = metrics.get("response_time", {})
            if response_time.get("avg", 0) > 2.0:
                recommendations.append(f"Agent {agent_name}: High response time ({response_time['avg']}s)")

            # Verificar tasa de fallos
            success_rate = self._calculate_success_rate(counters)
            if success_rate < 0.9:
                recommendations.append(f"Agent {agent_name}: Low success rate ({success_rate:.2%})")

        if not recommendations:
            recommendations.append("System performing within normal parameters")

        return recommendations

    def _calculate_success_rate(self, counters: Dict[str, int]) -> float:
        """Calcula tasa de éxito basada en contadores"""
        successful = counters.get("operations_successful", 0)
        failed = counters.get("operations_failed", 0)
        total = successful + failed

        if total == 0:
            return 1.0  # Sin operaciones = 100% éxito

        return successful / total

    def print_dashboard(self):
        """Imprime dashboard en consola"""
        report = self.generate_report()

        print("=" * 60)
        print("DASHBOARD DE MONITOREO - SISTEMA MULTIAGENTE")
        print("=" * 60)
        print(f"Tiempo: {report['report_time']}")

        # Sistema
        health = report['system_health']
        print(f"\nSISTEMA:")
        print(f"- Estado: {health['orchestrator_status']}")
        print(f"- Agentes activos: {health['total_agents']}")
        print(f"- Lista: {', '.join(health['active_agents'])}")

        # Performance
        print(f"\nPERFORMANCE:")
        for agent, perf in report['agent_performance'].items():
            print(f"- {agent}: {perf['status'].upper()}")
            print(f"  Response: {perf['avg_response_time']:.3f}s")
            print(f"  Messages: {perf['total_messages']}")
            print(f"  Success: {perf['success_rate']:.1%}")

        # Recomendaciones
        print(f"\nRECOMENDACIONES:")
        for rec in report['recommendations']:
            print(f"- {rec}")

        print("=" * 60)

    def export_json(self, filename: str = None):
        """Exporta dashboard a JSON"""
        if not filename:
            timestamp = int(time.time())
            filename = f"dashboard_report_{timestamp}.json"

        report = self.generate_report()

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Dashboard exportado a: {filename}")
        except Exception as e:
            print(f"Error exportando dashboard: {e}")

# Instancia global
dashboard = MonitoringDashboard()