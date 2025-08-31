#!/usr/bin/env python3
"""
Recover and process canonical Wikipedia/MusicBrainz data
Upload to S3 and vector store for production deployment

Usage:
    python recover-canonical-data.py --process-local-data
    python recover-canonical-data.py --upload-to-s3
    python recover-canonical-data.py --update-vector-store
"""

import json
import boto3
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
import requests
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CanonicalDataRecovery:
    """Recover and deploy canonical Wikipedia/MusicBrainz data"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'ut-processed-content'
        self.local_data_paths = [
            '/Users/shanandelp/Documents/UnitedTribes-Store/scraped-content/',
            '/Users/shanandelp/Documents/ClaudeCodeProjects/UnitedTribes/packages/ut-adapters/data/raw/'
        ]
        self.vector_store_url = "http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com"
        
    def discover_local_canonical_data(self) -> List[Dict[str, Any]]:
        """Find all canonical data in local directories"""
        logger.info("🔍 Discovering local canonical data...")
        
        canonical_data = []
        
        # Check scraped content directory
        scraped_path = Path(self.local_data_paths[0])
        if scraped_path.exists():
            for artist_dir in scraped_path.iterdir():
                if artist_dir.is_dir():
                    canonical_dir = artist_dir / 'canonical'
                    if canonical_dir.exists():
                        merged_file = canonical_dir / 'merged.json'
                        if merged_file.exists():
                            try:
                                with open(merged_file, 'r') as f:
                                    data = json.load(f)
                                    canonical_data.append({
                                        'artist': artist_dir.name,
                                        'source_file': str(merged_file),
                                        'data': data,
                                        'type': 'scraped_canonical'
                                    })
                                    logger.info(f"✅ Found canonical data for {artist_dir.name}")
                            except Exception as e:
                                logger.error(f"Error reading {merged_file}: {e}")
        
        # Check raw Wikipedia data
        wiki_path = Path(self.local_data_paths[1]) / 'wikipedia'
        if wiki_path.exists():
            for wiki_file in wiki_path.glob('*.json'):
                try:
                    with open(wiki_file, 'r') as f:
                        data = json.load(f)
                        canonical_data.append({
                            'artist': wiki_file.stem.replace('_', ' ').title(),
                            'source_file': str(wiki_file),
                            'data': data,
                            'type': 'raw_wikipedia'
                        })
                        logger.info(f"✅ Found Wikipedia data for {wiki_file.stem}")
                except Exception as e:
                    logger.error(f"Error reading {wiki_file}: {e}")
        
        logger.info(f"📊 Total canonical sources found: {len(canonical_data)}")
        return canonical_data
    
    def process_canonical_data(self, canonical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process canonical data into standardized format"""
        logger.info("⚙️  Processing canonical data...")
        
        processed_entities = []
        
        for item in canonical_data:
            try:
                if item['type'] == 'scraped_canonical':
                    entity = self._process_scraped_canonical(item)
                elif item['type'] == 'raw_wikipedia':
                    entity = self._process_raw_wikipedia(item)
                else:
                    continue
                    
                if entity:
                    processed_entities.append(entity)
                    
            except Exception as e:
                logger.error(f"Error processing {item['artist']}: {e}")
        
        logger.info(f"✅ Processed {len(processed_entities)} canonical entities")
        return processed_entities
    
    def _process_scraped_canonical(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process scraped canonical data format"""
        data = item['data']
        artist_name = item['artist']
        
        entity = {
            'entity_id': f"canonical_{artist_name.lower().replace(' ', '_')}",
            'entity_name': artist_name,
            'entity_type': 'artist',
            'source_attribution': [],
            'canonical_urls': {},
            'metadata': {
                'processing_date': datetime.utcnow().isoformat(),
                'source_type': 'canonical_recovery',
                'recovery_source': item['source_file']
            }
        }
        
        # Extract canonical URLs
        if 'canonical_links' in data:
            entity['canonical_urls'] = data['canonical_links']
        
        # Add Wikipedia data
        if 'wikipedia' in data:
            wiki_data = data['wikipedia']
            entity['source_attribution'].append({
                'source': 'Wikipedia',
                'url': wiki_data.get('url', ''),
                'title': wiki_data.get('title', ''),
                'content_type': 'reference',
                'content': wiki_data.get('full_article', wiki_data.get('summary', '')),
                'metadata': {
                    'word_count': wiki_data.get('word_count', 0),
                    'thumbnail': wiki_data.get('thumbnail', '')
                }
            })
            
            if 'url' in wiki_data:
                entity['canonical_urls']['wikipedia'] = wiki_data['url']
        
        # Add MusicBrainz data
        if 'musicbrainz' in data:
            mb_data = data['musicbrainz']
            mbid = mb_data.get('mbid', '')
            
            entity['source_attribution'].append({
                'source': 'MusicBrainz',
                'url': f'https://musicbrainz.org/artist/{mbid}',
                'title': mb_data.get('name', artist_name),
                'content_type': 'reference',
                'content': f"MusicBrainz ID: {mbid}, Type: {mb_data.get('type', 'Unknown')}",
                'metadata': {
                    'mbid': mbid,
                    'disambiguation': mb_data.get('disambiguation', ''),
                    'type': mb_data.get('type', '')
                }
            })
            
            if mbid:
                entity['canonical_urls']['musicbrainz'] = f'https://musicbrainz.org/artist/{mbid}'
        
        # Add works/discography
        if 'works' in data:
            works_content = f"Discography: {len(data['works'])} releases including " + \
                          ", ".join([w.get('title', 'Unknown') for w in data['works'][:5]])
            
            entity['source_attribution'].append({
                'source': 'MusicBrainz Discography',
                'url': entity['canonical_urls'].get('musicbrainz', ''),
                'title': f"{artist_name} Discography",
                'content_type': 'reference',
                'content': works_content,
                'metadata': {
                    'works_count': len(data['works']),
                    'works': data['works'][:10]  # First 10 works
                }
            })
        
        return entity
    
    def _process_raw_wikipedia(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Wikipedia data format"""
        data = item['data']
        artist_name = item['artist']
        
        entity = {
            'entity_id': f"wikipedia_{artist_name.lower().replace(' ', '_')}",
            'entity_name': artist_name,
            'entity_type': 'artist',
            'source_attribution': [{
                'source': 'Wikipedia',
                'url': data.get('url', ''),
                'title': data.get('title', artist_name),
                'content_type': 'reference',
                'content': data.get('content', data.get('summary', '')),
                'metadata': {
                    'page_id': data.get('page_id'),
                    'infobox': data.get('infobox', {}),
                    'discography': data.get('discography', [])
                }
            }],
            'canonical_urls': {
                'wikipedia': data.get('url', '')
            },
            'metadata': {
                'processing_date': datetime.utcnow().isoformat(),
                'source_type': 'wikipedia_recovery',
                'recovery_source': item['source_file']
            }
        }
        
        return entity
    
    def upload_to_s3(self, processed_entities: List[Dict[str, Any]]) -> str:
        """Upload processed canonical data to S3"""
        logger.info("📤 Uploading canonical data to S3...")
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"02-processed-content/{datetime.utcnow().strftime('%Y-%m-%d')}/canonical-recovery-{timestamp}.json"
        
        upload_data = {
            'recovery_timestamp': timestamp,
            'entities_count': len(processed_entities),
            'canonical_sources': list(set([url for entity in processed_entities 
                                         for url in entity['canonical_urls'].values()])),
            'entities': processed_entities
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(upload_data, indent=2, default=str).encode('utf-8'),
                ContentType='application/json'
            )
            
            logger.info(f"✅ Uploaded to S3: s3://{self.bucket_name}/{s3_key}")
            return f"s3://{self.bucket_name}/{s3_key}"
            
        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise
    
    def update_vector_store(self, s3_path: str) -> bool:
        """Notify vector store to reload with new canonical data"""
        logger.info("🔄 Updating vector store...")
        
        try:
            # First check if vector store is accessible
            health_response = requests.get(f"{self.vector_store_url}/health", timeout=10)
            if health_response.status_code != 200:
                logger.error("❌ Vector store not accessible")
                return False
            
            # Trigger reload (if endpoint exists)
            try:
                reload_response = requests.post(
                    f"{self.vector_store_url}/reload",
                    json={"s3_path": s3_path},
                    timeout=30
                )
                if reload_response.status_code == 200:
                    logger.info("✅ Vector store reload triggered")
                    return True
                else:
                    logger.warning(f"⚠️  Reload endpoint returned {reload_response.status_code}")
            except:
                logger.info("ℹ️  No reload endpoint - vector store will pick up data on next restart")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector store update failed: {e}")
            return False
    
    def save_recovery_report(self, canonical_data: List[Dict], processed_entities: List[Dict], s3_path: str) -> str:
        """Save detailed recovery report"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_file = f"/tmp/canonical-recovery-report-{timestamp}.json"
        
        report = {
            'recovery_timestamp': timestamp,
            'summary': {
                'sources_discovered': len(canonical_data),
                'entities_processed': len(processed_entities),
                's3_upload_path': s3_path,
                'canonical_urls_recovered': sum(len(e.get('canonical_urls', {})) for e in processed_entities)
            },
            'discovered_sources': [
                {
                    'artist': item['artist'],
                    'type': item['type'],
                    'source_file': item['source_file']
                }
                for item in canonical_data
            ],
            'canonical_urls': {
                entity['entity_name']: entity.get('canonical_urls', {})
                for entity in processed_entities
            },
            'processed_entities': processed_entities
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Recovery report saved: {report_file}")
        return report_file

def main():
    parser = argparse.ArgumentParser(description='Recover canonical Wikipedia/MusicBrainz data')
    parser.add_argument('--process-local-data', action='store_true', 
                       help='Process local canonical data')
    parser.add_argument('--upload-to-s3', action='store_true',
                       help='Upload processed data to S3')
    parser.add_argument('--update-vector-store', action='store_true',
                       help='Update vector store with new data')
    parser.add_argument('--full-recovery', action='store_true',
                       help='Run complete recovery process')
    
    args = parser.parse_args()
    
    recovery = CanonicalDataRecovery()
    
    if args.full_recovery or args.process_local_data:
        print("🚀 Starting canonical data recovery process...")
        
        # Discover local data
        canonical_data = recovery.discover_local_canonical_data()
        if not canonical_data:
            print("❌ No canonical data found locally")
            return
        
        # Process data
        processed_entities = recovery.process_canonical_data(canonical_data)
        if not processed_entities:
            print("❌ No entities processed successfully")
            return
        
        # Upload to S3
        if args.full_recovery or args.upload_to_s3:
            s3_path = recovery.upload_to_s3(processed_entities)
            
            # Update vector store
            if args.full_recovery or args.update_vector_store:
                recovery.update_vector_store(s3_path)
            
            # Save report
            report_file = recovery.save_recovery_report(canonical_data, processed_entities, s3_path)
            
            print(f"✅ Canonical data recovery complete!")
            print(f"📊 Summary:")
            print(f"   Sources found: {len(canonical_data)}")
            print(f"   Entities processed: {len(processed_entities)}")
            print(f"   S3 location: {s3_path}")
            print(f"   Report: {report_file}")
            
            # Print canonical URLs recovered
            print(f"\n🔗 Canonical URLs recovered:")
            for entity in processed_entities:
                urls = entity.get('canonical_urls', {})
                if urls:
                    print(f"   {entity['entity_name']}:")
                    for source, url in urls.items():
                        print(f"     - {source}: {url}")
        
    else:
        parser.print_help()

if __name__ == '__main__':
    main()