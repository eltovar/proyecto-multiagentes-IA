from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
import json
from pydantic import ConfigDict
from dotenv import load_dotenv

# Cargar .env explícitamente para que os.getenv() funcione
load_dotenv()

class Settings(BaseSettings): #Hereda de baseSetting para configuraciones automaticas de .env
    
    # WhatsApp Business API Configuration
    whatsapp_api_token: str
    whatsapp_verify_token: str
    whatsapp_phone_number_id: str
    whatsapp_app_secret: Optional[str] = None
    whatsapp_api_version: str = "v18.0"
    whatsapp_base_url: str = "https://graph.facebook.com"

    # OpenAI Configuration
    openai_api_key: str
    llm_model_name: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1000

    # Leadsales CRM Configuration
    leadsales_api_url: str
    leadsales_api_token: str
    leadsales_timeout: int = 30

    # Database Configuration
    database_url: str = "sqlite:///./multiagent_leads.db"

    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug_mode: bool = False
    log_level: str = "INFO"

    # Business Rules
    max_messages_per_day: int = 2100  # ~70 mensajes/dia
    response_timeout_seconds: int = 3
    handoff_protocol_enabled: bool = True

    # Flow Control Configuration (definen si el sistema se basa en un flujo rígido o usa el LLM (gpt-4o-mini) para la clasificación y ruteo.)
    fixed_flow_mode: bool = False  # ACTIVADO: Usa LLM ChatGPT-4o mini para clasificación
    llm_fallback_enabled: bool = True  # LLM activado para mejor precisión

    # Security
    webhook_verify_signature: bool = True

    # RAG Re-ranking Configuration
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_top_k: int = 3
    reranker_enabled: bool = True  # Feature flag para A/B testing

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Permite variables ENV adicionales (ej: DEPARTMENT_CONTACT_*)
    )


ENABLE_HOT_RELOAD = True
# Estados validos de conversacion - Refactorizado para flujo obligatorio
STATE_NUEVO = "NUEVO"
STATE_POLITICAS_PRESENTADAS = "POLITICAS_PRESENTADAS"
STATE_RECOPILANDO_NOMBRE = "RECOPILANDO_NOMBRE"
STATE_NOMBRE_OBTENIDO = "NOMBRE_OBTENIDO"
STATE_PREGUNTA_CONTRATO_INMOBILIARIA = "PREGUNTA_CONTRATO_INMOBILIARIA"
STATE_PREGUNTA_CUAL_INMOBILIARIA = "PREGUNTA_CUAL_INMOBILIARIA"
STATE_PREGUNTA_SOLICITUD_LIBERTADOR = "PREGUNTA_SOLICITUD_LIBERTADOR"
STATE_PREGUNTA_FECHA_NECESIDAD = "PREGUNTA_FECHA_NECESIDAD"
STATE_FLUJO_COMPLETADO = "FLUJO_COMPLETADO"
STATE_TRANSFERIDO = "TRANSFERIDO"

# Estados de SupportAgent
STATE_CONSULTA_INFORMATIVA = "CONSULTA_INFORMATIVA"
STATE_SOPORTE_ACTIVO = "SOPORTE_ACTIVO"

# Estados de LeadsalesAgent (Conversión CRM)
STATE_CAPTURANDO_DETALLES = "CAPTURANDO_DETALLES"
STATE_PROFUNDIZANDO_NECESIDAD = "PROFUNDIZANDO_NECESIDAD"
STATE_CONFIRMANDO_INFORMACION = "CONFIRMANDO_INFORMACION"
STATE_PROCESANDO_CRM = "PROCESANDO_CRM"
STATE_LEAD_CREADO = "LEAD_CREADO"

# Estado legacy (mantener para compatibilidad)
STATE_RECOPILANDO_NECESIDAD = "RECOPILANDO_NECESIDAD"

# Estados tri-path routing (NUEVO)
STATE_ROUTING_ANALYSIS = "ROUTING_ANALYSIS"
STATE_SUPPORT_ACTIVE = "SUPPORT_ACTIVE"
STATE_DEPARTMENT_REDIRECT = "DEPARTMENT_REDIRECT"

VALID_STATES = [
    # Estados de ReceptionAgent
    STATE_NUEVO,
    STATE_POLITICAS_PRESENTADAS,
    STATE_RECOPILANDO_NOMBRE,
    STATE_NOMBRE_OBTENIDO,
    STATE_PREGUNTA_CONTRATO_INMOBILIARIA,
    STATE_PREGUNTA_CUAL_INMOBILIARIA,
    STATE_PREGUNTA_SOLICITUD_LIBERTADOR,
    STATE_PREGUNTA_FECHA_NECESIDAD,
    STATE_FLUJO_COMPLETADO,
    STATE_TRANSFERIDO,
    # Estados de SupportAgent
    STATE_CONSULTA_INFORMATIVA,
    STATE_SOPORTE_ACTIVO,
    # Estados de LeadsalesAgent
    STATE_CAPTURANDO_DETALLES,
    STATE_PROFUNDIZANDO_NECESIDAD,
    STATE_CONFIRMANDO_INFORMACION,
    STATE_PROCESANDO_CRM,
    STATE_LEAD_CREADO,
    # Legacy state (mantener)
    STATE_RECOPILANDO_NECESIDAD,
    # Tri-path routing states
    STATE_ROUTING_ANALYSIS,
    STATE_SUPPORT_ACTIVE,
    STATE_DEPARTMENT_REDIRECT
]

