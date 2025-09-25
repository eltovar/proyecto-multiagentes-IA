"""
ConversationQueries: Consultas complejas y estadísticas.
Responsable de filtros, análisis y operaciones de consulta avanzadas.
"""

from typing import List, Dict, Any
from datetime import datetime
from app.state.models import ConversationState, get_database_connection

class ConversationQueries:

    def __init__(self):
        self.valid_states = ["NUEVO", "RECOPILANDO_NOMBRE", "RECOPILANDO_NECESIDAD", "TRANSFERIDO"]

    def get_conversations_by_state(self, state: str) -> List[ConversationState]:
        if state not in self.valid_states:
            print(f"[ConversationQueries] Estado inválido: {state}")
            return []

        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT whatsapp_id, state, customer_name, customer_needs, lead_id,
                   created_at, updated_at
            FROM conversations
            WHERE state = ?
            ORDER BY created_at DESC
        """, (state,))

        conversations = []
        for row in cursor.fetchall():
            conversations.append(ConversationState(
                whatsapp_id=row["whatsapp_id"],
                state=row["state"],
                customer_name=row["customer_name"],
                customer_needs=row["customer_needs"],
                lead_id=row["lead_id"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ))

        conn.close()
        print(f"[ConversationQueries] Encontradas {len(conversations)} conversaciones en estado {state}")
        return conversations

    def get_stats(self) -> Dict[str, Any]:
        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM conversations
            GROUP BY state
        """)
        stats_by_state = dict(cursor.fetchall())

        cursor.execute("SELECT COUNT(*) as total FROM conversations")
        total = cursor.fetchone()["total"]

        transferred_count = stats_by_state.get("TRANSFERIDO", 0)

        conn.close()

        return {
            "total_conversations": total,
            "conversations_by_state": stats_by_state,
            "active_handoffs": transferred_count,
            "ai_agents_active": total - transferred_count
        }

    def get_active_conversations(self) -> List[ConversationState]:
        active_states = ["NUEVO", "RECOPILANDO_NOMBRE", "RECOPILANDO_NECESIDAD"]
        conn = get_database_connection()
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(active_states))
        cursor.execute(f"""
            SELECT whatsapp_id, state, customer_name, customer_needs, lead_id,
                   created_at, updated_at
            FROM conversations
            WHERE state IN ({placeholders})
            ORDER BY updated_at DESC
        """, active_states)

        conversations = []
        for row in cursor.fetchall():
            conversations.append(ConversationState(
                whatsapp_id=row["whatsapp_id"],
                state=row["state"],
                customer_name=row["customer_name"],
                customer_needs=row["customer_needs"],
                lead_id=row["lead_id"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ))

        conn.close()
        print(f"[ConversationQueries] {len(conversations)} conversaciones activas (no transferidas)")
        return conversations

    def get_transferred_conversations(self) -> List[ConversationState]:
        return self.get_conversations_by_state("TRANSFERIDO")