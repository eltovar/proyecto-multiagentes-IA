import sys
import os

# Agregar parent al path temporalmente para importar config.py
parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

# Importar todo de app.config
try:
    # Forzar importación del archivo config.py en vez del paquete config/
    import importlib.util
    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
    spec = importlib.util.spec_from_file_location("app.config_file", config_file_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    # Re-exportar constantes
    Settings = config_module.Settings
    settings = config_module.settings

    # Estados de ReceptionAgent
    STATE_NUEVO = config_module.STATE_NUEVO
    STATE_POLITICAS_PRESENTADAS = config_module.STATE_POLITICAS_PRESENTADAS
    STATE_RECOPILANDO_NOMBRE = config_module.STATE_RECOPILANDO_NOMBRE
    STATE_NOMBRE_OBTENIDO = config_module.STATE_NOMBRE_OBTENIDO
    STATE_PREGUNTA_CONTRATO_INMOBILIARIA = config_module.STATE_PREGUNTA_CONTRATO_INMOBILIARIA
    STATE_PREGUNTA_CUAL_INMOBILIARIA = config_module.STATE_PREGUNTA_CUAL_INMOBILIARIA
    STATE_PREGUNTA_SOLICITUD_LIBERTADOR = config_module.STATE_PREGUNTA_SOLICITUD_LIBERTADOR
    STATE_PREGUNTA_FECHA_NECESIDAD = config_module.STATE_PREGUNTA_FECHA_NECESIDAD
    STATE_FLUJO_COMPLETADO = config_module.STATE_FLUJO_COMPLETADO
    STATE_TRANSFERIDO = config_module.STATE_TRANSFERIDO

    # Estados de SupportAgent
    STATE_TRANSFERIDO_SUPPORT = config_module.STATE_TRANSFERIDO_SUPPORT
    STATE_CONSULTA_INFORMATIVA = config_module.STATE_CONSULTA_INFORMATIVA
    STATE_SOPORTE_ACTIVO = config_module.STATE_SOPORTE_ACTIVO
    STATE_REDIRIGIDO_CARTERA = config_module.STATE_REDIRIGIDO_CARTERA
    STATE_REDIRIGIDO_MANTENIMIENTO = config_module.STATE_REDIRIGIDO_MANTENIMIENTO

    # Estados de LeadsalesAgent
    STATE_CAPTURANDO_DETALLES = config_module.STATE_CAPTURANDO_DETALLES
    STATE_PROFUNDIZANDO_NECESIDAD = config_module.STATE_PROFUNDIZANDO_NECESIDAD
    STATE_CONFIRMANDO_INFORMACION = config_module.STATE_CONFIRMANDO_INFORMACION
    STATE_PROCESANDO_CRM = config_module.STATE_PROCESANDO_CRM
    STATE_LEAD_CREADO = config_module.STATE_LEAD_CREADO

    # Estados legacy
    STATE_ESPERANDO_RESPUESTA_INICIAL = config_module.STATE_ESPERANDO_RESPUESTA_INICIAL
    STATE_RECOPILANDO_NECESIDAD = config_module.STATE_RECOPILANDO_NECESIDAD

    # Estados tri-path routing (NUEVO)
    STATE_ROUTING_ANALYSIS = config_module.STATE_ROUTING_ANALYSIS
    STATE_SUPPORT_ACTIVE = config_module.STATE_SUPPORT_ACTIVE
    STATE_DEPARTMENT_REDIRECT = config_module.STATE_DEPARTMENT_REDIRECT

    VALID_STATES = config_module.VALID_STATES

    # Configuración de departamentos (NUEVO)
    DEPARTMENT_CONTACTS = config_module.DEPARTMENT_CONTACTS

except Exception as e:
    # Fallback si falla la carga dinámica
    print(f"Warning: No se pudieron cargar constantes de app.config: {e}")
    settings = None

# Importar BusinessHoursConfig
from .business_hours import BusinessHoursConfig

__all__ = [
    "BusinessHoursConfig",
    "Settings",
    "settings",
    "STATE_NUEVO",
    "STATE_POLITICAS_PRESENTADAS",
    "STATE_RECOPILANDO_NOMBRE",
    "STATE_NOMBRE_OBTENIDO",
    "STATE_PREGUNTA_CONTRATO_INMOBILIARIA",
    "STATE_PREGUNTA_CUAL_INMOBILIARIA",
    "STATE_PREGUNTA_SOLICITUD_LIBERTADOR",
    "STATE_PREGUNTA_FECHA_NECESIDAD",
    "STATE_FLUJO_COMPLETADO",
    "STATE_TRANSFERIDO",
    "STATE_TRANSFERIDO_SUPPORT",
    "STATE_CONSULTA_INFORMATIVA",
    "STATE_SOPORTE_ACTIVO",
    "STATE_REDIRIGIDO_CARTERA",
    "STATE_REDIRIGIDO_MANTENIMIENTO",
    "STATE_CAPTURANDO_DETALLES",
    "STATE_PROFUNDIZANDO_NECESIDAD",
    "STATE_CONFIRMANDO_INFORMACION",
    "STATE_PROCESANDO_CRM",
    "STATE_LEAD_CREADO",
    "STATE_ESPERANDO_RESPUESTA_INICIAL",
    "STATE_RECOPILANDO_NECESIDAD",
    "STATE_ROUTING_ANALYSIS",
    "STATE_SUPPORT_ACTIVE",
    "STATE_DEPARTMENT_REDIRECT",
    "VALID_STATES",
    "DEPARTMENT_CONTACTS"
]

ENABLE_HOT_RELOAD = True  # O False, dependiendo de la configuración deseada
