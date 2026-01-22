"""
Base RAG (Retrieval-Augmented Generation) Module

This module provides a domain-agnostic RAG retriever that can be extended
for different domains like healthcare, finance, e-commerce, etc.
"""

import hashlib
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


class ChunkType(Enum):
    """Types of knowledge chunks"""
    DEFINITION = "definition"
    EXAMPLE = "example"
    MAPPING = "mapping"
    RULE = "rule"
    PATTERN = "pattern"
    GUIDELINE = "guideline"
    CONSTRAINT = "constraint"
    VALUESET = "valueset"
    PROFILE = "profile"


@dataclass
class RAGChunk:
    """A chunk of knowledge for RAG retrieval"""
    id: str
    content: str
    domain: str  # e.g., "healthcare", "finance", "general"
    resource_type: str  # e.g., "Patient", "Account", "Entity"
    chunk_type: ChunkType
    version: str = "1.0"
    canonical_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    trust_level: float = 1.0  # 0.0 to 1.0
    license: str = "internal"
    phi_flag: bool = False  # Protected Health Information flag
    pii_flag: bool = False  # Personally Identifiable Information flag
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "content": self.content,
            "domain": self.domain,
            "resource_type": self.resource_type,
            "chunk_type": self.chunk_type.value,
            "version": self.version,
            "canonical_url": self.canonical_url,
            "tags": self.tags,
            "trust_level": self.trust_level,
            "license": self.license,
            "phi_flag": self.phi_flag,
            "pii_flag": self.pii_flag,
            "metadata": self.metadata,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RAGChunk":
        """Create from dictionary"""
        data = data.copy()
        data["chunk_type"] = ChunkType(data["chunk_type"])
        data.pop("embedding", None)
        return cls(**data)


@dataclass
class RAGSearchResult:
    """Result from RAG search"""
    chunk: RAGChunk
    similarity_score: float
    rank: int


@dataclass
class RAGConfig:
    """Configuration for RAG retriever"""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    top_k: int = 5
    similarity_threshold: float = 0.3
    cache_dir: str = "./rag/cache"
    use_cache: bool = True


