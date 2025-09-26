from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Gestion centralizada de configuraciones Todo el sistema depende de estas confuguraciones.
    
    - WhatsApp Business API (Meta)
    - Google Gemini API
    - Leadsales CRM API
    """

    # WhatsApp Business API Configuration
    whatsapp_api_token: str
    whatsapp_verify_token: str
    whatsapp_phone_number_id: str
    whatsapp_app_secret: Optional[str] = None
    whatsapp_api_version: str = "v18.0"
    whatsapp_base_url: str = "https://graph.facebook.com"

    # Google Gemini Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-pro"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 1000

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
    fixed_flow_mode: bool = True  # Activa flujo fijo sin LLM (optimización costos)
    llm_fallback_enabled: bool = False  # LLM como fallback en errores

    # Security
    webhook_verify_signature: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Estados validos de conversacion
STATE_NUEVO = "NUEVO"
STATE_ESPERANDO_RESPUESTA_INICIAL = "ESPERANDO_RESPUESTA_INICIAL"
STATE_RECOPILANDO_NOMBRE = "RECOPILANDO_NOMBRE"
STATE_RECOPILANDO_NECESIDAD = "RECOPILANDO_NECESIDAD"
STATE_TRANSFERIDO = "TRANSFERIDO"

VALID_STATES = [
    STATE_NUEVO,
    STATE_ESPERANDO_RESPUESTA_INICIAL,
    STATE_RECOPILANDO_NOMBRE,
    STATE_RECOPILANDO_NECESIDAD,
    STATE_TRANSFERIDO
]

# Singleton para acceso global
settings = Settings()