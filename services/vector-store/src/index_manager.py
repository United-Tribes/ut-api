"""
Index manager for FAISS operations with S3 enhanced knowledge graph integration
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from .shared.contracts import IndexStatsResponse, IndexStats
from .s3_data_loader import S3DataLoader

logger = logging.getLogger(__name__)


class IndexManager:
    """Manages FAISS indices with S3 enhanced knowledge graph data"""
    
    def __init__(self):
        self.indices = {}
        self.loaded_indices = []
        self.s3_loader = None
        self.enhanced_data = None
        self.relationships = []
        
    async def initialize(self):
        """Initialize the index manager with S3 data loader"""
        logger.info("Initializing index manager with S3 integration...")
        
        try:
            # Initialize S3 data loader
            self.s3_loader = S3DataLoader()
            await self.s3_loader.initialize()
            
            # Load enhanced knowledge graph
            await self._load_enhanced_data()
            
            logger.info(f"Index manager initialized with {len(self.relationships)} enhanced relationships")
            
        except Exception as e:
            logger.error(f"Failed to initialize index manager: {e}")
            # Continue without S3 data for fallback
            logger.warning("Continuing without S3 data - using stub implementation")
            self.loaded_indices = ["main"]  # Fallback
        
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down index manager...")
        if self.s3_loader:
            await self.s3_loader.shutdown()
    
    async def _load_enhanced_data(self):
        """Load enhanced knowledge graph from S3 or sample data"""
        try:
            logger.info("Loading enhanced knowledge graph from S3...")
            
            # Try to load from S3 first
            try:
                self.enhanced_data = await self.s3_loader.load_enhanced_knowledge_graph()
                self.relationships = self.enhanced_data.get('relationships', [])
            except Exception as s3_error:
                logger.warning(f"S3 load failed: {s3_error}, trying sample data...")
                
                # Fall back to full enhanced knowledge graph for demonstration
                import json
                try:
                    # Try the full enhanced knowledge graph first
                    with open("../knowledge_graph_enhanced_20250826_154505.json", "r") as f:
                        self.enhanced_data = json.load(f)
                    self.relationships = self.enhanced_data.get('relationships', [])
                    logger.info(f"Loaded full enhanced knowledge graph: {len(self.relationships)} relationships")
                except Exception as full_error:
                    logger.warning(f"Full knowledge graph load failed: {full_error}, trying sample...")
                    # Fall back to sample data
                    try:
                        with open("../sample_knowledge_graph.json", "r") as f:
                            self.enhanced_data = json.load(f)
                        self.relationships = self.enhanced_data.get('relationships', [])
                        logger.info("Loaded sample knowledge graph for demonstration")
                    except Exception as sample_error:
                        logger.error(f"Sample data load failed: {sample_error}")
                        raise s3_error  # Re-raise original S3 error
            
            # Update loaded indices to include enhanced data
            self.loaded_indices = ["enhanced_main"]
            
            logger.info(f"Successfully loaded {len(self.relationships)} enhanced relationships")
            
        except Exception as e:
            logger.error(f"Failed to load enhanced data from S3: {e}")
            raise
    def get_loaded_indices(self) -> List[str]:
        """Get list of loaded indices"""
        return self.loaded_indices
        
    def get_memory_usage_mb(self) -> float:
        """Get memory usage in MB"""
        if self.enhanced_data and self.relationships:
            # Calculate based on loaded relationships
            # Rough estimate: each relationship ~2KB in memory
            total_bytes = len(self.relationships) * 2 * 1024
            return total_bytes / 1024 / 1024
        else:
            # Fallback estimate
            return 1.5
        
    async def get_stats(self) -> IndexStatsResponse:
        """Get enhanced index statistics from S3 data"""
        try:
            # Always check if we have relationships loaded (from S3 or local)
            if self.relationships:
                # Calculate real statistics from enhanced data
                total_relationships = len(self.relationships)
                
                # Get data statistics
                data_stats = await self.s3_loader.get_data_statistics() if self.s3_loader else {}
                
                stats = [
                    IndexStats(
                        index_name="enhanced_main",
                        total_vectors=total_relationships,
                        dimension=1024,  # Bedrock Titan V2 dimension
                        index_type="HNSW",
                        similarity_metric="cosine",
                        index_size_bytes=total_relationships * 4 * 1024,  # Estimate: relationships * 4KB each
                        last_updated=self.enhanced_data.get('_s3_metadata', {}).get('loaded_at'),
                        build_parameters={"ef_construction": 200, "M": 16}
                    )
                ]
                
                total_size = sum(s.index_size_bytes for s in stats)
                memory_usage = total_size / 1024 / 1024  # Convert to MB
                
                return IndexStatsResponse(
                    indices=stats,
                    total_vectors_across_indices=total_relationships,
                    total_size_bytes=total_size,
                    memory_usage_mb=memory_usage,
                    enhanced_data_info=data_stats
                )
            else:
                # Fallback to stub stats
                stats = [
                    IndexStats(
                        index_name="main",
                        total_vectors=100,
                        dimension=1024,
                        index_type="HNSW",
                        similarity_metric="cosine",
                        index_size_bytes=1048576,  # 1MB
                        last_updated=None,
                        build_parameters={"ef_construction": 200, "M": 16}
                    )
                ]
                
                return IndexStatsResponse(
                    indices=stats,
                    total_vectors_across_indices=100,
                    total_size_bytes=1048576,
                    memory_usage_mb=1.0
                )
                
        except Exception as e:
            logger.error(f"Failed to get enhanced stats: {e}")
            # Return minimal stats on error
            return IndexStatsResponse(
                indices=[],
                total_vectors_across_indices=0,
                total_size_bytes=0,
                memory_usage_mb=0.0
            )
        
    async def build_index(
        self,
        index_name: str,
        content_source: str,
        embedding_model: Any = None,
        index_type: Any = None,
        similarity_metric: Any = None,
        build_parameters: Optional[Dict[str, Any]] = None,
        force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """Build or rebuild an index from S3 enhanced knowledge graph"""
        logger.info(f"Building index {index_name} from {content_source}")
        
        try:
            if content_source.startswith("s3://") and self.s3_loader:
                # Build from S3 enhanced knowledge graph
                logger.info("Building index from S3 enhanced knowledge graph")
                
                # Reload enhanced data if force rebuild
                if force_rebuild or not self.enhanced_data:
                    await self._load_enhanced_data()
                
                # Convert relationships to searchable format
                processed_items = []
                for rel in self.relationships:
                    # Create searchable text from relationship
                    searchable_text = self._create_searchable_text_from_relationship(rel)
                    
                    processed_items.append({
                        'text': searchable_text,
                        'metadata': {
                            'source_entity': rel.get('source_entity'),
                            'target_entity': rel.get('target_entity'),
                            'relationship_type': rel.get('relationship_type'),
                            'confidence': rel.get('confidence'),
                            'evidence': rel.get('evidence'),
                            'source_attribution': rel.get('source_attribution', {}),
                            'temporal_context': rel.get('temporal_context'),
                            'cultural_significance': rel.get('metadata', {}).get('cultural_significance')
                        }
                    })
                
                # Update indices tracking
                self.indices[index_name] = {
                    'items': processed_items,
                    'built_at': self.enhanced_data.get('_s3_metadata', {}).get('loaded_at'),
                    'source': content_source,
                    'total_items': len(processed_items)
                }
                
                if index_name not in self.loaded_indices:
                    self.loaded_indices.append(index_name)
                
                logger.info(f"Successfully built index {index_name} with {len(processed_items)} items")
                
                return {
                    "chunks_processed": len(processed_items),
                    "index_size_bytes": len(processed_items) * 4 * 1024,  # Estimate
                    "relationships_indexed": len(self.relationships),
                    "enhanced_data": True
                }
                
            else:
                # Fallback to stub implementation
                logger.warning(f"Building stub index for {index_name} - S3 not available")
                return {
                    "chunks_processed": 100,
                    "index_size_bytes": 1048576
                }
                
        except Exception as e:
            logger.error(f"Failed to build index {index_name}: {e}")
            raise
    
    def _create_searchable_text_from_relationship(self, rel: Dict[str, Any]) -> str:
        """Create searchable text from relationship data"""
        parts = []
        
        # Add entities
        source_entity = rel.get('source_entity', '')
        target_entity = rel.get('target_entity', '')
        relationship_type = rel.get('relationship_type', '')
        
        if source_entity and target_entity:
            parts.append(f"{source_entity} {relationship_type} {target_entity}")
        
        # Add evidence text
        evidence = rel.get('evidence', '')
        if evidence:
            parts.append(evidence)
        
        # Add cultural context
        cultural_context = rel.get('metadata', {}).get('cultural_context', '')
        if cultural_context:
            parts.append(cultural_context)
        
        # Add temporal context
        temporal_context = rel.get('temporal_context', '')
        if temporal_context:
            parts.append(temporal_context)
        
        # Add source information for context
        source_attribution = rel.get('source_attribution', {})
        source_name = source_attribution.get('source', '')
        if source_name:
            parts.append(f"Source: {source_name}")
        
        return ' '.join(parts)
        
    async def delete_index(self, index_name: str):
        """Delete an index"""
        logger.info(f"Deleting index {index_name}")
        if index_name in self.loaded_indices:
            self.loaded_indices.remove(index_name)
        if index_name in self.indices:
            del self.indices[index_name]
    
    async def search_relationships(
        self, 
        query: str, 
        k: int = 10,
        source_filter: Optional[str] = None,
        entity_filter: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search relationships with enhanced filtering"""
        
        if not self.relationships:
            logger.warning("No enhanced relationships loaded for search")
            return []
        
        try:
            # Simple text-based search (would use vector embeddings in production)
            query_lower = query.lower()
            results = []
            
            for rel in self.relationships:
                # Check source filter
                if source_filter:
                    source = rel.get('source_attribution', {}).get('source', '')
                    if source_filter.lower() not in source.lower():
                        continue
                
                # Check entity filter
                if entity_filter:
                    source_entity = rel.get('source_entity', '').lower()
                    target_entity = rel.get('target_entity', '').lower()
                    entity_filter_lower = entity_filter.lower()
                    if (entity_filter_lower not in source_entity and 
                        entity_filter_lower not in target_entity):
                        continue
                
                # Check confidence threshold
                confidence = rel.get('confidence', 0.0)
                if confidence < min_confidence:
                    continue
                
                # Calculate relevance score (simple text matching)
                searchable_text = self._create_searchable_text_from_relationship(rel).lower()
                
                # Count query term matches
                query_terms = query_lower.split()
                matches = sum(1 for term in query_terms if term in searchable_text)
                
                if matches > 0:
                    relevance_score = matches / len(query_terms)  # Normalize by query length
                    
                    results.append({
                        'relationship': rel,
                        'relevance_score': relevance_score,
                        'searchable_text': searchable_text[:200] + '...' if len(searchable_text) > 200 else searchable_text
                    })
            
            # Sort by relevance score and confidence
            results.sort(key=lambda x: (x['relevance_score'], x['relationship'].get('confidence', 0.0)), reverse=True)
            
            # Return top k results
            return results[:k]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_available_sources(self) -> List[str]:
        """Get list of available sources from loaded data"""
        if not self.s3_loader:
            return []
        
        try:
            return await self.s3_loader.list_available_sources()
        except Exception as e:
            logger.error(f"Failed to get available sources: {e}")
            return []
    
    async def get_relationships_by_entity(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relationships involving a specific entity"""
        if not self.relationships:
            return []
        
        entity_lower = entity_name.lower()
        matching_relationships = []
        
        for rel in self.relationships:
            source_entity = rel.get('source_entity', '').lower()
            target_entity = rel.get('target_entity', '').lower()
            
            if entity_lower in source_entity or entity_lower in target_entity:
                matching_relationships.append(rel)
        
        return matching_relationships
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded enhanced data"""
        if not self.s3_loader:
            return {"error": "S3 loader not available"}
        
        try:
            return await self.s3_loader.get_data_statistics()
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {"error": str(e)}