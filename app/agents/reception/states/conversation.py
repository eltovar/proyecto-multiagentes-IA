"""
ConversationStateMachine - Máquina de estados para ReceptionAgent
Define transiciones válidas y validación de flujo obligatorio
"""

from enum import Enum
from typing import Dict, List, Optional, Set


class ReceptionState(Enum):
    """
    Estados del flujo obligatorio de ReceptionAgent.
    Mapeados desde config.py (líneas 56-64)
    """
    # Estados del flujo principal
    NUEVO = "NUEVO"
    POLITICAS_PRESENTADAS = "POLITICAS_PRESENTADAS"
    RECOPILANDO_NOMBRE = "RECOPILANDO_NOMBRE"
    NOMBRE_OBTENIDO = "NOMBRE_OBTENIDO"
    PREGUNTA_CONTRATO_INMOBILIARIA = "PREGUNTA_CONTRATO_INMOBILIARIA"
    PREGUNTA_CUAL_INMOBILIARIA = "PREGUNTA_CUAL_INMOBILIARIA"
    PREGUNTA_SOLICITUD_LIBERTADOR = "PREGUNTA_SOLICITUD_LIBERTADOR"
    PREGUNTA_FECHA_NECESIDAD = "PREGUNTA_FECHA_NECESIDAD"
    FLUJO_COMPLETADO = "FLUJO_COMPLETADO"

    # Estados especiales
    TRANSFERIDO = "TRANSFERIDO"
    LIMITE_ALCANZADO = "LIMITE_ALCANZADO"
    FUERA_DE_HORARIO = "FUERA_DE_HORARIO"

    @classmethod
    def from_string(cls, state_str: str) -> Optional['ReceptionState']:
        """Convierte string a ReceptionState"""
        try:
            return cls(state_str)
        except ValueError:
            return None


