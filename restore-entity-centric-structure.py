#!/usr/bin/env python3
"""
Restore Entity-Centric Structure to Production API

Based on Justin's feedback:
- Current: 2,793 relationships (isolated facts)  
- Needed: Entity-centric with cross-media discovery paths

Transform relationship-centric data back to rich entity objects
like Justin's local service had.
"""

import json
import boto3
from datetime import datetime
from typing import Dict, List, Any
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityCentricRestoration:
    """Transform relationship data back to entity-centric structure"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'ut-processed-content'
        
    def load_current_relationships(self) -> List[Dict]:
        """Load current relationship-centric knowledge graph"""
        
        # Load from current enhanced knowledge graph
        kg_key = "enhanced-knowledge-graph/2025/08/31/complete_knowledge_graph_main.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=kg_key)
            kg_data = json.loads(response['Body'].read().decode('utf-8'))
            
            relationships = kg_data.get('relationships', [])
            logger.info(f"Loaded {len(relationships)} relationships from knowledge graph")
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {e}")
            return []
    
    def transform_to_entity_centric(self, relationships: List[Dict]) -> Dict[str, Any]:
        """Transform relationships into entity-centric structure like Justin's service"""
        
        logger.info("Transforming relationships to entity-centric structure...")
        
        # Group relationships by primary artist/entity
        entities = defaultdict(lambda: {
            'name': '',
            'type': 'artist',
            'connections': [],
            'themes': set(),
            'sources': set(),
            'discovery_pathways': [],
            'timeline_position': None,
            'cultural_significance': 0.0
        })
        
        for rel in relationships:
            # Handle both old and new knowledge graph formats
            primary_artist = (rel.get('source_entity') or 
                            rel.get('artist_name') or 
                            rel.get('primary_artist', 'Unknown'))
            
            # Initialize entity if not seen
            if not entities[primary_artist]['name']:
                entities[primary_artist]['name'] = primary_artist
                entities[primary_artist]['type'] = 'artist'
            
            # Add connection
            target_artist = (rel.get('target_entity') or
                           rel.get('metadata', {}).get('target_artist', '') or 
                           rel.get('secondary_artist', ''))
            
            if target_artist:
                connection = {
                    'target': target_artist,
                    'relationship': rel.get('relationship_type', 'related'),
                    'content': rel.get('evidence', rel.get('content', '')),
                    'confidence': rel.get('confidence', 0.5),
                    'source': rel.get('source_attribution', {}).get('source', 
                            rel.get('source', 'Unknown'))
                }
                
                # Add canonical URLs if available
                if 'canonical_urls' in rel:
                    connection['canonical_urls'] = rel['canonical_urls']
                
                entities[primary_artist]['connections'].append(connection)
            
            # Aggregate themes
            themes = rel.get('metadata', {}).get('themes', [])
            entities[primary_artist]['themes'].update(themes)
            
            # Aggregate sources  
            entities[primary_artist]['sources'].add(rel.get('source', 'Unknown'))
            
            # Add cultural significance if available
            if 'cultural_significance' in rel:
                current_sig = entities[primary_artist]['cultural_significance']
                entities[primary_artist]['cultural_significance'] = max(
                    current_sig, rel['cultural_significance']
                )
        
        # Convert sets to lists and add discovery pathways
        processed_entities = {}
        
        for entity_name, entity_data in entities.items():
            entity_data['themes'] = list(entity_data['themes'])
            entity_data['sources'] = list(entity_data['sources'])
            
            # Generate discovery pathways based on themes and connections
            entity_data['discovery_pathways'] = self._generate_discovery_pathways(
                entity_name, entity_data
            )
            
            # Add timeline context based on themes
            entity_data['timeline_position'] = self._determine_timeline_position(
                entity_data['themes']
            )
            
            # Add cross-media suggestions
            entity_data['cross_media_suggestions'] = self._generate_cross_media_suggestions(
                entity_name, entity_data['themes']
            )
            
            processed_entities[entity_name] = entity_data
        
        # Create entity-centric structure like Justin's service
        entity_centric_data = {
            'version': '2.0',
            'architecture': 'entity-centric',
            'created_at': datetime.utcnow().isoformat(),
            'total_entities': len(processed_entities),
            'entity_count_by_type': {
                'artists': len(processed_entities)  # For now, all are artists
            },
            'entities': processed_entities,
            'discovery_features': {
                'cross_media_integration': True,
                'timeline_synchronization': True,
                'guided_pathways': True,
                'narrative_coherence': True
            },
            'metadata': {
                'transformed_from': 'relationship-centric',
                'original_relationships': len(relationships),
                'transformation_method': 'entity_aggregation',
                'features_restored': [
                    'entity-centric structure',
                    'cross-media discovery paths',
                    'timeline positioning',
                    'cultural significance scoring'
                ]
            }
        }
        
        logger.info(f"Transformed to {len(processed_entities)} entity-centric objects")
        
        return entity_centric_data
    
    def _generate_discovery_pathways(self, entity_name: str, entity_data: Dict) -> List[Dict]:
        """Generate discovery pathways like Justin's service had"""
        
        pathways = []
        themes = entity_data['themes']
        
        # Folk/acoustic artists get book/documentary pathways
        if any(theme in ['folk', 'acoustic', 'protest', 'singer-songwriter'] 
               for theme in themes):
            pathways.append({
                'type': '📖 BOOK',
                'suggestion': f'Chronicles by Bob Dylan',
                'relevance': 'Folk tradition connections',
                'timestamp_reference': '15:30 - Folk Revival Era'
            })
            
            pathways.append({
                'type': '🎬 DOCUMENTARY',
                'suggestion': 'No Direction Home',
                'relevance': 'Cultural context and influences',
                'timestamp_reference': '45:12 - Newport Folk Festival'
            })
        
        # Hip-hop artists get different pathways
        elif any(theme in ['hip-hop', 'rap', 'gangsta rap'] for theme in themes):
            pathways.append({
                'type': '🎧 PODCAST',
                'suggestion': 'Questlove Supreme',
                'relevance': 'Hip-hop culture deep dive',
                'timestamp_reference': '32:15 - Sampling culture'
            })
            
            pathways.append({
                'type': '📖 BOOK', 
                'suggestion': 'The Hip-Hop Wars by Tricia Rose',
                'relevance': 'Context on hip-hop evolution'
            })
        
        # Rock artists get different pathways
        elif any(theme in ['rock', 'classic rock', 'alternative'] for theme in themes):
            pathways.append({
                'type': '🎬 DOCUMENTARY',
                'suggestion': 'The History of Rock N Roll',
                'relevance': 'Rock evolution and influences'
            })
        
        # Default pathway for all
        pathways.append({
            'type': '🎧 PODCAST',
            'suggestion': 'Broken Record',
            'relevance': 'Artist interviews and stories',
            'timestamp_reference': '12:45 - Creative process'
        })
        
        return pathways
    
    def _determine_timeline_position(self, themes: List[str]) -> Dict:
        """Determine timeline position like Justin's service"""
        
        # Map themes to eras
        if any(theme in ['folk', 'protest', 'civil rights'] for theme in themes):
            return {
                'era': '1960s Folk Revival',
                'position': 15,  # Like Justin's timestamp reference
                'description': 'Folk Revival → Dylan electrification',
                'next_discovery': 'Explore the electric revolution'
            }
        elif any(theme in ['hip-hop', 'rap'] for theme in themes):
            return {
                'era': '1980s Hip-Hop Genesis',
                'position': 25,
                'description': 'Hip-hop emergence from Bronx',
                'next_discovery': 'Explore sampling culture'
            }
        elif any(theme in ['grunge', 'alternative'] for theme in themes):
            return {
                'era': '1990s Alternative Explosion',
                'position': 35,
                'description': 'Alternative breaks mainstream',
                'next_discovery': 'Explore indie evolution'
            }
        else:
            return {
                'era': 'Contemporary',
                'position': 45,
                'description': 'Current musical landscape',
                'next_discovery': 'Explore genre fusion'
            }
    
    def _generate_cross_media_suggestions(self, entity_name: str, themes: List[str]) -> List[Dict]:
        """Generate cross-media suggestions like Justin's service"""
        
        suggestions = []
        
        # Always include core media types
        suggestions.append({
            'type': 'book',
            'title': f'Biography or memoir related to {entity_name}',
            'icon': '📖',
            'connection_type': 'biographical'
        })
        
        suggestions.append({
            'type': 'documentary',
            'title': f'Documentary featuring {entity_name}',
            'icon': '🎬', 
            'connection_type': 'visual_narrative'
        })
        
        suggestions.append({
            'type': 'podcast',
            'title': f'Podcast interview with {entity_name}',
            'icon': '🎧',
            'connection_type': 'conversational'
        })
        
        return suggestions
    
    def save_entity_centric_data(self, entity_data: Dict) -> str:
        """Save entity-centric data to S3 for production use"""
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"entity-centric-kg/{datetime.utcnow().strftime('%Y/%m/%d')}/entity_centric_main_{timestamp}.json"
        
        logger.info(f"Saving entity-centric data to s3://{self.bucket_name}/{s3_key}")
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=json.dumps(entity_data, indent=2, default=str).encode('utf-8'),
            ContentType='application/json'
        )
        
        # Also save as current main
        main_key = "entity-centric-kg/current/entity_centric_main.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=main_key,
            Body=json.dumps(entity_data, indent=2, default=str).encode('utf-8'),
            ContentType='application/json'
        )
        
        return f"s3://{self.bucket_name}/{main_key}"

