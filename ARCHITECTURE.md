# KilluaDB - Multi-Agent Database Design System

## Complete Architecture Documentation

This document provides a comprehensive explanation of the entire multi-agent system architecture, from individual agents to the complete pipeline.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Individual Agents](#individual-agents)
   - [ManagerAgent](#1-manageragent)
   - [ConceptualDesignerAgent](#2-conceptualdesigneragent)
   - [ConceptualReviewerAgent](#3-conceptualrevieweragent)
   - [LogicalDesignerAgent](#4-logicaldesigneragent)
   - [Test & Validate Agents](#5-test--validate-agents-qaagent--executionagent)
   - [PhysicalDesignerAgent](#6-physicaldesigneragent)
   - [ReportAgent](#7-reportagent)
4. [Agent Collaboration](#agent-collaboration)
5. [RAG (Retrieval-Augmented Generation) System](#rag-system)
6. [Tools Reference](#tools-reference)
7. [Code Examples](#code-examples)
8. [Complete Pipeline Flow](#complete-pipeline-flow)

---

## System Overview

KilluaDB is an **automated database design system** that transforms natural language requirements into fully functional PostgreSQL schemas. It uses a **multi-agent architecture** powered by AutoGen (ag2), where specialized agents collaborate to handle different phases of database design:

```
Natural Language Requirements
         ↓
   [ManagerAgent] ←→ Requirement Analysis
         ↓
   [ConceptualDesignerAgent] ←→ [ConceptualReviewerAgent]
         ↓
   [LogicalDesignerAgent] ←→ Normalization (3NF) + RAG Tools
         ↓
   [QAAgent] → [ExecutionAgent] → Test & Validate
         ↓
   [PhysicalDesignerAgent] → PostgreSQL DDL
         ↓
   [ReportAgent] → Technical Documentation
```

### Key Technologies

| Component | Technology |
|-----------|------------|
| Agent Framework | AutoGen (ag2) v0.9.0 |
| LLM Providers | OpenAI, Anthropic, Google, HuggingFace |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Database | PostgreSQL |
| Visualization | Mermaid ER Diagrams |
| RAG System | Custom domain-aware retrieval |

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            KilluaDB Architecture                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                          SelectorGroupChat (Main Team)                      │  │
│  │                                                                             │  │
│  │   ┌──────────────┐    ┌─────────────────────────────────────────────────┐  │  │
│  │   │ManagerAgent  │    │                                                 │  │  │
│  │   │              │    │          (ConceptualAgent)                      │  │  │
│  │   │ • Requirement│    │   ┌───────────────────────────────────────┐    │  │  │
│  │   │   Analysis   │    │   │        RoundRobinGroupChat            │    │  │  │
│  │   │ • Final      │    │   │  ┌─────────────┐  ┌──────────────┐   │    │  │  │
│  │   │   Acceptance │    │   │  │ Conceptual  │  │ Conceptual   │   │    │  │  │
│  │   └──────────────┘    │   │  │ Designer    │←→│ Reviewer     │   │    │  │  │
│  │                        │   │  │ + RAG Tools │  │ + RAG Tools  │   │    │  │  │
│  │   ┌──────────────┐    │   │  └─────────────┘  └──────────────┘   │    │  │  │
│  │   │Logical       │    │   └───────────────────────────────────────┘    │  │  │
│  │   │Designer      │    └─────────────────────────────────────────────────┘  │  │
│  │   │Agent         │                                                          │  │
│  │   │              │    ┌────────────────────────────────────────────────┐   │  │
│  │   │ • 3NF Norm   │    │         Test & Validate Agents                 │   │  │
│  │   │ • Armstrong  │    │   ┌─────────────┐    ┌─────────────────┐      │   │  │
│  │   │ • RAG Tools  │    │   │  QAAgent    │ →  │ ExecutionAgent  │      │   │  │
│  │   └──────────────┘    │   │ • Test Gen  │    │ • Schema Valid  │      │   │  │
│  │                        │   └─────────────┘    └─────────────────┘      │   │  │
│  │                        └────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                         ↓                                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                        Sequential Pipeline                                  │  │
│  │   ┌────────────────────────┐         ┌────────────────────────┐            │  │
│  │   │  PhysicalDesignerAgent │    →    │      ReportAgent       │            │  │
│  │   │  • DDL Generation      │         │  • Markdown Report     │            │  │
│  │   │  • PostgreSQL Exec     │         │  • Documentation       │            │  │
│  │   │  • Self-Refinement     │         └────────────────────────┘            │  │
│  │   │  • RAG Tools           │                                                │  │
│  │   └────────────────────────┘                                                │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                            RAG System                                       │  │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │  │
│  │   │   Domain    │ →  │   Base RAG  │ →  │  RAG Tools  │                    │  │
│  │   │  Detection  │    │  Retriever  │    │  (7 funcs)  │                    │  │
│  │   └─────────────┘    └─────────────┘    └─────────────┘                    │  │
│  │                              ↓                                              │  │
│  │   ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                  Domain-Specific Retrievers                        │   │  │
│  │   │   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │   │  │
│  │   │   │ Healthcare │ │ E-Commerce │ │  Finance   │ │ Education  │     │   │  │
│  │   │   │  (Ground   │ │  (Ground   │ │  (Coming)  │ │  (Coming)  │     │   │  │
│  │   │   │   Truth)   │ │   Truth)   │ │     ◯      │ │     ◯      │     │   │  │
│  │   │   │     ✓      │ │     ✓      │ └────────────┘ └────────────┘     │   │  │
│  │   │   └────────────┘ └────────────┘                                    │   │  │
│  │   └────────────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Individual Agents

### 1. ManagerAgent

**Role**: Project Manager & Requirement Analyst

**Responsibilities**:
- Analyze natural language requirements
- Clarify ambiguities in user requirements
- Generate requirement analysis reports
- Final acceptance of the database design

**System Prompt Summary**:
```
You are an experienced project manager, but not responsible for database design.
Goals:
1. Generate requirement analysis reports
2. Generate acceptance reports
```

**Input**: Natural language requirements from user
**Output**: Structured requirement analysis JSON

**Code Definition**:
```python
manager = AssistantAgent(
    "ManagerAgent",
    description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
    model_client=model_client,
    system_message=get_manager_prompt(),
)
```

**Output Format**:
```json
{
    "requirement analysis results": "Your requirements analysis report."
}
```

---

### 2. ConceptualDesignerAgent

**Role**: Entity-Relationship Model Designer

**Responsibilities**:
- Identify entity sets and their attributes
- Define relationship sets between entities
- Determine mapping cardinality (1:1, 1:N, M:N)
- Use RAG tools for domain-specific guidance (healthcare, finance, etc.)

**Tools Available**:
- `detect_requirement_domain` - Detect if domain-specific knowledge is available
- `get_entity_guidance` - Get standard entity structures for domains
- `get_relationship_guidance` - Get relationship patterns between entities
- `query_domain_rag` - General domain knowledge search

**Code Definition**:
```python
conceptual_designer_agent = AssistantAgent(
    "ConceptualDesignerAgent",
    description="Concept designers design conceptual models based on requirements analysis. Can use RAG for domain-specific guidance.",
    model_client=model_client,
    tools=conceptual_rag_tools,  # RAG tools for domain knowledge
    system_message=get_conceptual_design_agent_prompt(),
    reflect_on_tool_use=True if conceptual_rag_tools else False,
)
```

**Output Format**:
```json
{
    "question": "",
    "output": {
        "Entity Set": {
            "Student": ["ID", "Name", "Age", "Department"],
            "Course": ["Number", "Credits", "Lecturer", "Class Time"]
        },
        "Relationship Set": {
            "Course Selection": {
                "Object": ["Student", "Course"],
                "Proportional Relationship": "Many-to-Many",
                "Relationship Attribute": ["Selection Time"]
            }
        }
    }
}
```

---

### 3. ConceptualReviewerAgent

**Role**: Conceptual Model Validator

**Responsibilities**:
- Validate entity sets follow naming conventions
- Check relationship attributes don't contain IDs
- Ensure all entities appear in relationships
- Validate cardinality types
- Use RAG for domain-specific validation

**Validation Logic** (Pseudocode from prompt):
```python
FUNCTION ValidateData(json_data):
    entity_sets = json_data['output']['Entity Set']
    relationship_sets = json_data['output']['Relationship Set']
    
    FOR relationship_name, details IN relationship_sets:
        IF ContainsID(details['Relationship Attribute']):
            PRINT "Relationship should not contain IDs"
        IF NOT IsValidProportionalRelationship(details['Proportional Relationship']):
            PRINT "Invalid proportional relationship type"
    
    FOR entity_name IN entity_sets:
        IF entity_name NOT IN entities_in_relationships:
            PRINT "Entity does not appear in any relationship"
```

**Code Definition**:
```python
conceptual_reviewer_agent = AssistantAgent(
    "ConceptualReviewerAgent",
    description="Determine whether the current conceptual model satisfies all constraints. Can use RAG for domain validation.",
    model_client=model_client,
    tools=reviewer_rag_tools,
    system_message=get_reviewer_prompt(),
    reflect_on_tool_use=True if reviewer_rag_tools else False,
)
```

**Output Format**:
```json
{
    "Evaluation result": "Approve or send to ConceptualDesignerAgent for revision",
    "Pseudocode output": "Validation completed with no errors",
    "Revision suggestion": "No changes needed"
}
```

---

### 4. LogicalDesignerAgent

**Role**: Relational Schema Designer & Normalizer

**Responsibilities**:
- Convert conceptual model to relational schemas
- Identify functional dependencies
- Validate and find primary keys using Armstrong's axioms
- Decompose to Third Normal Form (3NF)
- Handle 1:N (merge) and M:N (new table) relationships

**Tools Available**:

| Tool | Type | Description |
|------|------|-------------|
| `get_attribute_keys_by_arm_strong` | Built-in | Identify candidate keys from functional dependencies |
| `confirm_to_third_normal_form` | Built-in | Decompose schemas to 3NF |
| `get_cardinality_rules` | RAG | Get cardinality to SQL constraint mappings |
| `get_normalization_rules` | RAG | Get domain-specific normalization guidelines |
| `query_domain_rag` | RAG | Search for domain-specific patterns |

**RAG Tools Assignment**:
```python
# RAG tools for Logical Designer: cardinality, normalization, query
logical_rag_tools = [RAG_TOOLS[4], RAG_TOOLS[5], RAG_TOOLS[0]] if RAG_AVAILABLE else []
```

**Code Definition**:
```python
logical_designer_agent = AssistantAgent(
    "LogicalDesignerAgent",
    description="The logic designer designs the logical model based on the conceptual model.",
    model_client=model_client,
    tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form] + logical_rag_tools,
    system_message=get_logical_design_agent_prompt(),
    reflect_on_tool_use=True
)
```

**Key Algorithm - Armstrong's Axioms for Candidate Keys**:
```python
async def get_attribute_keys_by_arm_strong(dependencies_json: str):
    """
    Identify primary keys based on functional dependencies.
    Uses closure computation to find candidate keys.
    
    Input: {"Student": {"ID": ["Name", "Age"]}}
    Output: {"entity_primary_keys": {"Student": [["ID"]]}}
    """
    # Compute closure for each attribute combination
    # Find minimal superkeys (candidate keys)
```

**Output Format**:
```json
{
    "output": {
        "Student": {
            "Attribute": ["ID", "Name", "Age", "Department"],
            "Primary key": ["ID"],
            "Foreign key": {"Department": {"Department": "ID"}}
        },
        "Course Selection": {
            "Attribute": ["ID", "Number", "Selection Time"],
            "Primary key": ["ID", "Number"],
            "Foreign key": {
                "ID": {"Student": "ID"},
                "Number": {"Course": "Number"}
            }
        }
    }
}
```

---

### 5. Test & Validate Agents (QAAgent + ExecutionAgent)

The test and validation phase consists of two agents working together:

#### 5a. QAAgent

**Role**: Test Case Generator

**Responsibilities**:
- Generate test data for database operations
- Create test cases for INSERT, UPDATE, DELETE, QUERY
- Test entity integrity (unique, non-null PKs)
- Test referential integrity (valid FKs)

**Knowledge Applied**:
- Entity integrity: Primary keys must be unique and non-null
- Referential integrity: Foreign keys must reference existing values or be null

**Code Definition**:
```python
qa_agent = AssistantAgent(
    "QAAgent",
    description="QA engineers generate test cases based on requirement analysis.",
    model_client=model_client,
    system_message=get_QA_agent_prompt(),
    model_context=RoleChatCompletionContext(name='ManagerAgent'),  # Only sees requirement analysis
)
```

**Output Format**:
```json
{
    "Insert Test case": [
        "Insert major: software engineering, computer science",
        "Insert student: ID=12345, Name=Zhang San, Age=21"
    ],
    "Update Test case": [
        "Change major of student 12345 to software engineering"
    ],
    "Query Test case": [
        "View major name of student 12345"
    ],
    "Delete Test case": [
        "Delete student with ID 12345"
    ]
}
```

#### 5b. ExecutionAgent

**Role**: Schema Validator

**Responsibilities**:
- Evaluate if logical schemas satisfy test cases
- Check if operations can be performed on the schema
- Report errors to appropriate agents for revision

**Code Definition**:
```python
execution_agent = AssistantAgent(
    "ExecutionAgent",
    description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
    model_client=model_client,
    system_message=get_execution_agent_prompt(),
)
```

**Output Format**:
```json
{
    "Evaluation result": "Approve, send to ManagerAgent / Reject, send to ConceptualDesignerAgent / Reject, send to LogicalDesignerAgent",
    "intuitively check output": "All test cases can be performed on the schema"
}
```

#### Test & Validate Flow
```
QAAgent → ExecutionAgent → ManagerAgent (if approved)
                        → ConceptualDesignerAgent (if conceptual issues)
                        → LogicalDesignerAgent (if logical issues)
```

---

### 6. PhysicalDesignerAgent

**Role**: PostgreSQL DDL Generator

**Responsibilities**:
- Infer appropriate PostgreSQL data types
- Generate executable CREATE TABLE statements
- Design optimal indexing strategy
- Execute and validate DDL on PostgreSQL
- Self-refine on execution errors

**Tools Available**:
- `execute_sql_on_postgres` - Execute SQL statements
- `execute_ddl_statements` - Execute DDL with validation
- `validate_ddl_syntax` - Check DDL syntax before execution
- `infer_and_generate_ddl` - Auto-generate DDL from schema
- `test_postgres_connection` - Test database connectivity
- `get_datatype_mapping` - RAG: Get domain-specific type mappings
- `query_domain_rag` - RAG: Search for DDL patterns

**Data Type Inference Rules**:
```
ID Fields:
- *_id, id → SERIAL PRIMARY KEY
- uuid, guid → UUID DEFAULT gen_random_uuid()

String Fields:
- name, title → VARCHAR(255) NOT NULL
- description, content → TEXT
- email → VARCHAR(255) UNIQUE

Numeric Fields:
- age, count, quantity → INTEGER
- price, cost, salary → DECIMAL(10,2)

Date/Time Fields:
- *_date → DATE
- *_time → TIME
- created_at, updated_at → TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Code Definition**:
```python
physical_designer_agent = AssistantAgent(
    "PhysicalDesignerAgent",
    description='The physical designer designs and executes the SQL statements based on the logical model.',
    model_client=model_client,
    tools=[
        execute_sql_on_postgres,
        execute_ddl_statements,
        validate_ddl_syntax,
        infer_and_generate_ddl,
        test_postgres_connection,
    ] + physical_rag_tools,
    system_message=get_physical_design_agent_prompt(),
    reflect_on_tool_use=True,
)
```

**Self-Refinement Loop**:
```python
max_refinement_attempts = 3
refinement_attempt = 0
while refinement_attempt < max_refinement_attempts:
    last_message = physical_result.messages[-1].content
    if "Fail" in last_message or "Error" in last_message:
        refinement_attempt += 1
        # Analyze error and retry
        physical_result = await Console(
            physical_designer_agent.run_stream(task=refinement_prompt)
        )
    else:
        break
```

**Output Format**:
```json
{
    "DDL Think Steps": "Inference reasoning...",
    "DDL Output": "CREATE TABLE student (...);",
    "Index Think Steps": "Indexing strategy reasoning...",
    "Index Output": "CREATE INDEX idx_student_name ON student(name);",
    "Execution Status": "Success",
    "Data Type Summary": "student.id: SERIAL, student.name: VARCHAR(255)"
}
```

---

### 7. ReportAgent

**Role**: Documentation Generator

**Responsibilities**:
- Compile all agent outputs into structured report
- Format in professional Markdown
- Organize by design phases

**Code Definition**:
```python
report_agent = AssistantAgent(
    'ReportAgent',
    description='The report agent compiles the current information into a standardized report format.',
    model_client=model_client,
    system_message=get_report_prompt(),
)
```

**Output Structure**:
```markdown
# [Project Name] Technical Design Report

## 1. User Requirement
## 2. Conceptual Design
## 3. Logical Design
## 4. Physical Design

# Appendix
## 1. Requirements Analysis
## 2. Conceptual Design (Thought Process + Results)
## 3. Logical Design (Thought Process + Results)
## 4. Functional Validation (Test Cases + Results)
## 5. Physical Design (DDL + Indexes)
```

---

## Agent Collaboration

### Team Structures

#### 1. SocietyOfMindAgent (Nested Team)
The conceptual design phase uses a nested team structure:

```python
# Inner team: Conceptual Designer ↔ Conceptual Reviewer
inner_termination = TextMentionTermination("Approve") | max_messages_termination
inner_team = RoundRobinGroupChat(
    [conceptual_designer_agent, conceptual_reviewer_agent], 
    termination_condition=inner_termination
)

# Wrap as single agent for outer team
society_of_mind_agent = SocietyOfMindAgent(
    "ConceptualAgent",
    description='A team that designs conceptual models based on requirements analysis.',
    team=inner_team,
    model_client=model_client,
    instruction='Output the Final Answer formatted in json by ConceptualDesignerAgent.'
)
```

#### 2. SelectorGroupChat (Main Team)
The main team uses intelligent agent selection:

```python
team = SelectorGroupChat(
    [manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
    model_client=model_client,
    termination_condition=termination,
    allow_repeated_speaker=True,
    selector_prompt=get_selector_prompt(),
    selector_func=selector_func
)
```


---

## RAG System

The RAG (Retrieval-Augmented Generation) system provides domain-specific knowledge to agents.

### Architecture

```
rag/
├── __init__.py          # Module exports
├── base_rag.py          # Abstract base retriever class
├── rag_config.py        # Domain detection & configuration
├── rag_tools.py         # 7 tool functions for agents
└── domains/
    ├── __init__.py      # Domain retriever factory
    ├── healthcare/      # Healthcare domain (Ground Truth)
    │   ├── __init__.py
    │   ├── healthcare_config.py    # Healthcare type mappings
    │   └── healthcare_retriever.py # Healthcare retriever
    └── ecommerce/       # E-Commerce domain (Ground Truth)
        ├── __init__.py
        ├── ecommerce_config.py     # E-Commerce type mappings
        └── ecommerce_retriever.py  # E-Commerce retriever
```

### Domain Detection

```python
class Domain(Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    EDUCATION = "education"
    GENERAL = "general"

def detect_domain_from_text(text: str) -> Domain:
    """Auto-detect domain from requirement text"""
    text_lower = text.lower()
    
    # Healthcare keywords
    healthcare_keywords = ["patient", "hospital", "clinical", "medical", 
                          "diagnosis", "treatment", "medication", "healthcare"]
    if any(kw in text_lower for kw in healthcare_keywords):
        return Domain.HEALTHCARE
    
    # E-commerce keywords
    ecommerce_keywords = ["product", "cart", "order", "checkout", "shipping",
                          "inventory", "catalog", "customer", "e-commerce"]
    if any(kw in text_lower for kw in ecommerce_keywords):
        return Domain.ECOMMERCE
    
    # Finance keywords...
    return Domain.GENERAL
```

### RAG Tools for Agents

| Tool | Purpose | Used By |
|------|---------|---------|
| `detect_requirement_domain` | Detect domain from text | Conceptual, Reviewer |
| `get_entity_guidance` | Get standard entity structures | Conceptual |
| `get_relationship_guidance` | Get relationship patterns | Conceptual |
| `query_domain_rag` | General domain search | All agents |
| `get_cardinality_rules` | Cardinality → SQL constraints | Logical |
| `get_normalization_rules` | Domain normalization rules | Logical |
| `get_datatype_mapping` | Attribute → PostgreSQL types | Physical |

### Healthcare Domain (Ground Truth)

The Healthcare retriever provides domain-specific knowledge for schema design:

```python
class HealthcareRAGRetriever(BaseRAGRetriever):
    """Healthcare RAG using ground truth knowledge"""
    
    def _load_domain_knowledge(self) -> List[RAGChunk]:
        chunks = []
        chunks.extend(self._get_entity_definitions())    # Patient, Encounter, etc.
        chunks.extend(self._get_relationship_patterns()) # 1:N, M:N patterns
        chunks.extend(self._get_datatype_guidelines())   # Attribute → PostgreSQL
        chunks.extend(self._get_cardinality_rules())     # 0..1, 1..*, etc.
        chunks.extend(self._get_normalization_rules())   # Healthcare 3NF
        chunks.extend(self._get_healthcare_patterns())   # Design patterns
        chunks.extend(self._get_constraint_rules())      # CHECK constraints
        return chunks
```

**Healthcare Entities**:
- Patient, Provider, Encounter, Diagnosis
- Medication, Observation, Appointment
- Insurance, Organization

**PostgreSQL Type Mappings**:
```python
HEALTHCARE_POSTGRES_TYPE_MAP = {
    "patient_id": "UUID PRIMARY KEY",
    "date_of_birth": "DATE",
    "gender": "VARCHAR(20)",
    "email": "VARCHAR(255)",
    "phone": "VARCHAR(20)",
    "address": "TEXT",
    "diagnosis_code": "VARCHAR(20)",
    "amount": "DECIMAL(12,2)",
    # ... 100+ mappings
}
```

### E-Commerce Domain (Ground Truth)

The E-Commerce retriever provides online store-specific knowledge:

```python
class EcommerceRAGRetriever(BaseRAGRetriever):
    """E-Commerce RAG using ground truth knowledge"""
    
    def _load_domain_knowledge(self) -> List[RAGChunk]:
        chunks = []
        chunks.extend(self._get_entity_definitions())    # Customer, Product, Order, etc.
        chunks.extend(self._get_relationship_patterns()) # 1:N, M:N patterns
        chunks.extend(self._get_datatype_guidelines())   # Attribute → PostgreSQL
        chunks.extend(self._get_cardinality_rules())     # 0..1, 1..*, etc.
        chunks.extend(self._get_normalization_rules())   # E-commerce 3NF
        chunks.extend(self._get_ecommerce_patterns())    # Design patterns
        chunks.extend(self._get_constraint_rules())      # CHECK constraints
        return chunks
```

**E-Commerce Entities**:
- Customer, Product, Category, Order
- OrderItem, Cart, CartItem, Payment
- Inventory, Review, Coupon, Address

**PostgreSQL Type Mappings**:
```python
ECOMMERCE_POSTGRES_TYPE_MAP = {
    "customer_id": "UUID PRIMARY KEY",
    "sku": "VARCHAR(100) NOT NULL UNIQUE",
    "price": "DECIMAL(12,2) NOT NULL",
    "quantity": "INTEGER NOT NULL DEFAULT 0",
    "order_status": "VARCHAR(50) DEFAULT 'pending'",
    "stock_quantity": "INTEGER DEFAULT 0",
    # ... 100+ mappings
}
```

---

## Tools Reference

### PostgreSQL Tools

```python
POSTGRES_TOOLS = [
    execute_sql_on_postgres,      # Execute any SQL
    execute_ddl_statements,       # Execute DDL with validation
    validate_ddl_syntax,          # Syntax check
    infer_and_generate_ddl,       # Auto-generate from schema
    test_postgres_connection,     # Connection test
]
```

### Normalization Tools

```python
# Imported from shared.normalization_utils
compute_closure(base_set, deps)           # Attribute closure
find_candidate_keys(attrs, deps)          # Find minimal keys
get_attribute_keys_by_armstrong_single()  # Keys for single entity
```

### Mermaid Tools

```python
generate_mermaid_from_conceptual()  # Conceptual → Mermaid ER
generate_mermaid_from_logical()     # Logical → Mermaid ER
validate_mermaid_syntax()           # Syntax validation
conceptual_to_mermaid()             # Extract & convert
```

---

## Code Examples

### Complete Main Function

```python
async def main(args):
    # Initialize model client
    model_client = create_model_client(args.model_name)
    
    # Prepare RAG tools
    conceptual_rag_tools = RAG_TOOLS[:4] if RAG_AVAILABLE else []
    logical_rag_tools = [RAG_TOOLS[4], RAG_TOOLS[5], RAG_TOOLS[0]] if RAG_AVAILABLE else []
    physical_rag_tools = [RAG_TOOLS[3], RAG_TOOLS[0]] if RAG_AVAILABLE else []
    
    # Create agents (see individual agent sections)
    conceptual_designer_agent = AssistantAgent(...)
    logical_designer_agent = AssistantAgent(...)
    qa_agent = AssistantAgent(...)
    execution_agent = AssistantAgent(...)
    manager = AssistantAgent(...)
    conceptual_reviewer_agent = AssistantAgent(...)
    physical_designer_agent = AssistantAgent(...)
    report_agent = AssistantAgent(...)
    
    # Create nested team for conceptual design
    inner_team = RoundRobinGroupChat(
        [conceptual_designer_agent, conceptual_reviewer_agent],
        termination_condition=TextMentionTermination("Approve")
    )
    society_of_mind_agent = SocietyOfMindAgent("ConceptualAgent", team=inner_team, ...)
    
    # Create main team
    team = SelectorGroupChat(
        [manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
        selector_func=selector_func,
        ...
    )
    
    # Run logical design pipeline
    await Console(team.run_stream(task=args.requirement_text))
    await team.reset()
    
    # Run physical design
    physical_result = await Console(physical_designer_agent.run_stream(task=output_string))
    
    # Self-refinement loop
    max_attempts = 3
    for attempt in range(max_attempts):
        if "Error" in physical_result.messages[-1].content:
            physical_result = await Console(
                physical_designer_agent.run_stream(task=refinement_prompt)
            )
        else:
            break
    
    # Generate report
    result = await Console(report_agent.run_stream(task=output_string))
    
    return result.messages[1].content
```

### Running the System

```python
import argparse
import asyncio
from physical_design.agent_chat_physical import main

# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--model_name', default='gpt4')
parser.add_argument('--database_name', default='my_database')
parser.add_argument('--requirement_text', required=True)
args = parser.parse_args()

# Run the multi-agent system
result = asyncio.run(main(args))
print(result)
```

### Example Requirement

```python
requirement_text = """
A university needs a student course selection management system to maintain 
and track students' course selection information. Students have information 
such as student ID, name, age, department. Each student can take multiple 
courses and can drop or change courses within the specified time. Each course 
has information such as course number, course name, credits, lecturer and 
class time.
"""
```

---

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        COMPLETE PIPELINE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. USER INPUT                                                       │
│     "Design a student course selection system..."                    │
│                          ↓                                           │
│  2. MANAGER AGENT                                                    │
│     • Analyzes requirements                                          │
│     • Clarifies ambiguities                                          │
│     • Output: Requirement analysis report                            │
│                          ↓                                           │
│  3. CONCEPTUAL DESIGN (Nested Team)                                  │
│     ┌────────────────────────────────────────┐                      │
│     │  ConceptualDesigner ←→ ConceptualReviewer │                   │
│     │  • Identify entities (Student, Course)   │                    │
│     │  • Define relationships (Selection)      │                    │
│     │  • Validate constraints                  │                    │
│     │  • Use RAG for domain knowledge          │                    │
│     └────────────────────────────────────────┘                      │
│     Output: Entity-Relationship model (JSON)                         │
│                          ↓                                           │
│  4. LOGICAL DESIGN                                                   │
│     • Identify functional dependencies                               │
│     • Find primary keys (Armstrong's axioms)                         │
│     • Convert to relational schemas                                  │
│     • Normalize to 3NF                                               │
│     Output: Relational schemas with keys & constraints               │
│                          ↓                                           │
│  5. TEST & VALIDATE                                                  │
│     ┌─────────────────────────────────────────┐                      │
│     │ QAAgent → ExecutionAgent → ManagerAgent │                      │
│     └─────────────────────────────────────────┘                      │
│     • Generate test cases (INSERT/UPDATE/DELETE/QUERY)               │
│     • Validate schemas satisfy test cases                            │
│     • Report to Manager for acceptance                               │
│                          ↓                                           │
│  6. PHYSICAL DESIGN                                                  │
│     • Infer PostgreSQL data types                                    │
│     • Generate CREATE TABLE statements                               │
│     • Design indexes (PK, FK, search columns)                        │
│     • Execute on PostgreSQL                                          │
│     • Self-refine on errors (max 3 attempts)                         │
│     Output: Executable DDL statements                                │
│                          ↓                                           │
│  7. REPORT GENERATION                                                │
│     • Compile all outputs                                            │
│     • Format as Markdown document                                    │
│     • Include thought processes                                      │
│     Output: Technical Design Report                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Termination Conditions

```python
# Main team terminates on:
text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=15)
termination = text_mention_termination | max_messages_termination

# Nested conceptual team terminates on:
inner_termination = TextMentionTermination("Approve") | max_messages_termination
```

---

## File Structure Summary

```
Graduation_Project/
├── physical_design/
│   ├── agent_chat_physical.py   # Main orchestration
│   ├── user_prompt_english.py   # All agent prompts
│   ├── postgres_tools.py        # PostgreSQL tools
│   ├── mermaid_tools.py         # Mermaid generation
│   └── llm_tools.py             # LLM utilities
├── rag/
│   ├── base_rag.py              # Abstract retriever
│   ├── rag_config.py            # Domain detection
│   ├── rag_tools.py             # Agent tools
│   └── domains/
│       ├── healthcare/          # Healthcare domain (Ground Truth)
│       └── ecommerce/           # E-Commerce domain (Ground Truth)
├── shared/
│   └── normalization_utils.py   # 3NF algorithms
├── api/
│   └── app.py                   # FastAPI endpoint
├── llm_config.py                # LLM provider config
└── requirements.txt             # Dependencies
```

---

## Contributing

To add a new domain to the RAG system:

1. Create folder: `rag/domains/your_domain/`
2. Implement retriever extending `BaseRAGRetriever`
3. Add domain to `Domain` enum in `rag_config.py`
4. Add keywords to `detect_domain_from_text()`
5. Register in `rag/domains/__init__.py`

---

## License

Internal use - KilluaDB Project