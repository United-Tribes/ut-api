"""
FastAPI application for ut-vector-store service
Provides REST API for vector embeddings and semantic search
"""

from datetime import datetime
from typing import List, Dict, Any
import uuid
import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware

from .shared.contracts import (
    SearchRequest, SearchResponse, EmbeddingRequest, EmbeddingResponse,
    ContentAdditionRequest, ContentAdditionResponse, IndexBuildRequest, IndexBuildResponse,
    IndexStatsResponse, HealthResponse, ErrorResponse, WebhookEvent
)
from .vector_service import VectorService
from .embedding_service import EmbeddingService
from .index_manager import IndexManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
vector_service: VectorService = None
embedding_service: EmbeddingService = None
index_manager: IndexManager = None
build_jobs: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global vector_service, embedding_service, index_manager
    
    # Startup
    logger.info("Starting ut-vector-store service...")
    
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        index_manager = IndexManager()
        await index_manager.initialize()
        
        vector_service = VectorService(embedding_service, index_manager)
        await vector_service.initialize()
        
        logger.info("ut-vector-store service ready")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down ut-vector-store service...")
    if vector_service:
        await vector_service.shutdown()
    if embedding_service:
        await embedding_service.shutdown()
    if index_manager:
        await index_manager.shutdown()

# Create FastAPI app
app = FastAPI(
    title="UT-Vector-Store",
    description="Vector embeddings and semantic search microservice for United Tribes",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "ut-vector-store",
        "version": "1.1.0",
        "description": "Vector embeddings and semantic search microservice for United Tribes with S3 enhanced knowledge graph integration",
        "features": [
            "S3 enhanced knowledge graph integration",
            "2,787+ relationships with source attribution and URLs",
            "Source-filtered search (Billboard, Pitchfork, NPR, Guardian)",
            "Entity-specific relationship queries",
            "Cultural significance and temporal context",
            "Real-time confidence scoring and evidence",
            "Semantic similarity search with FAISS indices",
            "Complete source attribution preservation"
        ],
        "endpoints": {
            "search": "POST /search - Enhanced semantic similarity search with source attribution",
            "embed": "POST /embed - Generate embeddings",
            "content/add": "POST /content/add - Add content to index", 
            "index/build": "POST /index/build - Build index from S3 enhanced knowledge graph",
            "index/stats": "GET /index/stats - Enhanced index statistics",
            "sources": "GET /sources - List available sources",
            "entity/{name}": "GET /entity/{name} - Get relationships for specific entity",
            "data/summary": "GET /data/summary - Enhanced data summary",
            "health": "GET /health - Health check"
        },
        "s3_integration": {
            "bucket": "ut-processed-content",
            "enhanced_knowledge_graph": "enhanced-knowledge-graph/YYYY/MM/DD/complete_knowledge_graph_main_*.json",
            "source_attribution_preserved": True
        }
    }

