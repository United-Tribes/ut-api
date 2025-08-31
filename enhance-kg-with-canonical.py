#!/usr/bin/env python3
"""
Enhance existing knowledge graph with recovered canonical data
Add Wikipedia and MusicBrainz URLs to entities and relationships
"""

import json
import boto3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enhance_knowledge_graph_with_canonical():
    """Add canonical URLs to existing knowledge graph"""
    
    # Load current knowledge graph
    logger.info("📊 Loading current knowledge graph...")
    with open('/tmp/current_kg.json', 'r') as f:
        kg = json.load(f)
    
    # Load our recovered canonical data
    logger.info("🔗 Loading recovered canonical data...")
    s3_client = boto3.client('s3')
    
    # Get the latest canonical recovery file
    response = s3_client.list_objects_v2(
        Bucket='ut-processed-content',
        Prefix='02-processed-content/2025-08-31/canonical-recovery-'
    )
    
    if not response.get('Contents'):
        logger.error("❌ No canonical recovery data found")
        return
    
    latest_recovery = max(response['Contents'], key=lambda x: x['LastModified'])
    logger.info(f"📁 Using recovery file: {latest_recovery['Key']}")
    
    # Download canonical data
    obj = s3_client.get_object(Bucket='ut-processed-content', Key=latest_recovery['Key'])
    canonical_data = json.loads(obj['Body'].read().decode('utf-8'))
    
    # Create canonical URL mapping
    canonical_urls = {}
    for entity in canonical_data['entities']:
        artist_name = entity['entity_name'].lower()
        canonical_urls[artist_name] = entity.get('canonical_urls', {})
        
        # Also try variations
        canonical_urls[artist_name.replace(' ', '_')] = entity.get('canonical_urls', {})
        canonical_urls[artist_name.replace('_', ' ')] = entity.get('canonical_urls', {})
    
    logger.info(f"🎯 Canonical URLs available for: {list(canonical_urls.keys())}")
    
    # Enhance relationships with canonical URLs
    enhanced_count = 0
    new_canonical_relationships = []
    
    for relationship in kg.get('relationships', []):
        artist_name = relationship.get('primary_artist', '').lower()
        
        if artist_name in canonical_urls:
            urls = canonical_urls[artist_name]
            
            # Add canonical URLs to existing relationship metadata
            if 'canonical_urls' not in relationship:
                relationship['canonical_urls'] = urls
                enhanced_count += 1
            
            # Create new canonical relationship entries
            for source_type, url in urls.items():
                canonical_rel = {
                    'id': f"canonical_{source_type}_{artist_name.replace(' ', '_')}",
                    'primary_artist': relationship.get('primary_artist'),
                    'secondary_artist': f'{source_type.title()} Reference',
                    'relationship_type': 'canonical_reference',
                    'content': f'{relationship.get("primary_artist")} canonical {source_type} reference: {url}',
                    'source': f'{source_type.title()}',
                    'url': url,
                    'confidence': 1.0,
                    'canonical_urls': {source_type: url},
                    'metadata': {
                        'content_type': 'canonical_reference',
                        'source_type': source_type,
                        'recovery_timestamp': datetime.utcnow().isoformat()
                    }
                }
                new_canonical_relationships.append(canonical_rel)
    
    # Add new canonical relationships
    if 'relationships' not in kg:
        kg['relationships'] = []
    
    kg['relationships'].extend(new_canonical_relationships)
    
    # Update enhancement info
    if 'enhancement_info' not in kg:
        kg['enhancement_info'] = {}
    
    kg['enhancement_info']['canonical_enhancement'] = {
        'enhanced_existing_relationships': enhanced_count,
        'new_canonical_relationships': len(new_canonical_relationships),
        'canonical_sources_added': list(set(url.split('/')[2] for urls in canonical_urls.values() 
                                           for url in urls.values())),
        'enhancement_timestamp': datetime.utcnow().isoformat()
    }
    
    # Update totals
    kg['total_relationships'] = len(kg['relationships'])
    
    logger.info(f"✅ Enhanced {enhanced_count} existing relationships")
    logger.info(f"➕ Added {len(new_canonical_relationships)} new canonical relationships")
    logger.info(f"📊 Total relationships: {kg['total_relationships']}")
    
    # Save enhanced knowledge graph
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    enhanced_file = f'/tmp/enhanced_kg_with_canonical_{timestamp}.json'
    
    with open(enhanced_file, 'w') as f:
        json.dump(kg, f, indent=2, default=str)
    
    logger.info(f"💾 Enhanced knowledge graph saved: {enhanced_file}")
    
    # Upload to S3
    s3_key = f"enhanced-knowledge-graph/2025/08/31/complete_knowledge_graph_main_with_canonical_{timestamp}.json"
    
    s3_client.put_object(
        Bucket='ut-processed-content',
        Key=s3_key,
        Body=json.dumps(kg, indent=2, default=str).encode('utf-8'),
        ContentType='application/json'
    )
    
    logger.info(f"📤 Uploaded enhanced KG: s3://ut-processed-content/{s3_key}")
    
    # Also update the main path for vector store
    main_s3_key = "enhanced-knowledge-graph/2025/08/31/complete_knowledge_graph_main.json"
    s3_client.put_object(
        Bucket='ut-processed-content',
        Key=main_s3_key,
        Body=json.dumps(kg, indent=2, default=str).encode('utf-8'),
        ContentType='application/json'
    )
    
    logger.info(f"📤 Updated main KG path: s3://ut-processed-content/{main_s3_key}")
    
    return {
        'original_relationships': len(kg['relationships']) - len(new_canonical_relationships),
        'canonical_relationships_added': len(new_canonical_relationships),
        'total_relationships': kg['total_relationships'],
        's3_path': f"s3://ut-processed-content/{main_s3_key}",
        'canonical_sources': kg['enhancement_info']['canonical_enhancement']['canonical_sources_added']
    }

if __name__ == '__main__':
    result = enhance_knowledge_graph_with_canonical()
    
    print("\n🎉 Knowledge Graph Enhancement Complete!")
    print(f"📊 Original relationships: {result['original_relationships']}")
    print(f"➕ Canonical relationships added: {result['canonical_relationships_added']}")  
    print(f"🔢 Total relationships: {result['total_relationships']}")
    print(f"📍 S3 location: {result['s3_path']}")
    print(f"🔗 Canonical sources: {', '.join(result['canonical_sources'])}")