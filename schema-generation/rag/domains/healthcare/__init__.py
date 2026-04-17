"""
Healthcare Domain RAG Module

Provides ground-truth knowledge for healthcare database schema design including:
- Entity definitions (Patient, Provider, Encounter, etc.)
- Relationship patterns 
- Data type mappings
- Normalization rules
- Healthcare-specific constraints
"""

from .healthcare_retriever import HealthcareRAGRetriever
from .healthcare_config import (
    HealthcareConfig,
    HEALTHCARE_POSTGRES_TYPE_MAP,
    HEALTHCARE_CARDINALITY_MAP,
    HEALTHCARE_ENTITY_TYPES,
)

__all__ = [
    "HealthcareRAGRetriever",
    "HealthcareConfig",
    "HEALTHCARE_POSTGRES_TYPE_MAP",
    "HEALTHCARE_CARDINALITY_MAP",
    "HEALTHCARE_ENTITY_TYPES",
]
