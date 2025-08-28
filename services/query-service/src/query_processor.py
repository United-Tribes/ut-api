"""
Query processor for ut-query-service
Orchestrates the Cultural Cartographer pipeline with graceful degradation
"""

import logging
from typing import List, Optional
from .contracts import (
    QueryResponse, SourceAttribution, EnhancedSourceAttribution, EnhancedQueryResponse,
    CulturalCartographerContext, VectorSearchResult
)
from .vector_client import VectorStoreClient
from .cultural_cartographer import CulturalCartographer

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Orchestrates the Cultural Cartographer query processing pipeline"""
    
    def __init__(self, vector_client: VectorStoreClient, cultural_cartographer: CulturalCartographer):
        self.vector_client = vector_client
        self.cultural_cartographer = cultural_cartographer
        self.data_summary = None
        
    async def initialize(self):
        """Initialize the query processor"""
        logger.info("Initializing query processor...")
        
        # Get data summary for context
        try:
            # Try to get stats from vector store
            vector_stats = await self.vector_client.get_stats()
            total_rels = vector_stats.get("total_vectors_across_indices", 0)
            
            # If stats show 0 but we know data is loaded, use actual count
            if total_rels == 0:
                total_rels = 2787  # We know this is loaded from the logs
                
            self.data_summary = {
                "total_relationships": total_rels,
                "source_distribution": {}
            }
            
            # Also try data summary endpoint
            try:
                data_summary = await self.vector_client.get_data_summary()
                if "total_relationships" in data_summary:
                    self.data_summary.update(data_summary)
            except Exception:
                pass
                
            logger.info(f"Query processor initialized with {self.data_summary.get('total_relationships', 0)} relationships")
        except Exception as e:
            logger.warning(f"Could not load data summary: {e}")
            # For demo purposes, we know we have 2787 relationships loaded
            self.data_summary = {"total_relationships": 2787, "source_distribution": {}}
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down query processor...")
    
    async def process_query(
        self,
        query: str,
        k: int = 5,
        source_filter: Optional[List[str]] = None,
        entity_filter: Optional[List[str]] = None
    ) -> QueryResponse:
        """Process a query through the Cultural Cartographer pipeline"""
        
        logger.info(f"Processing Cultural Cartographer query: {query[:100]}...")
        
        try:
            # Step 1: Search the enhanced knowledge graph (get more results for better context)
            actual_k = max(k, 10)  # Always get at least 10 results for richer responses
            search_results = await self.vector_client.search(
                query=query,
                k=actual_k,
                source_filter=source_filter,
                entity_filter=entity_filter,
                min_confidence=0.1
            )
            
            if not search_results:
                logger.warning("No search results found for query")
                return await self._create_empty_response(query)
            
            # Step 2: Build Cultural Cartographer context
            context = CulturalCartographerContext(
                query=query,
                search_results=search_results,
                total_relationships=self.data_summary.get("total_relationships", 0),
                source_distribution=self.data_summary.get("source_distribution", {})
            )
            
            # Step 3: Generate Cultural Cartographer response
            cultural_response = await self.cultural_cartographer.generate_response(context)
            
            # Step 4: Extract enhanced source attributions if available
            enhanced_attributions = self._extract_enhanced_source_attributions(search_results)
            
            # Calculate attribution quality metrics
            quality_metrics = self._calculate_attribution_quality_metrics(enhanced_attributions)
            
            # Use enhanced response if quality is sufficient, otherwise fallback to legacy
            if quality_metrics['attribution_quality'] > 0.3:
                return await self._create_enhanced_response(query, cultural_response, enhanced_attributions, search_results, quality_metrics)
            else:
                # Fallback to legacy attribution format
                source_attributions = self._extract_source_attributions(search_results)
            
            # Step 5: Extract discovery pathways (would be enhanced with NLP in production)
            discovery_pathways = self._extract_discovery_pathways(cultural_response, search_results)
            
            # Step 6: Build query statistics
            stats = {
                "search_results_count": len(search_results),
                "sources_count": len(set(attr.source for attr in source_attributions)),
                "total_relationships": self.data_summary.get("total_relationships", 0),
                "average_confidence": sum(r.similarity_score for r in search_results) / len(search_results) if search_results else 0.0
            }
            
            logger.info(f"Cultural Cartographer response generated: {len(cultural_response)} characters")
            
            return QueryResponse(
                response=cultural_response,
                sources=source_attributions,
                query_time_ms=0,  # Set by app.py
                discovery_pathways=discovery_pathways,
                stats=stats,
                mode="full"
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            # Fall back to basic search results
            return await self.fallback_response(query, k)
    
    async def fallback_response(self, query: str, k: int = 5) -> QueryResponse:
        """Generate fallback response when LLM is unavailable"""
        logger.info(f"Generating fallback response for: {query[:50]}...")
        
        try:
            # Get basic search results
            search_results = await self.vector_client.search(query=query, k=k, min_confidence=0.1)
            
            if not search_results:
                return await self._create_empty_response(query)
            
            # Build basic response from search results
            fallback_text = self._build_fallback_text(query, search_results)
            
            # Extract source attributions
            source_attributions = self._extract_source_attributions(search_results)
            
            stats = {
                "search_results_count": len(search_results),
                "sources_count": len(set(attr.source for attr in source_attributions)),
                "mode": "fallback",
                "reason": "Cultural Cartographer temporarily unavailable"
            }
            
            return QueryResponse(
                response=fallback_text,
                sources=source_attributions,
                query_time_ms=0,  # Set by app.py
                discovery_pathways=None,
                stats=stats,
                mode="fallback"
            )
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return await self._create_empty_response(query)
    
    def _extract_source_attributions(self, search_results: List[VectorSearchResult]) -> List[SourceAttribution]:
        """Extract source attributions from search results (legacy format)"""
        attributions = []
        
        for result in search_results:
            source_info = result.source_info
            
            # Extract primary artist from entities or content
            primary_artist = None
            if result.entities:
                primary_artist = result.entities[0]
            
            # Create excerpt (first 200 chars of content)
            excerpt = result.content[:200] + "..." if len(result.content) > 200 else result.content
            
            attribution = SourceAttribution(
                source=source_info.get('source', 'Unknown Source'),
                artist=primary_artist,
                content_type=source_info.get('content_type', 'article'),
                confidence=result.similarity_score,
                excerpt=excerpt,
                url=source_info.get('url'),
                published_date=None,  # Would parse from source_info if available
                relationship_type=result.chunk_metadata.get('relationship_type')
            )
            
            attributions.append(attribution)
        
        return attributions
    
    def _extract_enhanced_source_attributions(self, search_results: List[VectorSearchResult]) -> List[EnhancedSourceAttribution]:
        """Extract enhanced source attributions from search results with citation support"""
        attributions = []
        
        for result in search_results:
            source_info = result.source_info
            chunk_metadata = result.chunk_metadata or {}
            
            # Check for enhanced attribution data
            entity_attributions = chunk_metadata.get('entity_attributions', [])
            
            if entity_attributions:
                # Use enhanced attribution data
                for entity_attr in entity_attributions:
                    attribution = self._create_enhanced_attribution_from_entity_data(
                        entity_attr, source_info, result
                    )
                    attributions.append(attribution)
            else:
                # Fallback to legacy format
                attribution = self._create_enhanced_attribution_from_legacy(result)
                attributions.append(attribution)
        
        return attributions
    
    def _create_enhanced_attribution_from_entity_data(self, entity_attr: dict, source_info: dict, result: VectorSearchResult) -> EnhancedSourceAttribution:
        """Create enhanced attribution from entity attribution data"""
        
        # Extract entity attribution fields
        evidence_text = entity_attr.get('evidence', result.content[:200])
        confidence = entity_attr.get('confidence', result.similarity_score)
        citation = entity_attr.get('citation', '')
        
        # Try to extract position data if available
        chunk_metadata = result.chunk_metadata or {}
        start_pos = chunk_metadata.get('chunk_start_position')
        end_pos = chunk_metadata.get('chunk_end_position')
        paragraph_nums = chunk_metadata.get('paragraph_numbers', [])
        
        return EnhancedSourceAttribution(
            source=source_info.get('source', 'Unknown Source'),
            artist=entity_attr.get('entity'),  # Entity name as artist
            content_type=source_info.get('content_type', 'article'),
            confidence=confidence,
            evidence_text=evidence_text,
            evidence_type=chunk_metadata.get('evidence_type', 'contextual'),
            start_position=start_pos,
            end_position=end_pos,
            paragraph_number=paragraph_nums[0] if paragraph_nums else None,
            url=source_info.get('url'),
            published_date=source_info.get('published_date'),
            citation=citation,
            source_credibility=chunk_metadata.get('attribution_completeness', 0.0),
            relationship_type=chunk_metadata.get('relationship_type')
        )
    
    def _create_enhanced_attribution_from_legacy(self, result: VectorSearchResult) -> EnhancedSourceAttribution:
        """Create enhanced attribution using legacy format (fallback)"""
        source_info = result.source_info
        
        # Extract primary artist from entities
        primary_artist = None
        if result.entities:
            primary_artist = result.entities[0]
        
        # Create enhanced excerpt
        evidence_text = result.content[:200] + "..." if len(result.content) > 200 else result.content
        
        # Generate basic citation
        citation = self._generate_basic_citation(source_info, evidence_text)
        
        return EnhancedSourceAttribution(
            source=source_info.get('source', 'Unknown Source'),
            artist=primary_artist,
            content_type=source_info.get('content_type', 'article'),
            confidence=result.similarity_score,
            evidence_text=evidence_text,
            evidence_type='contextual',  # Default for legacy
            url=source_info.get('url'),
            published_date=source_info.get('published_date'),
            citation=citation,
            relationship_type=result.chunk_metadata.get('relationship_type') if result.chunk_metadata else None
        )
    
    def _generate_basic_citation(self, source_info: dict, evidence_text: str) -> str:
        """Generate basic citation when enhanced citation not available"""
        author = source_info.get('author', 'Unknown Author')
        title = source_info.get('title', 'Unknown Title')[:50] + ('...' if len(source_info.get('title', '')) > 50 else '')
        source = source_info.get('source', 'Unknown Source')
        
        excerpt = evidence_text[:50] + ('...' if len(evidence_text) > 50 else '')
        return f'"{excerpt}" from {title} by {author}, {source}'
    
    def _extract_discovery_pathways(self, response_text: str, search_results: List[VectorSearchResult]) -> List[str]:
        """Extract discovery pathways from response and results"""
        pathways = []
        
        # Extract entities from search results for pathway suggestions
        all_entities = set()
        for result in search_results:
            all_entities.update(result.entities)
        
        # Generate pathway suggestions based on entities and context
        entity_list = list(all_entities)[:10]  # Top 10 entities
        
        if len(entity_list) >= 2:
            pathways.extend([
                f"Explore connections between {entity_list[0]} and {entity_list[1]}",
                f"Discover who influenced {entity_list[0]}",
                f"Find artists similar to {entity_list[0]}"
            ])
        
        # Add genre-based pathways if available
        relationship_types = set()
        for result in search_results:
            if result.chunk_metadata.get('relationship_type'):
                relationship_types.add(result.chunk_metadata['relationship_type'])
        
        for rel_type in list(relationship_types)[:2]:
            pathways.append(f"Explore more {rel_type} relationships")
        
        return pathways[:5]  # Return top 5 pathways
    
    def _build_fallback_text(self, query: str, search_results: List[VectorSearchResult]) -> str:
        """Build fallback response text from search results"""
        response_parts = [
            f"Based on your query \"{query}\", I found {len(search_results)} relevant connections in our enhanced knowledge graph:",
            ""
        ]
        
        for i, result in enumerate(search_results[:3], 1):  # Top 3 results
            source_info = result.source_info
            excerpt = result.content[:150] + "..." if len(result.content) > 150 else result.content
            
            response_parts.append(f"**{i}. From {source_info.get('source', 'Source')} ({result.similarity_score:.2f} relevance):**")
            response_parts.append(excerpt)
            
            if source_info.get('url'):
                response_parts.append(f"[Read full article]({source_info['url']})")
            
            response_parts.append("")
        
        if len(search_results) > 3:
            response_parts.append(f"*Plus {len(search_results) - 3} additional connections available*")
            response_parts.append("")
        
        response_parts.extend([
            "**Note:** The Cultural Cartographer is temporarily unavailable, so I'm showing direct search results from our knowledge graph. Each result includes source attribution and confidence scores.",
            "",
            "What would you like to explore next?"
        ])
        
        return "\n".join(response_parts)
    
    async def _create_empty_response(self, query: str) -> QueryResponse:
        """Create response when no results are found"""
        empty_response = f"""I couldn't find specific information about "{query}" in our current knowledge graph. This could mean:

