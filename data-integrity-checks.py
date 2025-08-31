#!/usr/bin/env python3
"""
Data Integrity Checks for UT-API
Prevents regression and data loss during deployments and cleanup operations

Usage:
    python data-integrity-checks.py --mode pre-cleanup
    python data-integrity-checks.py --mode pre-deployment  
    python data-integrity-checks.py --mode post-deployment
"""

import json
import boto3
import argparse
from datetime import datetime
from typing import Dict, List, Set, Tuple
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrityChecker:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.api_url = "http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com"
        
        # Expected content types that must be preserved
        self.required_content_types = {
            'canonical_sources': ['Billboard', 'Pitchfork', 'Guardian'],
            'podcast_sources': ['Fresh_Air', 'All_Songs_Considered', 'Broken_Record', 
                              'Questlove_Supreme', 'Switched_On_Pop', 'Sound_Opinions'],
            'reference_sources': ['Wikipedia', 'MusicBrainz', 'AllMusic'],  # Target state
            'url_patterns': {
                'billboard.com': 'Billboard canonical URLs',
                'pitchfork.com': 'Pitchfork canonical URLs', 
                'theguardian.com': 'Guardian canonical URLs',
                'wikipedia.org': 'Wikipedia reference URLs',
                'musicbrainz.org': 'MusicBrainz reference URLs'
            }
        }
        
        # Test artists that must return data
        self.test_artists = [
            'Beatles', 'Bob Dylan', 'Charlie Parker', 'Amy Winehouse',
            'Justin Bieber', 'Kendrick Lamar', 'Taylor Swift', '50 Cent'
        ]

    def create_content_inventory(self) -> Dict:
        """Create comprehensive inventory of current content"""
        logger.info("📋 Creating content inventory...")
        
        inventory = {
            'timestamp': datetime.utcnow().isoformat(),
            's3_content': self._inventory_s3_content(),
            'api_content': self._inventory_api_content(),
            'knowledge_graph': self._inventory_knowledge_graph(),
            'canonical_urls': self._inventory_canonical_urls()
        }
        
        return inventory

    def _inventory_s3_content(self) -> Dict:
        """Inventory all S3 content types and counts"""
        logger.info("🗂️  Inventorying S3 content...")
        
        inventory = {}
        bucket_name = 'ut-processed-content'
        
        try:
            # Get all objects in bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            content_types = {}
            total_objects = 0
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    total_objects += 1
                    
                    # Categorize by path structure
                    parts = key.split('/')
                    if len(parts) > 1:
                        category = parts[0]
                        content_types[category] = content_types.get(category, 0) + 1
                    
                    # Check for specific content types
                    if 'wikipedia' in key.lower():
                        content_types['wikipedia_files'] = content_types.get('wikipedia_files', 0) + 1
                    if 'musicbrainz' in key.lower():
                        content_types['musicbrainz_files'] = content_types.get('musicbrainz_files', 0) + 1
            
            inventory = {
                'total_objects': total_objects,
                'content_categories': content_types,
                'last_modified': max([obj['LastModified'].isoformat() for page in pages for obj in page.get('Contents', [])]) if total_objects > 0 else None
            }
            
        except Exception as e:
            logger.error(f"Error inventorying S3: {e}")
            inventory = {'error': str(e)}
        
        return inventory

    def _inventory_api_content(self) -> Dict:
        """Inventory API content types and capabilities"""
        logger.info("🔌 Inventorying API content...")
        
        inventory = {
            'health_status': None,
            'claude_mode': None,
            'artist_coverage': {},
            'source_types': set(),
            'url_domains': set()
        }
        
        try:
            # Health check
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            if health_response.status_code == 200:
                inventory['health_status'] = health_response.json().get('status')
            
            # Test each artist
            for artist in self.test_artists:
                try:
                    query_response = requests.post(
                        f"{self.api_url}/query",
                        json={"query": artist, "k": 3},
                        timeout=15
                    )
                    
                    if query_response.status_code == 200:
                        data = query_response.json()
                        inventory['claude_mode'] = data.get('mode', 'unknown')
                        
                        sources = data.get('sources', [])
                        inventory['artist_coverage'][artist] = {
                            'sources_count': len(sources),
                            'sources': [s.get('source', 'Unknown') for s in sources[:3]]
                        }
                        
                        # Track source types and URL domains
                        for source in sources:
                            inventory['source_types'].add(source.get('source', 'Unknown'))
                            url = source.get('url', '')
                            if url.startswith('http'):
                                domain = url.split('/')[2]
                                inventory['url_domains'].add(domain)
                                
                except Exception as e:
                    inventory['artist_coverage'][artist] = {'error': str(e)}
                    
        except Exception as e:
            logger.error(f"Error inventorying API: {e}")
            inventory['api_error'] = str(e)
        
        # Convert sets to lists for JSON serialization
        inventory['source_types'] = list(inventory['source_types'])
        inventory['url_domains'] = list(inventory['url_domains'])
        
        return inventory

    def _inventory_knowledge_graph(self) -> Dict:
        """Inventory knowledge graph statistics"""
        logger.info("🕸️  Inventorying knowledge graph...")
        
        try:
            # Download latest knowledge graph
            response = self.s3_client.list_objects_v2(
                Bucket='ut-processed-content',
                Prefix='enhanced-knowledge-graph/',
                MaxKeys=1
            )
            
            if 'Contents' in response:
                latest_key = response['Contents'][0]['Key']
                
                # Get object
                obj = self.s3_client.get_object(Bucket='ut-processed-content', Key=latest_key)
                kg_data = json.loads(obj['Body'].read())
                
                return {
                    'total_relationships': len(kg_data.get('relationships', [])),
                    'source_distribution': kg_data.get('enhancement_info', {}).get('source_distribution', {}),
                    'artists_count': len(eval(kg_data.get('artists', '{}'))),  # Safe eval for set literal
                    'last_updated': latest_key
                }
            else:
                return {'error': 'No knowledge graph found'}
                
        except Exception as e:
            logger.error(f"Error inventorying knowledge graph: {e}")
            return {'error': str(e)}

    def _inventory_canonical_urls(self) -> Dict:
        """Inventory canonical URL coverage"""
        logger.info("🔗 Inventorying canonical URLs...")
        
        url_coverage = {}
        
        try:
            # Test sample queries to see URL patterns
            test_queries = ['50 Cent', 'Beatles', 'Taylor Swift']
            
            for query in test_queries:
                response = requests.post(
                    f"{self.api_url}/query",
                    json={"query": query, "k": 5},
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    sources = data.get('sources', [])
                    
                    for source in sources:
                        url = source.get('url', '')
                        if url:
                            domain = url.split('/')[2] if url.startswith('http') else 'unknown'
                            
                            if domain not in url_coverage:
                                url_coverage[domain] = {
                                    'count': 0,
                                    'canonical': not domain.endswith('.txt.com'),
                                    'examples': []
                                }
                            
                            url_coverage[domain]['count'] += 1
                            if len(url_coverage[domain]['examples']) < 2:
                                url_coverage[domain]['examples'].append(url)
                                
        except Exception as e:
            logger.error(f"Error inventorying URLs: {e}")
            url_coverage['error'] = str(e)
        
        return url_coverage

    def validate_pre_cleanup(self, target_paths: List[str]) -> Tuple[bool, List[str]]:
        """Validate before cleanup operations"""
        logger.info("🛡️  Running pre-cleanup validation...")
        
        issues = []
        
        # Create baseline inventory
        baseline = self.create_content_inventory()
        
        # Check if any target paths contain critical content
        for path in target_paths:
            if any(keyword in path.lower() for keyword in ['artist', 'author', 'wiki', 'musicbrainz', 'canonical']):
                issues.append(f"⚠️  Target path '{path}' may contain canonical content")
        
        # Verify backup exists for deletion targets
        for path in target_paths:
            if path.startswith('s3://'):
                bucket_name = path.split('/')[2]
                
                # Check if backup exists
                try:
                    backup_key = f"99-archive/pre-cleanup-backup/{datetime.utcnow().strftime('%Y-%m-%d')}/{bucket_name}/"
                    response = self.s3_client.list_objects_v2(
                        Bucket='ut-processed-content',
                        Prefix=backup_key,
                        MaxKeys=1
                    )
                    
                    if 'Contents' not in response:
                        issues.append(f"❌ No backup found for {path} at {backup_key}")
                        
                except Exception as e:
                    issues.append(f"❌ Cannot verify backup for {path}: {e}")
        
        # Save pre-cleanup inventory
        inventory_path = f"/tmp/pre-cleanup-inventory-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(inventory_path, 'w') as f:
            json.dump(baseline, f, indent=2)
        logger.info(f"📁 Pre-cleanup inventory saved: {inventory_path}")
        
        return len(issues) == 0, issues

    def validate_post_deployment(self, baseline_inventory: Dict = None) -> Tuple[bool, List[str]]:
        """Validate after deployment"""
        logger.info("🔍 Running post-deployment validation...")
        
        issues = []
        current = self.create_content_inventory()
        
        # Check API health
        if current['api_content'].get('health_status') != 'healthy':
            issues.append(f"❌ API health status: {current['api_content'].get('health_status', 'unknown')}")
        
        # Check Claude mode
        if current['api_content'].get('claude_mode') == 'fallback':
            issues.append("❌ Claude in fallback mode - synthesis not working")
        
        # Check artist coverage
        for artist in self.test_artists:
            coverage = current['api_content']['artist_coverage'].get(artist, {})
            if 'error' in coverage:
                issues.append(f"❌ {artist} query failed: {coverage['error']}")
            elif coverage.get('sources_count', 0) == 0:
                issues.append(f"❌ {artist} returns no sources")
        
        # Check for canonical URL regression
        canonical_domains = ['billboard.com', 'pitchfork.com', 'theguardian.com']
        found_canonical = any(domain in current['canonical_urls'] for domain in canonical_domains)
        if not found_canonical:
            issues.append("❌ No canonical URLs found - major regression")
        
        # Compare with baseline if provided
        if baseline_inventory:
            baseline_relationships = baseline_inventory.get('knowledge_graph', {}).get('total_relationships', 0)
            current_relationships = current.get('knowledge_graph', {}).get('total_relationships', 0)
            
            if current_relationships < baseline_relationships * 0.9:  # Allow 10% variance
                issues.append(f"❌ Relationship count dropped significantly: {baseline_relationships} → {current_relationships}")
        
        return len(issues) == 0, issues

    def create_backup(self, source_paths: List[str]) -> str:
        """Create backup before destructive operations"""
        logger.info("💾 Creating backup...")
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_prefix = f"99-archive/pre-cleanup-backup/{timestamp}/"
        
        try:
            for source_path in source_paths:
                if source_path.startswith('s3://'):
                    # Parse S3 path
                    path_parts = source_path.replace('s3://', '').split('/')
                    source_bucket = path_parts[0]
                    source_key = '/'.join(path_parts[1:]) if len(path_parts) > 1 else ''
                    
                    # Copy to backup location
                    copy_source = {'Bucket': source_bucket, 'Key': source_key}
                    self.s3_client.copy_object(
                        CopySource=copy_source,
                        Bucket='ut-processed-content',
                        Key=f"{backup_prefix}{source_bucket}/{source_key}"
                    )
            
            logger.info(f"✅ Backup created at: s3://ut-processed-content/{backup_prefix}")
            return f"s3://ut-processed-content/{backup_prefix}"
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Data Integrity Checks for UT-API')
    parser.add_argument('--mode', choices=['pre-cleanup', 'pre-deployment', 'post-deployment', 'inventory'], 
                       required=True, help='Validation mode')
    parser.add_argument('--targets', nargs='*', help='Target paths for cleanup validation')
    parser.add_argument('--baseline', help='Baseline inventory file for comparison')
    
    args = parser.parse_args()
    
    checker = DataIntegrityChecker()
    
    if args.mode == 'inventory':
        # Just create and save inventory
        inventory = checker.create_content_inventory()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"content-inventory-{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2)
        
        print(f"📋 Content inventory saved: {filename}")
        
        # Print summary
        print(f"📊 Summary:")
        print(f"   S3 Objects: {inventory['s3_content'].get('total_objects', 'unknown')}")
        print(f"   API Status: {inventory['api_content'].get('health_status', 'unknown')}")
        print(f"   Claude Mode: {inventory['api_content'].get('claude_mode', 'unknown')}")
        print(f"   Knowledge Graph: {inventory['knowledge_graph'].get('total_relationships', 'unknown')} relationships")
        print(f"   Canonical URLs: {len(inventory['canonical_urls'])} domains")
        
    elif args.mode == 'pre-cleanup':
        if not args.targets:
            print("❌ --targets required for pre-cleanup validation")
            exit(1)
            
        success, issues = checker.validate_pre_cleanup(args.targets)
        
        if success:
            print("✅ Pre-cleanup validation passed")
            exit(0)
        else:
            print("❌ Pre-cleanup validation failed:")
            for issue in issues:
                print(f"   {issue}")
            exit(1)
            
    elif args.mode == 'post-deployment':
        baseline = None
        if args.baseline:
            with open(args.baseline, 'r') as f:
                baseline = json.load(f)
        
        success, issues = checker.validate_post_deployment(baseline)
        
        if success:
            print("✅ Post-deployment validation passed")
            exit(0)
        else:
            print("❌ Post-deployment validation failed:")
            for issue in issues:
                print(f"   {issue}")
            exit(1)

if __name__ == '__main__':
    main()