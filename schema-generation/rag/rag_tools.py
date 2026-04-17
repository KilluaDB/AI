"""
RAG Tools for Multi-Agent Database Design System

These tools are domain-aware and automatically detect whether to use
domain-specific knowledge (e.g., Healthcare, E-Commerce) or general knowledge.
"""

from typing import Optional, List, Dict, Any
from typing_extensions import Annotated

from .rag_config import Domain, detect_domain_from_text
from .base_rag import BaseRAGRetriever, RAGConfig, RAGSearchResult


# Global retriever cache
_retriever_cache: Dict[str, BaseRAGRetriever] = {}


def _get_retriever(domain: Domain) -> Optional[BaseRAGRetriever]:
    """Get or create a retriever for the specified domain"""
    domain_key = domain.value
    
    if domain_key in _retriever_cache:
        return _retriever_cache[domain_key]
    
    # Import domain-specific retrievers
    if domain == Domain.HEALTHCARE:
        try:
            from .domains.healthcare import HealthcareRAGRetriever
            retriever = HealthcareRAGRetriever()
            retriever.initialize()
            _retriever_cache[domain_key] = retriever
            return retriever
        except ImportError as e:
            print(f"Warning: Could not load Healthcare retriever: {e}")
            return None
    
    elif domain == Domain.ECOMMERCE:
        try:
            from .domains.ecommerce import EcommerceRAGRetriever
            retriever = EcommerceRAGRetriever()
            retriever.initialize()
            _retriever_cache[domain_key] = retriever
            return retriever
        except ImportError as e:
            print(f"Warning: Could not load E-Commerce retriever: {e}")
            return None
    
    # Add more domains here as they are implemented
    # elif domain == Domain.FINANCE:
    #     from .domains.finance import FinanceRAGRetriever
    #     retriever = FinanceRAGRetriever()
    #     retriever.initialize()
    #     _retriever_cache[domain_key] = retriever
    #     return retriever
    
    return None


def _get_retriever_for_text(text: str) -> Optional[BaseRAGRetriever]:
    """Get appropriate retriever based on text content"""
    domain = detect_domain_from_text(text)
    
    if domain == Domain.GENERAL:
        return None
    
    return _get_retriever(domain)


# ============== RAG Tools for Agents ==============


async def query_domain_rag(
    query: Annotated[str, "The search query to find relevant domain knowledge"],
    context: Annotated[str, "Additional context about the requirement to help detect domain"] = "",
    top_k: Annotated[int, "Number of results to return (default 5)"] = 5
) -> str:
    """
    Query the RAG system for domain-specific knowledge.
    
    This tool automatically detects the domain (healthcare, finance, etc.) from the query
    and retrieves relevant knowledge for database schema design.
    
    Use this when:
    - Designing schemas for domain-specific applications
    - Need guidance on entity structures and relationships
    - Want to understand industry-standard data models
    """
    try:
        # Detect domain from combined query and context
        combined_text = f"{query} {context}"
        retriever = _get_retriever_for_text(combined_text)
        
        if retriever is None:
            return "No domain-specific knowledge available for this query. Using general database design principles."
        
        results = retriever.search(query, top_k=top_k)
        
        if not results:
            return f"No relevant {retriever.get_domain()} knowledge found for query: {query}"
        
        # Format results
        output_parts = [f"### {retriever.get_domain().upper()} Knowledge Results\n"]
        for result in results:
            chunk = result.chunk
            output_parts.append(
                f"\n**[{chunk.resource_type} - {chunk.chunk_type.value}]** "
                f"(relevance: {result.similarity_score:.2f})\n"
                f"{chunk.content}\n"
                f"---"
            )
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"Error querying RAG system: {str(e)}"


