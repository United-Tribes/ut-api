"""
FastAPI application for ut-query-service
Cultural Cartographer RAG pipeline with enhanced S3 knowledge graph integration
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .contracts import QueryRequest, QueryResponse, EnhancedQueryResponse, HealthResponse
from .vector_client import VectorStoreClient
from .cultural_cartographer import CulturalCartographer
from .query_processor import QueryProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
vector_client: VectorStoreClient = None
cultural_cartographer: CulturalCartographer = None
query_processor: QueryProcessor = None
query_stats = {"total_queries": 0, "successful_queries": 0, "average_response_time_ms": 0}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global vector_client, cultural_cartographer, query_processor
    
    # Startup
    logger.info("Starting ut-query-service...")
    
    try:
        # Initialize vector store client (non-blocking)
        vector_store_url = os.getenv('VECTOR_STORE_URL', 'http://localhost:8002')
        vector_client = VectorStoreClient(vector_store_url)
        try:
            await vector_client.initialize()
        except Exception as e:
            logger.error(f"Vector store initialization failed: {e}")
            # Continue anyway - the app can work in degraded mode
        
        # Initialize cultural cartographer (Claude 3 Haiku)
        cultural_cartographer = CulturalCartographer()
        try:
            await cultural_cartographer.initialize()
        except Exception as e:
            logger.error(f"Cultural cartographer initialization failed: {e}")
            # Continue anyway
        
        # Initialize query processor
        query_processor = QueryProcessor(vector_client, cultural_cartographer)
        try:
            await query_processor.initialize()
        except Exception as e:
            logger.error(f"Query processor initialization failed: {e}")
            # Continue anyway
        
        logger.info("ut-query-service ready - Cultural Cartographer online")
        yield
        
    except Exception as e:
        logger.error(f"Critical startup failure: {e}")
        # Only fail if there's a critical error, not dependency issues
        raise
    
    # Shutdown
    logger.info("Shutting down ut-query-service...")
    if query_processor:
        await query_processor.shutdown()
    if cultural_cartographer:
        await cultural_cartographer.shutdown()
    if vector_client:
        await vector_client.shutdown()

# Create FastAPI app
app = FastAPI(
    title="UT-Query-Service",
    description="Cultural Cartographer RAG pipeline for United Tribes with S3 enhanced knowledge graph",
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

# API endpoints only - no web interface

@app.get("/")
async def api_root():
    """API root endpoint with service information"""
    return {
        "service": "ut-query-service",
        "description": "Cultural Cartographer RAG pipeline with S3 enhanced knowledge graph",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "query": "POST /query - Cultural Cartographer query processing",
            "health": "GET /health - Service health and dependencies",
            "stats": "GET /stats - Query statistics and performance",
            "api_info": "GET /api/info - Detailed API information"
        },
        "integration": {
            "vector_store": "ut-vector-store with S3 enhanced knowledge graph",
            "llm_provider": "AWS Bedrock Claude 3 Haiku",
            "knowledge_base": "2,787+ relationships with source attribution"
        },
        "usage": {
            "example_request": {
                "method": "POST",
                "url": "/query",
                "body": {
                    "query": "tell me about the Beatles",
                    "k": 5
                }
            }
        }
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Main Cultural Cartographer query endpoint"""
    if not query_processor:
        raise HTTPException(status_code=503, detail="Query processor not available")
    
    start_time = time.time()
    global query_stats
    query_stats["total_queries"] += 1
    
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Process the query through our Cultural Cartographer pipeline
        response = await query_processor.process_query(
            query=request.query,
            k=request.k,
            source_filter=request.source_filter,
            entity_filter=request.entity_filter
        )
        
        query_time_ms = int((time.time() - start_time) * 1000)
        response.query_time_ms = query_time_ms
        
        # Update stats
        query_stats["successful_queries"] += 1
        query_stats["average_response_time_ms"] = int(
            (query_stats["average_response_time_ms"] * (query_stats["successful_queries"] - 1) + query_time_ms) 
            / query_stats["successful_queries"]
        )
        
        logger.info(f"Query completed in {query_time_ms}ms")
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        # Graceful degradation - return search results without LLM synthesis
        try:
            fallback_response = await query_processor.fallback_response(request.query, request.k)
            query_time_ms = int((time.time() - start_time) * 1000)
            fallback_response.query_time_ms = query_time_ms
            return fallback_response
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail="Query processing unavailable")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        dependencies = {}
        
        # Check vector store connectivity
        if vector_client:
            vector_healthy = await vector_client.health_check()
            dependencies["vector_store"] = "healthy" if vector_healthy else "unhealthy"
        else:
            dependencies["vector_store"] = "unhealthy"
        
        # Check cultural cartographer (LLM)
        if cultural_cartographer:
            llm_healthy = await cultural_cartographer.health_check()
            dependencies["cultural_cartographer"] = "healthy" if llm_healthy else "unhealthy"
        else:
            dependencies["cultural_cartographer"] = "unhealthy"
        
        # Check query processor
        if query_processor:
            dependencies["query_processor"] = "healthy"
        else:
            dependencies["query_processor"] = "unhealthy"
        
        overall_status = "healthy" if all(
            status == "healthy" for status in dependencies.values()
        ) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            dependencies=dependencies,
            query_stats=query_stats,
            last_query_time=None  # Would track in production
        )
        
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get query statistics and performance metrics"""
    return {
        "service": "ut-query-service",
        "version": "1.0.0",
        "stats": query_stats,
        "vector_store_stats": await vector_client.get_stats() if vector_client else None,
        "cultural_cartographer_info": {
            "model": "claude-3-haiku-20240307",
            "provider": "aws_bedrock",
            "features": ["source_attribution", "discovery_pathways", "cross_media_recommendations"]
        }
    }

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "service": "ut-query-service",
        "description": "Cultural Cartographer RAG pipeline with S3 enhanced knowledge graph",
        "version": "1.0.0",
        "features": [
            "Cultural cartographer identity with discovery pathways",
            "Enhanced source attribution from S3 knowledge graph",
            "Graceful degradation during rate limits",
            "Cross-media recommendations (music → podcasts → books)",
            "Flexible query processing - no rigid classification"
        ],
        "endpoints": {
            "query": "POST /query - Cultural Cartographer query processing",
            "health": "GET /health - Service health and dependencies",
            "stats": "GET /stats - Query statistics and performance",
            "ui": "GET / - Web interface for cultural discovery"
        },
        "integration": {
            "vector_store": "ut-vector-store with S3 enhanced knowledge graph",
            "llm_provider": "AWS Bedrock Claude 3 Haiku",
            "knowledge_base": "2,787+ relationships with source attribution"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)