"""
Few-Shot Example Retriever

This module powers the RAG system as a *dynamic few-shot retriever*. Given an input
requirement (natural-language text), it finds the most similar past requirements from a
hand-curated example store and returns their `requirement -> relational schema` pairs so the
design agents can use them as few-shot guidance.

It is intentionally simple and dependency-light:
- Embeddings come from `sentence-transformers` when available.
- If `sentence-transformers` is not installed, it falls back to a word-frequency embedding so
  the system still works (with lower retrieval quality).
- Similarity is plain cosine similarity over the requirement embeddings.

Examples live as JSON files in `rag/examples/<domain>.json`. See `rag/README.md`.
"""

import glob
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .rag_config import RAGConfig


@dataclass
class FewShotExample:
    """A single worked example: a requirement and its target relational schema."""
    id: str
    domain: str
    requirement: str
    output: Dict[str, Any]  # {Table: {"Attributes": [...], "Primary key": [...], "Foreign key": {...}}}
    embedding: Optional[np.ndarray] = field(default=None, repr=False)


@dataclass
class FewShotResult:
    """An example plus its similarity score against the query."""
    example: FewShotExample
    similarity_score: float
    rank: int


class FewShotRetriever:
    """
    Loads the curated example store and retrieves the most similar examples for a query.

    Usage:
        retriever = FewShotRetriever()
        retriever.initialize()
        results = retriever.search("A hospital tracks patients and their visits", top_k=3)
        text = retriever.format_as_fewshot(results)
    """

    def __init__(self, config: Optional[RAGConfig] = None, examples_dir: Optional[str] = None):
        self.config = config or RAGConfig()
        # Default to the examples/ directory next to this file.
        self.examples_dir = examples_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "examples"
        )
        self.examples: List[FewShotExample] = []
        self.embeddings: Optional[np.ndarray] = None
        self._embedding_model = None
        self._initialized = False

    # ------------------------------------------------------------------ loading

    def load_examples(self) -> List[FewShotExample]:
        """Read every rag/examples/*.json file into FewShotExample objects."""
        examples: List[FewShotExample] = []

        if not os.path.isdir(self.examples_dir):
            print(f"Warning: examples directory not found: {self.examples_dir}")
            return examples

        for path in sorted(glob.glob(os.path.join(self.examples_dir, "*.json"))):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception as e:
                print(f"Warning: could not load examples file {path}: {e}")
                continue

            domain_fallback = os.path.splitext(os.path.basename(path))[0]
            for i, rec in enumerate(records):
                requirement = rec.get("requirement", "").strip()
                output = rec.get("output", {})
                if not requirement or not output:
                    continue
                examples.append(
                    FewShotExample(
                        id=rec.get("id") or f"{domain_fallback}_{i}",
                        domain=rec.get("domain", domain_fallback),
                        requirement=requirement,
                        output=output,
                    )
                )

        return examples

    # ------------------------------------------------------------- initialization

    def initialize(self, force_reload: bool = False) -> bool:
        """Load examples and compute their embeddings."""
        if self._initialized and not force_reload:
            return True

        try:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer(self.config.embedding_model)
        except ImportError:
            print("Warning: sentence-transformers not installed. Using fallback embeddings.")
            self._embedding_model = None

        self.examples = self.load_examples()
        if not self.examples:
            print(f"Warning: no few-shot examples loaded from {self.examples_dir}")
            return False

        self._generate_embeddings()
        self._initialized = True
        return True

    def _generate_embeddings(self):
        """Embed every example's requirement text."""
        if self._embedding_model is None:
            self.embeddings = self._generate_fallback_embeddings()
        else:
            requirements = [ex.requirement for ex in self.examples]
            self.embeddings = self._embedding_model.encode(
                requirements, convert_to_numpy=True, show_progress_bar=False
            )

        for i, ex in enumerate(self.examples):
            ex.embedding = self.embeddings[i]

    def _build_vocab(self) -> Dict[str, int]:
        vocab: Dict[str, int] = {}
        for ex in self.examples:
            for word in ex.requirement.lower().split():
                if word not in vocab:
                    vocab[word] = len(vocab)
        return vocab

    def _generate_fallback_embeddings(self) -> np.ndarray:
        """Simple normalized word-frequency embeddings (used when ST is unavailable)."""
        self._vocab = self._build_vocab()
        dim = min(len(self._vocab), self.config.embedding_dim) or 1
        embeddings = np.zeros((len(self.examples), dim))

        for i, ex in enumerate(self.examples):
            for word in ex.requirement.lower().split():
                idx = self._vocab.get(word)
                if idx is not None and idx < dim:
                    embeddings[i, idx] += 1
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] /= norm

        return embeddings

    def _compute_query_embedding(self, query: str) -> np.ndarray:
        """Embed a query the same way the corpus was embedded."""
        if self._embedding_model is not None:
            return self._embedding_model.encode(query, convert_to_numpy=True)

        # Fallback: reuse the vocabulary built for the corpus.
        dim = self.embeddings.shape[1]
        embedding = np.zeros(dim)
        vocab = getattr(self, "_vocab", {})
        for word in query.lower().split():
            idx = vocab.get(word)
            if idx is not None and idx < dim:
                embedding[idx] += 1
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding /= norm
        return embedding

    # ----------------------------------------------------------------- searching

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        domain: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[FewShotResult]:
        """
        Return the most similar examples to `query`, ranked by cosine similarity.

        Args:
            query: The requirement / NLP text to match against.
            top_k: How many examples to return (defaults to config.top_k).
            domain: Optional domain filter (e.g. "healthcare"). None = search all domains.
            min_similarity: Drop results below this cosine score.
        """
        if not self._initialized:
            self.initialize()
        if not self.examples:
            return []

        top_k = top_k or self.config.top_k
        query_embedding = self._compute_query_embedding(query)
        similarities = np.dot(self.embeddings, query_embedding)

        scored = []
        for ex, sim in zip(self.examples, similarities):
            if domain and ex.domain != domain:
                continue
            if sim < min_similarity:
                continue
            scored.append((ex, float(sim)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            FewShotResult(example=ex, similarity_score=score, rank=i + 1)
            for i, (ex, score) in enumerate(scored[:top_k])
        ]

    # ----------------------------------------------------------------- formatting

    @staticmethod
    def format_as_fewshot(results: List[FewShotResult]) -> str:
        """Render search results as a few-shot markdown block for an LLM prompt."""
        if not results:
            return "No similar examples were found for this requirement."

        parts = [
            "### Similar worked examples (requirement → relational schema)\n"
            "Use these as references for table / primary-key / foreign-key structure. "
            "Adapt them to the current requirement — do not copy verbatim.\n"
        ]
        for r in results:
            ex = r.example
            schema_json = json.dumps(ex.output, indent=2, ensure_ascii=False)
            parts.append(
                f"\n#### Example {r.rank} — domain: {ex.domain} (relevance: {r.similarity_score:.2f})\n"
                f"Requirement:\n{ex.requirement}\n\n"
                f"Relational schema:\n```json\n{schema_json}\n```\n---"
            )
        return "\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Counts of loaded examples by domain (for diagnostics)."""
        if not self.examples:
            return {"total_examples": 0}
        by_domain: Dict[str, int] = {}
        for ex in self.examples:
            by_domain[ex.domain] = by_domain.get(ex.domain, 0) + 1
        return {"total_examples": len(self.examples), "by_domain": by_domain}


# Module-level singleton (lazy) -------------------------------------------------

_retriever_singleton: Optional[FewShotRetriever] = None


def get_retriever() -> FewShotRetriever:
    """Get the shared, lazily-initialized retriever instance."""
    global _retriever_singleton
    if _retriever_singleton is None:
        _retriever_singleton = FewShotRetriever()
        _retriever_singleton.initialize()
    return _retriever_singleton
