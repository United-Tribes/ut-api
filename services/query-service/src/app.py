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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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

# Static files not needed - serving inline HTML

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the Cultural Cartographer web interface"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>United Tribes - Media Discovery and Consumption for the AI Era</title>
    <style>
        body { 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
            max-width: 900px; 
            margin: 0 auto; 
            padding: 40px 20px; 
            background: #f5f2ed; 
            color: #3d2f2a;
        }
        h1 { 
            color: #2a1f1a; 
            margin-bottom: 8px; 
            font-size: 42px;
            font-weight: 300;
            letter-spacing: -1px;
        }
        .tagline { 
            color: #6b5d54; 
            margin-bottom: 35px; 
            font-size: 18px;
            font-weight: 300;
        }
        .query-box { 
            width: 100%; 
            padding: 18px 20px; 
            margin: 15px 0; 
            font-size: 16px; 
            border: 2px solid #c4b5aa; 
            border-radius: 6px; 
            box-sizing: border-box; 
            background: #fdfcfa;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #3d2f2a;
        }
        .query-box::placeholder {
            color: #9b8b80;
        }
        .query-box:focus {
            outline: none;
            border-color: #8b7355;
            background: white;
        }
        .submit-btn { 
            padding: 18px 40px; 
            font-size: 16px; 
            background: #6b5d54; 
            color: #f5f2ed; 
            border: none; 
            cursor: pointer; 
            border-radius: 6px; 
            transition: all 0.3s; 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 500;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .submit-btn:hover { 
            background: #4a3f37; 
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(74, 63, 55, 0.2);
        }
        .response { 
            background: white; 
            padding: 30px; 
            margin: 25px 0; 
            white-space: pre-wrap; 
            word-wrap: break-word;
            overflow-wrap: break-word;
            border-radius: 6px;
            box-shadow: 0 2px 12px rgba(74, 63, 55, 0.08);
            line-height: 1.7;
            max-width: 100%;
            color: #3d2f2a;
            border: 1px solid #e8e2db;
        }
        .response a {
            color: #8b7355;
            text-decoration: underline;
        }
        .response a:hover {
            color: #6b5d54;
        }
        .sources { margin-top: 30px; }
        .sources h3 { 
            color: #2a1f1a; 
            margin-bottom: 20px; 
            font-weight: 400;
            font-size: 20px;
        }
        .source-item { 
            background: white; 
            padding: 18px; 
            margin: 12px 0; 
            border-left: 4px solid #8b7355; 
            border-radius: 4px;
            box-shadow: 0 1px 6px rgba(74, 63, 55, 0.06);
            border-right: 1px solid #e8e2db;
            border-top: 1px solid #e8e2db;
            border-bottom: 1px solid #e8e2db;
        }
        .source-item strong { 
            color: #2a1f1a; 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 500;
        }
        .source-item em { 
            color: #6b5d54; 
            display: block; 
            margin: 10px 0; 
            line-height: 1.6; 
            font-style: normal;
        }
        .source-item a { 
            color: #8b7355; 
            text-decoration: none; 
            font-weight: 500; 
        }
        .source-item a:hover { 
            text-decoration: underline; 
        }
        .source-item small {
            color: #9b8b80;
        }
    </style>
</head>
<body>
    <h1>United Tribes</h1>
    <p class="tagline">Media Discovery and Consumption for the AI Era</p>
    
    <div>
        <input type="text" id="queryInput" class="query-box" placeholder="Ask us about music and books" />
        <button onclick="submitQuery()" class="submit-btn">DISCOVER</button>
    </div>
    
    <div id="response" class="response" style="display: none;"></div>
    <div id="sources" class="sources" style="display: none;"></div>
    
    <script>
        async function submitQuery() {
            const query = document.getElementById('queryInput').value;
            if (!query.trim()) return;
            
            const responseDiv = document.getElementById('response');
            const sourcesDiv = document.getElementById('sources');
            
            responseDiv.textContent = 'Mapping cultural connections...';
            responseDiv.style.display = 'block';
            sourcesDiv.style.display = 'none';
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query, k: 10})
                });
                
                const data = await response.json();
                
                // Convert URLs in text to clickable links
                let responseText = data.response;
                responseText = responseText.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
                responseText = responseText.replace(/(https?:\/\/[^\s\]]+)/g, '<a href="$1" target="_blank">$1</a>');
                
                responseDiv.innerHTML = responseText;
                
                if (data.sources && data.sources.length > 0) {
                    // Clean up source names
                    const cleanSourceName = (name) => {
                        if (name.includes('Fresh_Air')) return 'NPR Fresh Air';
                        if (name.includes('All_Songs_Considered')) return 'NPR All Songs Considered';
                        if (name.includes('Broken_Record')) return 'Broken Record Podcast';
                        if (name.includes('Sound_Opinions')) return 'Sound Opinions';
                        if (name.includes('Switched_On_Pop')) return 'Switched On Pop';
                        if (name.includes('.Txt Analysis')) {
                            return name.split('_').slice(0, 3).join(' ');
                        }
                        return name;
                    };
                    
                    // Sort sources by confidence score
                    const sortedSources = data.sources.sort((a, b) => b.confidence - a.confidence);
                    
                    sourcesDiv.innerHTML = '<h3>Sources & Evidence (Ranked by Relevance):</h3>' + 
                        sortedSources.map((source, idx) => 
                            `<div class="source-item">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong>${idx + 1}. ${cleanSourceName(source.source)}</strong>
                                    <span style="background: ${source.confidence > 0.7 ? '#4CAF50' : source.confidence > 0.4 ? '#FF9800' : '#f44336'}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                                        ${(source.confidence * 100).toFixed(0)}% relevant
                                    </span>
                                </div>
                                <em>${source.excerpt}</em>
                                ${source.relationship_type ? `<small style="color: #666;">Relationship: ${source.relationship_type}</small><br>` : ''}
                                ${source.url ? `<a href="${source.url}" target="_blank">View original source →</a>` : ''}
                            </div>`
                        ).join('');
                    sourcesDiv.style.display = 'block';
                }
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
            }
        }
        
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitQuery();
        });
    </script>
</body>
</html>
        """)

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