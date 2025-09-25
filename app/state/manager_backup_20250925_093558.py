"""
    Gestor de estado para operaciones CRUD en conversaciones.

    Maneja todas las operaciones de base de datos para el estado de conversaciones,
    incluyendo creacion, lectura, actualizacion y eliminacion.

    CRITICO: El Handoff Protocol se implementa aqui - una vez TRANSFERIDO, no se permite modificar el estado.
    """

import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.state.models import ConversationState, get_database_connection
from app.config import STATE_NUEVO, STATE_TRANSFERIDO, VALID_STATES
import structlog

logger = structlog.get_logger()

class StateManager:
    
    def get_conversation(self, whatsapp_id: str) -> Optional[ConversationState]:
        """
        Obtiene una conversacion por WhatsApp ID.

        Args:
            whatsapp_id: ID unico del usuario de WhatsApp

        Returns:
            ConversationState o None si no existe
        """
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

    def create_conversation(self, whatsapp_id: str) -> ConversationState:
        """
        Crea una nueva conversacion en estado NUEVO.

        Args:
            whatsapp_id: ID unico del usuario de WhatsApp

        Returns:
            ConversationState: Nueva conversacion creada

        Raises:
            sqlite3.IntegrityError: Si la conversacion ya existe
        """
        conn = get_database_connection()
        cursor = conn.cursor()

        now = datetime.now()
        cursor.execute("""
            INSERT INTO conversations (whatsapp_id, state, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (whatsapp_id, STATE_NUEVO, now, now))

        conn.commit()
        conn.close()

        logger.info("Nueva conversacion creada", whatsapp_id=whatsapp_id, state=STATE_NUEVO)

        return ConversationState(
            whatsapp_id=whatsapp_id,
            state=STATE_NUEVO,
            created_at=now,
            updated_at=now
        )

    def update_conversation_state(
        self,
        whatsapp_id: str,
        new_state: str,
        customer_name: Optional[str] = None,
        customer_needs: Optional[str] = None,
        lead_id: Optional[str] = None
    ) -> bool:
        """
        Actualiza el estado de una conversacion.

        HANDOFF PROTOCOL: Si el estado actual es TRANSFERIDO, NO se permite
        ninguna modificacion (los agentes IA estan bloqueados).

        Args:
            whatsapp_id: ID unico del usuario
            new_state: Nuevo estado (debe estar en VALID_STATES)
            customer_name: Nombre del cliente (opcional)
            customer_needs: Necesidades del cliente (opcional)
            lead_id: ID del lead en Leadsales (opcional)

        Returns:
            bool: True si se actualizo, False si esta bloqueado por Handoff Protocol

        Raises:
            ValueError: Si new_state no es valido
        """
        if new_state not in VALID_STATES:
            raise ValueError(f"Estado invalido: {new_state}. Estados validos: {VALID_STATES}")

        # Verificar estado actual (Handoff Protocol)
        current_conversation = self.get_conversation(whatsapp_id)
        if current_conversation and current_conversation.state == STATE_TRANSFERIDO:
            logger.warning(
                "Handoff Protocol activo - Conversacion bloqueada para agentes IA",
                whatsapp_id=whatsapp_id,
                current_state=STATE_TRANSFERIDO,
                attempted_new_state=new_state
            )
            return False

        conn = get_database_connection()
        cursor = conn.cursor()

        # Construir query dinamicamente
        update_fields = ["state = ?", "updated_at = ?"]
        params = [new_state, datetime.now()]

        if customer_name is not None:
            update_fields.append("customer_name = ?")
            params.append(customer_name)

        if customer_needs is not None:
            update_fields.append("customer_needs = ?")
            params.append(customer_needs)

        if lead_id is not None:
            update_fields.append("lead_id = ?")
            params.append(lead_id)

        params.append(whatsapp_id)

        query = f"""
            UPDATE conversations
            SET {', '.join(update_fields)}
            WHERE whatsapp_id = ?
        """

        cursor.execute(query, params)
        updated_rows = cursor.rowcount
        conn.commit()
        conn.close()

        if updated_rows > 0:
            logger.info(
                "Estado de conversacion actualizado",
                whatsapp_id=whatsapp_id,
                new_state=new_state,
                customer_name=customer_name,
                lead_id=lead_id
            )
            return True
        else:
            logger.warning("Conversacion no encontrada para actualizar", whatsapp_id=whatsapp_id)
            return False

    def get_or_create_conversation(self, whatsapp_id: str) -> ConversationState:
        """
        Obtiene una conversacion existente o crea una nueva.

        Args:
            whatsapp_id: ID unico del usuario de WhatsApp

        Returns:
            ConversationState: Conversacion existente o nueva
        """
        conversation = self.get_conversation(whatsapp_id)
        if conversation:
            return conversation
        else:
            return self.create_conversation(whatsapp_id)

    def get_conversations_by_state(self, state: str) -> List[ConversationState]:
        """
        Obtiene todas las conversaciones en un estado especifico.

        Args:
            state: Estado a filtrar

        Returns:
            List[ConversationState]: Lista de conversaciones
        """
        if state not in VALID_STATES:
            raise ValueError(f"Estado invalido: {state}")

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
        return conversations

    def is_conversation_transferred(self, whatsapp_id: str) -> bool:
        """
        Verifica si una conversacion esta en estado TRANSFERIDO (Handoff Protocol).

        Args:
            whatsapp_id: ID unico del usuario

        Returns:
            bool: True si esta transferida, False si pueden actuar agentes IA
        """
        conversation = self.get_conversation(whatsapp_id)
        return conversation is not None and conversation.state == STATE_TRANSFERIDO

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas de conversaciones.

        Returns:
            Dict con estadisticas detalladas
        """
        conn = get_database_connection()
        cursor = conn.cursor()

        # Conversaciones por estado
        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM conversations
            GROUP BY state
        """)
        stats_by_state = dict(cursor.fetchall())

        # Total
        cursor.execute("SELECT COUNT(*) as total FROM conversations")
        total = cursor.fetchone()["total"]

        # Conversaciones transferidas (Handoff activo)
        transferred_count = stats_by_state.get(STATE_TRANSFERIDO, 0)

        conn.close()

        return {
            "total_conversations": total,
            "conversations_by_state": stats_by_state,
            "active_handoffs": transferred_count,
            "ai_agents_active": total - transferred_count
        }

# Singleton para uso global
state_manager = StateManager()