class BaseRAGRetriever(ABC):
    """
    Abstract base class for domain-specific RAG retrievers.
    
    Subclasses should implement:
    - _load_domain_knowledge(): Load domain-specific knowledge chunks
    - get_domain(): Return the domain name
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.chunks: List[RAGChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self._embedding_model = None
        self._initialized = False
        
        # Create cache directory
        os.makedirs(self.config.cache_dir, exist_ok=True)
    
    @abstractmethod
    def get_domain(self) -> str:
        """Return the domain name (e.g., 'healthcare', 'finance')"""
        pass
    
    @abstractmethod
    def _load_domain_knowledge(self) -> List[RAGChunk]:
        """Load domain-specific knowledge chunks"""
        pass
    
    def initialize(self, force_reload: bool = False) -> bool:
        """Initialize the RAG retriever"""
        if self._initialized and not force_reload:
            return True
        
        try:
            # Try to load sentence-transformers
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer(self.config.embedding_model)
        except ImportError:
            print("Warning: sentence-transformers not installed. Using fallback mode.")
            self._embedding_model = None
        
        # Load domain knowledge
        self.chunks = self._load_domain_knowledge()
        
        if not self.chunks:
            print(f"Warning: No knowledge chunks loaded for domain '{self.get_domain()}'")
            return False
        
        # Generate embeddings
        self._generate_embeddings()
        self._initialized = True
        
        return True
    
    def _generate_embeddings(self):
        """Generate embeddings for all chunks"""
        if self._embedding_model is None:
            # Fallback: simple TF-IDF-like embeddings
            self.embeddings = self._generate_fallback_embeddings()
            return
        
        contents = [chunk.content for chunk in self.chunks]
        self.embeddings = self._embedding_model.encode(
            contents,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        # Store embeddings in chunks
        for i, chunk in enumerate(self.chunks):
            chunk.embedding = self.embeddings[i]
    
    def _generate_fallback_embeddings(self) -> np.ndarray:
        """Generate simple fallback embeddings using word frequency"""
        # Build vocabulary
        vocab = {}
        for chunk in self.chunks:
            words = chunk.content.lower().split()
            for word in words:
                if word not in vocab:
                    vocab[word] = len(vocab)
        
        # Create embeddings
        dim = min(len(vocab), self.config.embedding_dim)
        embeddings = np.zeros((len(self.chunks), dim))
        
        for i, chunk in enumerate(self.chunks):
            words = chunk.content.lower().split()
            for word in words:
                if word in vocab and vocab[word] < dim:
                    embeddings[i, vocab[word]] += 1
            # Normalize
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] /= norm
        
        return embeddings
    
    def _compute_query_embedding(self, query: str) -> np.ndarray:
        """Compute embedding for a query"""
        if self._embedding_model is not None:
            return self._embedding_model.encode(query, convert_to_numpy=True)
        
        # Fallback
        embedding = np.zeros(self.embeddings.shape[1])
        words = query.lower().split()
        vocab = {chunk.content.lower().split()[j]: j 
                 for chunk in self.chunks 
                 for j in range(min(len(chunk.content.lower().split()), embedding.shape[0]))}
        
        for word in words:
            if word in vocab and vocab[word] < embedding.shape[0]:
                embedding[vocab[word]] += 1
        
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding /= norm
        
        return embedding
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        resource_types: Optional[List[str]] = None,
        chunk_types: Optional[List[ChunkType]] = None,
        min_trust_level: float = 0.0,
        tags: Optional[List[str]] = None
    ) -> List[RAGSearchResult]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            resource_types: Filter by resource types
            chunk_types: Filter by chunk types
            min_trust_level: Minimum trust level
            tags: Filter by tags (any match)
        
        Returns:
            List of search results with similarity scores
        """
        if not self._initialized:
            self.initialize()
        
        if not self.chunks:
            return []
        
        top_k = top_k or self.config.top_k
        
        # Compute query embedding
        query_embedding = self._compute_query_embedding(query)
        
        # Compute similarities
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Filter and rank
        results = []
        for i, (chunk, sim) in enumerate(zip(self.chunks, similarities)):
            # Apply filters
            if sim < self.config.similarity_threshold:
                continue
            if resource_types and chunk.resource_type not in resource_types:
                continue
            if chunk_types and chunk.chunk_type not in chunk_types:
                continue
            if chunk.trust_level < min_trust_level:
                continue
            if tags and not any(tag in chunk.tags for tag in tags):
                continue
            
            results.append((chunk, float(sim)))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return [
            RAGSearchResult(chunk=chunk, similarity_score=score, rank=i+1)
            for i, (chunk, score) in enumerate(results[:top_k])
        ]
    
    def get_context_for_prompt(
        self,
        query: str,
        max_chunks: int = 5,
        max_tokens: int = 2000
    ) -> str:
        """
        Get formatted context for inclusion in LLM prompt.
        
        Args:
            query: The query or requirement text
            max_chunks: Maximum number of chunks to include
            max_tokens: Approximate maximum tokens (characters / 4)
        
        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=max_chunks)
        
        if not results:
            return ""
        
        context_parts = [f"### {self.get_domain().upper()} Knowledge Context\n"]
        total_chars = 0
        max_chars = max_tokens * 4
        
        for result in results:
            chunk = result.chunk
            chunk_text = f"\n**[{chunk.resource_type} - {chunk.chunk_type.value}]** (relevance: {result.similarity_score:.2f})\n{chunk.content}\n"
            
            if total_chars + len(chunk_text) > max_chars:
                break
            
            context_parts.append(chunk_text)
            total_chars += len(chunk_text)
        
        return "".join(context_parts)
    
    def add_chunk(self, chunk: RAGChunk):
        """Add a new chunk to the retriever"""
        self.chunks.append(chunk)
        
        # Regenerate embeddings for the new chunk
        if self._embedding_model is not None:
            new_embedding = self._embedding_model.encode(
                chunk.content, convert_to_numpy=True
            )
            chunk.embedding = new_embedding
            
            if self.embeddings is not None:
                self.embeddings = np.vstack([self.embeddings, new_embedding])
            else:
                self.embeddings = new_embedding.reshape(1, -1)
    
    def save_cache(self, filepath: Optional[str] = None):
        """Save chunks to cache file"""
        filepath = filepath or os.path.join(
            self.config.cache_dir, 
            f"{self.get_domain()}_cache.json"
        )
        
        data = {
            "domain": self.get_domain(),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "config": {
                "embedding_model": self.config.embedding_model,
                "embedding_dim": self.config.embedding_dim
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_cache(self, filepath: Optional[str] = None) -> bool:
        """Load chunks from cache file"""
        filepath = filepath or os.path.join(
            self.config.cache_dir, 
            f"{self.get_domain()}_cache.json"
        )
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.chunks = [RAGChunk.from_dict(c) for c in data["chunks"]]
            return True
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded knowledge"""
        if not self.chunks:
            return {"total_chunks": 0}
        
        stats = {
            "total_chunks": len(self.chunks),
            "domain": self.get_domain(),
            "by_resource_type": {},
            "by_chunk_type": {},
            "avg_trust_level": sum(c.trust_level for c in self.chunks) / len(self.chunks)
        }
        
        for chunk in self.chunks:
            rt = chunk.resource_type
            ct = chunk.chunk_type.value
            stats["by_resource_type"][rt] = stats["by_resource_type"].get(rt, 0) + 1
            stats["by_chunk_type"][ct] = stats["by_chunk_type"].get(ct, 0) + 1
        
        return stats


def generate_chunk_id(content: str, resource_type: str, domain: str) -> str:
    """Generate a unique ID for a chunk"""
    hash_input = f"{domain}:{resource_type}:{content[:100]}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:12]
