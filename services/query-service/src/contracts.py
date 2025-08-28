"""
Data contracts for ut-query-service
Cultural Cartographer query processing and response formats
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    """Cultural Cartographer query request"""
    query: str = Field(..., description="User query for cultural exploration")
    k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    source_filter: Optional[List[str]] = Field(default=None, description="Filter by sources (Billboard, Pitchfork, etc)")
    entity_filter: Optional[List[str]] = Field(default=None, description="Filter by specific artists/entities")
    
    @validator('query')
    def validate_query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class SourceAttribution(BaseModel):
    """Source attribution for query responses"""
    source: str = Field(..., description="Content source (Billboard, Pitchfork, NPR, etc)")
    artist: Optional[str] = Field(default=None, description="Primary artist mentioned")
    content_type: str = Field(..., description="Type of content (article, review, interview)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    excerpt: str = Field(..., description="Relevant excerpt from source")
    url: Optional[str] = Field(default=None, description="Source URL")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    relationship_type: Optional[str] = Field(default=None, description="Type of relationship described")

class EnhancedSourceAttribution(BaseModel):
    """Enhanced source attribution with citation system support"""
    source: str = Field(..., description="Content source (Billboard, Pitchfork, etc)")
    artist: Optional[str] = Field(default=None, description="Primary artist mentioned")
    content_type: str = Field(..., description="Type of content (article, review, interview)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    # Enhanced attribution fields
    evidence_text: str = Field(..., description="Exact quoted evidence text")
    evidence_type: str = Field(default="contextual", description="Type of evidence (direct_quote, contextual, etc)")
    
    # Position tracking
    start_position: Optional[int] = Field(default=None, description="Start position in source")
    end_position: Optional[int] = Field(default=None, description="End position in source") 
    paragraph_number: Optional[int] = Field(default=None, description="Paragraph number")
    
    # Enhanced metadata
    url: Optional[str] = Field(default=None, description="Source URL")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    citation: Optional[str] = Field(default=None, description="Formatted citation")
    source_credibility: Optional[float] = Field(default=None, description="Source credibility score")
    relationship_type: Optional[str] = Field(default=None, description="Type of relationship described")
    
    def get_position_info(self) -> str:
        """Get human-readable position information"""
        if self.paragraph_number:
            return f"Paragraph {self.paragraph_number}"
        elif self.start_position and self.end_position:
            return f"Characters {self.start_position}-{self.end_position}"
        else:
            return "Position unknown"
    
    def get_enhanced_excerpt(self, max_length: int = 200) -> str:
        """Get enhanced excerpt with position context"""
        excerpt = self.evidence_text
        if len(excerpt) > max_length:
            excerpt = excerpt[:max_length] + "..."
        
        position_info = self.get_position_info()
        return f"{excerpt} [{position_info}]"

class QueryResponse(BaseModel):
    """Cultural Cartographer response"""
    response: str = Field(..., description="Cultural Cartographer analysis and recommendations")
    sources: List[SourceAttribution] = Field(default_factory=list, description="Source attributions")
    query_time_ms: int = Field(..., description="Total query processing time")
    discovery_pathways: Optional[List[str]] = Field(default=None, description="Suggested follow-up queries")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Query processing statistics")
    mode: str = Field(default="full", description="Response mode: 'full' or 'fallback'")

class EnhancedQueryResponse(BaseModel):
    """Enhanced query response with attribution quality metrics"""
    response: str = Field(..., description="Cultural Cartographer analysis and recommendations")
    sources: List[EnhancedSourceAttribution] = Field(default_factory=list, description="Enhanced source attributions")
    query_time_ms: int = Field(..., description="Total query processing time")
    discovery_pathways: Optional[List[str]] = Field(default=None, description="Suggested follow-up queries")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Query processing statistics")
    mode: str = Field(default="full", description="Response mode: 'full' or 'fallback'")
    
    # Enhanced metrics
    attribution_quality: float = Field(default=0.0, description="Overall attribution quality score")
    citation_readiness: float = Field(default=0.0, description="Percentage of citation-ready sources")
    source_verification_score: float = Field(default=0.0, description="Source verification success rate")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service health status")
    dependencies: Dict[str, str] = Field(..., description="Dependency health status")
    query_stats: Dict[str, Any] = Field(..., description="Query processing statistics")
    last_query_time: Optional[datetime] = Field(default=None, description="Last successful query")

class VectorSearchResult(BaseModel):
    """Result from vector store search"""
    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    source_info: Dict[str, Any] = Field(..., description="Source information")
    entities: List[str] = Field(default_factory=list, description="Entities in chunk")
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    # Enhanced fields for citation system
    entity_attributions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Enhanced entity attributions")

class CulturalCartographerContext(BaseModel):
    """Context for Cultural Cartographer LLM"""
    query: str = Field(..., description="Original user query")
    search_results: List[VectorSearchResult] = Field(..., description="Vector search results")
    total_relationships: int = Field(..., description="Total relationships in knowledge base")
    source_distribution: Dict[str, int] = Field(default_factory=dict, description="Sources represented")
    
class QueryStats(BaseModel):
    """Query processing statistics"""
    total_queries: int = Field(default=0, description="Total queries processed")
    successful_queries: int = Field(default=0, description="Successful queries")
    failed_queries: int = Field(default=0, description="Failed queries")
    fallback_queries: int = Field(default=0, description="Queries using fallback mode")
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    llm_usage_stats: Dict[str, Any] = Field(default_factory=dict, description="LLM usage statistics")
    
class ErrorResponse(BaseModel):
    """Error response format"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fallback_available: bool = Field(default=False, description="Whether fallback mode is available")