"""
ConversationCRUD: Operaciones básicas de base de datos.
Responsable de crear, leer, actualizar y eliminar conversaciones.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.state.models import ConversationState, get_database_connection

class ConversationCRUD:

    def create_conversation(self, whatsapp_id: str) -> ConversationState:
        conn = get_database_connection()
        cursor = conn.cursor()

        now = datetime.now()
        cursor.execute("""
            INSERT INTO conversations (whatsapp_id, state, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (whatsapp_id, "NUEVO", now, now))

        conn.commit()
        conn.close()

        print(f"[ConversationCRUD] Nueva conversación creada: {whatsapp_id}")

        return ConversationState(
            whatsapp_id=whatsapp_id,
            state="NUEVO",
            created_at=now,
            updated_at=now
        )

    def get_conversation(self, whatsapp_id: str) -> Optional[ConversationState]:
        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT whatsapp_id, state, customer_name, customer_needs, lead_id,
                   created_at, updated_at
            FROM conversations
            WHERE whatsapp_id = ?
        """, (whatsapp_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return ConversationState(
                whatsapp_id=row["whatsapp_id"],
                state=row["state"],
                customer_name=row["customer_name"],
                customer_needs=row["customer_needs"],
                lead_id=row["lead_id"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            )
        return None

    def update_conversation_data(self, whatsapp_id: str, data: Dict[str, Any]) -> bool:
        conn = get_database_connection()
        cursor = conn.cursor()

        fields = ["updated_at = ?"]
        params = [datetime.now()]

        for key, value in data.items():
            if key in ["customer_name", "customer_needs", "lead_id"] and value is not None:
                fields.append(f"{key} = ?")
                params.append(value)

        params.append(whatsapp_id)

        cursor.execute(f"""
            UPDATE conversations
            SET {', '.join(fields)}
            WHERE whatsapp_id = ?
        """, params)

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if updated:
            print(f"[ConversationCRUD] Datos actualizados: {whatsapp_id}")

        return updated

    def delete_conversation(self, whatsapp_id: str) -> bool:
        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM conversations WHERE whatsapp_id = ?", (whatsapp_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        if deleted:
            print(f"[ConversationCRUD] Conversación eliminada: {whatsapp_id}")

        return deleted