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
    """ Strategy base para scoring de leads."""

    def __init__(self, name: str):
  
        self.name = name

    @abstractmethod
    def score(self, lead_data: Dict[str, Any]) -> ScoringResult:
        """Calcula scoring del lead."""
        pass

    def validate_data(self, lead_data: Dict[str, Any]) -> bool:
        """ Valida que lead_data tenga campos requeridos """
        return bool(lead_data)


class LeadTagger(ABC):
    """ Strategy base para generacion de tags. """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_tags(self, lead_data: Dict[str, Any]) -> List[str]:
        """ Genera tags para el lead. """
        pass


class PriorityClassifier(ABC):
    """ clasificacion de prioridad. 
        Determina que tan urgente es contactar al lead.
    """

    def __init__(self, name: str):
    
        self.name = name

    @abstractmethod
    def classify(self, lead_data: Dict[str, Any]) -> str:
     """Clasifica prioridad del lead"""
     pass
