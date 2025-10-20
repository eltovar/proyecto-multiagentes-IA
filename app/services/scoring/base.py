"""
Base classes for Strategy Pattern - Lead Scoring
Elimina complejidad ciclomatica mediante estrategias especializadas
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ScoringResult:
    """Resultado de scoring estructurado"""
    score: float  # 0.0 - 100.0
    confidence: float  # 0.0 - 1.0
    factors: Dict[str, Any]  # Factores que contribuyeron al score
    tags: List[str]  # Tags generadas
    reasoning: str  # Explicacion del score


class LeadScorer(ABC):
    """
    Strategy base para scoring de leads.

    Ventajas sobre metodos monoliticos:
    - Complejidad ciclomatica reducida (cada scorer es simple)
    - Testeable independientemente
    - Extensible (nuevos scorers sin modificar existentes)
    - Reutilizable (mismo scorer en multiples contextos)
    """

    def __init__(self, name: str):
        """
        Args:
            name: Nombre descriptivo del scorer
        """
        self.name = name

    @abstractmethod
    def score(self, lead_data: Dict[str, Any]) -> ScoringResult:
        """
        Calcula score del lead.

        Args:
            lead_data: Datos del lead a evaluar

        Returns:
            ScoringResult con score y metadata
        """
        pass

    def validate_data(self, lead_data: Dict[str, Any]) -> bool:
        """
        Valida que lead_data tenga campos requeridos.

        Args:
            lead_data: Datos del lead

        Returns:
            True si datos validos
        """
        return bool(lead_data)


class LeadTagger(ABC):
    """
    Strategy base para generacion de tags.

    Tags ayudan a categorizar y priorizar leads en CRM.
    """

    def __init__(self, name: str):
        """
        Args:
            name: Nombre descriptivo del tagger
        """
        self.name = name

    @abstractmethod
    def generate_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """
        Genera tags para el lead.

        Args:
            lead_data: Datos del lead

        Returns:
            Lista de tags generadas
        """
        pass


class PriorityClassifier(ABC):
    """
    Strategy base para clasificacion de prioridad.

    Determina que tan urgente es contactar al lead.
    """

    def __init__(self, name: str):
        """
        Args:
            name: Nombre descriptivo del classifier
        """
        self.name = name

    @abstractmethod
    def classify(self, lead_data: Dict[str, Any]) -> str:
        """
        Clasifica prioridad del lead.

        Args:
            lead_data: Datos del lead

        Returns:
            Nivel de prioridad (ej: "ALTA", "MEDIA", "BAJA")
        """
        pass
