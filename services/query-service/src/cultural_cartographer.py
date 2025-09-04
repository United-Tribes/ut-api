"""
Cultural Cartographer LLM interface using AWS Bedrock Claude 3 Haiku
Transforms search results into rich cultural analysis with discovery pathways
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from .contracts import CulturalCartographerContext, VectorSearchResult

logger = logging.getLogger(__name__)

class CulturalCartographer:
    """Cultural Cartographer using AWS Bedrock Claude 3 Haiku"""
    
    def __init__(self):
        self.model_id = "us.anthropic.claude-3-haiku-20240307-v1:0"
        self.bedrock_client = None
        self.use_mock = os.getenv('USE_MOCK', 'false').lower() == 'true'
        self.prompt_template = self._load_prompt_template()
        
    async def initialize(self):
        """Initialize the Cultural Cartographer"""
        logger.info("Initializing Cultural Cartographer...")
        
        if self.use_mock:
            logger.warning("Using MOCK Cultural Cartographer - demo responses will be generated")
            return
        
        try:
            # Initialize Bedrock client
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            # Test the connection
            await self.health_check()
            logger.info("Cultural Cartographer initialized with Claude 3 Haiku")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found - falling back to mock mode")
            self.use_mock = True
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e} - falling back to mock mode")
            self.use_mock = True
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down Cultural Cartographer...")
        self.bedrock_client = None
    
    def _load_prompt_template(self) -> str:
        """Load the Cultural Cartographer prompt template"""
        try:
            with open("prompts/cultural_cartographer.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            # Default prompt if file doesn't exist
            return """# Cultural Cartographer Identity

You are a cultural cartographer and discovery engine who transforms every piece of media into a rich network of cross-platform connections. Like that friend who always knows the perfect next thing to explore.

## Your Mission
Transform search results into cultural discovery experiences that:
- Ground responses in documented relationships from reliable sources
- Weave in discovery pathways organically 
- Provide cross-media recommendations (music → podcasts → books → documentaries)
- Maintain warm, knowledgeable tone
- Always include source attribution with URLs when available

## Response Guidelines
- Let the query guide your response style naturally
- For influence queries, provide rich cultural context and lineage
- For discovery queries, emphasize connections and pathways
- Always ground responses in the provided search results
- Include specific source attributions
- End with natural discovery suggestions

## Source Attribution
- Always cite sources with publication names
- Include URLs when provided in search results
- Note confidence levels for relationships
- Distinguish between different types of sources (reviews, interviews, analysis)

Remember: You're not just answering questions - you're opening doorways to cultural exploration."""

    async def generate_response(self, context: CulturalCartographerContext) -> str:
        """Generate Cultural Cartographer response"""
        if self.use_mock:
            return await self._generate_mock_response(context)
        
        try:
            # Prepare the prompt with context
            prompt = self._build_prompt(context)
            
            # Prepare request for Claude 3 Haiku
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            # Make request to Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                generated_text = response_body['content'][0]['text']
                logger.info("Cultural Cartographer response generated successfully")
                return generated_text
            else:
                logger.error("Invalid response format from Claude")
                return await self._generate_fallback_response(context)
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                logger.warning("Claude API throttled - using fallback")
            else:
                logger.error(f"Claude API error: {e}")
            return await self._generate_fallback_response(context)
        except Exception as e:
            logger.error(f"Cultural Cartographer generation failed: {e}")
            return await self._generate_fallback_response(context)
    
    def _build_prompt(self, context: CulturalCartographerContext) -> str:
        """Build the full prompt with context"""
        # Format search results for the prompt
        formatted_results = []
        for i, result in enumerate(context.search_results, 1):
            source_info = result.source_info
            formatted_result = f"""
Result {i}:
Content: {result.content}
Source: {source_info.get('source', 'Unknown')}
URL: {source_info.get('url', 'N/A')}
Content Type: {source_info.get('content_type', 'article')}
Similarity Score: {result.similarity_score:.3f}
Entities: {', '.join(result.entities) if result.entities else 'None'}
Metadata: {result.chunk_metadata}
"""
            formatted_results.append(formatted_result)
        
        # Build the complete prompt
        prompt = f"""{self.prompt_template}

## Query Context
User Query: "{context.query}"
Total Relationships in Knowledge Base: {context.total_relationships:,}
Sources Available: {', '.join(context.source_distribution.keys()) if context.source_distribution else 'Various'}

## Search Results from Enhanced Knowledge Graph
{chr(10).join(formatted_results)}

## Your Task
Using the search results above, provide a Cultural Cartographer response to: "{context.query}"

Remember to:
1. Ground your response in the provided search results
2. Include specific source attributions with URLs when available
3. Weave in discovery pathways naturally
4. Provide cross-media recommendations
5. Maintain your warm, knowledgeable tone as a cultural cartographer