async def get_entity_guidance(
    entity_description: Annotated[str, "Description of the entity you want guidance for"],
    context: Annotated[str, "Context about the domain and requirements"] = ""
) -> str:
    """
    Get guidance on entity design based on domain standards.
    
    Use this when:
    - Identifying entities from requirements
    - Determining attributes for an entity
    - Understanding standard entity structures
    """
    try:
        combined_text = f"{entity_description} {context}"
        retriever = _get_retriever_for_text(combined_text)
        
        if retriever is None:
            return f"No domain-specific guidance available. General entity design: identify key attributes, define primary key, consider relationships."
        
        results = retriever.search(
            f"entity definition attributes {entity_description}",
            top_k=3
        )
        
        if not results:
            return f"No specific guidance found for entity: {entity_description}"
        
        output_parts = [f"### Entity Guidance for: {entity_description}\n"]
        for result in results:
            output_parts.append(f"\n{result.chunk.content}\n---")
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"Error getting entity guidance: {str(e)}"


async def get_relationship_guidance(
    entity1: Annotated[str, "First entity in the relationship"],
    entity2: Annotated[str, "Second entity in the relationship"],
    context: Annotated[str, "Context about the domain"] = ""
) -> str:
    """
    Get guidance on relationships between entities based on domain standards.
    
    Use this when:
    - Determining relationship type (1:1, 1:N, M:N)
    - Understanding how entities should be connected
    - Designing junction tables
    """
    try:
        combined_text = f"{entity1} {entity2} relationship {context}"
        retriever = _get_retriever_for_text(combined_text)
        
        if retriever is None:
            return f"No domain-specific guidance available for {entity1}-{entity2} relationship."
        
        query = f"relationship between {entity1} and {entity2} cardinality foreign key"
        results = retriever.search(query, top_k=3)
        
        if not results:
            return f"No specific relationship guidance found for {entity1} and {entity2}."
        
        output_parts = [f"### Relationship Guidance: {entity1} ↔ {entity2}\n"]
        for result in results:
            output_parts.append(f"\n{result.chunk.content}\n---")
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"Error getting relationship guidance: {str(e)}"


async def get_datatype_mapping(
    attribute_name: Annotated[str, "Name of the attribute to get type mapping for"],
    context: Annotated[str, "Context about the domain and data"] = ""
) -> str:
    """
    Get PostgreSQL data type mapping for domain-specific attributes.
    
    Use this when:
    - Determining appropriate SQL data types
    - Physical schema design
    - Need constraints for specific data types
    """
    try:
        combined_text = f"{attribute_name} {context}"
        retriever = _get_retriever_for_text(combined_text)
        
        if retriever is None:
            # Return general type inference
            return f"""
General Data Type Mapping for '{attribute_name}':
- If ID field: SERIAL PRIMARY KEY or UUID
- If name/title: VARCHAR(255)
- If description: TEXT
- If date: DATE
- If datetime: TIMESTAMP WITH TIME ZONE
- If boolean/flag: BOOLEAN
- If money/price: DECIMAL(10,2)
- If count/quantity: INTEGER
- If email: VARCHAR(255) with CHECK
- If phone: VARCHAR(20)
- Default: VARCHAR(255)
"""
        
        query = f"data type mapping {attribute_name} PostgreSQL"
        results = retriever.search(query, top_k=2)
        
        if not results:
            return f"No specific type mapping found for: {attribute_name}"
        
        output_parts = [f"### Data Type Mapping for: {attribute_name}\n"]
        for result in results:
            output_parts.append(f"\n{result.chunk.content}\n---")
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"Error getting datatype mapping: {str(e)}"


