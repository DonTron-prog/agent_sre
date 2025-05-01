"""
FastAPI application for the RAG API.
"""

import time
from typing import Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from code_rag import __version__
from code_rag.api.routes import router
from code_rag.config import get_settings
from code_rag.utils.helpers import logger


# Create the FastAPI application
app = FastAPI(
    title="Code RAG API",
    description="API for retrieving and generating solutions to code errors",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log requests and responses.
    
    Args:
        request: The incoming request
        call_next: The next middleware or endpoint handler
        
    Returns:
        Response: The response
    """
    # Generate a unique request ID
    request_id = str(time.time())
    
    # Log the request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    # Process the request
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Log the response
    logger.info(f"Response {request_id}: {response.status_code} ({process_time:.2f}ms)")
    
    # Add processing time header
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint.
    
    Returns:
        Dict[str, str]: Welcome message
    """
    return {
        "message": "Welcome to the Code RAG API",
        "version": __version__,
        "docs": "/docs",
    }


# Include the API routes
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    # This is for development only
    import uvicorn
    
    uvicorn.run(
        "code_rag.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )