# KilluaDB API

**Base URL:** `http://localhost:8080`

---


## Endpoints

### `GET /health`
```bash
curl http://localhost:8080/health
```

### `POST /schema/generate`
Waits for all agents to finish and returns everything at once.
```bash
curl -X POST http://localhost:8080/schema/generate \
  -H "Content-Type: application/json" \
  -d '{"requirement_text": "A university needs a course selection system", "model_name": "deepseek", "database_name": "uni_db"}'
```
Returns: `mmd` (Mermaid diagram), `db_schema` (JSON tables), `ddl` (PostgreSQL DDL), `full_report`, `generation_time`.

### `POST /schema/generate/stream`
Same as above but streams each agent's output live as Server-Sent Events. Use this when you want to show progress to the user.
```bash
curl -N -X POST http://localhost:8080/schema/generate/stream \
  -H "Content-Type: application/json" \
  -d '{"requirement_text": "A university needs a course selection system", "model_name": "deepseek"}'
```

#### Streaming

The stream sends one JSON event per line in SSE format:
```
data: {"type": "phase",         "phase": "logical_design",  "status": "start"}
data: {"type": "agent_message", "phase": "logical_design",  "agent": "ManagerAgent", "content": "..."}
data: {"type": "tool_call",     "phase": "logical_design",  "agent": "ConceptualDesignerAgent", "content": "..."}
data: {"type": "tool_result",   "phase": "logical_design",  "agent": "ConceptualDesignerAgent", "content": "..."}
data: {"type": "agent_message", "phase": "logical_design",  "agent": "LogicalDesignerAgent", "content": "..."}
data: {"type": "phase",         "phase": "logical_design",  "status": "complete"}
data: {"type": "mermaid",       "content": "erDiagram\n  Student ||--o{ Enrollment : takes\n  ...", "valid": true}
data: {"type": "phase",         "phase": "physical_design", "status": "start"}
data: {"type": "agent_message", "phase": "physical_design", "agent": "PhysicalDesignerAgent", "content": "CREATE TABLE ..."}
data: {"type": "phase",         "phase": "physical_design", "status": "complete"}
data: {"type": "phase",         "phase": "report",          "status": "start"}
data: {"type": "agent_message", "phase": "report",          "agent": "ReportAgent", "content": "# Final Report ..."}
data: {"type": "phase",         "phase": "report",          "status": "complete"}
data: {"type": "done",          "message": "Schema generation complete"}
data: [DONE]
```

Phases in order: `logical_design` → `physical_design` → `report`.

#### What each event carries

| `type` | Fields | Store? |
|---|---|---|
| `phase` | `phase`, `status` (start/complete/refinement), `message` | Track for progress UI |
| `agent_message` | `agent`, `phase`, `content` | Yes — main output to display and save |
| `mermaid` | `content` (full Mermaid source), `valid` (boolean) | **Yes — this is your ER diagram** |
| `tool_call` | `agent`, `phase`, `content` | Optional — useful for a debug panel |
| `tool_result` | `agent`, `phase`, `content` | Optional |
| `thinking` | `agent`, `phase`, `content` | Optional — show as "thinking…" |
| `error` | `message`, `detail` (stack trace) | Yes — show to user |
| `done` | `message` | Yes — trigger completed state in UI |

#### Where to get each output

| Output | How |
|---|---|
| **Mermaid / ER diagram** | `type == "mermaid"` → `event.content` |
| **PostgreSQL DDL** | `type == "agent_message"` and `agent == "PhysicalDesignerAgent"` and `phase == "physical_design"` → last such `content` |
| **Final report** | `type == "agent_message"` and `agent == "ReportAgent"` → `content` |


### `POST /schema/generate/stream/mock`
Same SSE format but returns fake pre-scripted events — no API key needed. Use this to test your integration.
```bash
curl -N -X POST http://localhost:8080/schema/generate/stream/mock \
  -H "Content-Type: application/json" \
  -d '{"requirement_text": "any text", "model_name": "deepseek"}'
```

### `POST /mermaid/validate`
```bash
curl -X POST http://localhost:8080/mermaid/validate \
  -H "Content-Type: application/json" \
  -d '{"mermaid_code": "erDiagram\n  Student ||--o{ Enrollment : takes"}'
```

### `GET /postgres/test` (Dokcer compose)
```bash
curl http://localhost:8080/postgres/test
```

### `POST /postgres/execute` (Dokcer compose)
```bash
curl -X POST http://localhost:8080/postgres/execute \
  -H "Content-Type: application/json" \
  -d '{"ddl_statements": "CREATE TABLE t (id SERIAL PRIMARY KEY);", "database_name": "uni_db"}'
```


