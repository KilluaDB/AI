"""
General RAG Configuration

Domain-agnostic configuration for the RAG system.
Domain-specific configurations should extend these base classes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Domain(Enum):
    """Supported domains"""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    EDUCATION = "education"
    GENERAL = "general"


@dataclass
class RAGConfig:
    """Base RAG configuration"""
    # Embedding settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    
    # Search settings
    top_k: int = 5
    similarity_threshold: float = 0.3
    
    # Cache settings
    cache_dir: str = "./rag/cache"
    use_cache: bool = True
    
    # Domain
    domain: Domain = Domain.GENERAL


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    normalize: bool = True
    batch_size: int = 32


@dataclass
class VectorStoreConfig:
    """Configuration for vector store"""
    store_type: str = "memory"  # "memory", "faiss", "chroma", "qdrant"
    persist_directory: Optional[str] = None
    collection_name: str = "rag_chunks"


# Common PostgreSQL data type mappings used across domains
COMMON_POSTGRES_TYPE_MAP: Dict[str, str] = {
    # String types
    "string": "VARCHAR(255)",
    "text": "TEXT",
    "char": "CHAR(1)",
    
    # Numeric types
    "integer": "INTEGER",
    "int": "INTEGER",
    "bigint": "BIGINT",
    "smallint": "SMALLINT",
    "decimal": "DECIMAL(18,2)",
    "float": "DOUBLE PRECISION",
    "double": "DOUBLE PRECISION",
    "number": "NUMERIC",
    
    # Boolean
    "boolean": "BOOLEAN",
    "bool": "BOOLEAN",
    
    # Date/Time
    "date": "DATE",
    "time": "TIME",
    "datetime": "TIMESTAMP",
    "timestamp": "TIMESTAMP WITH TIME ZONE",
    
    # Binary
    "binary": "BYTEA",
    "blob": "BYTEA",
    
    # JSON
    "json": "JSONB",
    "object": "JSONB",
    "array": "JSONB",
    
    # UUID
    "uuid": "UUID",
    "guid": "UUID",
    
    # Special
    "url": "VARCHAR(2048)",
    "uri": "VARCHAR(2048)",
    "email": "VARCHAR(255)",
    "phone": "VARCHAR(20)",
}


# Common cardinality mappings
CARDINALITY_MAP: Dict[str, Dict[str, Any]] = {
    "0..1": {
        "nullable": True,
        "constraint": None,
        "description": "Optional, at most one"
    },
    "1..1": {
        "nullable": False,
        "constraint": "NOT NULL",
        "description": "Required, exactly one"
    },
    "0..*": {
        "nullable": True,
        "constraint": None,
        "description": "Optional, any number",
        "requires_junction_table": True
    },
    "1..*": {
        "nullable": False,
        "constraint": "NOT NULL",
        "description": "Required, one or more",
        "requires_junction_table": True
    },
}


def detect_domain_from_text(text: str) -> Domain:
    """
    Detect the domain from requirement text.
    
    Args:
        text: The requirement text to analyze
    
    Returns:
        Detected domain
    """
    text_lower = text.lower()
    
    # Healthcare keywords
    healthcare_keywords = [
        "patient", "hospital", "clinic", "doctor", "physician", "nurse",
        "diagnosis", "treatment", "medication", "prescription", "medical",
        "healthcare", "health care", "health-care", "ehr", "emr",
        "encounter", "observation", "condition", "procedure", "allergy",
        "immunization", "vital signs", "lab result", "radiology",
        "icd-10", "icd10", "snomed", "loinc", "rxnorm", "cpt",
        "hipaa", "phi", "protected health", "clinical"
    ]
    
    # Finance keywords
    finance_keywords = [
        "bank", "account", "transaction", "payment", "loan", "credit",
        "debit", "interest", "balance", "ledger", "financial", "finance",
        "investment", "stock", "bond", "portfolio", "trading", "forex",
        "currency", "exchange", "money", "fund", "deposit", "withdraw",
        "mortgage", "insurance", "premium", "claim", "policy"
    ]
    
    # E-commerce keywords
    ecommerce_keywords = [
        "product", "cart", "order", "checkout", "shipping", "inventory",
        "catalog", "customer", "vendor", "supplier", "warehouse",
        "e-commerce", "ecommerce", "online store", "marketplace",
        "sku", "price", "discount", "promotion", "coupon"
    ]
    
    # Education keywords
    education_keywords = [
        "student", "teacher", "course", "class", "grade", "school",
        "university", "college", "enrollment", "semester", "curriculum",
        "assignment", "exam", "lecture", "degree", "diploma", "transcript"
    ]
    
    # Count matches
    healthcare_count = sum(1 for kw in healthcare_keywords if kw in text_lower)
    finance_count = sum(1 for kw in finance_keywords if kw in text_lower)
    ecommerce_count = sum(1 for kw in ecommerce_keywords if kw in text_lower)
    education_count = sum(1 for kw in education_keywords if kw in text_lower)
    
    # Determine domain
    max_count = max(healthcare_count, finance_count, ecommerce_count, education_count)
    
    if max_count == 0:
        return Domain.GENERAL
    
    if healthcare_count == max_count:
        return Domain.HEALTHCARE
    elif finance_count == max_count:
        return Domain.FINANCE
    elif ecommerce_count == max_count:
        return Domain.ECOMMERCE
    elif education_count == max_count:
        return Domain.EDUCATION
    
    return Domain.GENERAL
