"""
Utilidad de logging de errores estandarizada para clases no-agente
"""

from typing import Optional, Dict, Any


def log_error(component_name: str, error_message: str, exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
    """
    Función estandarizada de logging de errores para componentes del sistema

    Args:
        component_name: Nombre del componente (ej: "LLMService", "WhatsAppService")
        error_message: Mensaje descriptivo del error
        exception: Excepción opcional para incluir detalles
        context: Contexto adicional opcional
    """
    error_msg = f"[{component_name}] ERROR: {error_message}"

    if exception:
        error_msg += f" - {type(exception).__name__}: {str(exception)}"

    if context:
        error_msg += f" - Context: {context}"

    print(error_msg)


def log_info(component_name: str, message: str):
    """
    Función estandarizada de logging de información

    Args:
        component_name: Nombre del componente
        message: Mensaje informativo
    """
    print(f"[{component_name}] {message}")