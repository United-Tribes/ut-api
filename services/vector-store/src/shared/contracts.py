"""
Data contracts for ut-vector-store service
Defines standard formats for vector operations and semantic search
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class SimilarityMetric(str, Enum):
    """Similarity metrics for vector search"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean" 
    DOT_PRODUCT = "dot_product"


class IndexType(str, Enum):
    """FAISS index types"""
    FLAT = "flat"  # Exact search
    HNSW = "hnsw"  # Hierarchical Navigable Small World
    IVF = "ivf"    # Inverted File Index


class EmbeddingModel(str, Enum):
    """Available embedding models"""
    TITAN_V2 = "amazon.titan-embed-text-v2:0"
    COHERE_EMBED = "cohere.embed-english-v3"


class SourceInfo(BaseModel):
    """Enhanced source attribution information"""
    source: str = Field(..., description="Content source (pitchfork, npr, etc)")
    title: str = Field(..., description="Original content title")
    url: Optional[str] = Field(default=None, description="Source URL")
    author: Optional[str] = Field(default=None, description="Content author")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    content_type: str = Field(..., description="Type of source content")
    
    # Enhanced attribution fields
    scraped_at: Optional[datetime] = Field(default=None, description="When content was scraped")
    domain: Optional[str] = Field(default=None, description="Source domain for filtering")
    credibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Source credibility")
    
    def get_domain(self) -> str:
        """Extract domain from URL for filtering"""
        if self.url:
            try:
                from urllib.parse import urlparse
                return urlparse(self.url).netloc
            except:
                return "unknown"
        return "unknown"


class EntityAttribution(BaseModel):
    """Entity attribution within a chunk"""
    entity: str = Field(..., description="Entity name")
    evidence: str = Field(..., description="Supporting text evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Attribution confidence")
    citation: str = Field(..., description="Formatted citation string")
    position_in_source: Optional[int] = Field(default=None, description="Position in original source")

class ChunkMetadata(BaseModel):
    """Enhanced metadata for content chunks with rich attribution"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    source_info: SourceInfo = Field(..., description="Source attribution")
    entities: List[str] = Field(default_factory=list, description="Entities in chunk")
    chunk_type: str = Field(..., description="Type of content in chunk")
    
    # Enhanced chunk positioning
    chunk_start_position: Optional[int] = Field(default=None, description="Start position in source")
    chunk_end_position: Optional[int] = Field(default=None, description="End position in source")
    chunk_length: int = Field(..., description="Chunk content length")
    paragraph_numbers: List[int] = Field(default_factory=list, description="Paragraph numbers spanned")
    
    # Entity attribution data
    entity_count: int = Field(default=0, description="Number of entities in chunk")
    entity_attributions: List[EntityAttribution] = Field(default_factory=list, description="Entity attributions")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Entity relationships in chunk")
    
    # Citation metadata
    citation_ready: bool = Field(default=False, description="Has entities with citations")
    source_verifiable: bool = Field(default=False, description="Source URL available and accessible")
    attribution_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Attribution coverage ratio")
    
    # Legacy fields
    temporal_context: Optional[str] = Field(default=None, description="Time period context")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Chunk quality score")
    additional_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class VectorChunk(BaseModel):
    """Content chunk with embedding vector"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk text content")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Chunk content cannot be empty')
        return v.strip()


class SearchRequest(BaseModel):
    """Enhanced semantic search request with source-aware filtering"""
    query: str = Field(..., description="Search query")
    k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    
    # Enhanced source filtering
    source_filter: Optional[List[str]] = Field(default=None, description="Filter by content sources")
    author_filter: Optional[List[str]] = Field(default=None, description="Filter by authors")
    domain_filter: Optional[List[str]] = Field(default=None, description="Filter by source domains")
    url_filter: Optional[List[str]] = Field(default=None, description="Filter by specific URLs")
    
    # Entity and content filtering
    entity_filter: Optional[List[str]] = Field(default=None, description="Filter by entities")
    content_type_filter: Optional[List[str]] = Field(default=None, description="Filter by content type")
    
    # Attribution filtering
    citation_ready_only: bool = Field(default=False, description="Only return citation-ready results")
    source_verifiable_only: bool = Field(default=False, description="Only return verifiable sources")
    min_attribution_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum attribution coverage")
    
    # Quality filtering
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    min_credibility: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum source credibility")
    temporal_filter: Optional[str] = Field(default=None, description="Filter by time period")
    
    # Date range filtering
    published_after: Optional[datetime] = Field(default=None, description="Published after date")
    published_before: Optional[datetime] = Field(default=None, description="Published before date")
    
    # Advanced search options
    include_citations: bool = Field(default=True, description="Include citation information in results")
    highlight_query: bool = Field(default=True, description="Highlight query terms in excerpts")
    
    @validator('query')
    def validate_query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()


