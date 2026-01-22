"""
E-Commerce Domain RAG Module

Provides ground-truth knowledge for e-commerce database schema design.
"""

from .ecommerce_retriever import EcommerceRAGRetriever
from .ecommerce_config import (
    EcommerceConfig,
    ECOMMERCE_POSTGRES_TYPE_MAP,
    ECOMMERCE_CARDINALITY_MAP,
    ECOMMERCE_LOOKUP_TABLES,
    ECOMMERCE_ENTITY_TYPES,
    ECOMMERCE_RELATIONSHIPS,
)

__all__ = [
    "EcommerceRAGRetriever",
    "EcommerceConfig",
    "ECOMMERCE_POSTGRES_TYPE_MAP",
    "ECOMMERCE_CARDINALITY_MAP",
    "ECOMMERCE_LOOKUP_TABLES",
    "ECOMMERCE_ENTITY_TYPES",
    "ECOMMERCE_RELATIONSHIPS",
]
