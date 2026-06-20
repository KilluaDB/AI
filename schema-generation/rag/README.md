# RAG in the Schema-Generation System — How It Works Now

This is the report on how the RAG (Retrieval-Augmented Generation) component works in our system.
RAG now provides **two complementary capabilities**, both exposed as agent tools:

1. **Dynamic few-shot retrieval** — find the most similar past requirements and show their worked
   relational schemas as few-shot examples.
2. **Domain knowledge rules** — explicit per-domain "ground-truth" design rules (which attributes
   *must* be present, which are *recommended*, relationship/cardinality patterns, datatype mappings,
   normalization guidelines).

`RAG_TOOLS` exposes the full set (1 few-shot tool + 7 knowledge tools = 8 tools). `FEWSHOT_TOOLS`
and `KNOWLEDGE_TOOLS` expose each group separately for per-agent wiring.

---

## 1. Capability A — dynamic few-shot retrieval

> For each input requirement, RAG embeds the requirement text, finds the **2–3 most similar past
> requirements** from a curated example store, and returns their **`requirement → relational schema`**
> pairs. The design agents use those pairs as **few-shot examples** while producing the schema.

```
input requirement
      │   (an agent calls the tool)
      ▼
get_similar_examples(requirement, top_k=3)
      │   1. embed the requirement (sentence-transformers, MiniLM)
      │   2. cosine-similarity vs. every stored example requirement
      │   3. take the top-k
      ▼
top-3 { requirement → {Table: {Attributes, Primary key, Foreign key}} } pairs
      │   formatted as a few-shot markdown block
      ▼
returned into the calling agent's context
```

Code: [`fewshot_retriever.py`](fewshot_retriever.py) + [`rag_tools.py`](rag_tools.py). Data:
[`examples/`](examples/).

---

## 2. Capability B — domain knowledge rules

The knowledge base stores curated, per-domain design rules as searchable chunks and serves them
through seven tools. Example — the Patient entity definition surfaces *required* vs. *recommended*
attributes:

```
HEALTHCARE ENTITY: Patient
REQUIRED ATTRIBUTES:
  - patient_id: SERIAL PRIMARY KEY
  - medical_record_number (MRN): VARCHAR(50) UNIQUE NOT NULL
  - first_name / last_name: VARCHAR(100) NOT NULL
  - date_of_birth: DATE NOT NULL
RECOMMENDED ATTRIBUTES:
  - middle_name, gender, ssn, marital_status, ...
```

| Tool | Returns |
|------|---------|
| `detect_requirement_domain` | Which domain (and whether knowledge is available). |
| `get_entity_guidance` | Standard entity structure — required vs. recommended attributes. |
| `get_relationship_guidance` | Relationship patterns and cardinalities between entities. |
| `get_datatype_mapping` | Domain attribute → PostgreSQL type + constraints. |
| `get_cardinality_rules` | Cardinality (0..1, 1..1, 0..*, 1..*) → SQL constraints. |
| `get_normalization_rules` | Domain-specific 1NF/2NF/3NF guidance. |
| `query_domain_rag` | General semantic search over the domain knowledge. |

**Domains with a knowledge base:** Healthcare (15 chunks) and E-Commerce (25 chunks). Finance and
Education currently have **few-shot examples** but **no knowledge base** (they were placeholders in
the original system). Code: [`knowledge_tools.py`](knowledge_tools.py) + [`base_rag.py`](base_rag.py)
+ [`domains/`](domains/).

---

## 3. When RAG is used — as tools

All RAG capabilities are **on-demand agent tools**: an agent decides to call them (the system prompts
tell it to). Per-agent wiring in [`design/agent_chat_physical.py`](../design/agent_chat_physical.py)
(`_build_rag_tool_groups`):

| Agent | Few-shot (`get_similar_examples`) | Domain knowledge tools |
|-------|:---:|---|
| **ConceptualDesignerAgent** | ✅ | detect_requirement_domain, get_entity_guidance, get_relationship_guidance, query_domain_rag |
| **LogicalDesignerAgent** | ✅ | get_cardinality_rules, get_normalization_rules, query_domain_rag |
| **ConceptualReviewerAgent** | ✅ | detect_requirement_domain, get_entity_guidance, get_relationship_guidance, query_domain_rag |
| **PhysicalDesignerAgent** | ❌ | get_datatype_mapping, query_domain_rag |
| QA / Execution / Manager / Report | ❌ | — |

The prompts that instruct agents to call these tools live in
[`design/user_prompt_english.py`](../design/user_prompt_english.py) under the
**"RAG: Similar Examples + Domain Knowledge"** sections.

The tool import (`from rag import ...`) is wrapped in a `try/except`, so if the `rag` package or its
dependencies are missing, the pipeline still runs — just without RAG tools.

---

## 4. The data — the few-shot example store

Examples are plain JSON files, one per domain, in [`examples/`](examples/):