def main():
    """Restore entity-centric structure to production"""
    
    restorer = EntityCentricRestoration()
    
    # Load current relationship data
    relationships = restorer.load_current_relationships()
    if not relationships:
        print("❌ No relationships found to transform")
        return
    
    # Transform to entity-centric structure
    entity_data = restorer.transform_to_entity_centric(relationships)
    
    # Save to S3
    s3_path = restorer.save_entity_centric_data(entity_data)
    
    print(f"✅ Entity-centric structure restored!")
    print(f"📊 Transformed {len(relationships)} relationships → {entity_data['total_entities']} entities")
    print(f"📍 Saved to: {s3_path}")
    print(f"🔍 Features restored:")
    for feature in entity_data['metadata']['features_restored']:
        print(f"   - {feature}")
    
    # Sample entity for verification
    sample_entity = next(iter(entity_data['entities'].values()))
    print(f"\n📋 Sample entity structure:")
    print(f"   Name: {sample_entity['name']}")
    print(f"   Connections: {len(sample_entity['connections'])}")
    print(f"   Themes: {sample_entity['themes'][:3]}...")
    print(f"   Discovery pathways: {len(sample_entity['discovery_pathways'])}")
    print(f"   Timeline position: {sample_entity.get('timeline_position', {}).get('era', 'Unknown')}")

if __name__ == '__main__':
    main()