#!/usr/bin/env python3
"""
Directly inject canonical relationships into knowledge graph
Since artists like Aerosmith aren't in the current KG, we need to add them
"""

import json
import boto3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inject_canonical_relationships():
    """Inject canonical data as new relationships into knowledge graph"""
    
    # Load current knowledge graph
    logger.info("📊 Loading current knowledge graph...")
    with open('/tmp/current_kg.json', 'r') as f:
        kg = json.load(f)
    
    # Load canonical data
    logger.info("🔗 Loading canonical recovery data...")
    s3_client = boto3.client('s3')
    
    obj = s3_client.get_object(
        Bucket='ut-processed-content', 
        Key='02-processed-content/2025-08-31/canonical-recovery-20250831_014539.json'
    )
    canonical_data = json.loads(obj['Body'].read().decode('utf-8'))
    
    # Create canonical relationships
    new_relationships = []
    
    for entity in canonical_data['entities']:
        artist_name = entity['entity_name']
        logger.info(f"🎯 Processing {artist_name}...")
        
        # Create base canonical relationship for the artist
        base_rel = {
            'id': f"canonical_{artist_name.lower().replace(' ', '_')}_base",
            'primary_artist': artist_name,
            'secondary_artist': 'Canonical References',
            'relationship_type': 'canonical_info',
            'content': f"{artist_name} canonical reference sources available",
            'source': 'Canonical Recovery',
            'url': '',
            'confidence': 1.0,
            'canonical_urls': entity.get('canonical_urls', {}),
            'metadata': {
                'content_type': 'canonical_reference',
                'recovery_timestamp': datetime.utcnow().isoformat(),
                'source_count': len(entity.get('source_attribution', []))
            }
        }
        new_relationships.append(base_rel)
        
        # Create relationship for each source attribution
        for i, source_attr in enumerate(entity.get('source_attribution', [])):
            source_rel = {
                'id': f"canonical_{artist_name.lower().replace(' ', '_')}_{source_attr['source'].lower()}_{i}",
                'primary_artist': artist_name,
                'secondary_artist': source_attr['source'],
                'relationship_type': 'canonical_source',
                'content': source_attr['content'][:500] + ('...' if len(source_attr['content']) > 500 else ''),
                'source': source_attr['source'],
                'url': source_attr.get('url', ''),
                'confidence': 1.0,
                'canonical_urls': entity.get('canonical_urls', {}),
                'metadata': {
                    'content_type': source_attr.get('content_type', 'reference'),
                    'title': source_attr.get('title', ''),
                    'source_metadata': source_attr.get('metadata', {}),
                    'recovery_timestamp': datetime.utcnow().isoformat()
                }
            }
            new_relationships.append(source_rel)
            logger.info(f"  ➕ Added {source_attr['source']} relationship")
    
    # Add to knowledge graph
    if 'relationships' not in kg:
        kg['relationships'] = []
    
    original_count = len(kg['relationships'])
    kg['relationships'].extend(new_relationships)
    kg['total_relationships'] = len(kg['relationships'])
    
    # Update enhancement info
    if 'enhancement_info' not in kg:
        kg['enhancement_info'] = {}
    
    kg['enhancement_info']['canonical_injection'] = {
        'injected_relationships': len(new_relationships),
        'canonical_artists_added': len(canonical_data['entities']),
        'canonical_sources': list(set([rel['source'] for rel in new_relationships])),
        'canonical_urls': list(set([url for rel in new_relationships 
                                   for url in rel.get('canonical_urls', {}).values()])),
        'injection_timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"✅ Original relationships: {original_count}")
    logger.info(f"➕ Injected relationships: {len(new_relationships)}")
    logger.info(f"📊 Total relationships: {kg['total_relationships']}")
    
    # Save enhanced knowledge graph
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    enhanced_file = f'/tmp/kg_with_canonical_injection_{timestamp}.json'
    
    with open(enhanced_file, 'w') as f:
        json.dump(kg, f, indent=2, default=str)
    
    logger.info(f"💾 Enhanced knowledge graph saved: {enhanced_file}")
    
    # Upload to S3 - update the main path the vector store uses
    main_s3_key = "enhanced-knowledge-graph/2025/08/31/complete_knowledge_graph_main.json"
    s3_client.put_object(
        Bucket='ut-processed-content',
        Key=main_s3_key,
        Body=json.dumps(kg, indent=2, default=str).encode('utf-8'),
        ContentType='application/json'
    )
    
    logger.info(f"📤 Updated main KG path: s3://ut-processed-content/{main_s3_key}")
    
    return {
        'original_relationships': original_count,
        'injected_relationships': len(new_relationships),
        'total_relationships': kg['total_relationships'],
        's3_path': f"s3://ut-processed-content/{main_s3_key}",
        'canonical_sources': kg['enhancement_info']['canonical_injection']['canonical_sources'],
        'canonical_urls': kg['enhancement_info']['canonical_injection']['canonical_urls']
    }

if __name__ == '__main__':
    result = inject_canonical_relationships()
    
    print("\n🎉 Canonical Relationships Injection Complete!")
    print(f"📊 Original relationships: {result['original_relationships']}")
    print(f"➕ Injected relationships: {result['injected_relationships']}")
    print(f"🔢 Total relationships: {result['total_relationships']}")
    print(f"📍 S3 location: {result['s3_path']}")
    print(f"🔗 Canonical URLs added:")
    for url in result['canonical_urls']:
        print(f"   - {url}")
    print(f"📚 Canonical sources: {', '.join(result['canonical_sources'])}")