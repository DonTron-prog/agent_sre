"""
Pydantic models for the REST API.
"""

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


class QueryRequest(BaseModel):
    """Request model for the query endpoint."""
    
    model_config = ConfigDict(extra="forbid")
    
    error_message: str = Field(
        ...,
        description="The error message to find solutions for",
        min_length=1,
    )
    num_results: Optional[int] = Field(
        default=3,
        description="Number of relevant results to retrieve",
        ge=1,
        le=10,
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Temperature for LLM generation (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    max_tokens: Optional[int] = Field(
        default=1024,
        description="Maximum tokens for LLM response",
        ge=1,
        le=4096,
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response",
    )


class ReferenceItem(BaseModel):
    """Model for a reference item in the response."""
    
    id: str = Field(..., description="Unique identifier for the reference")
    error: str = Field(..., description="Error message of the reference")
    solution: str = Field(..., description="Solution for the error")
    similarity_score: float = Field(
        ...,
        description="Similarity score between the query and reference",
        ge=0.0,
        le=1.0,
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Additional metadata for the reference",
    )


class ResponseMetadata(BaseModel):
    """Model for response metadata."""
    
    model_used: str = Field(..., description="LLM model used for generating the solution")
    tokens_used: Optional[int] = Field(default=None, description="Number of tokens used")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    num_references: int = Field(..., description="Number of references used")


class QueryResponse(BaseModel):
    """Response model for the query endpoint."""
    
    solution: str = Field(..., description="Generated solution for the error")
    references: List[ReferenceItem] = Field(..., description="References used for generating the solution")
    metadata: ResponseMetadata = Field(..., description="Metadata about the response")
    error: Optional[str] = Field(default=None, description="Error message if any")


class HealthCheckResponse(BaseModel):
    """Response model for the health check endpoint."""
    
    status: str = Field(..., description="Overall status of the API")
    components: Dict[str, bool] = Field(..., description="Status of each component")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    error: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(default=None, description="Additional error details")