# CONFIGURACIÓN DE DEPARTAMENTOS (Todos los agentes deben adherirse estrictamente a estas transiciones.)
# Defaults hardcoded como fallback (valores actuales)
_DEFAULT_DEPARTMENT_CONTACTS = {
    "propietarios": {
        "phone": "322 502 1493",
        "name": "Departamento de Propietarios",
        "hours": "Lun-Vie 8AM-6PM",
        "services": ["Reportes de inmuebles", "Administración", "Consultas propietarios"],
        "keywords": ["propietario", "dueño", "arrendador", "mi inmueble"]
    },
    "proveedores": {
        "phone": "323 515 8007",
        "name": "Departamento de Proveedores",
        "hours": "Lun-Vie 8AM-5PM",
        "services": ["Alianzas comerciales", "Materiales", "Servicios"],
        "keywords": ["proveedor", "materiales", "servicios", "alianza"]
    },
    "contratos": {
        "phone": "320 649 1288",
        "name": "Departamento de Contratos",
        "hours": "Lun-Vie 8AM-6PM",
        "services": ["Renovación contratos", "Cláusulas", "Términos legales"],
        "keywords": ["contrato", "renovar", "cancelar", "cláusula"]
    },
    "reparaciones": {
        "phone": "323 515 8007",
        "name": "Mantenimiento y Reparaciones",
        "hours": "24/7 Emergencias",
        "services": ["Reparaciones urgentes", "Mantenimiento preventivo", "Emergencias"],
        "keywords": ["reparación", "daño", "arreglo", "fuga", "mantenimiento"]
    },
    "abogados": {
        "phone": "321 789 8679",
        "name": "Departamento Legal",
        "hours": "Lun-Vie 9AM-5PM",
        "services": ["Asesoría jurídica", "Demandas", "Trámites legales"],
        "keywords": ["abogado", "legal", "demanda", "jurídico"]
    }
}

def get_department_contacts() -> Dict[str, Dict[str, Any]]:
    """ Obtener diccionario de contactos de departamentos """
    
    env_json = os.getenv("DEPARTMENT_CONTACTS_JSON")
    if env_json:
        try:
            contacts = json.loads(env_json)
            print("[Config] DEPARTMENT_CONTACTS cargado desde ENV (JSON)")
            return contacts
        except json.JSONDecodeError as e:
            print(f"[Config] WARNING: DEPARTMENT_CONTACTS_JSON inválido: {e}")
            print("[Config] Usando valores por defecto (fallback)")
            return _DEFAULT_DEPARTMENT_CONTACTS

    # Opción 2: Variables individuales por departamento
    contacts = {}
    any_env_found = False

    for dept_key in _DEFAULT_DEPARTMENT_CONTACTS.keys():
        dept_upper = dept_key.upper()

        # Buscar variables ENV para este departamento
        phone = os.getenv(f"DEPARTMENT_CONTACT_{dept_upper}_PHONE")
        name = os.getenv(f"DEPARTMENT_CONTACT_{dept_upper}_NAME")
        hours = os.getenv(f"DEPARTMENT_CONTACT_{dept_upper}_HOURS")

        if phone or name or hours:
            any_env_found = True
            # Usar ENV con fallback a defaults para campos faltantes
            default = _DEFAULT_DEPARTMENT_CONTACTS[dept_key]
            contacts[dept_key] = {
                "phone": phone or default["phone"],
                "name": name or default["name"],
                "hours": hours or default["hours"],
                "services": default["services"],  # No configurable por ENV
                "keywords": default["keywords"]   # No configurable por ENV
            }
        else:
            # Usar defaults completos
            contacts[dept_key] = _DEFAULT_DEPARTMENT_CONTACTS[dept_key]

    if any_env_found:
        print("[Config] DEPARTMENT_CONTACTS cargado parcialmente desde ENV")
    else:
        print("[Config] WARNING: DEPARTMENT_CONTACTS usando valores por defecto (no ENV configurado)")

    return contacts

# Lazy loading - se carga al primer acceso
_DEPARTMENT_CONTACTS_CACHE = None

def get_department_contact(dept: str) -> Optional[Dict[str, Any]]:
    """ Obtiene configuración de un departamento específico. """
    global _DEPARTMENT_CONTACTS_CACHE

    if _DEPARTMENT_CONTACTS_CACHE is None:
        _DEPARTMENT_CONTACTS_CACHE = get_department_contacts()

    return _DEPARTMENT_CONTACTS_CACHE.get(dept)

# Backward compatibility: variable global
DEPARTMENT_CONTACTS = get_department_contacts()

# Singleton para acceso global
settings = Settings()