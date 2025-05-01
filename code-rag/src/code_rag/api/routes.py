"""
API routes for the REST API.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from code_rag import __version__
from code_rag.api.models import (
    ErrorResponse,
    HealthCheckResponse,
    QueryRequest,
    QueryResponse,
    ReferenceItem,
    ResponseMetadata,
)
from code_rag.config import Settings, get_settings
from code_rag.core.rag import CodeRAG
from code_rag.utils.helpers import logger


router = APIRouter()


def get_rag_client(settings: Settings = Depends(get_settings)) -> CodeRAG:
    """
    Dependency to get a RAG client.
    
    Args:
        settings: Settings instance
        
    Returns:
        CodeRAG: RAG client instance
    """
    return CodeRAG(settings=settings)


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    rag_client: CodeRAG = Depends(get_rag_client),
) -> Dict[str, Any]:
    """
    Query the RAG system with an error message.
    
    Args:
        request: Query request
        rag_client: RAG client instance
        
    Returns:
        Dict[str, Any]: Query response
    """
    try:
        # Handle streaming separately
        if request.stream:
            return await handle_streaming_response(request, rag_client)
        
        # Process the query
        start_time = time.time()
        result = rag_client.query(
            error_message=request.error_message,
            num_results=request.num_results,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        end_time = time.time()
        
        # Format references as ReferenceItem objects
        references = [
            {
                "id": ref.get("id", ""),
                "error": ref.get("error", ""),
                "solution": ref.get("solution", ""),
                "similarity_score": ref.get("similarity_score", 0.0),
                "metadata": ref.get("metadata", {}),
            }
            for ref in result.get("references", [])
        ]
        
        # Get metadata
        metadata = result.get("metadata", {})
        if "processing_time_ms" not in metadata:
            metadata["processing_time_ms"] = int((end_time - start_time) * 1000)
        
        # Format the response
        response = {
            "solution": result.get("solution", "No solution generated."),
            "references": references,
            "metadata": {
                "model_used": metadata.get("model_used", "unknown"),
                "tokens_used": metadata.get("tokens_used", 0),
                "processing_time_ms": metadata.get("processing_time_ms", 0),
                "num_references": len(references),
            },
        }
        
        # Add error if present
        if "error" in result:
            response["error"] = result["error"]
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}",
        )


async def handle_streaming_response(
    request: QueryRequest,
    rag_client: CodeRAG,
) -> StreamingResponse:
    """
    Handle streaming response for the query endpoint.
    
    Args:
        request: Query request
        rag_client: RAG client instance
        
    Returns:
        StreamingResponse: Streaming response
    """
    # This is a placeholder - implementing real-time streaming with OpenRouter
    # would require additional work with SSE or WebSockets
    async def stream_generator():
        result = rag_client.query(
            error_message=request.error_message,
            num_results=request.num_results,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        
        # Yield the solution in chunks
        solution = result.get("solution", "")
        chunk_size = 20  # Characters per chunk
        for i in range(0, len(solution), chunk_size):
            chunk = solution[i:i+chunk_size]
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.05)  # Simulate streaming delay
        
        # Yield the final complete response
        yield f"data: {json.dumps(result)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    rag_client: CodeRAG = Depends(get_rag_client),
) -> Dict[str, Any]:
    """
    Check the health of the API.
    
    Args:
        rag_client: RAG client instance
        
    Returns:
        Dict[str, Any]: Health check response
    """
    try:
        # Get component status
        component_status = rag_client.health_check()
        
        # Determine overall status
        status = "ok" if component_status.get("healthy", False) else "degraded"
        
        return {
            "status": status,
            "components": component_status,
            "version": __version__,
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "components": {"error": str(e)},
            "version": __version__,
        }