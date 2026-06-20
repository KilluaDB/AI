"""
RAG Configuration

Configuration and lightweight domain detection for the few-shot RAG system.
Domain detection is optional — the retriever searches all examples by default and only uses
the detected domain when a caller explicitly asks to filter by it.
"""

import os
from dataclasses import dataclass
from enum import Enum


class Domain(Enum):
    """Domains that have a curated example set (plus GENERAL fallback)."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    EDUCATION = "education"
    GENERAL = "general"


@dataclass
class RAGConfig:
    """Configuration for the few-shot retriever."""
    # Embedding settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Retrieval settings
    top_k: int = 3

    # Where the curated example files live (defaults to rag/examples next to this module)
    examples_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")


def detect_domain_from_text(text: str) -> Domain:
    """
    Best-effort domain detection from requirement text via keyword matching.

    This is optional metadata — the retriever ranks by semantic similarity across all domains.
    """
    text_lower = text.lower()

    healthcare_keywords = [
        "patient", "hospital", "clinic", "doctor", "physician", "nurse",
        "diagnosis", "treatment", "medication", "prescription", "medical",
        "healthcare", "health care", "health-care", "ehr", "emr",
        "encounter", "observation", "condition", "procedure", "allergy",
        "immunization", "vital signs", "lab result", "radiology",
        "icd-10", "icd10", "snomed", "loinc", "rxnorm", "cpt",
        "hipaa", "phi", "protected health", "clinical",
    ]

    finance_keywords = [
        "bank", "account", "transaction", "payment", "loan", "credit",
        "debit", "interest", "balance", "ledger", "financial", "finance",
        "investment", "stock", "bond", "portfolio", "trading", "forex",
        "currency", "exchange", "money", "fund", "deposit", "withdraw",
        "mortgage", "insurance", "premium", "claim", "policy",
    ]

    ecommerce_keywords = [
        "product", "cart", "order", "checkout", "shipping", "inventory",
        "catalog", "customer", "vendor", "supplier", "warehouse",
        "e-commerce", "ecommerce", "online store", "marketplace",
        "sku", "price", "discount", "promotion", "coupon",
    ]

    education_keywords = [
        "student", "teacher", "course", "class", "grade", "school",
        "university", "college", "enrollment", "semester", "curriculum",
        "assignment", "exam", "lecture", "degree", "diploma", "transcript",
    ]

    counts = {
        Domain.HEALTHCARE: sum(1 for kw in healthcare_keywords if kw in text_lower),
        Domain.FINANCE: sum(1 for kw in finance_keywords if kw in text_lower),
        Domain.ECOMMERCE: sum(1 for kw in ecommerce_keywords if kw in text_lower),
        Domain.EDUCATION: sum(1 for kw in education_keywords if kw in text_lower),
    }

    max_count = max(counts.values())
    if max_count == 0:
        return Domain.GENERAL

    # Return the highest-scoring domain (insertion order breaks ties deterministically).
    for domain, count in counts.items():
        if count == max_count:
            return domain

    return Domain.GENERAL
