"""Módulo de monitoreo del sistema multiagente"""

from .logger import structured_logger, performance_tracker, get_logger
from .metrics import performance_monitor

# Lazy import de dashboard para evitar imports circulares
# dashboard importa orchestrator legacy que puede no existir
dashboard = None

def get_dashboard():
    """Lazy loading de dashboard"""
    global dashboard
    if dashboard is None:
        from .dashboard import dashboard as _dashboard
        dashboard = _dashboard
    return dashboard

__all__ = [
    'structured_logger',
    'performance_tracker',
    'performance_monitor',
    'get_logger',
    'get_dashboard'
]