```
examples/
  healthcare.json   (12 examples)
  ecommerce.json    (12 examples)
  finance.json      (12 examples)
  education.json    (12 examples)
  general.json      (10 examples — domain-agnostic fallback)
```

Each file is a list of records with this shape (the `output` matches the format used by
`datasets/RSchema/annotation.jsonl` and what the pipeline itself produces):

```json
{
  "id": "hc_01",
  "domain": "healthcare",
  "requirement": "A hospital needs to manage patients and their visits. Each patient has a Medical Record Number, Name, ...",
  "output": {
    "Patient": {
      "Attributes": ["Medical Record Number", "Name", "Date of Birth", "Gender", "Phone Number"],
      "Primary key": ["Medical Record Number"],
      "Foreign key": {}
    },
    "Visit": {
      "Attributes": ["Visit Number", "Admission Date", "Discharge Date", "Department", "Medical Record Number"],
      "Primary key": ["Visit Number"],
      "Foreign key": { "Medical Record Number": { "Patient": "Medical Record Number" } }
    }
  }
}
```

Conventions (mirroring the dataset): words in attribute names are separated (`Airplane Number`);
many-to-many relationships become a junction table with a composite primary key; a foreign key is
written as `{"<column>": {"<ReferencedTable>": "<referenced column>"}}`.

---

## 5. How few-shot retrieval works

Implemented in [`fewshot_retriever.py`](fewshot_retriever.py):

1. **Load** — on first use, every `examples/*.json` file is read into `FewShotExample` objects
   (pooled across all domains).
2. **Embed** — each example's `requirement` text is embedded with
   `sentence-transformers/all-MiniLM-L6-v2`. If `sentence-transformers` is not installed, the
   retriever falls back to a normalized word-frequency embedding so it still functions (lower
   quality). Embedding happens once and is reused for the process lifetime (lazy singleton via
   `get_retriever()`).
3. **Search** — the query requirement is embedded the same way; cosine similarity is computed against
   all stored requirement embeddings; the top-`k` (default 3) are returned, ranked.
   - Retrieval is **global by default** — it searches all domains and returns the most similar
     examples regardless of domain (similar requirements naturally cluster into the same domain).
   - An optional `domain=` filter exists for callers that want to restrict to one domain.
   - `detect_domain_from_text()` (in [`rag_config.py`](rag_config.py)) is kept for diagnostics/optional
     filtering; it is **not** the primary retrieval path.
4. **Format** — `format_as_fewshot()` renders the hits as a markdown block (requirement + pretty
   relational schema, with a relevance score) suitable for an LLM prompt.

---

## 6. Configuration

`RAGConfig` in [`rag_config.py`](rag_config.py):

| Setting | Default | Meaning |
|---------|---------|---------|
| `embedding_model` | `sentence-transformers/all-MiniLM-L6-v2` | Sentence embedding model. |
| `embedding_dim` | `384` | Embedding dimension (also caps the fallback embedding). |
| `top_k` | `3` | Default number of examples returned. |
| `examples_dir` | `rag/examples` | Where the example JSON files live. |

---

## 7. How to extend

- **Add few-shot examples (any domain):** append records to `examples/<domain>.json` with a natural
  `requirement` and an `output` in the `{Table: {Attributes, Primary key, Foreign key}}` shape. No code
  changes — picked up on next load.
- **Add domain-knowledge rules:** add chunks in the domain retriever under `domains/<domain>/` (entity
  definitions with required/recommended attributes, relationship patterns, datatype maps, etc.). To add
  a brand-new knowledge domain, create `domains/<domain>/` with a retriever subclassing
  `BaseRAGRetriever` and register it in `domains/__init__.py` and `knowledge_tools.py::_get_retriever`.
- **Tune retrieval:** change `top_k` / `embedding_model` in `RAGConfig`.

---

## 8. Module layout

```
rag/
  rag_tools.py          # get_similar_examples (few-shot tool); FEWSHOT_TOOLS
  fewshot_retriever.py  # FewShotRetriever (embed + cosine + fallback)
  examples/*.json       # few-shot example store (healthcare, ecommerce, finance, education, general)
  knowledge_tools.py    # 7 domain-knowledge tools; KNOWLEDGE_TOOLS
  base_rag.py           # BaseRAGRetriever, RAGChunk, ChunkType (knowledge-base engine)
  domains/              # healthcare/ and ecommerce/ knowledge retrievers + configs
  rag_config.py         # Domain enum, detect_domain_from_text, RAGConfig
  __init__.py           # RAG_TOOLS = FEWSHOT_TOOLS + KNOWLEDGE_TOOLS
```

> Both retrieval paths rank by semantic similarity and therefore need `sentence-transformers`
> installed (in `requirements.txt`) for good results. Without it they fall back to a weak
> word-frequency embedding so the system still runs.