class SearchResult(BaseModel):
    """Enhanced search result with citation information"""
    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    source_info: SourceInfo = Field(..., description="Source attribution")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity to query")
    
    # Entity information
    entities: List[str] = Field(default_factory=list, description="Entities in chunk")
    entity_attributions: List[EntityAttribution] = Field(default_factory=list, description="Entity attributions")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Entity relationships")
    
    # Citation information
    citations: List[str] = Field(default_factory=list, description="Formatted citations for entities")
    primary_citation: Optional[str] = Field(default=None, description="Primary source citation")
    citation_ready: bool = Field(default=False, description="Has properly attributed citations")
    source_verifiable: bool = Field(default=False, description="Source is verifiable")
    
    # Position and context
    chunk_position: Optional[Dict[str, int]] = Field(default=None, description="Position in original source")
    paragraph_numbers: List[int] = Field(default_factory=list, description="Paragraph numbers")
    excerpt: Optional[str] = Field(default=None, description="Highlighted excerpt")
    
    # Quality metrics
    attribution_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Attribution coverage")
    source_credibility: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Source credibility score")
    
    # Legacy metadata
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")
    
    def get_formatted_citation(self, style: str = "apa") -> str:
        """Generate formatted citation in specified style"""
        if self.primary_citation:
            return self.primary_citation
        
        # Fallback basic citation
        author = self.source_info.author or "Unknown Author"
        title = self.source_info.title or "Unknown Title"
        source = self.source_info.source or "Unknown Source"
        
        if style.lower() == "apa":
            return f"{author}. {title}. {source}."
        elif style.lower() == "mla":
            return f'{author}. "{title}." {source}.'
        elif style.lower() == "chicago":
            return f'{author}, "{title}," {source}.'
        else:
            return f"{title} by {author} from {source}"


class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    results: List[SearchResult] = Field(..., description="Search results")
    search_time_ms: int = Field(..., description="Search execution time")
    total_results: int = Field(..., description="Total available results")
    query_embedding_time_ms: int = Field(..., description="Query embedding time")
    filters_applied: Dict[str, Any] = Field(..., description="Applied search filters")


class EmbeddingRequest(BaseModel):
    """Request for content embedding"""
    content: Union[str, List[str]] = Field(..., description="Content to embed")
    model: EmbeddingModel = Field(default=EmbeddingModel.TITAN_V2, description="Embedding model")
    normalize: bool = Field(default=True, description="Normalize embeddings")
    batch_size: int = Field(default=10, ge=1, le=50, description="Batch size for processing")


class EmbeddingResponse(BaseModel):
    """Response from embedding generation"""
    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    embedding_time_ms: int = Field(..., description="Embedding generation time")
    model_used: str = Field(..., description="Model used for embeddings")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens processed")


class ContentAdditionRequest(BaseModel):
    """Request to add content to index"""
    chunks: List[VectorChunk] = Field(..., description="Chunks to add to index")
    index_name: str = Field(default="main", description="Target index name")
    update_if_exists: bool = Field(default=True, description="Update if chunk exists")


class ContentAdditionResponse(BaseModel):
    """Response from content addition"""
    chunks_added: int = Field(..., description="Number of chunks added")
    chunks_updated: int = Field(..., description="Number of chunks updated")
    chunks_failed: int = Field(..., description="Number of chunks that failed")
    processing_time_ms: int = Field(..., description="Processing time")
    index_stats: Dict[str, Any] = Field(..., description="Updated index statistics")


