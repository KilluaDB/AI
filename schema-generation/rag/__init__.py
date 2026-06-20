"""
RAG (Retrieval-Augmented Generation) Module

This module provides TWO complementary capabilities for the multi-agent design system:

1. Dynamic few-shot retrieval (`get_similar_examples`):
   For each input requirement, find the most similar past requirements and return their
   `requirement -> relational schema` pairs to use as few-shot examples.
   Data: rag/examples/<domain>.json. Code: fewshot_retriever.py + rag_tools.py.

2. Domain knowledge tools (per-domain "ground-truth" rules):
   Explicit design rules for a detected domain — standard entity attributes (required vs.
   recommended), relationship/cardinality patterns, PostgreSQL datatype mappings, and
   normalization guidelines. Domains: Healthcare, E-Commerce.
   Code: knowledge_tools.py + domains/<domain>/.

`RAG_TOOLS` exposes the full set (few-shot + knowledge). `FEWSHOT_TOOLS` and `KNOWLEDGE_TOOLS`
expose each group separately for per-agent wiring. See rag/README.md.
"""

from .rag_config import (
    Domain,
    RAGConfig,
    detect_domain_from_text,
)

# --- Few-shot example retrieval -------------------------------------------------
from .fewshot_retriever import (
    FewShotExample,
    FewShotResult,
    FewShotRetriever,
    get_retriever,
)
from .rag_tools import (
    get_similar_examples,
    FEWSHOT_TOOLS,
)

# --- Domain knowledge base ------------------------------------------------------
from .base_rag import (
    BaseRAGRetriever,
    RAGChunk,
    RAGSearchResult,
    ChunkType,
    generate_chunk_id,
)
from .knowledge_tools import (
    query_domain_rag,
    get_entity_guidance,
    get_relationship_guidance,
    get_datatype_mapping,
    get_cardinality_rules,
    get_normalization_rules,
    detect_requirement_domain,
    KNOWLEDGE_TOOLS,
)
from .domains import get_domain_retriever, get_retriever_for_text

# Full tool set: few-shot retrieval + domain knowledge rules.
RAG_TOOLS = FEWSHOT_TOOLS + KNOWLEDGE_TOOLS

__all__ = [
    # Configuration
    "Domain",
    "RAGConfig",
    "detect_domain_from_text",
    # Few-shot retrieval
    "FewShotExample",
    "FewShotResult",
    "FewShotRetriever",
    "get_retriever",
    "get_similar_examples",
    "FEWSHOT_TOOLS",
    # Domain knowledge base
    "BaseRAGRetriever",
    "RAGChunk",
    "RAGSearchResult",
    "ChunkType",
    "generate_chunk_id",
    "query_domain_rag",
    "get_entity_guidance",
    "get_relationship_guidance",
    "get_datatype_mapping",
    "get_cardinality_rules",
    "get_normalization_rules",
    "detect_requirement_domain",
    "KNOWLEDGE_TOOLS",
    "get_domain_retriever",
    "get_retriever_for_text",
    # Combined
    "RAG_TOOLS",
]
