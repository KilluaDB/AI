# RAG Module for Domain-Aware Database Design

This module provides a **domain-aware** Retrieval-Augmented Generation (RAG) system 
designed to help generate high-quality relational database schemas for various domains.
The system uses **ground truth** domain knowledge to guide schema design decisions.

## Supported Domains

| Domain | Status | Knowledge Type |
|--------|--------|----------------|
| Healthcare | ✅ Available | Entity definitions, relationship patterns, constraints |
| E-Commerce | ✅ Available | Product catalog, orders, inventory, payments |
| Finance | 🔜 Coming Soon | Financial data patterns |
| Education | 🔜 Coming Soon | Educational data models |

## Features

- **Automatic Domain Detection**: Analyzes requirement text to detect the domain
- **Ground Truth Knowledge**: Pre-built knowledge for database schema design
- **Semantic Search**: Uses sentence-transformers for similarity-based retrieval
- **Rich Metadata**: Each chunk includes domain, entity_type, chunk_type, tags
- **Agent Integration**: Provides tool functions for AutoGen multi-agent systems
- **Extensible Architecture**: Easy to add new domains

## Project Structure

```
rag/
├── __init__.py          # Module exports
├── base_rag.py          # Base RAG retriever class
├── rag_config.py        # General configuration & domain detection
├── rag_tools.py         # Agent tool functions
├── README.md
├── cache/               # Cached embeddings
└── domains/
    ├── __init__.py      # Domain retriever factory
    ├── healthcare/      # Healthcare domain
    │   ├── __init__.py
    │   ├── healthcare_config.py      # Healthcare-specific config
    │   └── healthcare_retriever.py   # Healthcare RAG retriever
    └── ecommerce/       # E-Commerce domain
        ├── __init__.py
        ├── ecommerce_config.py       # E-Commerce-specific config
        └── ecommerce_retriever.py    # E-Commerce RAG retriever
```

## Healthcare Domain Knowledge (Ground Truth)

The healthcare domain provides comprehensive knowledge for designing healthcare database schemas:

### Entity Definitions
Complete schema guidance for common healthcare entities:
- **Patient**: Demographics, identifiers, contact info, preferences
- **Provider**: Practitioner/physician information, credentials, specialties
- **Encounter**: Patient visits, admissions, appointments
- **Diagnosis**: Medical conditions, ICD codes, clinical findings
- **Medication**: Prescriptions, drug information, dosages
- **Observation**: Lab results, vital signs, measurements
- **Appointment**: Scheduling, booking, availability
- **Insurance**: Coverage, policies, claims
- **Organization**: Healthcare facilities, departments, locations

### Relationship Patterns
SQL examples for common healthcare relationships:
- Patient → Encounter (1:N)
- Encounter ↔ Diagnosis (M:N via junction table)
- Provider → Encounter (1:N)
- Medication → Encounter (N:1)
- Observation → Encounter (N:1)
- Patient → Insurance (1:N)
- Appointment → Patient + Provider (N:1 each)

### Cardinality Rules
PostgreSQL implementations for each cardinality type:
- **0..1**: Optional single value (nullable foreign key)
- **1..1**: Required single value (NOT NULL foreign key)
- **0..*** : Optional multiple values (junction table, nullable FK)
- **1..*** : Required multiple values (at least one required)
- **N:1, 1:N, M:N**: All with SQL examples

### Design Patterns
- **Temporal Data**: Effective dates, history tracking
- **Audit Trail**: Created/modified timestamps, user tracking
- **Status Tracking**: State machines for records
- **Address Management**: Multi-address support
- **Contact Information**: Multiple contact methods
- **Polymorphic Associations**: Flexible references
- **Soft Delete**: Logical deletion with is_active flags

### Normalization Rules
Healthcare-specific examples for:
- **1NF**: Atomic values, repeating groups
- **2NF**: Partial dependencies
- **3NF**: Transitive dependencies

### Constraint Rules
CHECK constraints for data validation:
- Patient: Date of birth, gender codes, email format
- Encounter: Date validation, status values
- Medication: Dosage units, frequency validation

## E-Commerce Domain Knowledge (Ground Truth)

The e-commerce domain provides comprehensive knowledge for designing online store database schemas:

### Entity Definitions
Complete schema guidance for common e-commerce entities:
- **Customer**: Account info, authentication, loyalty programs
- **Product**: Catalog items, SKUs, variants, pricing
- **Category**: Hierarchical product classification
- **Order**: Purchase transactions, status tracking
- **OrderItem**: Line items with price snapshots
- **Cart**: Shopping cart with session support
- **Payment**: Payment transactions, gateway integration
- **Inventory**: Stock tracking across warehouses
- **Review**: Customer ratings and reviews
- **Coupon**: Discount codes and promotions
- **Address**: Shipping and billing addresses

### Relationship Patterns
SQL examples for common e-commerce relationships:
- Customer → Order (1:N)
- Order → OrderItem (1:N)
- Product ↔ Category (M:N)
- Product → ProductVariant (1:N)
- Cart → CartItem (1:N)
- Product → Review (1:N)
- Product → Inventory (1:N per warehouse)

### Design Patterns
- **Dynamic Pricing**: Price tiers, wholesale pricing
- **Inventory Management**: Reservations, multi-warehouse
- **Order State Machine**: Status transitions with validation
- **Product Search**: Full-text search with filtering
- **Audit Trail**: Change tracking for compliance
- Observation: Value ranges, status codes

## Usage

### Basic Usage

