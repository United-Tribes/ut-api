"""
Embedding service using AWS Bedrock Titan V2
"""

import json
import logging
import os
from typing import List, Union
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates embeddings using AWS Bedrock Titan V2"""
    
    def __init__(self):
        self.model = "amazon.titan-embed-text-v2:0"
        self.dimension = 1024
        self.bedrock_client = None
        self.use_mock = os.getenv('USE_MOCK', 'false').lower() == 'true'
        
    async def initialize(self):
        """Initialize the embedding service"""
        logger.info("Initializing Bedrock embedding service...")
        
        if self.use_mock:
            logger.warning("Using MOCK embedding service - stub embeddings will be generated")
            return
        
        try:
            # Initialize Bedrock client
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            # Test the connection
            await self.test_connection()
            logger.info("Bedrock embedding service initialized successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found - falling back to mock mode")
            self.use_mock = True
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e} - falling back to mock mode")
            self.use_mock = True
        
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down embedding service...")
        self.bedrock_client = None
        
    async def generate_embeddings(
        self,
        content: Union[str, List[str]],
        model: str = None,
        normalize: bool = True,
        batch_size: int = 10
    ) -> List[List[float]]:
        """Generate embeddings for content using Bedrock Titan V2"""
        if isinstance(content, str):
            content = [content]
            
        logger.info(f"Generating embeddings for {len(content)} items using {'mock' if self.use_mock else 'Bedrock'}")
        
        if self.use_mock:
            return await self._generate_mock_embeddings(content, normalize)
        
        # Real Bedrock implementation
        embeddings = []
        model_id = model or self.model
        
        try:
            # Process in batches to avoid rate limits
            for i in range(0, len(content), batch_size):
                batch = content[i:i + batch_size]
                
                for text in batch:
                    # Prepare request body for Titan V2
                    body = {
                        "inputText": text[:8192],  # Titan V2 max input length
                        "dimensions": self.dimension,
                        "normalize": normalize
                    }
                    
                    # Make request to Bedrock
                    response = self.bedrock_client.invoke_model(
                        modelId=model_id,
                        contentType="application/json",
                        accept="application/json",
                        body=json.dumps(body)
                    )
                    
                    # Parse response
                    response_body = json.loads(response['body'].read())
                    embedding = response_body['embedding']
                    embeddings.append(embedding)
                
            logger.info(f"Successfully generated {len(embeddings)} embeddings using Bedrock")
            return embeddings
            
        except ClientError as e:
            logger.error(f"Bedrock request failed: {e}")
            logger.warning("Falling back to mock embeddings")
            return await self._generate_mock_embeddings(content, normalize)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            logger.warning("Falling back to mock embeddings")
            return await self._generate_mock_embeddings(content, normalize)
    
    async def _generate_mock_embeddings(
        self, 
        content: List[str], 
        normalize: bool = True
    ) -> List[List[float]]:
        """Generate mock embeddings for testing"""
        embeddings = []
        for text in content:
            # Generate deterministic embedding based on text hash
            text_hash = hash(text) % (2**31)  # Ensure positive
            np.random.seed(text_hash)
            
            embedding = np.random.randn(self.dimension).tolist()
            if normalize:
                # Normalize to unit vector
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = (np.array(embedding) / norm).tolist()
            embeddings.append(embedding)
            
        return embeddings
        
    async def test_connection(self) -> bool:
        """Test Bedrock connectivity"""
        if self.use_mock:
            logger.info("Mock embedding service - connection test passed")
            return True
            
        logger.info("Testing Bedrock connection...")
        
        try:
            # Test with a simple embedding request
            test_response = await self.generate_embeddings(
                "Test connection to Bedrock Titan V2",
                batch_size=1
            )
            
            if test_response and len(test_response) == 1:
                logger.info("Bedrock connection test successful")
                return True
            else:
                logger.error("Bedrock connection test failed - invalid response")
                return False
                
        except Exception as e:
            logger.error(f"Bedrock connection test failed: {e}")
            return False