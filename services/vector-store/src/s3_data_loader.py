"""
S3 data loader for consuming enhanced knowledge graph data
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3DataLoader:
    """Loads enhanced knowledge graph data from S3"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv('UT_PROCESSED_BUCKET', 'ut-processed-content')
        self.s3_client = None
        
    async def initialize(self):
        """Initialize S3 client"""
        logger.info("Initializing S3 data loader...")
        
        try:
            # Initialize S3 client (use AWS credential chain)
            self.s3_client = boto3.client(
                's3',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 data loader initialized successfully - bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket {self.bucket_name} not found")
            else:
                logger.error(f"Failed to access S3 bucket: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 data loader: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down S3 data loader...")
        self.s3_client = None
    
    async def load_enhanced_knowledge_graph(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Load the enhanced knowledge graph from S3"""
        
        if not self.s3_client:
            raise RuntimeError("S3 data loader not initialized")
        
        # If no date specified, look for the most recent one
        if not date:
            date = await self._find_latest_enhanced_data()
        
        # Look for the main enhanced knowledge graph file
        prefix = f"enhanced-knowledge-graph/{date}/"
        
        try:
            # List objects to find the main knowledge graph file
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = response.get('Contents', [])
            
            # Find the main knowledge graph file (contains "complete_knowledge_graph_main")
            main_file = None
            for obj in objects:
                key = obj['Key']
                if 'complete_knowledge_graph_main' in key and key.endswith('.json'):
                    main_file = key
                    break
            
            if not main_file:
                # Fallback to any complete knowledge graph file
                for obj in objects:
                    key = obj['Key']
                    if 'complete_knowledge_graph' in key and key.endswith('.json'):
                        main_file = key
                        break
            
            if not main_file:
                raise ValueError(f"No enhanced knowledge graph found for date {date}")
            
            logger.info(f"Loading enhanced knowledge graph: s3://{self.bucket_name}/{main_file}")
            
            # Load the knowledge graph
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=main_file
            )
            
            content = json.loads(response['Body'].read().decode('utf-8'))
            
            # Validate the content
            relationships = content.get('relationships', [])
            if not relationships:
                raise ValueError("No relationships found in knowledge graph")
            
            logger.info(f"Successfully loaded {len(relationships)} enhanced relationships")
            
            # Add metadata about the loaded data
            content['_s3_metadata'] = {
                'bucket': self.bucket_name,
                'key': main_file,
                'loaded_at': datetime.utcnow().isoformat(),
                'size_bytes': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat() if 'LastModified' in response else None
            }
            
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"Enhanced knowledge graph not found: {date}")
                raise ValueError(f"No enhanced knowledge graph found for date {date}")
            else:
                logger.error(f"Failed to load enhanced knowledge graph: {e}")
                raise
        except Exception as e:
            logger.error(f"Error loading enhanced knowledge graph: {e}")
            raise
    
    async def load_relationships_by_source(self, source: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load relationships filtered by source (Billboard, Pitchfork, etc.)"""
        
        if not date:
            date = await self._find_latest_enhanced_data()
        
        # Check if source-specific file exists
        safe_source = source.lower().replace(' ', '-').replace('.', '').replace('/', '-')
        source_key = f"enhanced-knowledge-graph/{date}/by-source/{safe_source}_relationships.json"
        
        try:
            logger.info(f"Loading relationships for source {source}: s3://{self.bucket_name}/{source_key}")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=source_key
            )
            
            content = json.loads(response['Body'].read().decode('utf-8'))
            relationships = content.get('relationships', [])
            
            logger.info(f"Successfully loaded {len(relationships)} relationships for {source}")
            return relationships
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # Fallback to filtering from main knowledge graph
                logger.warning(f"Source-specific file not found, filtering from main knowledge graph")
                main_data = await self.load_enhanced_knowledge_graph(date)
                relationships = main_data.get('relationships', [])
                
                # Filter by source
                filtered = [
                    rel for rel in relationships
                    if rel.get('source_attribution', {}).get('source', '').lower() == source.lower()
                ]
                
                logger.info(f"Filtered {len(filtered)} relationships for {source} from main knowledge graph")
                return filtered
            else:
                raise
    
    async def load_processed_content_chunks(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load processed content chunks for vector indexing"""
        
        if not date:
            date = await self._find_latest_processed_content()
        
        # Look for processed content chunks
        prefix = f"processed-content/{date}/chunks/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = response.get('Contents', [])
            all_chunks = []
            
            for obj in objects:
                key = obj['Key']
                if key.endswith('.json'):
                    logger.debug(f"Loading chunks from: s3://{self.bucket_name}/{key}")
                    
                    response = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                    
                    content = json.loads(response['Body'].read().decode('utf-8'))
                    chunks = content.get('chunks', [])
                    all_chunks.extend(chunks)
            
            logger.info(f"Successfully loaded {len(all_chunks)} processed content chunks")
            return all_chunks
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"No processed content chunks found for date {date}")
                return []
            else:
                raise
    
    async def _find_latest_enhanced_data(self) -> str:
        """Find the latest date with enhanced knowledge graph data"""
        
        prefix = "enhanced-knowledge-graph/"
        
        try:
            # List all dates under enhanced-knowledge-graph/
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            # Extract dates from common prefixes
            dates = []
            for prefix_info in response.get('CommonPrefixes', []):
                prefix_path = prefix_info['Prefix']
                # Extract date from path like "enhanced-knowledge-graph/2025/08/26/"
                parts = prefix_path.strip('/').split('/')
                if len(parts) >= 4:  # enhanced-knowledge-graph/YYYY/MM/DD/
                    date_str = f"{parts[1]}/{parts[2]}/{parts[3]}"
                    dates.append(date_str)
            
            if not dates:
                raise ValueError("No enhanced knowledge graph data found in S3")
            
            # Return the latest date
            latest = max(dates)
            logger.info(f"Found latest enhanced data date: {latest}")
            return latest
            
        except Exception as e:
            logger.error(f"Failed to find latest enhanced data: {e}")
            raise
    
    async def _find_latest_processed_content(self) -> str:
        """Find the latest date with processed content chunks"""
        
        prefix = "processed-content/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            dates = []
            for prefix_info in response.get('CommonPrefixes', []):
                prefix_path = prefix_info['Prefix']
                parts = prefix_path.strip('/').split('/')
                if len(parts) >= 4:  # processed-content/YYYY/MM/DD/
                    date_str = f"{parts[1]}/{parts[2]}/{parts[3]}"
                    dates.append(date_str)
            
            if not dates:
                # Fallback to enhanced knowledge graph date if no processed content
                logger.warning("No processed content found, using enhanced knowledge graph date")
                return await self._find_latest_enhanced_data()
            
            latest = max(dates)
            logger.info(f"Found latest processed content date: {latest}")
            return latest
            
        except Exception as e:
            logger.error(f"Failed to find latest processed content: {e}")
            # Fallback to enhanced knowledge graph
            return await self._find_latest_enhanced_data()
    
    async def list_available_sources(self, date: Optional[str] = None) -> List[str]:
        """List available sources in the enhanced knowledge graph"""
        
        if not date:
            date = await self._find_latest_enhanced_data()
        
        try:
            # Try to get sources from by-source directory first
            prefix = f"enhanced-knowledge-graph/{date}/by-source/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            sources = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith('_relationships.json'):
                    # Extract source name from filename
                    filename = key.split('/')[-1]
                    source_slug = filename.replace('_relationships.json', '')
                    # Convert back to proper source name
                    source = source_slug.replace('-', ' ').title()
                    sources.append(source)
            
            if sources:
                logger.info(f"Found {len(sources)} sources: {sources}")
                return sorted(sources)
            
            # Fallback: analyze main knowledge graph
            main_data = await self.load_enhanced_knowledge_graph(date)
            relationships = main_data.get('relationships', [])
            
            sources = set()
            for rel in relationships:
                source = rel.get('source_attribution', {}).get('source')
                if source:
                    sources.add(source)
            
            source_list = sorted(list(sources))
            logger.info(f"Found {len(source_list)} sources from main knowledge graph: {source_list[:5]}...")
            return source_list
            
        except Exception as e:
            logger.error(f"Failed to list available sources: {e}")
            return []
    
    async def get_data_statistics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the loaded data"""
        
        if not date:
            date = await self._find_latest_enhanced_data()
        
        try:
            main_data = await self.load_enhanced_knowledge_graph(date)
            relationships = main_data.get('relationships', [])
            
            # Count by source
            source_counts = {}
            confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
            relationship_types = {}
            
            for rel in relationships:
                # Source counts
                source = rel.get('source_attribution', {}).get('source', 'Unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
                
                # Confidence distribution
                confidence = rel.get('confidence', 0.0)
                if confidence >= 0.8:
                    confidence_distribution['high'] += 1
                elif confidence >= 0.6:
                    confidence_distribution['medium'] += 1
                else:
                    confidence_distribution['low'] += 1
                
                # Relationship types
                rel_type = rel.get('relationship_type', 'unknown')
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            return {
                'date': date,
                'total_relationships': len(relationships),
                'source_distribution': source_counts,
                'confidence_distribution': confidence_distribution,
                'relationship_types': relationship_types,
                'enhancement_info': main_data.get('enhancement_info', {}),
                'loaded_from_s3': main_data.get('_s3_metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get data statistics: {e}")
            return {'error': str(e)}