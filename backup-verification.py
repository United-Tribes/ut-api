#!/usr/bin/env python3
"""
Mandatory backup verification before S3 cleanup operations
Prevents data loss by ensuring backups exist before deletion

Usage:
    python backup-verification.py --verify-paths s3://bucket/path1 s3://bucket/path2
    python backup-verification.py --create-backup s3://artists-authors/
"""

import boto3
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupVerifier:
    """Verify backups exist before allowing destructive S3 operations"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.backup_bucket = 'ut-processed-content'
        self.backup_prefix = '99-archive/pre-cleanup-backup/'
    
    def create_backup(self, source_paths: List[str]) -> Dict[str, str]:
        """Create mandatory backups before cleanup"""
        logger.info("🛡️  Creating mandatory backups...")
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_locations = {}
        
        for source_path in source_paths:
            try:
                if source_path.startswith('s3://'):
                    backup_location = self._backup_s3_path(source_path, timestamp)
                    backup_locations[source_path] = backup_location
                    logger.info(f"✅ Backup created: {source_path} → {backup_location}")
                else:
                    logger.warning(f"⚠️  Unsupported path format: {source_path}")
                    
            except Exception as e:
                logger.error(f"❌ Backup failed for {source_path}: {e}")
                raise
        
        # Save backup manifest
        manifest_path = f"{self.backup_prefix}{timestamp}/backup-manifest.json"
        manifest = {
            'timestamp': timestamp,
            'backup_locations': backup_locations,
            'created_by': 'backup-verification.py',
            'source_paths': source_paths
        }
        
        self.s3_client.put_object(
            Bucket=self.backup_bucket,
            Key=manifest_path,
            Body=json.dumps(manifest, indent=2, default=str).encode('utf-8'),
            ContentType='application/json'
        )
        
        logger.info(f"📄 Backup manifest saved: s3://{self.backup_bucket}/{manifest_path}")
        return backup_locations
    
    def _backup_s3_path(self, source_path: str, timestamp: str) -> str:
        """Backup entire S3 path to archive location"""
        # Parse source path
        path_parts = source_path.replace('s3://', '').split('/')
        source_bucket = path_parts[0]
        source_prefix = '/'.join(path_parts[1:]) if len(path_parts) > 1 else ''
        
        # Create backup location
        backup_key_prefix = f"{self.backup_prefix}{timestamp}/{source_bucket}/"
        if source_prefix:
            backup_key_prefix += f"{source_prefix}/"
        
        # List and copy all objects
        paginator = self.s3_client.get_paginator('list_objects_v2')
        copy_count = 0
        
        list_params = {'Bucket': source_bucket}
        if source_prefix:
            list_params['Prefix'] = source_prefix
        
        for page in paginator.paginate(**list_params):
            for obj in page.get('Contents', []):
                source_key = obj['Key']
                backup_key = f"{backup_key_prefix}{source_key}"
                
                # Copy object
                copy_source = {'Bucket': source_bucket, 'Key': source_key}
                self.s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.backup_bucket,
                    Key=backup_key
                )
                copy_count += 1
        
        logger.info(f"📦 Copied {copy_count} objects to backup")
        return f"s3://{self.backup_bucket}/{backup_key_prefix}"
    
    def verify_backups_exist(self, target_paths: List[str]) -> Tuple[bool, List[str]]:
        """Verify backups exist for paths before allowing deletion"""
        logger.info("🔍 Verifying backups exist for target paths...")
        
        issues = []
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        for path in target_paths:
            if path.startswith('s3://'):
                bucket_name = path.split('/')[2]
                
                # Look for recent backups (last 7 days)
                backup_found = False
                for days_back in range(7):
                    check_date = (datetime.utcnow().date() - 
                                datetime.timedelta(days=days_back)).strftime('%Y%m%d')
                    
                    # Check for backup with this date
                    backup_prefix = f"{self.backup_prefix}{check_date}*/{bucket_name}/"
                    
                    try:
                        response = self.s3_client.list_objects_v2(
                            Bucket=self.backup_bucket,
                            Prefix=self.backup_prefix,
                            MaxKeys=1
                        )
                        
                        # Look through all backup directories
                        for obj in response.get('Contents', []):
                            if f"/{bucket_name}/" in obj['Key']:
                                backup_found = True
                                logger.info(f"✅ Backup found for {path}: {obj['Key']}")
                                break
                                
                        if backup_found:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error checking backups: {e}")
                
                if not backup_found:
                    issues.append(f"❌ No backup found for {path}")
                    issues.append(f"   Run: python backup-verification.py --create-backup {path}")
            else:
                issues.append(f"⚠️  Non-S3 path, cannot verify backup: {path}")
        
        return len(issues) == 0, issues
    
    def list_available_backups(self) -> List[Dict]:
        """List all available backups"""
        logger.info("📋 Listing available backups...")
        
        backups = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=self.backup_bucket, Prefix=self.backup_prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('backup-manifest.json'):
                    try:
                        # Get manifest
                        response = self.s3_client.get_object(
                            Bucket=self.backup_bucket,
                            Key=obj['Key']
                        )
                        manifest = json.loads(response['Body'].read().decode('utf-8'))
                        manifest['manifest_key'] = obj['Key']
                        backups.append(manifest)
                    except Exception as e:
                        logger.error(f"Error reading manifest {obj['Key']}: {e}")
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='Backup verification before S3 cleanup')
    parser.add_argument('--verify-paths', nargs='*', 
                       help='Verify backups exist for these S3 paths')
    parser.add_argument('--create-backup', nargs='*',
                       help='Create backups for these S3 paths')
    parser.add_argument('--list-backups', action='store_true',
                       help='List all available backups')
    
    args = parser.parse_args()
    
    verifier = BackupVerifier()
    
    if args.list_backups:
        backups = verifier.list_available_backups()
        print(f"\n📋 Found {len(backups)} backup sets:")
        for backup in backups:
            print(f"  {backup['timestamp']}: {len(backup.get('source_paths', []))} paths backed up")
            for path in backup.get('source_paths', [])[:3]:
                print(f"    - {path}")
            if len(backup.get('source_paths', [])) > 3:
                print(f"    ... and {len(backup.get('source_paths', [])) - 3} more")
    
    elif args.create_backup:
        print(f"\n🛡️  Creating backups for {len(args.create_backup)} paths...")
        backup_locations = verifier.create_backup(args.create_backup)
        print(f"✅ Backups created successfully!")
        for source, backup in backup_locations.items():
            print(f"  {source} → {backup}")
    
    elif args.verify_paths:
        success, issues = verifier.verify_backups_exist(args.verify_paths)
        
        if success:
            print("✅ All backups verified - safe to proceed with cleanup")
            exit(0)
        else:
            print("❌ Backup verification failed:")
            for issue in issues:
                print(f"  {issue}")
            exit(1)
    
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    main()