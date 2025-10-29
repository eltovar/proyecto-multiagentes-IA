#Definicion de tablas
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import STATE_NUEVO, VALID_STATES

class ConversationState:
    """
   ConversationState que representa el estado de una conversación y contiene las funciones para inicializar y conectar a la base de datos SQLite
    """
    def __init__(
        self,
        conversation_id: str = None,
        whatsapp_id: str = None,
        whatsapp: str = None,
        state: str = STATE_NUEVO,
        customer_name: Optional[str] = None,
        customer_needs: Optional[str] = None,
        lead_id: Optional[str] = None,
        current_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # conversation_id puede ser pasado directamente o derivado de whatsapp_id
        self.conversation_id = conversation_id or whatsapp_id or whatsapp or ""
        self.whatsapp_id = whatsapp_id or conversation_id or ""
        self.whatsapp = whatsapp  # Número WhatsApp completo con prefijo
        self.state = state
        self.customer_name = customer_name
        self.customer_needs = customer_needs
        self.lead_id = lead_id
        self.current_agent = current_agent
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

        # Validar estado
        if state not in VALID_STATES:
            raise ValueError(f"Estado invalido: {state}. Estados validos: {VALID_STATES}")

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario para serializacion."""
        return {
            "conversation_id": self.conversation_id,
            "whatsapp_id": self.whatsapp_id,
            "whatsapp": self.whatsapp,
            "state": self.state,
            "customer_name": self.customer_name,
            "customer_needs": self.customer_needs,
            "lead_id": self.lead_id,
            "current_agent": self.current_agent,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Crea una instancia desde un diccionario."""
        return cls(
            conversation_id=data.get("conversation_id"),
            whatsapp_id=data.get("whatsapp_id"),
            whatsapp=data.get("whatsapp"),
            state=data.get("state", STATE_NUEVO),
            customer_name=data.get("customer_name"),
            customer_needs=data.get("customer_needs"),
            lead_id=data.get("lead_id"),
            current_agent=data.get("current_agent"),
            metadata=data.get("metadata"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )

def get_database_connection() -> sqlite3.Connection:
    """
    Crea conexion a la base de datos SQLite.

    Returns:
        sqlite3.Connection: Conexion configurada con Row factory
    """
    db_path = "multiagent_leads.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
    return conn

def initialize_database() -> None:
    """
    Inicializa la base de datos SQLite con las tablas necesarias.
    Crea las tablas: conversations: Estado de conversaciones con clientes
    """
    
    print("= Inicializando base de datos SQLite...")

    conn = get_database_connection()
    cursor = conn.cursor()

    # Tabla de conversaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            whatsapp_id TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'NUEVO',
            customer_name TEXT,
            customer_needs TEXT,
            lead_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Indices para optimizacion
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_state
        ON conversations(state)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_created
        ON conversations(created_at)
    """)

    # Trigger para actualizar updated_at automaticamente
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_conversations_timestamp
        AFTER UPDATE ON conversations
        BEGIN
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE whatsapp_id = NEW.whatsapp_id;
        END
    """)

    conn.commit()
    conn.close()

    print(" Base de datos inicializada correctamente")
    print(f"=> Ubicacion: {os.path.abspath('multiagent_leads.db')}")

def get_database_stats() -> Dict[str, Any]:
    """
    Obtiene estadisticas de la base de datos.

    Returns: Dict con estadisticas de conversaciones por estado
    """
    conn = get_database_connection()
    cursor = conn.cursor()

    # Contar conversaciones por estado
    cursor.execute("""
        SELECT state, COUNT(*) as count
        FROM conversations
        GROUP BY state
    """)

    stats = {"conversations_by_state": dict(cursor.fetchall())}

    # Total de conversaciones
    cursor.execute("SELECT COUNT(*) as total FROM conversations")
    stats["total_conversations"] = cursor.fetchone()["total"]

    conn.close()
    return stats

if __name__ == "__main__":
    # Ejecuta directamente para inicializar
    initialize_database()