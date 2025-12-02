"""
Main FastAPI Backend for MCP Tool-Calling Agent
Provides REST API endpoints for agent interaction
"""
import json
import logging
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our agent and tools
from agent import mcp_agent
from tool_manager import tool_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Tool-Calling Agent API",
    description="AI Agent with Tool Calling capabilities using Model Context Protocol style",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Pydantic models for request/response validation
class AgentQuery(BaseModel):
    query: str = Field(..., description="The user query to process")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    
class AgentResponse(BaseModel):
    query: str
    final_answer: str
    tools_used: List[str]
    steps: List[str]
    raw_outputs: List[Dict[str, Any]]
    execution_time_seconds: float
    success: bool
    timestamp: str
    context: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agent_info: Dict[str, Any]
    
class ToolSchema(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

# Serve static files (frontend)
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page"""
    try:
        frontend_path = Path("frontend/index.html")
        if frontend_path.exists():
            return HTMLResponse(content=frontend_path.read_text(), status_code=200)
        else:
            return HTMLResponse(content="""
                <html>
                    <body>
                        <h1>MCP Tool-Calling Agent</h1>
                        <p>Frontend not found. Please ensure frontend files are in the frontend directory.</p>
                        <p>API Documentation: <a href="/docs">/docs</a></p>
                    </body>
                </html>
            """)
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

@app.post("/agent", response_model=AgentResponse)
async def process_agent_query(query_data: AgentQuery) -> AgentResponse:
    """
    Process a query using the MCP agent
    
    This endpoint accepts a user query and returns a structured response
    with the agent's answer, execution steps, and tool outputs.
    """
    try:
        logger.info(f"Received query: {query_data.query}")
        
        # Process query using the agent
        response = await mcp_agent.process_query(
            query=query_data.query,
            context=query_data.context
        )
        
        return AgentResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing agent query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.post("/upload-pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a PDF file for processing
    
    This endpoint accepts PDF uploads and stores them for use with
    the PDF summarizer tool.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded PDF: {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "file_path": str(file_path),
            "size_bytes": file_path.stat().st_size,
            "upload_time": datetime.now().isoformat(),
            "message": "PDF uploaded successfully. You can now reference it in queries."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@app.get("/tools")
async def get_tools() -> Dict[str, Any]:
    """
    Get information about available tools
    
    Returns a list of all available tools with their schemas
    and current status.
    """
    try:
        tools = tool_manager.get_available_tools()
        stats = tool_manager.get_statistics()
        
        return {
            "success": True,
            "tools": tools,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving tools: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    
    Returns the current status of the agent and all its components.
    """
    try:
        health_info = mcp_agent.health_check()
        agent_info = mcp_agent.get_agent_info()
        
        status = "healthy" if health_info.get("agent_status") == "healthy" else "unhealthy"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            agent_info={
                **health_info,
                **agent_info
            }
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return HealthResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            agent_info={"error": str(e)}
        )

@app.get("/agent/suggestions")
async def get_tool_suggestions(query: str) -> Dict[str, Any]:
    """
    Get tool suggestions for a query
    
    This endpoint analyzes a query and suggests which tools
    might be appropriate without executing them.
    """
    try:
        if not query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query parameter is required"
            )
        
        suggestions = mcp_agent.get_tool_suggestions(query)
        available_tools = mcp_agent.get_available_tools()
        
        # Get detailed info for suggested tools
        suggested_tool_info = []
        for tool_name in suggestions:
            for tool in available_tools:
                if tool['name'] == tool_name:
                    suggested_tool_info.append(tool)
                    break
        
        return {
            "success": True,
            "query": query,
            "suggested_tools": suggestions,
            "tool_details": suggested_tool_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting suggestions: {str(e)}"
        )

@app.get("/uploads")
async def list_uploads() -> Dict[str, Any]:
    """
    List uploaded files
    
    Returns a list of all uploaded PDF files available for processing.
    """
    try:
        uploads = []
        
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.glob("*.pdf"):
                stat_info = file_path.stat()
                uploads.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": stat_info.st_size,
                    "size_human": _format_bytes(stat_info.st_size),
                    "upload_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                })
        
        return {
            "success": True,
            "uploads": uploads,
            "total_files": len(uploads),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing uploads: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing uploads: {str(e)}"
        )

@app.delete("/uploads/{filename}")
async def delete_upload(filename: str) -> Dict[str, Any]:
    """
    Delete an uploaded file
    
    Removes a specific uploaded PDF file from the server.
    """
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        file_path.unlink()
        logger.info(f"Deleted upload: {filename}")
        
        return {
            "success": True,
            "message": f"File {filename} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )

@app.get("/agent/info")
async def get_agent_info() -> Dict[str, Any]:
    """
    Get detailed information about the agent
    
    Returns comprehensive information about the agent's capabilities,
    configuration, and current status.
    """
    try:
        info = mcp_agent.get_agent_info()
        return {
            "success": True,
            **info
        }
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting agent info: {str(e)}"
        )

# Utility functions
def _format_bytes(bytes_value: int) -> str:
    """Convert bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_value >= 1024 and i < len(size_names) - 1:
        bytes_value /= 1024.0
        i += 1
    
    return f"{bytes_value:.1f} {size_names[i]}"

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Resource not found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting MCP Tool-Calling Agent API")
    logger.info(f"Available tools: {list(tool_manager.tools.keys())}")
    
    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    logger.info("MCP Tool-Calling Agent API started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when shutting down"""
    logger.info("Shutting down MCP Tool-Calling Agent API")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )