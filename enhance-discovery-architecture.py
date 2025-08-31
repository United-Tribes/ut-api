#!/usr/bin/env python3
"""
Transform AWS API from relationship-centric to discovery-oriented architecture
Adds narrative structure, temporal organization, and cross-media integration

Key Enhancements:
1. Temporal Organization - Add timeframes and chronological eras
2. Thematic Clustering - Group relationships into cultural narratives  
3. Cross-Media Integration - Connect books, documentaries, podcasts
4. Guided Discovery - Create contextual pathways for exploration
5. Narrative Coherence - Transform facts into meaningful stories
"""

import json
import boto3
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscoveryArchitectureEnhancer:
    """Transform relationship data into discovery-oriented narratives"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'ut-processed-content'
        
        # Define cultural eras for temporal organization
        self.cultural_eras = {
            '1930s-1940s': {
                'name': 'Folk Roots Era',
                'themes': ['Dust Bowl', 'labor movements', 'traditional folk'],
                'key_artists': ['Woody Guthrie', 'Lead Belly', 'Pete Seeger']
            },
            '1950s-1960s': {
                'name': 'Folk Revival',
                'themes': ['civil rights', 'protest songs', 'coffee houses'],
                'key_artists': ['Bob Dylan', 'Joan Baez', 'Phil Ochs']
            },
            '1960s-1970s': {
                'name': 'Electric Revolution',
                'themes': ['rock fusion', 'counterculture', 'Woodstock'],
                'key_artists': ['Dylan electric', 'The Band', 'Neil Young']
            },
            '1970s-1980s': {
                'name': 'Punk & New Wave',
                'themes': ['DIY ethics', 'social rebellion', 'underground'],
                'key_artists': ['Patti Smith', 'Television', 'Talking Heads']
            },
            '1980s-1990s': {
                'name': 'Hip-Hop Evolution',
                'themes': ['urban narratives', 'sampling culture', 'social commentary'],
                'key_artists': ['Public Enemy', 'N.W.A', 'Tupac', 'Biggie']
            },
            '1990s-2000s': {
                'name': 'Alternative Mainstream',
                'themes': ['indie rock', 'grunge', 'nu-metal'],
                'key_artists': ['Nirvana', 'Radiohead', 'Beck']
            },
            '2000s-2010s': {
                'name': 'Digital Revolution',
                'themes': ['streaming', 'bedroom producers', 'viral culture'],
                'key_artists': ['Kanye West', 'Arctic Monkeys', 'Bon Iver']
            },
            '2010s-2020s': {
                'name': 'Genre Fluidity',
                'themes': ['playlist culture', 'genre-blending', 'social media'],
                'key_artists': ['Kendrick Lamar', 'Taylor Swift', 'Billie Eilish']
            }
        }
        
        # Define narrative threads that connect across eras
        self.narrative_threads = {
            'protest_evolution': {
                'name': 'From Dust Bowl to Black Lives Matter',
                'description': 'The evolution of protest music as social commentary',
                'eras': ['1930s-1940s', '1950s-1960s', '1960s-1970s', '1980s-1990s', '2010s-2020s'],
                'key_moments': [
                    'Woody Guthrie\'s "This Land Is Your Land"',
                    'Dylan\'s "Blowin\' in the Wind"',
                    'Public Enemy\'s "Fight the Power"',
                    'Kendrick Lamar\'s "Alright"'
                ]
            },
            'folk_to_indie': {
                'name': 'Folk DNA in Modern Indie',
                'description': 'How folk traditions evolved into contemporary indie music',
                'eras': ['1930s-1940s', '1950s-1960s', '1990s-2000s', '2000s-2010s'],
                'key_connections': [
                    'Woody Guthrie → Bob Dylan',
                    'Dylan → Beck',
                    'Folk Revival → Bon Iver',
                    'Traditional → Fleet Foxes'
                ]
            },
            'blues_to_hiphop': {
                'name': 'Blues to Hip-Hop Pipeline',
                'description': 'The transformation of African American musical expression',
                'eras': ['1930s-1940s', '1960s-1970s', '1980s-1990s', '2010s-2020s'],
                'key_evolution': [
                    'Delta Blues storytelling',
                    'Electric blues revolution',
                    'Sampling blues in hip-hop',
                    'Modern trap blues'
                ]
            }
        }
        
        # Cross-media discovery pathways
        self.discovery_pathways = {
            'books': {
                'Chronicles': {'artist': 'Bob Dylan', 'type': 'autobiography', 'era': '1950s-1960s'},
                'Bound for Glory': {'artist': 'Woody Guthrie', 'type': 'biography', 'era': '1930s-1940s'},
                'Just Kids': {'artist': 'Patti Smith', 'type': 'memoir', 'era': '1970s-1980s'},
                'The Autobiography of Gucci Mane': {'artist': 'Gucci Mane', 'type': 'autobiography', 'era': '2000s-2010s'}
            },
            'documentaries': {
                'No Direction Home': {'subject': 'Bob Dylan', 'director': 'Martin Scorsese', 'era': '1950s-1960s'},
                'The Last Waltz': {'subject': 'The Band', 'director': 'Martin Scorsese', 'era': '1960s-1970s'},
                'Hip-Hop Evolution': {'subject': 'Hip-Hop History', 'type': 'series', 'era': '1980s-1990s'},
                'Miss Americana': {'subject': 'Taylor Swift', 'platform': 'Netflix', 'era': '2010s-2020s'}
            },
            'podcasts': {
                'Song Exploder': {'focus': 'creative process', 'host': 'Hrishikesh Hirway'},
                'Broken Record': {'focus': 'artist interviews', 'hosts': 'Rick Rubin, Malcolm Gladwell'},
                'Dissect': {'focus': 'album analysis', 'host': 'Cole Cuchna'},
                'Fresh Air': {'focus': 'cultural commentary', 'host': 'Terry Gross'}
            }
        }
    
    def enhance_relationship_with_discovery(self, relationship: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a raw relationship into a discovery-oriented entity"""
        
        enhanced = relationship.copy()
        
        # Add temporal context
        artist_name = relationship.get('artist_name', '')
        enhanced['temporal_context'] = self._get_temporal_context(artist_name)
        
        # Add thematic narrative
        themes = relationship.get('metadata', {}).get('themes', [])
        enhanced['narrative_thread'] = self._get_narrative_thread(themes, artist_name)
        
        # Add discovery pathways
        enhanced['discovery_pathways'] = self._generate_discovery_pathways(
            artist_name, 
            relationship.get('metadata', {}).get('target_artist', ''),
            themes
        )
        
        # Add cultural significance score
        enhanced['cultural_significance'] = self._calculate_cultural_significance(
            relationship,
            enhanced.get('temporal_context', {}),
            enhanced.get('narrative_thread', {})
        )
        
        # Transform content into narrative format
        enhanced['narrative_content'] = self._create_narrative_content(
            relationship.get('content', ''),
            enhanced.get('temporal_context', {}),
            enhanced.get('discovery_pathways', [])
        )
        
        return enhanced
    
    def _get_temporal_context(self, artist_name: str) -> Dict[str, Any]:
        """Determine the temporal era and context for an artist"""
        
        # Map artist to era (simplified - would use more sophisticated matching)
        artist_lower = artist_name.lower()
        
        for era_key, era_data in self.cultural_eras.items():
            for key_artist in era_data['key_artists']:
                if key_artist.lower() in artist_lower or artist_lower in key_artist.lower():
                    return {
                        'era': era_key,
                        'era_name': era_data['name'],
                        'era_themes': era_data['themes'],
                        'chronological_position': self._get_era_position(era_key)
                    }
        
        # Default to contemporary if not found
        return {
            'era': '2010s-2020s',
            'era_name': 'Contemporary',
            'era_themes': ['modern', 'current'],
            'chronological_position': 8
        }
    
    def _get_era_position(self, era_key: str) -> int:
        """Get chronological position of era"""
        era_order = list(self.cultural_eras.keys())
        return era_order.index(era_key) + 1 if era_key in era_order else 0
    
    def _get_narrative_thread(self, themes: List[str], artist_name: str) -> Dict[str, Any]:
        """Find the narrative thread this relationship belongs to"""
        
        # Match themes to narrative threads
        for thread_key, thread_data in self.narrative_threads.items():
            # Check if themes align with thread
            if any(theme in ' '.join(themes).lower() for theme in ['protest', 'social']) and thread_key == 'protest_evolution':
                return {
                    'thread_id': thread_key,
                    'thread_name': thread_data['name'],
                    'thread_description': thread_data['description'],
                    'position_in_narrative': self._get_narrative_position(artist_name, thread_data)
                }
            elif any(theme in ' '.join(themes).lower() for theme in ['folk', 'indie']) and thread_key == 'folk_to_indie':
                return {
                    'thread_id': thread_key,
                    'thread_name': thread_data['name'],
                    'thread_description': thread_data['description']
                }
            elif any(theme in ' '.join(themes).lower() for theme in ['hip-hop', 'rap', 'blues']) and thread_key == 'blues_to_hiphop':
                return {
                    'thread_id': thread_key,
                    'thread_name': thread_data['name'],
                    'thread_description': thread_data['description']
                }
        
        return {
            'thread_id': 'general',
            'thread_name': 'Musical Evolution',
            'thread_description': 'Part of the broader musical landscape'
        }
    
    def _get_narrative_position(self, artist_name: str, thread_data: Dict) -> str:
        """Determine where this artist fits in the narrative"""
        # Simplified - would use more sophisticated analysis
        return 'contemporary_expression'
    
    def _generate_discovery_pathways(self, primary_artist: str, secondary_artist: str, themes: List[str]) -> List[Dict]:
        """Generate cross-media discovery suggestions"""
        
        pathways = []
        
        # Book recommendations
        for book_title, book_data in self.discovery_pathways['books'].items():
            if primary_artist.lower() in book_data.get('artist', '').lower():
                pathways.append({
                    'type': '📖 BOOK',
                    'title': book_title,
                    'relevance': 'Primary artist autobiography',
                    'discovery_value': f"Understand {primary_artist}'s perspective and journey"
                })
        
        # Documentary recommendations
        for doc_title, doc_data in self.discovery_pathways['documentaries'].items():
            if primary_artist.lower() in doc_data.get('subject', '').lower():
                pathways.append({
                    'type': '🎬 DOCUMENTARY',
                    'title': doc_title,
                    'relevance': 'Visual exploration of artist',
                    'discovery_value': f"See {primary_artist} in cultural context"
                })
        
        # Podcast recommendations based on themes
        if any('hip-hop' in theme.lower() for theme in themes):
            pathways.append({
                'type': '🎧 PODCAST',
                'title': 'Dissect',
                'relevance': 'Deep album analysis',
                'discovery_value': 'Understand the craft behind the music'
            })
        
        if not pathways:
            # Default pathway
            pathways.append({
                'type': '🎧 PODCAST',
                'title': 'Song Exploder',
                'relevance': 'Artist creative process',
                'discovery_value': 'Learn how artists create their work'
            })
        
        return pathways
    
    def _calculate_cultural_significance(self, relationship: Dict, temporal: Dict, narrative: Dict) -> float:
        """Calculate cultural significance score (0-1)"""
        
        score = 0.0
        
        # Base confidence
        score += relationship.get('confidence', 0.5) * 0.3
        
        # Temporal importance (earlier eras get bonus for historical significance)
        era_position = temporal.get('chronological_position', 8)
        score += (9 - era_position) / 8 * 0.2  # Earlier eras score higher
        
        # Narrative thread importance
        if narrative.get('thread_id') != 'general':
            score += 0.2
        
        # Relationship type importance
        rel_type = relationship.get('metadata', {}).get('relationship_type', '')
        if rel_type in ['influence', 'inspiration', 'mentor']:
            score += 0.2
        elif rel_type in ['collaboration', 'contemporary']:
            score += 0.1
        
        # Theme significance
        themes = relationship.get('metadata', {}).get('themes', [])
        significant_themes = ['protest', 'civil rights', 'revolution', 'pioneer', 'breakthrough']
        if any(theme in ' '.join(themes).lower() for theme in significant_themes):
            score += 0.1
        
        return min(score, 1.0)
    
    def _create_narrative_content(self, original_content: str, temporal: Dict, pathways: List[Dict]) -> str:
        """Transform raw content into narrative format with discovery prompts"""
        
        # Start with temporal context
        narrative = f"[{temporal.get('era_name', 'Contemporary')}] "
        
        # Add the original content
        narrative += original_content
        
        # Add discovery prompt
        if pathways:
            pathway = pathways[0]  # Use first pathway
            narrative += f" → {pathway['type']} Discover: {pathway['title']} - {pathway['discovery_value']}"
        
        return narrative
    
    def process_knowledge_graph(self, kg_path: str) -> Dict[str, Any]:
        """Process entire knowledge graph with discovery enhancements"""
        
        logger.info("📊 Loading knowledge graph...")
        
        # Download knowledge graph
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=kg_path)
        kg = json.loads(response['Body'].read().decode('utf-8'))
        
        logger.info(f"🔄 Enhancing {len(kg.get('relationships', []))} relationships...")
        
        # Enhance each relationship
        enhanced_relationships = []
        narrative_threads = {}
        temporal_organization = {}
        
        for relationship in kg.get('relationships', []):
            enhanced = self.enhance_relationship_with_discovery(relationship)
            enhanced_relationships.append(enhanced)
            
            # Organize by narrative thread
            thread_id = enhanced.get('narrative_thread', {}).get('thread_id', 'general')
            if thread_id not in narrative_threads:
                narrative_threads[thread_id] = []
            narrative_threads[thread_id].append(enhanced)
            
            # Organize by temporal era
            era = enhanced.get('temporal_context', {}).get('era', 'unknown')
            if era not in temporal_organization:
                temporal_organization[era] = []
            temporal_organization[era].append(enhanced)
        
        # Create enhanced knowledge graph
        enhanced_kg = {
            'version': '2.0',
            'architecture': 'discovery-oriented',
            'created_at': datetime.utcnow().isoformat(),
            'total_relationships': len(enhanced_relationships),
            'relationships': enhanced_relationships,
            'narrative_threads': {
                thread_id: {
                    'name': self.narrative_threads.get(thread_id, {}).get('name', thread_id),
                    'description': self.narrative_threads.get(thread_id, {}).get('description', ''),
                    'relationship_count': len(relationships)
                }
                for thread_id, relationships in narrative_threads.items()
            },
            'temporal_organization': {
                era: {
                    'name': self.cultural_eras.get(era, {}).get('name', era),
                    'themes': self.cultural_eras.get(era, {}).get('themes', []),
                    'relationship_count': len(relationships)
                }
                for era, relationships in temporal_organization.items()
            },
            'discovery_pathways': self.discovery_pathways,
            'cultural_eras': self.cultural_eras,
            'enhancement_metadata': {
                'enhanced_from': kg_path,
                'enhancement_type': 'discovery_architecture',
                'features_added': [
                    'temporal_context',
                    'narrative_threads',
                    'discovery_pathways',
                    'cultural_significance',
                    'narrative_content'
                ]
            }
        }
        
        logger.info("✅ Discovery architecture enhancement complete")
        
        return enhanced_kg
    
    def save_enhanced_graph(self, enhanced_kg: Dict[str, Any]) -> str:
        """Save enhanced knowledge graph to S3"""
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"discovery-knowledge-graph/{datetime.utcnow().strftime('%Y/%m/%d')}/discovery_kg_{timestamp}.json"
        
        logger.info(f"📤 Saving enhanced graph to s3://{self.bucket_name}/{s3_key}")
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=json.dumps(enhanced_kg, indent=2, default=str).encode('utf-8'),
            ContentType='application/json'
        )
        
        # Also update the main discovery graph path
        main_key = "discovery-knowledge-graph/current/discovery_kg_main.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=main_key,
            Body=json.dumps(enhanced_kg, indent=2, default=str).encode('utf-8'),
            ContentType='application/json'
        )
        
        return f"s3://{self.bucket_name}/{main_key}"

def main():
    """Transform API to discovery-oriented architecture"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhance API with discovery architecture')
    parser.add_argument('--kg-path', default='enhanced-knowledge-graph/2025/08/31/complete_knowledge_graph_main.json',
                       help='Path to current knowledge graph in S3')
    parser.add_argument('--test-mode', action='store_true', help='Test with sample data')
    
    args = parser.parse_args()
    
    enhancer = DiscoveryArchitectureEnhancer()
    
    if args.test_mode:
        # Test with a sample relationship
        test_relationship = {
            'id': 'test_1',
            'artist_name': 'Bob Dylan',
            'content': 'Bob Dylan influence on modern folk music',
            'source': 'Test',
            'confidence': 0.9,
            'metadata': {
                'target_artist': 'Fleet Foxes',
                'relationship_type': 'influence',
                'themes': ['folk', 'songwriting']
            }
        }
        
        enhanced = enhancer.enhance_relationship_with_discovery(test_relationship)
        print(json.dumps(enhanced, indent=2, default=str))
    else:
        # Process full knowledge graph
        enhanced_kg = enhancer.process_knowledge_graph(args.kg_path)
        s3_path = enhancer.save_enhanced_graph(enhanced_kg)
        
        print(f"✅ Discovery architecture enhancement complete!")
        print(f"📊 Enhanced {enhanced_kg['total_relationships']} relationships")
        print(f"🧵 Created {len(enhanced_kg['narrative_threads'])} narrative threads")
        print(f"📅 Organized into {len(enhanced_kg['temporal_organization'])} temporal eras")
        print(f"📍 Saved to: {s3_path}")

if __name__ == '__main__':
    main()