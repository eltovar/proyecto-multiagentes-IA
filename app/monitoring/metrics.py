#!/usr/bin/env python3
"""Sistema de métricas de performance"""

import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict, deque

@dataclass
class MetricData:
    """Datos de una métrica"""
    name: str
    value: float
    timestamp: float
    agent: str
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Recolector de métricas del sistema"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.counters = defaultdict(int)

    def record_metric(self, agent: str, name: str, value: float, tags: Dict[str, str] = None):
        """Registra una métrica"""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            agent=agent,
            tags=tags or {}
        )

        metric_key = f"{agent}.{name}"
        self.metrics[metric_key].append(metric)

    def increment_counter(self, agent: str, counter_name: str):
        """Incrementa un contador"""
        counter_key = f"{agent}.{counter_name}"
        self.counters[counter_key] += 1

    def get_agent_metrics(self, agent: str, minutes: int = 5) -> Dict[str, Any]:
        """Obtiene métricas de un agente en los últimos N minutos"""
        cutoff_time = time.time() - (minutes * 60)
        agent_metrics = {}

        # Métricas de valores
        for metric_key, metric_deque in self.metrics.items():
            if metric_key.startswith(f"{agent}."):
                metric_name = metric_key.split(".", 1)[1]
                recent_values = [
                    m.value for m in metric_deque
                    if m.timestamp >= cutoff_time
                ]

                if recent_values:
                    agent_metrics[metric_name] = {
                        "count": len(recent_values),
                        "avg": round(sum(recent_values) / len(recent_values), 3),
                        "min": round(min(recent_values), 3),
                        "max": round(max(recent_values), 3),
                        "latest": round(recent_values[-1], 3)
                    }

        # Contadores
        counters = {}
        for counter_key, count in self.counters.items():
            if counter_key.startswith(f"{agent}."):
                counter_name = counter_key.split(".", 1)[1]
                counters[counter_name] = count

        return {
            "agent": agent,
            "time_window": f"{minutes} minutes",
            "metrics": agent_metrics,
            "counters": counters,
            "timestamp": time.time()
        }

    def get_system_overview(self) -> Dict[str, Any]:
        """Obtiene vista general del sistema"""
        agents = set()
        total_metrics = 0

        for metric_key in self.metrics.keys():
            agent = metric_key.split(".", 1)[0]
            agents.add(agent)
            total_metrics += len(self.metrics[metric_key])

        return {
            "active_agents": list(agents),
            "total_agents": len(agents),
            "total_metrics": total_metrics,
            "total_counters": len(self.counters),
            "timestamp": time.time()
        }

class PerformanceMonitor:
    """Monitor de performance integrado"""

    def __init__(self):
        self.collector = MetricsCollector()
        self.start_times = {}

    def start_operation(self, agent: str, operation: str) -> str:
        """Inicia monitoreo de operación"""
        timer_id = f"{agent}_{operation}_{int(time.time() * 1000)}"
        self.start_times[timer_id] = time.time()
        self.collector.increment_counter(agent, "operations_started")
        return timer_id

    def end_operation(self, agent: str, operation: str, timer_id: str, success: bool = True):
        """Termina monitoreo de operación"""
        if timer_id not in self.start_times:
            return

        duration = time.time() - self.start_times[timer_id]
        del self.start_times[timer_id]

        # Registrar métricas
        self.collector.record_metric(agent, f"{operation}_duration", duration)
        self.collector.increment_counter(agent, "operations_completed")

        if success:
            self.collector.increment_counter(agent, "operations_successful")
        else:
            self.collector.increment_counter(agent, "operations_failed")

    def record_message_processed(self, agent: str, response_time: float):
        """Registra mensaje procesado"""
        self.collector.record_metric(agent, "response_time", response_time)
        self.collector.increment_counter(agent, "messages_processed")

    def record_transfer(self, from_agent: str, to_agent: str, success: bool):
        """Registra transferencia entre agentes"""
        self.collector.increment_counter(from_agent, "transfers_out")
        self.collector.increment_counter(to_agent, "transfers_in")

        if success:
            self.collector.increment_counter("system", "successful_transfers")
        else:
            self.collector.increment_counter("system", "failed_transfers")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos para dashboard"""
        system_overview = self.collector.get_system_overview()
        agent_data = {}

        for agent in system_overview["active_agents"]:
            agent_data[agent] = self.collector.get_agent_metrics(agent, minutes=5)

        return {
            "system": system_overview,
            "agents": agent_data,
            "timestamp": time.time()
        }

# Instancia global
performance_monitor = PerformanceMonitor()