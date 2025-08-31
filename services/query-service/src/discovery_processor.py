"""
Discovery-oriented query processor
Provides narrative-driven cultural exploration with cross-media pathways
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscoveryProcessor:
    """Process queries with discovery-oriented narrative structure"""
    
    def __init__(self):
        self.narrative_prompts = {
            'temporal_bridge': "This connection spans from {era1} to {era2}, showing how {theme} evolved over {span} years",
            'cultural_thread': "Part of the {thread_name} narrative: {description}",
            'discovery_pathway': "Explore deeper through {pathway_type}: {suggestion}",
            'significance': "Cultural significance: {score:.1%} - {reason}"
        }
    
    def enhance_sources_with_discovery(self, sources: List[Dict], knowledge_graph: Dict) -> List[Dict]:
        """Enhance sources with discovery-oriented metadata"""
        
        enhanced_sources = []
        narrative_threads = knowledge_graph.get('narrative_threads', {})
        temporal_org = knowledge_graph.get('temporal_organization', {})
        
        for source in sources:
            enhanced = source.copy()
            
            # Find matching relationship in knowledge graph
            relationship = self._find_relationship_in_graph(
                source.get('artist', ''),
                source.get('content', ''),
                knowledge_graph.get('relationships', [])
            )
            
            if relationship:
                # Add temporal context
                if 'temporal_context' in relationship:
                    enhanced['temporal_context'] = relationship['temporal_context']
                    enhanced['era'] = relationship['temporal_context'].get('era_name', 'Contemporary')
                
                # Add narrative thread
                if 'narrative_thread' in relationship:
                    thread = relationship['narrative_thread']
                    enhanced['narrative_thread'] = thread.get('thread_name', '')
                    enhanced['narrative_description'] = thread.get('thread_description', '')
                
                # Add discovery pathways
                if 'discovery_pathways' in relationship:
                    enhanced['discovery_pathways'] = relationship['discovery_pathways']
                
                # Add cultural significance
                if 'cultural_significance' in relationship:
                    enhanced['cultural_significance'] = relationship['cultural_significance']
                
                # Transform content to narrative format
                if 'narrative_content' in relationship:
                    enhanced['narrative_content'] = relationship['narrative_content']
            
            enhanced_sources.append(enhanced)
        
        return enhanced_sources
    
    def _find_relationship_in_graph(self, artist: str, content: str, relationships: List[Dict]) -> Optional[Dict]:
        """Find matching relationship in knowledge graph"""
        
        artist_lower = artist.lower()
        content_lower = content.lower()
        
        for rel in relationships:
            if (rel.get('artist_name', '').lower() == artist_lower or 
                rel.get('primary_artist', '').lower() == artist_lower):
                
                # Check if content matches
                rel_content = rel.get('content', '').lower()
                if any(word in rel_content for word in content_lower.split()[:5]):
                    return rel
        
        return None
    
    def generate_discovery_response(self, query: str, sources: List[Dict], knowledge_graph: Dict) -> str:
        """Generate narrative-driven discovery response"""
        
        # Group sources by era and narrative thread
        eras = {}
        threads = {}
        
        for source in sources:
            era = source.get('era', 'Contemporary')
            if era not in eras:
                eras[era] = []
            eras[era].append(source)
            
            thread = source.get('narrative_thread', 'General')
            if thread not in threads:
                threads[thread] = []
            threads[thread].append(source)
        
        # Build narrative response
        response_parts = []
        
        # Start with temporal context
        if len(eras) > 1:
            era_names = list(eras.keys())
            response_parts.append(
                f"Your query spans multiple eras of music history: {', '.join(era_names)}. "
            )
        elif eras:
            era_name = list(eras.keys())[0]
            response_parts.append(f"This exploration takes us to the {era_name} era. ")
        
        # Add narrative thread context
        if len(threads) > 1:
            response_parts.append(
                f"These connections weave through {len(threads)} cultural narratives. "
            )
        
        # Add main content synthesis
        for source in sources[:3]:  # Focus on top sources
            if 'narrative_content' in source:
                response_parts.append(source['narrative_content'] + " ")
            else:
                # Fallback to regular content
                response_parts.append(f"{source.get('excerpt', source.get('content', ''))} ")
        
        # Add discovery pathways
        discovery_paths = []
        for source in sources:
            if 'discovery_pathways' in source:
                for pathway in source['discovery_pathways'][:2]:
                    path_str = f"{pathway['type']} {pathway['title']}"
                    if path_str not in discovery_paths:
                        discovery_paths.append(path_str)
        
        if discovery_paths:
            response_parts.append(
                f"\n\n🔍 Discovery Pathways:\n" + "\n".join(f"• {path}" for path in discovery_paths[:5])
            )
        
        # Add cultural significance insight
        high_significance = [s for s in sources if s.get('cultural_significance', 0) > 0.7]
        if high_significance:
            response_parts.append(
                f"\n\n⭐ High Cultural Significance: These connections represent pivotal moments in music history."
            )
        
        return " ".join(response_parts)
    
    def extract_discovery_metadata(self, sources: List[Dict]) -> Dict[str, Any]:
        """Extract discovery-oriented metadata from sources"""
        
        metadata = {
            'eras_covered': list(set(s.get('era', 'Contemporary') for s in sources)),
            'narrative_threads': list(set(s.get('narrative_thread', '') for s in sources if s.get('narrative_thread'))),
            'discovery_pathways': [],
            'average_cultural_significance': 0.0,
            'temporal_span': None
        }
        
        # Collect unique discovery pathways
        pathways = {}
        for source in sources:
            if 'discovery_pathways' in source:
                for pathway in source['discovery_pathways']:
                    key = f"{pathway['type']}_{pathway['title']}"
                    if key not in pathways:
                        pathways[key] = pathway
        
        metadata['discovery_pathways'] = list(pathways.values())[:10]
        
        # Calculate average cultural significance
        significances = [s.get('cultural_significance', 0.5) for s in sources]
        if significances:
            metadata['average_cultural_significance'] = sum(significances) / len(significances)
        
        # Determine temporal span
        if metadata['eras_covered']:
            metadata['temporal_span'] = f"{metadata['eras_covered'][0]} to {metadata['eras_covered'][-1]}"
        
        return metadata