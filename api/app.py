"""
SchemaAgent FastAPI Application

Pure HTTP API for database schema generation.
Uses LLM to generate both Mermaid diagrams and JSON schema.
"""
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from physical_design.agent_chat_physical import main as agent_main
from physical_design.llm_tools import (
    extract_conceptual_design,
    extract_mermaid_from_output,
    extract_ddl_from_output,
    generate_mermaid_er,
    generate_json_schema,
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
    db_schema: Optional[Dict[str, Any]] = Field(None, description="JSON representation of the database schema")
    full_report: Optional[str] = Field(None, description="Full design report in markdown")
    ddl: Optional[str] = Field(None, description="DDL statements for PostgreSQL")
    generation_time: Optional[float] = Field(None, description="Time taken in seconds")



@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SchemaAgent API",
        "version": "1.0.0",
        "description": "Automated Relational Database Design System",
        "endpoints": {
            "POST /schema/generate": "Generate database schema from requirements",
            "GET /health": "Health check endpoint",
            # "GET /models": "List available models"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# @app.get("/models")
# async def get_models():
#     """Get list of available LLM models."""
#     return {"models": list_available_models()}


@app.post("/schema/generate", response_model=SchemaGenerateResponse)
async def generate_schema(request: SchemaGenerateRequest):
    """
    Generate database schema from natural language requirements.
    
    Uses the multi-agent system to:
    1. Analyze requirements
    2. Design conceptual model (entities and relationships)
    3. Design logical model (normalized tables)
    4. Design physical model (DDL statements for PostgreSQL)
    5. Generate Mermaid ER diagram
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
        
        # Extract conceptual design
        conceptual_design = extract_conceptual_design(output_string)
        
       
        mmd_content, _ = generate_mermaid_er(conceptual_design, model_name=model_name)
        
        
        # if not mmd_content:
        #     mmd_content = extract_mermaid_from_output(output_string)
        
        # Extract DDL statements
        ddl_statements = extract_ddl_from_output(output_string)
        
        
        schema_json = generate_json_schema(conceptual_design, ddl_statements, model_name=model_name)
        
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        return SchemaGenerateResponse(
            success=True,
            message="Schema generated successfully",
            error=None,
            mmd=mmd_content,
            # mmd_file_path=mmd_file_path,
            db_schema=schema_json,
            full_report=output_string,
            ddl=ddl_statements,
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
            mmd_file_path=None,
            db_schema=None,
            full_report=None,
            ddl=None,
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
