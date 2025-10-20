"""
Lead Scoring Strategies Package
Strategy Pattern para reducir complejidad ciclomática
"""

from .base import (
    LeadScorer,
    LeadTagger,
    PriorityClassifier,
    ScoringResult
)

from .strategies import (
    # Scorers
    DemoQualityScorer,
    InterestLevelScorer,
    ConversionProbabilityScorer,
    CompositeLeadScorer,
    # Taggers
    TransactionTypeTagger,
    PropertyTypeTagger,
    UrgencyTagger,
    MetadataTagger,
    # Priority Classifiers
    UrgencyPriorityClassifier
)

__all__ = [
    "LeadScorer", "LeadTagger", "PriorityClassifier", "ScoringResult",
    "DemoQualityScorer", "InterestLevelScorer", "ConversionProbabilityScorer", "CompositeLeadScorer",
    "TransactionTypeTagger", "PropertyTypeTagger", "UrgencyTagger", "MetadataTagger",
    "UrgencyPriorityClassifier"
]