@app.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Perform semantic similarity search"""
    if not vector_service:
        raise HTTPException(status_code=503, detail="Vector service not available")
    
    try:
        logger.info(f"Processing search query: {request.query[:50]}...")
        
        start_time = time.time()
        
        # Perform search
        results = await vector_service.search(
            query=request.query,
            k=request.k,
            source_filter=request.source_filter,
            entity_filter=request.entity_filter,
            content_type_filter=request.content_type_filter,
            min_confidence=request.min_confidence,
            temporal_filter=request.temporal_filter
        )
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Search completed: {len(results.results)} results in {search_time_ms}ms")
        
        # Update search time in response
        results.search_time_ms = search_time_ms
        
        # Add enhanced metadata to response
        if hasattr(results, 'filters_applied') and results.filters_applied is None:
            results.filters_applied = {}
        
        # Add search metadata
        results.filters_applied.update({
            "enhanced_search": True,
            "s3_source": "ut-processed-content",
            "relationship_based": True
        })
        
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate vector embeddings for content"""
    if not embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not available")
    
    try:
        start_time = time.time()
        
        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings(
            content=request.content,
            model=request.model,
            normalize=request.normalize,
            batch_size=request.batch_size
        )
        
        embedding_time_ms = int((time.time() - start_time) * 1000)
        
        return EmbeddingResponse(
            embeddings=embeddings,
            embedding_time_ms=embedding_time_ms,
            model_used=request.model.value,
            total_tokens=None  # Would be calculated in real implementation
        )
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/content/add", response_model=ContentAdditionResponse)
async def add_content_to_index(request: ContentAdditionRequest):
    """Add processed content to search index"""
    if not vector_service:
        raise HTTPException(status_code=503, detail="Vector service not available")
    
    try:
        start_time = time.time()
        
        # Add content to index
        result = await vector_service.add_content(
            chunks=request.chunks,
            index_name=request.index_name,
            update_if_exists=request.update_if_exists
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        result.processing_time_ms = processing_time_ms
        
        logger.info(f"Added {result.chunks_added} chunks to index {request.index_name}")
        
        return result
        
    except Exception as e:
        logger.error(f"Content addition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/build", response_model=IndexBuildResponse)
async def build_index(
    request: IndexBuildRequest,
    background_tasks: BackgroundTasks
):
    """Build or rebuild search index"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not available")
    
    build_id = str(uuid.uuid4())
    
    # Add to build jobs tracking
    build_jobs[build_id] = {
        "status": "started",
        "started_at": datetime.utcnow(),
        "index_name": request.index_name,
        "content_source": request.content_source
    }
    
    # Start build in background
    background_tasks.add_task(_build_index_background, build_id, request)
    
    logger.info(f"Started index build {build_id} for {request.index_name}")
    
    return IndexBuildResponse(
        build_id=build_id,
        status="started",
        index_name=request.index_name,
        chunks_processed=0,
        build_time_ms=0,
        index_size_bytes=0
    )

@app.get("/index/build/{build_id}", response_model=IndexBuildResponse)
async def get_build_status(build_id: str):
    """Get status of index build operation"""
    if build_id not in build_jobs:
        raise HTTPException(status_code=404, detail="Build job not found")
    
    job = build_jobs[build_id]
    
    return IndexBuildResponse(
        build_id=build_id,
        status=job["status"],
        index_name=job["index_name"],
        chunks_processed=job.get("chunks_processed", 0),
        build_time_ms=job.get("build_time_ms", 0),
        index_size_bytes=job.get("index_size_bytes", 0),
        error_message=job.get("error_message")
    )

@app.get("/index/stats", response_model=IndexStatsResponse)
async def get_index_stats():
    """Get statistics for all indices"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not available")
    
    try:
        return await index_manager.get_stats()
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        dependencies = {}
        loaded_indices = []
        memory_usage = 0.0
        
        # Check vector service
        if vector_service:
            dependencies["vector_service"] = "healthy"
        else:
            dependencies["vector_service"] = "unhealthy"
        
        # Check embedding service
        if embedding_service:
            try:
                await embedding_service.test_connection()
                dependencies["bedrock_embedding"] = "healthy"
            except Exception:
                dependencies["bedrock_embedding"] = "unhealthy"
        else:
            dependencies["bedrock_embedding"] = "unhealthy"
        
        # Check index manager
        if index_manager:
            try:
                loaded_indices = index_manager.get_loaded_indices()
                memory_usage = index_manager.get_memory_usage_mb()
                dependencies["index_manager"] = "healthy"
            except Exception as e:
                logger.warning(f"Index manager methods failed: {e}")
                dependencies["index_manager"] = "degraded"
                loaded_indices = []
                memory_usage = 0.0
        else:
            dependencies["index_manager"] = "unhealthy"
        
        # Determine overall status
        if all(status == "healthy" for status in dependencies.values()):
            overall_status = "healthy"
        elif any(status in ["healthy", "degraded"] for status in dependencies.values()):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            dependencies=dependencies,
            loaded_indices=loaded_indices,
            memory_usage_mb=memory_usage,
            last_successful_search=None,  # Would track in real implementation
            last_successful_embedding=None  # Would track in real implementation
        )
        
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/webhook/content-processed")
async def handle_processed_content_webhook(
    event: WebhookEvent,
    background_tasks: BackgroundTasks
):
    """Handle webhook from ut-content-processor when content is processed"""
    try:
        if event.event_type == "content_processed":
            # Queue content for indexing
            background_tasks.add_task(_process_webhook_content, event.content_data)
            
            return {"message": "Content queued for indexing", "event_id": event.event_id}
        else:
            logger.warning(f"Unknown webhook event type: {event.event_type}")
            return {"message": "Event type not supported"}
            
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/index/{index_name}")
async def delete_index(index_name: str):
    """Delete an index"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not available")
    
    try:
        await index_manager.delete_index(index_name)
        logger.info(f"Deleted index {index_name}")
        return {"message": f"Index {index_name} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete index {index_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources")
async def list_available_sources():
    """List available sources from enhanced knowledge graph"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not available")
    
    try:
        sources = await index_manager.get_available_sources()
        return {"sources": sources, "total": len(sources)}
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entity/{entity_name}")
async def get_entity_relationships(entity_name: str):
    """Get all relationships for a specific entity"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not available")
    
    try:
        relationships = await index_manager.get_relationships_by_entity(entity_name)
        
        # Format relationships for response
        formatted_relationships = []
        for rel in relationships:
            formatted_relationships.append({
                "source_entity": rel.get('source_entity'),
                "target_entity": rel.get('target_entity'),
                "relationship_type": rel.get('relationship_type'),
                "confidence": rel.get('confidence'),
                "evidence": rel.get('evidence'),
                "source_attribution": rel.get('source_attribution'),
                "temporal_context": rel.get('temporal_context')
            })
        
        return {
            "entity": entity_name,
            "relationships": formatted_relationships,
            "total": len(formatted_relationships)
        }
    except Exception as e:
        logger.error(f"Failed to get entity relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/summary")
async def get_data_summary():
    """Get summary of loaded enhanced data"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not available")
    
    try:
        summary = await index_manager.get_data_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get data summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.exception(f"Unhandled exception: {exc}")
    
    return HTTPException(
        status_code=500,
        detail=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            details={"exception": str(exc)}
        ).model_dump()
    )

