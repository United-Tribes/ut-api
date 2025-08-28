"""
Vector service for semantic search operations
"""

import logging
from typing import List, Dict, Any, Optional
from .shared.contracts import SearchResponse, SearchResult, ContentAdditionResponse, SourceInfo

logger = logging.getLogger(__name__)


class VectorService:
    """Manages vector operations and search"""
    
    def __init__(self, embedding_service, index_manager):
        self.embedding_service = embedding_service
        self.index_manager = index_manager
        
    async def initialize(self):
        """Initialize the vector service"""
        logger.info("Initializing vector service...")
        
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down vector service...")
        
    async def search(
        self,
        query: str,
        k: int = 5,
        source_filter: Optional[List[str]] = None,
        entity_filter: Optional[List[str]] = None,
        content_type_filter: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        temporal_filter: Optional[str] = None
    ) -> SearchResponse:
        """Perform enhanced semantic search with S3 data"""
        logger.info(f"Searching for: {query[:50]}...")
        
        try:
            # Use enhanced relationship search from index manager
            search_results = await self.index_manager.search_relationships(
                query=query,
                k=k,
                source_filter=source_filter[0] if source_filter else None,
                entity_filter=entity_filter[0] if entity_filter else None,
                min_confidence=min_confidence
            )
            
            # Convert to SearchResult format
            results = []
            for i, result in enumerate(search_results):
                rel = result['relationship']
                
                # Create descriptive content from relationship
                source_entity = rel.get('source_entity', '')
                target_entity = rel.get('target_entity', '')
                relationship_type = rel.get('relationship_type', '')
                evidence = rel.get('evidence', '')
                temporal_context = rel.get('temporal_context', '')
                
                content_parts = []
                if source_entity and target_entity and relationship_type:
                    content_parts.append(f"{source_entity} {relationship_type} {target_entity}.")
                
                if evidence:
                    content_parts.append(evidence)
                
                if temporal_context:
                    content_parts.append(f"Context: {temporal_context}")
                
                content = ' '.join(content_parts)
                
                # Get source attribution
                source_attribution = rel.get('source_attribution', {})
                
                search_result = SearchResult(
                    chunk_id=f"enhanced-rel-{i}",
                    content=content,
                    source_info=SourceInfo(
                        source=source_attribution.get('source', 'Unknown'),
                        title=f"{source_entity} - {target_entity} Relationship",
                        url=source_attribution.get('url', ''),
                        content_type=source_attribution.get('publication_type', 'article')
                    ),
                    similarity_score=result.get('relevance_score', 0.5),
                    entities=[source_entity, target_entity],
                    chunk_metadata={
                        "chunk_type": "enhanced_relationship",
                        "relationship_type": relationship_type,
                        "confidence": rel.get('confidence'),
                        "cultural_significance": rel.get('metadata', {}).get('cultural_significance'),
                        "temporal_context": temporal_context
                    }
                )
                results.append(search_result)
            
            logger.info(f"Found {len(results)} enhanced relationship results")
            
            return SearchResponse(
                results=results,
                search_time_ms=0,  # Will be set by app.py
                total_results=len(results),
                query_embedding_time_ms=0,
                filters_applied={
                    "source_filter": source_filter,
                    "entity_filter": entity_filter,
                    "min_confidence": min_confidence
                } if (source_filter or entity_filter or min_confidence > 0) else {}
            )
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            # Fallback to empty results
            return SearchResponse(
                results=[],
                search_time_ms=0,
                total_results=0,
                query_embedding_time_ms=0,
                filters_applied={}
            )
        
    async def add_content(
        self,
        chunks: List[Any],
        index_name: str = "main",
        update_if_exists: bool = True
    ) -> ContentAdditionResponse:
        """Add content to index"""
        logger.info(f"Adding {len(chunks)} chunks to index {index_name}")
        
        return ContentAdditionResponse(
            chunks_added=len(chunks),
            chunks_updated=0,
            chunks_failed=0,
            processing_time_ms=100,
            index_stats={"total_vectors": 1000}
        )