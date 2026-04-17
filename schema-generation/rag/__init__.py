"""
RAG (Retrieval-Augmented Generation) Module for Database Design

This module provides domain-aware RAG capabilities for the multi-agent
database design system. It automatically detects the domain from requirements
and uses appropriate domain-specific knowledge ("ground truth") for schema design.

Supported Domains:
- Healthcare (entity definitions, relationship patterns, constraints)
- Finance (coming soon)
- E-commerce (coming soon)
- Education (coming soon)

Each domain provides:
- Entity definitions with required/recommended attributes
- Relationship patterns with cardinality rules
- PostgreSQL datatype mappings
- Normalization rules and examples
- Design patterns (temporal data, audit trails, etc.)
- Constraint rules and validation

Usage:
    from rag import RAG_TOOLS, detect_domain_from_text
    
    # Add RAG tools to agents
    agent = AssistantAgent(
        "MyAgent",
        tools=RAG_TOOLS,
        ...
    )
    
    # Manually detect domain
    domain = detect_domain_from_text("Patient management system...")
"""

from .base_rag import (
    BaseRAGRetriever,
    RAGChunk,
    RAGSearchResult,
    RAGConfig,
    ChunkType,
    generate_chunk_id,
)

from .rag_config import (
    Domain,
    detect_domain_from_text,
    COMMON_POSTGRES_TYPE_MAP,
    CARDINALITY_MAP,
)

from .rag_tools import (
    query_domain_rag,
    get_entity_guidance,
    get_relationship_guidance,
    get_datatype_mapping,
    get_cardinality_rules,
    get_normalization_rules,
    detect_requirement_domain,
    RAG_TOOLS,
)

from .domains import get_domain_retriever, get_retriever_for_text

__all__ = [
    # Base classes
    "BaseRAGRetriever",
    "RAGChunk",
    "RAGSearchResult",
    "RAGConfig",
    "ChunkType",
    "generate_chunk_id",
    
    # Configuration
    "Domain",
    "detect_domain_from_text",
    "COMMON_POSTGRES_TYPE_MAP",
    "CARDINALITY_MAP",
    
    # Tools
    "query_domain_rag",
    "get_entity_guidance",
    "get_relationship_guidance",
    "get_datatype_mapping",
    "get_cardinality_rules",
    "get_normalization_rules",
    "detect_requirement_domain",
    "RAG_TOOLS",
    
    # Domain retrievers
    "get_domain_retriever",
    "get_retriever_for_text",
]
