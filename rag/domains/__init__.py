"""
Domain-specific RAG retrievers package.
"""

from typing import Optional
from ..base_rag import BaseRAGRetriever, RAGConfig
from ..rag_config import Domain, detect_domain_from_text


def get_domain_retriever(domain: Domain, config: Optional[RAGConfig] = None) -> Optional[BaseRAGRetriever]:
    """
    Get the appropriate domain-specific RAG retriever.
    
    Args:
        domain: The domain to get retriever for
        config: Optional RAG configuration
    
    Returns:
        Domain-specific retriever or None if not available
    """
    if domain == Domain.HEALTHCARE:
        from .healthcare import HealthcareRAGRetriever
        return HealthcareRAGRetriever(config)
    
    elif domain == Domain.ECOMMERCE:
        from .ecommerce import EcommerceRAGRetriever
        return EcommerceRAGRetriever(config)
    
    # Add more domains here as they are implemented
    # elif domain == Domain.FINANCE:
    #     from .finance import FinanceRAGRetriever
    #     return FinanceRAGRetriever(config)
    
    return None


def get_retriever_for_text(text: str, config: Optional[RAGConfig] = None) -> Optional[BaseRAGRetriever]:
    """
    Get the appropriate RAG retriever based on text content.
    
    Args:
        text: The requirement text to analyze
        config: Optional RAG configuration
    
    Returns:
        Domain-specific retriever or None if no domain detected
    """
    domain = detect_domain_from_text(text)
    
    if domain == Domain.GENERAL:
        return None
    
    return get_domain_retriever(domain, config)


__all__ = [
    "get_domain_retriever",
    "get_retriever_for_text",
    "Domain",
]