class ConversationStateMachine:
    """
    Máquina de estados que define:
    - Transiciones válidas entre estados
    - Validación de flujo obligatorio
    - Estados terminales
    """

    def __init__(self):
        """
        Define el grafo de transiciones del flujo obligatorio.

        Flujo normal:
        NUEVO → POLITICAS_PRESENTADAS → RECOPILANDO_NOMBRE → NOMBRE_OBTENIDO
        → PREGUNTA_CONTRATO_INMOBILIARIA → [PREGUNTA_CUAL_INMOBILIARIA]
        → PREGUNTA_SOLICITUD_LIBERTADOR → PREGUNTA_FECHA_NECESIDAD
        → FLUJO_COMPLETADO → TRANSFERIDO
        """
        self.transitions: Dict[ReceptionState, List[ReceptionState]] = {
            # Inicio del flujo
            ReceptionState.NUEVO: [
                ReceptionState.POLITICAS_PRESENTADAS,
                ReceptionState.FUERA_DE_HORARIO,  # Si es fuera de horario
            ],

            # Captura de nombre (puede tener reintentos)
            ReceptionState.POLITICAS_PRESENTADAS: [
                ReceptionState.RECOPILANDO_NOMBRE,
                ReceptionState.NOMBRE_OBTENIDO,  # Si LLM extrae nombre directo
            ],

            ReceptionState.RECOPILANDO_NOMBRE: [
                ReceptionState.RECOPILANDO_NOMBRE,  # Reintento
                ReceptionState.NOMBRE_OBTENIDO,
            ],

            # Preguntas obligatorias
            ReceptionState.NOMBRE_OBTENIDO: [
                ReceptionState.PREGUNTA_CONTRATO_INMOBILIARIA,
            ],

            ReceptionState.PREGUNTA_CONTRATO_INMOBILIARIA: [
                ReceptionState.PREGUNTA_CUAL_INMOBILIARIA,  # Si tiene contrato
                ReceptionState.PREGUNTA_SOLICITUD_LIBERTADOR,  # Si no tiene
            ],

            ReceptionState.PREGUNTA_CUAL_INMOBILIARIA: [
                ReceptionState.PREGUNTA_SOLICITUD_LIBERTADOR,
            ],

            ReceptionState.PREGUNTA_SOLICITUD_LIBERTADOR: [
                ReceptionState.PREGUNTA_FECHA_NECESIDAD,
            ],

            ReceptionState.PREGUNTA_FECHA_NECESIDAD: [
                ReceptionState.FLUJO_COMPLETADO,
            ],

            # Estados terminales
            ReceptionState.FLUJO_COMPLETADO: [
                ReceptionState.TRANSFERIDO,  # Transfer a LeadsalesAgent
            ],

            # Estados especiales (terminales)
            ReceptionState.LIMITE_ALCANZADO: [],
            ReceptionState.FUERA_DE_HORARIO: [],
            ReceptionState.TRANSFERIDO: [],
        }

        # Estados terminales (no permiten más transiciones)
        self.terminal_states: Set[ReceptionState] = {
            ReceptionState.TRANSFERIDO,
            ReceptionState.LIMITE_ALCANZADO,
            ReceptionState.FUERA_DE_HORARIO,
        }

    def is_valid_transition(
        self,
        from_state: str,
        to_state: str
    ) -> bool:
        """
        Valida si la transición entre estados es permitida.

        Args:
            from_state: Estado actual (string)
            to_state: Estado destino (string)

        Returns:
            True si la transición es válida
        """
        current = ReceptionState.from_string(from_state)
        next_state = ReceptionState.from_string(to_state)

        if not current or not next_state:
            return False

        # Estados terminales no permiten transiciones
        if current in self.terminal_states:
            return False

        # Verificar si la transición está definida
        allowed_transitions = self.transitions.get(current, [])
        return next_state in allowed_transitions

    def get_next_states(self, current_state: str) -> List[str]:
        """
        Retorna lista de estados válidos desde el estado actual.

        Args:
            current_state: Estado actual (string)

        Returns:
            Lista de strings de estados válidos
        """
        state = ReceptionState.from_string(current_state)
        if not state:
            return []

        next_states = self.transitions.get(state, [])
        return [s.value for s in next_states]

    def is_terminal_state(self, state: str) -> bool:
        """
        Verifica si un estado es terminal.

        Args:
            state: Estado a verificar (string)

        Returns:
            True si es estado terminal
        """
        state_enum = ReceptionState.from_string(state)
        return state_enum in self.terminal_states if state_enum else False

    def get_flow_progress(self, current_state: str) -> float:
        """
        Calcula el progreso del flujo (0.0 a 1.0).

        Args:
            current_state: Estado actual (string)

        Returns:
            Porcentaje de progreso (0.0 = inicio, 1.0 = completado)
        """
        # Orden del flujo principal
        flow_order = [
            ReceptionState.NUEVO,
            ReceptionState.POLITICAS_PRESENTADAS,
            ReceptionState.RECOPILANDO_NOMBRE,
            ReceptionState.NOMBRE_OBTENIDO,
            ReceptionState.PREGUNTA_CONTRATO_INMOBILIARIA,
            ReceptionState.PREGUNTA_SOLICITUD_LIBERTADOR,
            ReceptionState.PREGUNTA_FECHA_NECESIDAD,
            ReceptionState.FLUJO_COMPLETADO,
        ]

        state = ReceptionState.from_string(current_state)
        if not state or state not in flow_order:
            return 0.0

        current_index = flow_order.index(state)
        return current_index / (len(flow_order) - 1)

    def validate_flow_integrity(
        self,
        conversation_history: List[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Valida que el historial de estados sea coherente.

        Args:
            conversation_history: Lista de estados en orden cronológico

        Returns:
            (is_valid, error_message)
        """
        if not conversation_history:
            return False, "Historial vacío"

        if len(conversation_history) == 1:
            return True, None

        # Validar cada transición
        for i in range(len(conversation_history) - 1):
            from_state = conversation_history[i]
            to_state = conversation_history[i + 1]

            if not self.is_valid_transition(from_state, to_state):
                return False, f"Transición inválida: {from_state} → {to_state}"

        return True, None

    def get_required_fields(self, state: str) -> List[str]:
        """
        Retorna campos requeridos para avanzar desde un estado.

        Args:
            state: Estado actual (string)

        Returns:
            Lista de campos requeridos en conversation data
        """
        state_enum = ReceptionState.from_string(state)

        required_fields_map = {
            ReceptionState.POLITICAS_PRESENTADAS: [],
            ReceptionState.RECOPILANDO_NOMBRE: [],
            ReceptionState.NOMBRE_OBTENIDO: ["customer_name"],
            ReceptionState.PREGUNTA_CONTRATO_INMOBILIARIA: ["customer_name"],
            ReceptionState.PREGUNTA_CUAL_INMOBILIARIA: ["tiene_contrato_inmobiliaria"],
            ReceptionState.PREGUNTA_SOLICITUD_LIBERTADOR: ["customer_name"],
            ReceptionState.PREGUNTA_FECHA_NECESIDAD: ["tiene_solicitud_libertador"],
            ReceptionState.FLUJO_COMPLETADO: ["customer_name", "fecha_necesidad"],
        }

        return required_fields_map.get(state_enum, [])

    def __repr__(self) -> str:
        return f"<ConversationStateMachine: {len(self.transitions)} states>"
