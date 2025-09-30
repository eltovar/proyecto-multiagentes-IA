#!/usr/bin/env python3
"""Sistema de logging estructurado por agente """

import json
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class StructuredLogger:
    """Logger estructurado para sistema multiagente"""

    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)

    def log_agent_action(self, agent_name: str, action: str, data: Dict[str, Any] = None):
        """Log de acción de agente"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "data": data or {},
            "level": "INFO"
        }
        self._write_log(f"{agent_name}.log", log_entry)

    def log_performance(self, agent_name: str, metrics: Dict[str, Any]):
        """Log de métricas de performance"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "type": "performance",
            "metrics": metrics,
            "level": "METRICS"
        }
        self._write_log("performance.log", log_entry)

    def log_error(self, agent_name: str, error: str, context: Dict[str, Any] = None):
        """Log de errores"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "error": error,
            "context": context or {},
            "level": "ERROR"
        }
        self._write_log("errors.log", log_entry)

    def log_transfer(self, from_agent: str, to_agent: str, success: bool, data: Dict[str, Any]):
        """Log de transferencias entre agentes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "success": success,
            "data": data,
            "level": "TRANSFER"
        }
        self._write_log("transfers.log", log_entry)

    def _write_log(self, filename: str, log_entry: Dict[str, Any]):
        """Escribe log a archivo"""
        try:
            log_file = self.logs_dir / filename
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error escribiendo log: {e}")

class PerformanceTracker:
    """Tracker de performance por agente"""

    def __init__(self):
        self.metrics = {}
        self.logger = StructuredLogger()

    def start_timer(self, agent_name: str, operation: str) -> str:
        """Inicia timer para operación"""
        timer_id = f"{agent_name}_{operation}_{int(time.time() * 1000)}"
        if agent_name not in self.metrics:
            self.metrics[agent_name] = {}
        if "timers" not in self.metrics[agent_name]:
            self.metrics[agent_name]["timers"] = {}

        self.metrics[agent_name]["timers"][timer_id] = {
            "operation": operation,
            "start_time": time.time()
        }
        return timer_id

    def end_timer(self, agent_name: str, timer_id: str):
        """Termina timer y registra métrica"""
        try:
            timer = self.metrics[agent_name]["timers"][timer_id]
            duration = time.time() - timer["start_time"]

            operation = timer["operation"]
            if "performance" not in self.metrics[agent_name]:
                self.metrics[agent_name]["performance"] = {}
            if operation not in self.metrics[agent_name]["performance"]:
                self.metrics[agent_name]["performance"][operation] = []

            self.metrics[agent_name]["performance"][operation].append(duration)

            # Log performance
            self.logger.log_performance(agent_name, {
                "operation": operation,
                "duration": round(duration, 3),
                "timer_id": timer_id
            })

            del self.metrics[agent_name]["timers"][timer_id]
        except Exception as e:
            print(f"Error ending timer: {e}")

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de agente"""
        if agent_name not in self.metrics:
            return {"agent": agent_name, "stats": "No data"}

        agent_metrics = self.metrics[agent_name].get("performance", {})
        stats = {}

        for operation, times in agent_metrics.items():
            if times:
                stats[operation] = {
                    "count": len(times),
                    "avg_time": round(sum(times) / len(times), 3),
                    "min_time": round(min(times), 3),
                    "max_time": round(max(times), 3)
                }

        return {"agent": agent_name, "stats": stats}

# Instancias globales
structured_logger = StructuredLogger()
performance_tracker = PerformanceTracker()