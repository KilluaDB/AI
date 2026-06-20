"""
SchemaAgent FastAPI Application

Pure HTTP API for database schema generation.
Uses LLM to generate both Mermaid diagrams and JSON schema.
"""
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from design.agent_chat_physical import main as agent_main, stream_main
from design.llm_tools import (
    extract_conceptual_design,
    extract_mermaid_from_output,
    extract_ddl_from_output,
    generate_mermaid_er,
    generate_mermaid_from_schema,
    generate_json_schema,
    extract_json_from_output,
    extract_conceptual_schema_json,
    extract_logical_schema_json,
)
from design.mermaid_tools import (
    generate_mermaid_from_conceptual,
    generate_mermaid_from_logical,
    validate_mermaid_syntax,
    validate_mermaid_with_cli,
    render_mermaid_to_svg,
    conceptual_to_mermaid,
)
from design.postgres_tools import (
    test_postgres_connection,
    execute_ddl_statements,
    validate_ddl_syntax,
    infer_and_generate_ddl,
    PostgreSQLConnection,
)
from llm_config import list_available_models

# Initialize FastAPI app
app = FastAPI(
    title="KilluaDB SchemaGenerator",
    description="Automated Relational Database Design System using Multi-Agent AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SchemaGenerateRequest(BaseModel):
    """Request model for schema generation"""
    requirement_text: str = Field(
        ...,
        description="Natural language description of database requirements",
        example="A university needs a student course selection management system."
    )
    model_name: str = Field(
        default="deepseek",
        description="LLM model to use for generation",
        example="deepseek"
    )
    database_name: str = Field(
        default="schema_db",
        description="Name of the database to create",
        example="university_db"
    )


class SchemaGenerateResponse(BaseModel):
    """Response model for schema generation"""
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    mmd: Optional[str] = Field(None, description="Mermaid ER diagram code")
    mmd_valid: Optional[bool] = Field(None, description="Whether the Mermaid diagram is valid")
    db_schema: Optional[Dict[str, Any]] = Field(None, description="JSON representation of the database schema")
    full_report: Optional[str] = Field(None, description="Full design report in markdown")
    ddl: Optional[str] = Field(None, description="DDL statements for PostgreSQL")
    index_statements: Optional[str] = Field(None, description="Index creation statements")
    generation_time: Optional[float] = Field(None, description="Time taken in seconds")


class MermaidValidateRequest(BaseModel):
    """Request model for Mermaid validation"""
    mermaid_code: str = Field(..., description="Mermaid diagram code to validate")


class MermaidValidateResponse(BaseModel):
    """Response model for Mermaid validation"""
    valid: bool = Field(..., description="Whether the Mermaid syntax is valid")
    errors: Optional[List[str]] = Field(None, description="List of validation errors")
    message: str = Field(..., description="Validation message")


class PostgresTestResponse(BaseModel):
    """Response model for PostgreSQL connection test"""
    connected: bool = Field(..., description="Whether the connection was successful")
    version: Optional[str] = Field(None, description="PostgreSQL version")
    database: Optional[str] = Field(None, description="Connected database name")
    error: Optional[str] = Field(None, description="Error message if connection failed")


class DDLExecuteRequest(BaseModel):
    """Request model for DDL execution"""
    ddl_statements: str = Field(..., description="DDL statements to execute")
    database_name: str = Field(default="schema_agent", description="Target database name")


class DDLExecuteResponse(BaseModel):
    """Response model for DDL execution"""
    success: bool = Field(..., description="Whether all statements executed successfully")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Execution results per statement")
    summary: Optional[str] = Field(None, description="Execution summary")



@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SchemaAgent API",
        "version": "1.0.0",
        "description": "Automated Relational Database Design System",
        "endpoints": {
            "POST /schema/generate": "Generate database schema from requirements (full response)",
            "POST /schema/generate/stream": "Stream schema generation with real-time agent thinking (SSE)",
            "POST /mermaid/validate": "Validate Mermaid diagram syntax",
            "GET /postgres/test": "Test PostgreSQL connection",
            "POST /postgres/execute": "Execute DDL statements on PostgreSQL",
            "GET /health": "Health check endpoint",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/mermaid/validate", response_model=MermaidValidateResponse)
async def validate_mermaid(request: MermaidValidateRequest):
    """
    Validate Mermaid diagram syntax.
    
    This endpoint validates the syntax of a Mermaid diagram without rendering it.
    """
    is_valid, errors = validate_mermaid_syntax(request.mermaid_code)
    
    return MermaidValidateResponse(
        valid=is_valid,
        errors=errors if not is_valid else None,
        message="Mermaid syntax is valid" if is_valid else f"Found {len(errors)} validation errors"
    )


@app.get("/postgres/test", response_model=PostgresTestResponse)
async def test_postgres():
    """
    Test PostgreSQL database connection.
    
    Uses environment variables for connection parameters:
    - POSTGRES_HOST (default: localhost)
    - POSTGRES_PORT (default: 5432)
    - POSTGRES_USER (default: postgres)
    - POSTGRES_PASSWORD (default: postgres)
    - POSTGRES_DATABASE (default: schema_agent)
    """
    import asyncio
    result = await test_postgres_connection()
    
    return PostgresTestResponse(
        connected=result.get("connected", False),
        version=result.get("version"),
        database=result.get("database"),
        error=result.get("error")
    )


@app.post("/postgres/execute", response_model=DDLExecuteResponse)
async def execute_ddl(request: DDLExecuteRequest):
    """
    Execute DDL statements on PostgreSQL database.
    
    This endpoint executes the provided DDL statements and returns the results.
    """
    import asyncio
    result = await execute_ddl_statements(request.ddl_statements, request.database_name)
    
    return DDLExecuteResponse(
        success=result.get("success", False),
        results=result.get("results"),
        summary=result.get("summary")
    )


# @app.get("/models")
# async def get_models():
#     """Get list of available LLM models."""
#     return {"models": list_available_models()}


@app.post("/schema/generate/stream")
async def generate_schema_stream(request: SchemaGenerateRequest):
    """
    Stream schema generation with real-time agent thinking output (Server-Sent Events).

    Each SSE event is a JSON object on a ``data:`` line followed by two newlines.
    Possible event shapes:

    - Phase marker:
        {"type": "phase", "phase": "<name>", "status": "start"|"complete"|"refinement",
         "message": "...", "attempt": <int>}

    - Agent text message:
        {"type": "agent_message", "agent": "<AgentName>", "phase": "<name>", "content": "..."}

    - Tool call:
        {"type": "tool_call", "agent": "<AgentName>", "phase": "<name>", "content": "..."}

    - Tool result:
        {"type": "tool_result", "agent": "<AgentName>", "phase": "<name>", "content": "..."}

    - Internal reasoning (if model exposes it):
        {"type": "thinking", "agent": "<AgentName>", "phase": "<name>", "content": "..."}

    - Error:
        {"type": "error", "message": "...", "detail": "..."}

    - Stream end sentinel:
        {"type": "done", "message": "Schema generation complete"}

    After the final JSON event the server sends ``data: [DONE]`` (OpenAI-compatible sentinel).
    """
    available_models = list_available_models()
    if request.model_name and request.model_name not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{request.model_name}'. Available: {available_models}"
        )

    model_name = request.model_name or "deepseek"

    agent_parser = argparse.ArgumentParser()
    args = agent_parser.parse_args([])
    args.model_name = model_name
    args.database_name = request.database_name
    args.requirement_text = request.requirement_text

    async def event_generator():
        try:
            async for event in stream_main(args):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            import traceback
            yield (
                f"data: {json.dumps({'type': 'error', 'message': str(exc), 'detail': traceback.format_exc()})}\n\n"
            )
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/schema/generate/stream/mock")
async def generate_schema_stream_mock(request: SchemaGenerateRequest):
    """
    Mock streaming endpoint — same SSE format as /schema/generate/stream but uses
    pre-scripted fake agent messages. Use this to test the stream format without
    real LLM API keys.
    """
    import asyncio

    req_text = request.requirement_text

    mock_events = [
        {"type": "phase",         "phase": "logical_design",  "status": "start",    "message": "Starting logical schema design"},
        {"type": "agent_message", "phase": "logical_design",  "agent": "ManagerAgent",
         "content": f"Analyzing requirement: \"{req_text[:80]}...\"\nI will decompose this into entities and relationships."},
        {"type": "tool_call",     "phase": "logical_design",  "agent": "ConceptualDesignerAgent",
         "content": "[Tool: get_similar_examples] {\"requirement\": \"" + req_text[:60] + "\"}"},
        {"type": "tool_result",   "phase": "logical_design",  "agent": "ConceptualDesignerAgent",
         "content": "[Result]: 3 similar examples retrieved (top domain: education)"},
        {"type": "agent_message", "phase": "logical_design",  "agent": "ConceptualDesignerAgent",
         "content": '{"question":"","output":{"Entity Set":{"Student":{"Attributes":["student_id","name","age"],"Primary Key":["student_id"]},"Course":{"Attributes":["course_id","name","credits","lecturer"],"Primary Key":["course_id"]}},"Relationship Set":{"Enrollment":{"Entities":["Student","Course"],"Cardinality":"M:N","Attributes":["enroll_date"]}}}}'},
        {"type": "agent_message", "phase": "logical_design",  "agent": "ConceptualReviewerAgent",
         "content": "The conceptual model correctly captures all entities and relationships. Approve"},
        {"type": "agent_message", "phase": "logical_design",  "agent": "LogicalDesignerAgent",
         "content": '{"tables":[{"name":"Student","columns":["student_id SERIAL","name VARCHAR(100)","age INT"],"primary_key":["student_id"]},{"name":"Course","columns":["course_id SERIAL","name VARCHAR(100)","credits INT","lecturer VARCHAR(100)"],"primary_key":["course_id"]},{"name":"Enrollment","columns":["student_id INT","course_id INT","enroll_date DATE"],"primary_key":["student_id","course_id"],"foreign_keys":["student_id -> Student","course_id -> Course"]}]}'},
        {"type": "agent_message", "phase": "logical_design",  "agent": "QAAgent",
         "content": "Test cases:\n1. INSERT INTO Student VALUES (1,'Alice',20)\n2. INSERT INTO Course VALUES (1,'Math',3,'Prof. Smith')\n3. INSERT INTO Enrollment VALUES (1,1,'2024-01-15')\n4. SELECT * FROM Student WHERE student_id=1"},
        {"type": "agent_message", "phase": "logical_design",  "agent": "ExecutionAgent",
         "content": "All 4 test cases pass. Schema is logically consistent. TERMINATE"},
        {"type": "phase",         "phase": "logical_design",  "status": "complete"},
        {"type": "mermaid",
         "content": "erDiagram\n    Student {\n        int student_id PK\n        string name\n        int age\n    }\n    Course {\n        int course_id PK\n        string name\n        int credits\n        string lecturer\n    }\n    Enrollment {\n        int student_id FK\n        int course_id FK\n        date enroll_date\n    }\n    Student ||--o{ Enrollment : takes\n    Course ||--o{ Enrollment : has",
         "valid": True},
        {"type": "phase",         "phase": "physical_design", "status": "start",    "message": "Starting physical DDL generation"},
        {"type": "agent_message", "phase": "physical_design", "agent": "PhysicalDesignerAgent",
         "content": "Generating PostgreSQL DDL based on the logical schema..."},
        {"type": "tool_call",     "phase": "physical_design", "agent": "PhysicalDesignerAgent",
         "content": "[Tool: validate_ddl_syntax] CREATE TABLE Student (student_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, age INT);"},
        {"type": "tool_result",   "phase": "physical_design", "agent": "PhysicalDesignerAgent",
         "content": "[Result]: DDL syntax valid"},
        {"type": "agent_message", "phase": "physical_design", "agent": "PhysicalDesignerAgent",
         "content": "```sql\nCREATE TABLE Student (\n    student_id SERIAL PRIMARY KEY,\n    name VARCHAR(100) NOT NULL,\n    age INT\n);\n\nCREATE TABLE Course (\n    course_id SERIAL PRIMARY KEY,\n    name VARCHAR(100) NOT NULL,\n    credits INT NOT NULL,\n    lecturer VARCHAR(100)\n);\n\nCREATE TABLE Enrollment (\n    student_id INT NOT NULL,\n    course_id INT NOT NULL,\n    enroll_date DATE,\n    PRIMARY KEY (student_id, course_id),\n    FOREIGN KEY (student_id) REFERENCES Student(student_id),\n    FOREIGN KEY (course_id) REFERENCES Course(course_id)\n);\n```"},
        {"type": "phase",         "phase": "physical_design", "status": "complete"},
        {"type": "phase",         "phase": "report",          "status": "start",    "message": "Generating final report"},
        {"type": "agent_message", "phase": "report",          "agent": "ReportAgent",
         "content": f"# Database Design Report\n\n## Requirement\n{req_text[:120]}...\n\n## Entities\n- **Student**: student_id, name, age\n- **Course**: course_id, name, credits, lecturer\n- **Enrollment**: student_id, course_id, enroll_date\n\n## DDL\nSee physical design output above.\n\n## Notes\n```sql\nCREATE DATABASE {request.database_name};\n```"},
        {"type": "phase",         "phase": "report",          "status": "complete"},
        {"type": "done",          "message": "Schema generation complete"},
    ]

    async def event_generator():
        for event in mock_events:
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.3)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/schema/generate", response_model=SchemaGenerateResponse)
async def generate_schema(request: SchemaGenerateRequest):
    """
    Generate database schema from natural language requirements.
    
    Uses the multi-agent system to:
    1. Analyze requirements
    2. Design conceptual model (entities and relationships)
    3. Design logical model (normalized tables)
    4. Design physical model (DDL statements for PostgreSQL)
    5. Generate Mermaid ER diagram (by parsing, not LLM - faster and more reliable)
    6. Generate JSON schema representation
    
    Returns:
        SchemaGenerateResponse with mmd diagram, JSON schema, DDL, and full report
    """
    start_time = datetime.now()
    
    try:
        # Validate model name
        available_models = list_available_models()
        if request.model_name and request.model_name not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model name '{request.model_name}'. Available models: {available_models}"
            )
        
        model_name = request.model_name if request.model_name else "deepseek"
        
        # Create args object for the agent
        agent_parser = argparse.ArgumentParser()
        agent_parser.add_argument('--model_name', default=model_name)
        agent_parser.add_argument('--database_name', default=request.database_name)
        agent_parser.add_argument('--requirement_text', default=request.requirement_text)
        args = agent_parser.parse_args([])
        args.model_name = model_name
        args.database_name = request.database_name
        args.requirement_text = request.requirement_text
        
        # Run the agent system
        print(f"Starting schema generation with model: {model_name}")
        output_string = await agent_main(args)
        print("Agent output received")
        
        # Extract conceptual design
        conceptual_design = extract_conceptual_design(output_string)
        
        # Try parsing-based Mermaid generation first (faster, more reliable)
        mmd_content = None
        mmd_valid = None
        
        # Extract conceptual schema JSON for parsing-based generation
        conceptual_schema = extract_conceptual_schema_json(output_string)
        if conceptual_schema:
            print("Using parsing-based Mermaid generation")
            mmd_content = generate_mermaid_from_conceptual(conceptual_schema)
            if mmd_content:
                is_valid, errors = validate_mermaid_syntax(mmd_content)
                mmd_valid = is_valid
                if not is_valid:
                    print(f"Mermaid validation warnings: {errors}")
        
        # Fallback to LLM-based generation if parsing failed
        if not mmd_content and conceptual_design:
            print("Fallback to LLM-based Mermaid generation")
            mmd_content, _ = generate_mermaid_er(conceptual_design, model_name=model_name)
            if mmd_content:
                is_valid, errors = validate_mermaid_syntax(mmd_content)
                mmd_valid = is_valid

        # Extract DDL statements
        ddl_statements = extract_ddl_from_output(output_string)
        
        # Extract logical schema for JSON output
        logical_schema = extract_logical_schema_json(output_string)
        
        # Generate JSON schema (use logical schema if available, otherwise use LLM)
        if logical_schema:
            schema_json = {"tables": logical_schema}
        else:
            schema_json = generate_json_schema(conceptual_design, ddl_statements, model_name=model_name)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        return SchemaGenerateResponse(
            success=True,
            message="Schema generated successfully",
            error=None,
            mmd=mmd_content,
            mmd_valid=mmd_valid,
            db_schema=schema_json,
            full_report=output_string,
            ddl=ddl_statements,
            index_statements=None,  # Will be included in ddl if generated by physical agent
            generation_time=generation_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error during schema generation: {error_detail}")
        
        return SchemaGenerateResponse(
            success=False,
            message="Schema generation failed",
            error=str(e),
            mmd=None,
            mmd_valid=None,
            db_schema=None,
            full_report=None,
            ddl=None,
            index_statements=None,
            generation_time=generation_time
        )


# ============== Main Entry Point ==============

def start_server(host: str = "0.0.0.0", port: int = 8080):
    """Start the FastAPI server programmatically"""
    print(f"Starting SchemaAgent API server on http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SchemaAgent API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    start_server(host=args.host, port=args.port)