class IndexBuildRequest(BaseModel):
    """Request to build or rebuild index"""
    index_name: str = Field(default="main", description="Index name")
    content_source: str = Field(..., description="Source of content to index")
    embedding_model: EmbeddingModel = Field(default=EmbeddingModel.TITAN_V2)
    index_type: IndexType = Field(default=IndexType.HNSW, description="FAISS index type")
    similarity_metric: SimilarityMetric = Field(default=SimilarityMetric.COSINE)
    build_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Index build parameters")
    force_rebuild: bool = Field(default=False, description="Force rebuild even if index exists")


class IndexBuildResponse(BaseModel):
    """Response from index build operation"""
    build_id: str = Field(..., description="Build operation identifier")
    status: str = Field(..., description="Build status")
    index_name: str = Field(..., description="Index name")
    chunks_processed: int = Field(..., description="Number of chunks processed")
    build_time_ms: int = Field(..., description="Build time in milliseconds")
    index_size_bytes: int = Field(..., description="Index file size")
    error_message: Optional[str] = Field(default=None, description="Error if build failed")


class IndexStats(BaseModel):
    """Statistics about an index"""
    index_name: str = Field(..., description="Index name")
    total_vectors: int = Field(..., description="Total vectors in index")
    dimension: int = Field(..., description="Vector dimension")
    index_type: str = Field(..., description="FAISS index type")
    similarity_metric: str = Field(..., description="Similarity metric used")
    index_size_bytes: int = Field(..., description="Index file size")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    build_parameters: Dict[str, Any] = Field(..., description="Index build parameters")
    search_performance: Optional[Dict[str, float]] = Field(default=None, description="Search performance metrics")


class IndexStatsResponse(BaseModel):
    """Response containing index statistics"""
    indices: List[IndexStats] = Field(..., description="Statistics for all indices")
    total_vectors_across_indices: int = Field(..., description="Total vectors across all indices")
    total_size_bytes: int = Field(..., description="Total size of all indices")
    memory_usage_mb: float = Field(..., description="Current memory usage")
    enhanced_data_info: Optional[Dict[str, Any]] = Field(default=None, description="Enhanced knowledge graph statistics")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall service status")
    dependencies: Dict[str, str] = Field(..., description="Dependency health status")
    loaded_indices: List[str] = Field(..., description="Currently loaded indices")
    memory_usage_mb: float = Field(..., description="Memory usage")
    last_successful_search: Optional[datetime] = Field(default=None, description="Last successful search")
    last_successful_embedding: Optional[datetime] = Field(default=None, description="Last successful embedding")


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebhookEvent(BaseModel):
    """Webhook event from content processor"""
    event_type: str = Field(..., description="Type of webhook event")
    source_service: str = Field(..., description="Service sending the webhook")
    content_data: Dict[str, Any] = Field(..., description="Processed content data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_id: str = Field(..., description="Unique event identifier")


class BatchProcessingRequest(BaseModel):
    """Request for batch processing operations"""
    operation: str = Field(..., description="Batch operation type")
    items: List[Dict[str, Any]] = Field(..., description="Items to process")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Processing batch size")
    parallel_workers: int = Field(default=4, ge=1, le=10, description="Number of parallel workers")


class BatchProcessingResponse(BaseModel):
    """Response from batch processing"""
    operation: str = Field(..., description="Operation type")
    total_items: int = Field(..., description="Total items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    processing_time_ms: int = Field(..., description="Total processing time")
    batch_results: List[Dict[str, Any]] = Field(..., description="Detailed results per batch")
    errors: List[str] = Field(default_factory=list, description="Error messages")


class IndexConfiguration(BaseModel):
    """Configuration for index building"""
    embedding_model: EmbeddingModel = Field(default=EmbeddingModel.TITAN_V2)
    dimension: int = Field(default=1024, ge=128, le=4096)
    similarity_metric: SimilarityMetric = Field(default=SimilarityMetric.COSINE)
    index_type: IndexType = Field(default=IndexType.HNSW)
    build_parameters: Dict[str, Any] = Field(default_factory=dict)
    search_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('build_parameters')
    def validate_build_parameters(cls, v):
        # Set default HNSW parameters if not provided
        if not v:
            return {
                "ef_construction": 200,
                "M": 16
            }
        return v
    
    @validator('search_parameters')
    def validate_search_parameters(cls, v):
        # Set default search parameters if not provided
        if not v:
            return {
                "ef_search": 100
            }
        return v