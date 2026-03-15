"""
Text-to-SQL FastAPI Service
Uses the multi-agent system (Selector, Decomposer, Refiner) for SQL generation.
SQL execution is handled by the Go backend for security.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Text-to-SQL Agent Service",
    description="Generates SQL queries from natural language using multi-agent system (Selector → Decomposer → Refiner)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Go backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Go backend IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service (lazy - will be initialized on first request)
agent_service = None


def get_agent_service():
    """
    Get or initialize the agent service.
    
    Configuration priority:
    1. Environment variables (LLM_API_KEY, LLM_MODEL, LLM_API_BASE)
    2. Fallback to api_config.py defaults
    """
    global agent_service
    if agent_service is None:
        from agent_service import AgentService
        
        # Get from env vars, or pass None to fall back to api_config.py
        api_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or None
        model_name = os.getenv("LLM_MODEL") or None
        api_base = os.getenv("LLM_API_BASE") or None
        
        agent_service = AgentService(
            api_key=api_key,
            model_name=model_name,
            api_base=api_base
        )
        logger.info(f"AgentService initialized")
    
    return agent_service


# ============================================================================
# Request/Response Models
# ============================================================================

class DatabaseConnection(BaseModel):
    """Database connection details"""
    host: str = Field(..., description="Database host IP or hostname")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")


class GenerateSQLRequest(BaseModel):
    """Request to generate SQL from natural language"""
    question: str = Field(..., description="Natural language question", min_length=1)
    db_connection: DatabaseConnection = Field(..., description="Database connection for schema extraction")
    hint: Optional[str] = Field(default="", description="Optional hint/evidence to guide SQL generation")
    use_agents: bool = Field(default=True, description="Use multi-agent pipeline (True) or simple single-call (False)")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Show me all users who ordered more than 5 products",
                "db_connection": {
                    "host": "172.30.0.2",
                    "port": 5432,
                    "database": "user_db",
                    "user": "postgres",
                    "password": "secret"
                },
                "hint": "Join users with orders table",
                "use_agents": True
            }
        }


class GenerateSQLResponse(BaseModel):
    """Response containing generated SQL"""
    success: bool
    sql: Optional[str] = None
    error: Optional[str] = None
    tables_used: Optional[List[str]] = None
    mode: str = Field(default="agents", description="Generation mode: 'agents' or 'simple'")


class SchemaRequest(BaseModel):
    """Request to get database schema"""
    db_connection: DatabaseConnection


class SchemaResponse(BaseModel):
    """Response containing database schema"""
    success: bool
    schema: Optional[dict] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for Go backend to verify service is running"""
    return HealthResponse(
        status="healthy",
        service="text-to-sql-agents",
        version="2.0.0"
    )


@app.post("/api/v1/generate", response_model=GenerateSQLResponse, tags=["SQL Generation"])
async def generate_sql(request: GenerateSQLRequest):
    """
    Generate SQL from natural language question using multi-agent pipeline.
    
    The pipeline consists of:
    1. **Selector**: Identifies relevant tables and columns from the schema
    2. **Decomposer**: Breaks complex questions into sub-questions
    3. **Refiner**: Validates and fixes the generated SQL
    
    Set `use_agents=False` for faster simple generation (single LLM call).
    
    The Go backend should:
    1. Validate the generated SQL using existing security measures
    2. Execute the SQL against the user's database
    3. Log the query to history
    4. Return results to the user
    """
    logger.info(f"Generating SQL for: {request.question[:100]}...")
    
    try:
        service = get_agent_service()
    except RuntimeError as e:
        return GenerateSQLResponse(
            success=False,
            error=str(e),
            mode="error"
        )
    
    db_config = {
        "host": request.db_connection.host,
        "port": request.db_connection.port,
        "database": request.db_connection.database,
        "user": request.db_connection.user,
        "password": request.db_connection.password
    }
    
    try:
        if request.use_agents:
            # Use full multi-agent pipeline
            result = service.generate_sql_with_agents(
                question=request.question,
                db_config=db_config,
                hint=request.hint or ""
            )
            mode = "agents"
        else:
            # Use simple single-call generation
            result = service.generate_sql_simple(
                question=request.question,
                db_config=db_config,
                hint=request.hint or ""
            )
            mode = "simple"
        
        return GenerateSQLResponse(
            success=result["success"],
            sql=result.get("sql"),
            error=result.get("error"),
            tables_used=result.get("tables_used"),
            mode=mode
        )
        
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        return GenerateSQLResponse(
            success=False,
            error="Failed to generate SQL. Please try rephrasing your question.",
            mode="error"
        )


@app.post("/api/v1/generate/simple", response_model=GenerateSQLResponse, tags=["SQL Generation"])
async def generate_sql_simple(request: GenerateSQLRequest):
    """
    Generate SQL using simple single-LLM-call approach.
    Faster but less sophisticated than the multi-agent pipeline.
    
    Use this for:
    - Simple queries
    - When speed is more important than accuracy
    - Testing/debugging
    """
    logger.info(f"Generating SQL (simple mode) for: {request.question[:100]}...")
    
    try:
        service = get_agent_service()
    except RuntimeError as e:
        return GenerateSQLResponse(
            success=False,
            error=str(e),
            mode="error"
        )
    
    db_config = {
        "host": request.db_connection.host,
        "port": request.db_connection.port,
        "database": request.db_connection.database,
        "user": request.db_connection.user,
        "password": request.db_connection.password
    }
    
    try:
        result = service.generate_sql_simple(
            question=request.question,
            db_config=db_config,
            hint=request.hint or ""
        )
        
        return GenerateSQLResponse(
            success=result["success"],
            sql=result.get("sql"),
            error=result.get("error"),
            tables_used=result.get("tables_used"),
            mode="simple"
        )
        
    except Exception as e:
        logger.error(f"Simple SQL generation failed: {e}")
        return GenerateSQLResponse(
            success=False,
            error="Failed to generate SQL.",
            mode="error"
        )


@app.post("/api/v1/schema", response_model=SchemaResponse, tags=["Schema"])
async def get_schema(request: SchemaRequest):
    """
    Get database schema (useful for debugging and UI display).
    
    Returns table names, column information, primary keys, and foreign key relationships.
    """
    try:
        service = get_agent_service()
    except RuntimeError as e:
        return SchemaResponse(success=False, error=str(e))
    
    db_config = {
        "host": request.db_connection.host,
        "port": request.db_connection.port,
        "database": request.db_connection.database,
        "user": request.db_connection.user,
        "password": request.db_connection.password
    }
    
    try:
        schema = service.get_schema_from_db(db_config)
        return SchemaResponse(success=True, schema=schema)
    except Exception as e:
        logger.error(f"Schema extraction failed: {e}")
        return SchemaResponse(
            success=False,
            error="Failed to extract database schema. Please check connection details."
        )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Text-to-SQL Agent Service starting...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY environment variable not set!")
    else:
        logger.info("GROQ_API_KEY configured")
    
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    logger.info(f"LLM Model: {model}")
    logger.info("Service ready to accept requests")
    logger.info("Pipeline: Selector → Decomposer → Refiner")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Text-to-SQL Agent Service shutting down...")


# ============================================================================
# Run with Uvicorn
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5001")),
        reload=True,
        log_level="info"
    )