async def _build_index_background(build_id: str, request: IndexBuildRequest):
    """Background task for index building"""
    try:
        build_jobs[build_id]["status"] = "building"
        
        start_time = time.time()
        
        # Build the index
        result = await index_manager.build_index(
            index_name=request.index_name,
            content_source=request.content_source,
            embedding_model=request.embedding_model,
            index_type=request.index_type,
            similarity_metric=request.similarity_metric,
            build_parameters=request.build_parameters,
            force_rebuild=request.force_rebuild
        )
        
        build_time = int((time.time() - start_time) * 1000)
        
        # Update job status
        build_jobs[build_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "chunks_processed": result.get("chunks_processed", 0),
            "build_time_ms": build_time,
            "index_size_bytes": result.get("index_size_bytes", 0)
        })
        
        logger.info(f"Index build {build_id} completed successfully")
        
    except Exception as e:
        # Update error status
        build_jobs[build_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error_message": str(e)
        })
        
        logger.error(f"Index build {build_id} failed: {e}")

async def _process_webhook_content(content_data: Dict[str, Any]):
    """Background task for processing webhook content"""
    try:
        # Convert content to chunks and add to index
        # This would implement the actual content processing
        logger.info(f"Processing webhook content: {content_data.get('content_id')}")
        
        # Placeholder implementation
        if vector_service:
            # Would convert content_data to VectorChunk objects and add to index
            pass
            
    except Exception as e:
        logger.error(f"Webhook content processing failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)