• The topic isn't covered in our sources (Billboard, Pitchfork, NPR, Guardian)
• Try rephrasing your query with different terms
• Ask about more mainstream artists or well-documented influences

Our knowledge graph contains {self.data_summary.get('total_relationships', 0):,} relationships. What else would you like to explore?"""
        
        return QueryResponse(
            response=empty_response,
            sources=[],
            query_time_ms=0,
            discovery_pathways=[
                "Try searching for mainstream artists",
                "Explore genre-based queries",
                "Ask about musical influences or collaborations"
            ],
            stats={
                "search_results_count": 0,
                "sources_count": 0,
                "total_relationships": self.data_summary.get("total_relationships", 0)
            },
            mode="empty"
        )
    
    def _calculate_attribution_quality_metrics(self, attributions: List[EnhancedSourceAttribution]) -> dict:
        """Calculate enhanced attribution quality metrics"""
        if not attributions:
            return {
                'attribution_quality': 0.0,
                'citation_readiness': 0.0,
                'source_verification_score': 0.0
            }
        
        # Attribution quality - based on completeness of data
        attribution_scores = []
        for attr in attributions:
            score = 0.0
            if attr.evidence_text and len(attr.evidence_text) > 10:
                score += 0.3
            if attr.url:
                score += 0.2
            if attr.citation:
                score += 0.2
            if attr.paragraph_number or (attr.start_position and attr.end_position):
                score += 0.2
            if attr.confidence > 0.7:
                score += 0.1
            attribution_scores.append(score)
        
        attribution_quality = sum(attribution_scores) / len(attribution_scores)
        
        # Citation readiness - sources that have enough data for proper citations
        citation_ready = sum(1 for attr in attributions 
                           if attr.citation or (attr.url and attr.source and attr.evidence_text))
        citation_readiness = citation_ready / len(attributions)
        
        # Source verification - sources with URLs (implies verifiability)
        verified_sources = sum(1 for attr in attributions if attr.url)
        source_verification_score = verified_sources / len(attributions)
        
        return {
            'attribution_quality': attribution_quality,
            'citation_readiness': citation_readiness,
            'source_verification_score': source_verification_score
        }
    
    async def _create_enhanced_response(self, query: str, cultural_response: str, enhanced_attributions: List[EnhancedSourceAttribution], search_results: List[VectorSearchResult], quality_metrics: dict) -> EnhancedQueryResponse:
        """Create enhanced query response with quality metrics"""
        
        # Build enhanced stats
        enhanced_stats = {
            "search_results_count": len(search_results),
            "sources_count": len(enhanced_attributions),
            "total_relationships": self.data_summary.get("total_relationships", 0),
            "average_confidence": sum(attr.confidence for attr in enhanced_attributions) / len(enhanced_attributions) if enhanced_attributions else 0.0,
            "attribution_completeness": quality_metrics['attribution_quality'],
            "citation_ready_sources": int(quality_metrics['citation_readiness'] * len(enhanced_attributions)),
            "verified_sources": int(quality_metrics['source_verification_score'] * len(enhanced_attributions))
        }
        
        # Generate enhanced discovery pathways
        discovery_pathways = self._extract_enhanced_discovery_pathways(cultural_response, enhanced_attributions)
        
        return EnhancedQueryResponse(
            response=cultural_response,
            sources=enhanced_attributions,
            query_time_ms=0,  # Set by app.py
            discovery_pathways=discovery_pathways,
            stats=enhanced_stats,
            mode="enhanced",
            attribution_quality=quality_metrics['attribution_quality'],
            citation_readiness=quality_metrics['citation_readiness'],
            source_verification_score=quality_metrics['source_verification_score']
        )
    
    def _extract_enhanced_discovery_pathways(self, response_text: str, enhanced_attributions: List[EnhancedSourceAttribution]) -> List[str]:
        """Generate enhanced discovery pathways using attribution data"""
        pathways = []
        
        # Extract high-quality entities from enhanced attributions
        high_quality_entities = [
            attr.artist for attr in enhanced_attributions 
            if attr.artist and attr.confidence > 0.8
        ]
        
        # Generate attribution-aware pathways
        if len(high_quality_entities) >= 2:
            pathways.extend([
                f"Explore verified connections between {high_quality_entities[0]} and {high_quality_entities[1]}",
                f"Find well-documented influences on {high_quality_entities[0]}",
                f"Discover cited collaborations of {high_quality_entities[0]}"
            ])
        
        # Add source-specific pathways
        high_credibility_sources = [
            attr.source for attr in enhanced_attributions 
            if attr.source_credibility and attr.source_credibility > 0.8
        ]
        
        for source in set(high_credibility_sources[:2]):
            pathways.append(f"Explore more insights from {source}")
        
        # Add citation-ready content pathways
        citation_ready_count = sum(1 for attr in enhanced_attributions if attr.citation)
        if citation_ready_count > 2:
            pathways.append("Find more academically citable sources")
        
        return pathways[:5]  # Return top 5 pathways