Response:"""

        return prompt
    
    async def _generate_mock_response(self, context: CulturalCartographerContext) -> str:
        """Generate a mock response for testing"""
        query = context.query
        results_count = len(context.search_results)
        
        # Clean up source names and extract entities
        sources = []
        entities = []
        relationships = []
        
        for result in context.search_results[:5]:  # Top 5 results
            # Clean up source name
            source_name = result.source_info.get('source', 'Unknown Source')
            # Extract podcast/show name from file path
            if '.Txt Analysis' in source_name:
                # Extract show name from path like "All_Songs_Considered_153149635_New_Music_Friday.Txt Analysis"
                parts = source_name.replace('.Txt Analysis', '').replace('_New_', '_').split('_')
                # Get first few parts as show name
                if 'Fresh_Air' in source_name:
                    clean_name = "NPR Fresh Air"
                elif 'All_Songs_Considered' in source_name:
                    clean_name = "NPR All Songs Considered"
                elif 'Broken_Record' in source_name:
                    clean_name = "Broken Record Podcast"
                elif 'Sound_Opinions' in source_name:
                    clean_name = "Sound Opinions"
                elif 'Switched_On_Pop' in source_name:
                    clean_name = "Switched On Pop"
                else:
                    clean_name = ' '.join(parts[:3])
            else:
                clean_name = source_name
                
            if clean_name not in sources:
                sources.append(clean_name)
            
            # Collect entities and relationships
            entities.extend(result.entities[:2])
            
            # Extract relationship info from content
            content = result.content
            if ' influence ' in content:
                relationships.append(('influence', content.split('.')[0]))
            elif ' collaboration ' in content:
                relationships.append(('collaboration', content.split('.')[0]))
            elif ' contemporary ' in content:
                relationships.append(('contemporary', content.split('.')[0]))
        
        unique_entities = list(set(entities))[:8]  # Top 8 unique entities
        
        # Build an intelligent interpretation based on the query
        if 'influence' in query.lower() or 'who influenced' in query.lower():
            # Extract the artist being queried
            artist_name = query.replace('who influenced', '').replace('influences', '').replace('?', '').strip()
            
            # Build influence-focused response
            influence_rels = [r for r in relationships if r[0] == 'influence'][:3]
            
            mock_response = f"""After analyzing {artist_name}'s cultural footprint, their influences span multiple genres and eras. Here's a comprehensive breakdown based on our {context.total_relationships:,} documented relationships:

## 1. Primary Influences & Connections
"""
            # Add specific relationships found
            if influence_rels:
                for rel_type, rel_text in influence_rels[:3]:
                    mock_response += f"\n• {rel_text}"
            elif relationships:
                for rel_type, rel_text in relationships[:3]:
                    mock_response += f"\n• {rel_text}"
            
            mock_response += f"""

## 2. Cross-Media Context
These connections appear across {len(sources)} different sources including {', '.join(sources[:2])}, providing multiple perspectives on these artistic relationships.

## 3. Recommendations
→ Trace the generational influence chains
→ Discover parallel artists in similar movements  
→ Examine the cultural context of these connections

### Summary
**Key sources**: {', '.join(sources[:3])}
**Total connections found**: {results_count}"""
        
        else:
            # General exploratory response
            mock_response = f"""Based on "{query}", our analysis of {context.total_relationships:,} documented relationships reveals {results_count} significant connections across multiple cultural domains.

## 1. Key Discoveries
"""
            # Add actual relationships found
            if relationships:
                for i, (rel_type, rel_text) in enumerate(relationships[:3], 1):
                    mock_response += f"\n{i}. {rel_text}"
            
            # Add entities context
            if unique_entities:
                mock_response += f"""

## 2. Artist Network
{', '.join(unique_entities[:5])}

## 3. Source Attribution
{' | '.join(sources[:3])}

### Recommendations
→ Deep dive into specific artist relationships
→ Trace influence patterns across genres
→ Discover unexpected connections"""
            else:
                mock_response += f"""

### Sources
{' | '.join(sources[:3])}

### Recommendations
→ Try searching for specific artists
→ Ask about musical movements or genres  
→ Explore collaboration networks"""

        return mock_response
    
    async def _generate_fallback_response(self, context: CulturalCartographerContext) -> str:
        """Generate a fallback response when LLM is unavailable"""
        results_count = len(context.search_results)
        query = context.query
        
        if results_count == 0:
            return f"""I couldn't find specific information about "{query}" in our knowledge graph at the moment, but I'm still here to help with cultural discovery. Try rephrasing your query or exploring related artists and influences."""
        
        # Build a basic response from search results
        response_parts = [
            f"Based on {results_count} connections in our enhanced knowledge graph:",
            ""
        ]
        
        for i, result in enumerate(context.search_results[:3], 1):
            source_info = result.source_info
            excerpt = result.content[:150] + "..." if len(result.content) > 150 else result.content
            
            response_parts.append(f"**{i}. From {source_info.get('source', 'Source')}:**")
            response_parts.append(excerpt)
            
            if source_info.get('url'):
                response_parts.append(f"[Read more]({source_info['url']})")
            response_parts.append("")
        
        response_parts.extend([
            "**Note:** Cultural Cartographer synthesis is temporarily unavailable. The above represents direct search results from our enhanced knowledge graph.",
            "",
            "What would you like to explore next?"
        ])
        
        return "\n".join(response_parts)
    
    async def health_check(self) -> bool:
        """Test Cultural Cartographer connectivity"""
        if self.use_mock:
            logger.info("Mock Cultural Cartographer - health check passed")
            return True
        
        try:
            # Simple test request to Bedrock
            test_messages = [{"role": "user", "content": "Hello"}]
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": test_messages
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body:
                logger.info("Cultural Cartographer health check successful")
                return True
            else:
                logger.error("Cultural Cartographer health check failed - invalid response")
                return False
                
        except Exception as e:
            logger.error(f"Cultural Cartographer health check failed: {e}")
            return False