```python
from rag import detect_domain_from_text, get_retriever_for_text

# Detect domain from requirement
requirement = "Design a patient management system for tracking visits and diagnoses"
domain = detect_domain_from_text(requirement)
print(f"Detected domain: {domain}")  # Domain.HEALTHCARE

# Get appropriate retriever
retriever = get_retriever_for_text(requirement)
if retriever:
    retriever.initialize()
    results = retriever.search("patient demographics", top_k=5)
```

### Using RAG Tools with Agents

```python
from rag import RAG_TOOLS

# All tools are domain-aware - they auto-detect the domain from query context
from rag import (
    query_domain_rag,           # General domain knowledge search
    get_entity_guidance,        # Entity structure guidance
    get_relationship_guidance,  # Relationship patterns
    get_datatype_mapping,       # Data type mappings
    get_cardinality_rules,      # Cardinality to SQL constraints
    get_normalization_rules,    # Normalization guidelines
    detect_requirement_domain,  # Explicit domain detection
)

# Query for domain-specific guidance (auto-detects healthcare from keywords)
result = await query_domain_rag(
    query="Patient demographics database schema",
    context="hospital information system",
    top_k=5
)

# Get entity design guidance
guidance = await get_entity_guidance(
    entity_description="patient with medical records",
    context="healthcare system"
)

# Get relationship guidance
relationship = await get_relationship_guidance(
    entity1="Patient",
    entity2="Encounter",
    context="hospital visits"
)

# Get PostgreSQL data type mapping
datatype = await get_datatype_mapping(
    attribute_name="birth_date",
    context="patient demographics"
)

# Get normalization recommendations
normalization = await get_normalization_rules(
    table_name="patient",
    attributes=["id", "name", "identifier", "address", "gender"],
    is_healthcare=True
)
```

## PostgreSQL Type Mappings

The healthcare module includes 100+ attribute-to-PostgreSQL type mappings:

| Attribute Pattern | PostgreSQL Type |
|------------------|-----------------|
| `*_id`, `id` | UUID PRIMARY KEY |
| `*_date`, `date_of_*` | DATE |
| `*_time`, `*_timestamp` | TIMESTAMP WITH TIME ZONE |
| `name`, `*_name` | VARCHAR(255) |
| `email` | VARCHAR(255) with email constraint |
| `phone`, `*_phone` | VARCHAR(20) |
| `amount`, `*_amount` | DECIMAL(12,2) |
| `is_*`, `has_*` | BOOLEAN |
| `status` | VARCHAR(50) |
| `notes`, `*_notes` | TEXT |
| `address_*` | Various VARCHAR types |

## Chunk Types

Each RAG chunk has a `chunk_type` indicating its content:

| Type | Description |
|------|-------------|
| `definition` | Entity definition with attributes |
| `relationship` | Relationship pattern with SQL |
| `constraint` | Cardinality and constraint rules |
| `mapping` | Datatype mapping guidance |
| `normalization` | Normalization rules and examples |
| `pattern` | Design pattern guidance |

## Configuration

### Environment Variables

```bash
# Embedding model (sentence-transformers)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector store type (memory, faiss, chroma, qdrant)
VECTOR_STORE_TYPE=memory

# Number of results to retrieve
RAG_TOP_K=5
```

### Programmatic Configuration

```python
from rag import RAGConfig
from rag.domains.healthcare import HealthcareRAGRetriever, HealthcareConfig

config = RAGConfig(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    top_k=5,
    min_relevance=0.3
)

retriever = HealthcareRAGRetriever(config)
retriever.initialize()

# Search for guidance
results = retriever.search("patient encounter relationship")
```

## Adding a New Domain

1. Create a new folder under `rag/domains/`:
```
rag/domains/finance/
├── __init__.py
├── finance_config.py
└── finance_retriever.py
```

2. Implement the domain retriever extending `BaseRAGRetriever`:
```python
from rag.base_rag import BaseRAGRetriever, RAGChunk

class FinanceRAGRetriever(BaseRAGRetriever):
    def _load_domain_chunks(self) -> List[RAGChunk]:
        chunks = []
        # Add entity definitions
        chunks.extend(self._get_entity_definitions())
        # Add relationship patterns
        chunks.extend(self._get_relationship_patterns())
        # ... more ground truth knowledge
        return chunks
```

3. Update `rag/domains/__init__.py`:
```python
if domain == Domain.FINANCE:
    from .finance import FinanceRAGRetriever
    return FinanceRAGRetriever(config)
```

4. Add domain keywords in `rag/rag_config.py`:
```python
DOMAIN_KEYWORDS = {
    Domain.FINANCE: [
        "account", "transaction", "ledger", "balance",
        "payment", "invoice", "banking", ...
    ],
    ...
}
```

## Ground Truth Philosophy

This RAG system uses a **ground truth** approach rather than retrieving from external sources:

1. **Pre-built Knowledge**: All domain knowledge is defined in code, ensuring consistency
2. **Schema Design Focus**: Knowledge is tailored for PostgreSQL database design
3. **Best Practices**: Incorporates database design best practices (normalization, indexing, constraints)
4. **Domain Expertise**: Each domain module encapsulates expert knowledge for that field
5. **Maintainability**: Easy to update and version control the knowledge base

## Requirements

- Python 3.10+
- sentence-transformers
- numpy

Optional:
- faiss-cpu (for FAISS vector store)
- chromadb (for Chroma vector store)
- qdrant-client (for Qdrant vector store)

## License

This module is part of the Multi-Agent Database Design System.