async def get_cardinality_rules(
    relationship: Annotated[str, "Description of the relationship"],
    context: Annotated[str, "Context about the domain"] = ""
) -> str:
    """
    Get cardinality rules and SQL constraint mappings.
    
    Use this when:
    - Determining cardinality (0..1, 1..1, 0..*, 1..*)
    - Converting cardinality to SQL constraints
    - Deciding between embedding and separate tables
    """
    try:
        combined_text = f"{relationship} {context}"
        retriever = _get_retriever_for_text(combined_text)
        
        if retriever is None:
            return """
General Cardinality Rules:
- 0..1 (optional single): Nullable column in same table
- 1..1 (required single): NOT NULL column in same table  
- 0..* (optional many): Separate child table with nullable FK
- 1..* (required many): Separate child table with NOT NULL FK
- M:N relationships: Junction table with composite key
"""
        
        query = f"cardinality constraint {relationship} nullable foreign key"
        results = retriever.search(query, top_k=2)
        
        if not results:
            return f"No specific cardinality rules found for: {relationship}"
        
        output_parts = [f"### Cardinality Rules for: {relationship}\n"]
        for result in results:
            output_parts.append(f"\n{result.chunk.content}\n---")
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"Error getting cardinality rules: {str(e)}"


async def get_normalization_rules(
    schema_description: Annotated[str, "Description of the schema or table to normalize"],
    context: Annotated[str, "Context about the domain"] = ""
) -> str:
    """
    Get domain-specific normalization guidelines.
    
    Use this when:
    - Normalizing to 3NF
    - Deciding what to split into separate tables
    - Domain-specific normalization patterns
    """
    try:
        combined_text = f"{schema_description} {context}"
        retriever = _get_retriever_for_text(combined_text)
        
        if retriever is None:
            return """
General Normalization Guidelines:
1. First Normal Form (1NF): No repeating groups, atomic values
2. Second Normal Form (2NF): No partial dependencies on composite keys
3. Third Normal Form (3NF): No transitive dependencies

Common patterns:
- Repeating groups → separate child table
- Lookup values → reference table
- Multi-valued attributes → junction table
"""
        
        query = f"normalization {schema_description} third normal form 3NF"
        results = retriever.search(query, top_k=2)
        
        if not results:
            return f"No specific normalization rules found for: {schema_description}"
        
        output_parts = [f"### Normalization Rules for: {schema_description}\n"]
        for result in results:
            output_parts.append(f"\n{result.chunk.content}\n---")
        
        return "\n".join(output_parts)
    
    except Exception as e:
        return f"Error getting normalization rules: {str(e)}"


async def detect_requirement_domain(
    requirement_text: Annotated[str, "The requirement text to analyze"]
) -> str:
    """
    Detect the domain of a requirement text.
    
    Use this when:
    - Starting a new database design
    - Determining if domain-specific knowledge is available
    - Deciding which RAG tools to use
    """
    domain = detect_domain_from_text(requirement_text)
    
    domain_info = {
        Domain.HEALTHCARE: "Healthcare domain detected. Ground-truth knowledge is available for Patient, Encounter, Observation, Condition, Medication, and other clinical entities.",
        Domain.FINANCE: "Finance domain detected. Knowledge about accounts, transactions, and financial entities may be available.",
        Domain.ECOMMERCE: "E-commerce domain detected. Ground-truth knowledge is available for Customer, Product, Order, Cart, Payment, Inventory, and other e-commerce entities.",
        Domain.EDUCATION: "Education domain detected. Knowledge about students, courses, and academic structures may be available.",
        Domain.GENERAL: "No specific domain detected. Using general database design principles."
    }
    
    return f"""
Domain Detection Result: **{domain.value.upper()}**

{domain_info[domain]}

Available RAG tools for this domain:
- query_domain_rag: Search domain knowledge
- get_entity_guidance: Get entity structure guidance
- get_relationship_guidance: Get relationship patterns
- get_datatype_mapping: Get data type mappings
- get_cardinality_rules: Get cardinality constraints
- get_normalization_rules: Get normalization guidelines
"""


# List of RAG tools for agent registration
RAG_TOOLS = [
    query_domain_rag,
    get_entity_guidance,
    get_relationship_guidance,
    get_datatype_mapping,
    get_cardinality_rules,
    get_normalization_rules,
    detect_requirement_domain,
]
