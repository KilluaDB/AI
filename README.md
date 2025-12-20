# SchemaAgent API

A REST API for automated database schema generation using Multi-Agent AI.


## Endpoints


### 1. `GET /health` - Health Check

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-20T10:30:00.000000"
}
```

---

### 2. `POST /schema/generate` - Generate Schema

Generates a complete database schema from natural language requirements.

#### Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `requirement_text` | `string` | ✅ Yes | - | Natural language description of database requirements |
| `model_name` | `string` | No | `"deepseek"` | LLM model to use (`deepseek`, `gpt4`, `chatgpt`, etc.) |
| `database_name` | `string` | No | `"schema_db"` | Name of the database to create |

**Example Request:**
```json
{
  "requirement_text": "A university needs a student course selection management system...",
  "model_name": "deepseek",
  "database_name": "university_db"
}
```

#### Response

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the generation was successful |
| `message` | `string` | Status message |
| `error` | `string \| null` | Error message if generation failed |
| `mmd` | `string \| null` | Mermaid ER diagram code |
| `db_schema` | `object \| null` | JSON representation of the database schema |
| `full_report` | `string \| null` | Full design report in markdown |
| `ddl` | `string \| null` | DDL statements for PostgreSQL |
| `generation_time` | `float \| null` | Time taken in seconds |

**Example Response:**
```json
{
  "success": true,
  "message": "Schema generated successfully",
  "error": null,
  "mmd": "erDiagram\n    Student {...}",
  "db_schema": {
    "entities": [...],
    "relationships": [...],
    "tables": [...],
    "ddl_statements": "...",
    "index_statements": "..."
  },
  "full_report": "# Technical Design Report...",
  "ddl": "CREATE TABLE Student (...);",
  "generation_time": 45.23
}
```

---

## Quick Start

### Using cURL

```bash
curl -X POST "http://localhost:8080/schema/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement_text": "A university needs a student course selection management system to maintain and track students course selection information. Students have information such as student ID, name, age. Each student can take multiple courses. Each course has information such as course number, course name, credits, lecturer and class time.",
    "model_name": "deepseek",
    "database_name": "university_db"
  }'
```