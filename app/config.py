from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Gestion centralizada de configuraciones Todo el sistema depende de estas confuguraciones.
    
    - WhatsApp Business API (Meta)
    - gpm 4o mini
    - Leadsales CRM API
    """

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

    # Flow Control Configuration
    fixed_flow_mode: bool = False  # ACTIVADO: Usa LLM ChatGPT-4o mini para clasificación
    llm_fallback_enabled: bool = True  # LLM activado para mejor precisión

    # Security
    webhook_verify_signature: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

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
STATE_TRANSFERIDO_SUPPORT = "TRANSFERIDO_SUPPORT"
STATE_CONSULTA_INFORMATIVA = "CONSULTA_INFORMATIVA"
STATE_SOPORTE_ACTIVO = "SOPORTE_ACTIVO"
STATE_REDIRIGIDO_CARTERA = "REDIRIGIDO_CARTERA"
STATE_REDIRIGIDO_MANTENIMIENTO = "REDIRIGIDO_MANTENIMIENTO"

# Estados de LeadsalesAgent (Conversión CRM)
STATE_CAPTURANDO_DETALLES = "CAPTURANDO_DETALLES"
STATE_PROFUNDIZANDO_NECESIDAD = "PROFUNDIZANDO_NECESIDAD"
STATE_CONFIRMANDO_INFORMACION = "CONFIRMANDO_INFORMACION"
STATE_PROCESANDO_CRM = "PROCESANDO_CRM"
STATE_LEAD_CREADO = "LEAD_CREADO"

# Estados legacy (mantener para compatibilidad)
STATE_ESPERANDO_RESPUESTA_INICIAL = "ESPERANDO_RESPUESTA_INICIAL"
STATE_RECOPILANDO_NECESIDAD = "RECOPILANDO_NECESIDAD"

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
    STATE_TRANSFERIDO_SUPPORT,
    STATE_CONSULTA_INFORMATIVA,
    STATE_SOPORTE_ACTIVO,
    STATE_REDIRIGIDO_CARTERA,
    STATE_REDIRIGIDO_MANTENIMIENTO,
    # Estados de LeadsalesAgent
    STATE_CAPTURANDO_DETALLES,
    STATE_PROFUNDIZANDO_NECESIDAD,
    STATE_CONFIRMANDO_INFORMACION,
    STATE_PROCESANDO_CRM,
    STATE_LEAD_CREADO,
    # Legacy states
    STATE_ESPERANDO_RESPUESTA_INICIAL,
    STATE_RECOPILANDO_NECESIDAD
]

# Singleton para acceso global
settings = Settings()