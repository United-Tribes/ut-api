"""
Vector store client for ut-query-service
Interfaces with ut-vector-store's enhanced S3 knowledge graph
"""

import logging
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from .contracts import VectorSearchResult

logger = logging.getLogger(__name__)

class VectorStoreClient:
    """Client for ut-vector-store service with S3 enhanced knowledge graph"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=5)  # Reduced timeout for faster startup
        
    async def initialize(self):
        """Initialize the vector store client"""
        logger.info(f"Initializing vector store client: {self.base_url}")
        
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        # Test connectivity (non-blocking - don't fail startup)
        try:
            is_healthy = await self.health_check()
            if is_healthy:
                logger.info("Vector store client initialized successfully")
            else:
                logger.warning("Vector store is not healthy, but continuing with initialization")
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            logger.info("Vector store client initialized successfully (degraded mode)")
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        logger.info("Vector store client shutdown")
    
    async def health_check(self) -> bool:
        """Check vector store health"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        k: int = 5,
        source_filter: Optional[List[str]] = None,
        entity_filter: Optional[List[str]] = None,
        min_confidence: float = 0.0
    ) -> List[VectorSearchResult]:
        """Search the enhanced knowledge graph"""
        search_request = {
            "query": query,
            "k": k,
            "min_confidence": min_confidence
        }
        
        if source_filter:
            search_request["source_filter"] = source_filter
        if entity_filter:
            search_request["entity_filter"] = entity_filter
        
        try:
            logger.info(f"Searching vector store: {query[:50]}...")
            
            async with self.session.post(
                f"{self.base_url}/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for result_data in data.get("results", []):
                        result = VectorSearchResult(
                            chunk_id=result_data.get("chunk_id", ""),
                            content=result_data.get("content", ""),
                            similarity_score=result_data.get("similarity_score", 0.0),
                            source_info=result_data.get("source_info", {}),
                            entities=result_data.get("entities", []),
                            chunk_metadata=result_data.get("chunk_metadata", {})
                        )
                        results.append(result)
                    
                    logger.info(f"Retrieved {len(results)} enhanced search results")
                    return results
                else:
                    error_text = await response.text()
                    logger.error(f"Vector search failed: {response.status} - {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            async with self.session.get(f"{self.base_url}/index/stats") as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {e}")
            return {}
    
    async def get_available_sources(self) -> List[str]:
        """Get list of available sources"""
        try:
            async with self.session.get(f"{self.base_url}/sources") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("sources", [])
                return []
        except Exception as e:
            logger.error(f"Failed to get available sources: {e}")
            return []
    
    async def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get relationships for a specific entity"""
        try:
            async with self.session.get(f"{self.base_url}/entity/{entity_name}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("relationships", [])
                return []
        except Exception as e:
            logger.error(f"Failed to get entity relationships: {e}")
            return []
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get enhanced data summary"""
        try:
            async with self.session.get(f"{self.base_url}/data/summary") as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {}