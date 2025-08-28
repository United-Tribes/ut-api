# UT-Query-Service

RAG pipeline and user interface microservice for United Tribes. Provides the cultural cartographer experience with flexible query processing.

## Overview

UT-Query-Service is responsible for:
- Processing user queries with semantic understanding
- Coordinating with ut-vector-store for content retrieval
- Generating responses using the Cultural Cartographer LLM prompts
- Serving the web interface for United Tribes discovery
- Providing graceful degradation during rate limits

## Architecture

```
[User Query] → [Query Processing] → [Vector Search] → [Cultural Cartographer] → [Response]
                     ↓                    ↑                    ↓
              [Flexible Prompts]    [ut-vector-store]    [Web Interface]
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run service
uvicorn src.app:app --host 0.0.0.0 --port 8004 --reload

# Access web interface
open http://localhost:8004
```

## Features

### ✅ Flexible Query Processing
- **No rigid query classification** - LLM adapts naturally to any input
- **Single intelligent prompt** handles all query types organically
- **Natural adaptation** - Simple questions get direct answers, complex ones get rich analysis

### ✅ Cultural Cartographer Identity
- **Discovery-first analysis** - Every response includes pathways for further exploration
- **Cross-media recommendations** - Music → Podcasts → Books → Documentaries
- **Warm, knowledgeable tone** - Like that friend who always knows the perfect next thing

### ✅ Graceful Degradation
- **When LLM available**: Full cultural cartographer experience
- **When rate limited**: Useful search results with context and connections
- **No failures** - Always returns something valuable

## API Endpoints

- `POST /query` - Main RAG query endpoint
- `GET /` - Serve web interface
- `GET /health` - Service health check
- `GET /stats` - Query statistics and performance metrics

## Configuration

### Environment Variables
- `BEDROCK_ACCESS_KEY_ID` - AWS Bedrock credentials
- `BEDROCK_SECRET_ACCESS_KEY` - AWS Bedrock credentials
- `BEDROCK_REGION` - AWS region (default: us-east-1)
- `VECTOR_STORE_URL` - URL for ut-vector-store service
- `LOG_LEVEL` - Logging level (INFO, DEBUG)

### Cultural Cartographer Prompts
Edit `prompts/cultural_cartographer.md` to customize the LLM behavior:

```markdown
## Cultural Cartographer Identity
You are a cultural cartographer and discovery engine who transforms every piece of media into a rich network of cross-platform connections...

## Response Guidelines
- Let the query guide your response style naturally
- For influence queries, provide rich cultural context
- Always ground responses in documented relationships
- Weave in discovery pathways organically
```

## Data Contracts

### Query Request
```json
{
  "query": "Who influenced Amy Winehouse?",
  "k": 5
}
```

### Query Response
```json
{
  "response": "Rich cultural analysis with discovery pathways...",
  "sources": [
    {
      "source": "Rolling Stone",
      "artist": "Amy Winehouse", 
      "content_type": "article",
      "confidence": 0.8,
      "excerpt": "Content preview...",
      "url": "https://source-url.com"
    }
  ],
  "query_time_ms": 2500,
  "stats": {
    "total_chunks": 2763,
    "search_results_count": 5
  }
}
```

## Service Integration

### With ut-vector-store
- `POST /search` - Semantic similarity search
- `GET /stats` - Index statistics

### With ut-content-processor (future)
- Real-time content processing for new queries
- Entity relationship updates

## Development

### Running Tests
```bash
pytest tests/ -v --cov=src
```

### Local Development with Mock Data
```bash
# Use mock responses during development
export USE_MOCK=true
uvicorn src.app:app --reload
```

### Performance Testing
```bash
# Load test the query endpoint
python tests/load_test.py --queries 100 --concurrent 10
```

## Deployment

### Docker
```bash
# Build image
docker build -f docker/Dockerfile -t ut-query-service:latest .

# Run container
docker run -p 8004:8004 --env-file .env ut-query-service:latest
```

### Kubernetes
```bash
# Deploy to cluster
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Monitoring

### Health Checks
- **Endpoint**: `GET /health`
- **Dependencies**: Vector store connectivity, LLM service status
- **Metrics**: Response times, success rates, error counts

### Performance Metrics
- **Query latency**: Target <5s for 95th percentile
- **Success rate**: Target >99% availability  
- **Graceful degradation**: Fallback response rate during throttling

### Alerts
- Query latency > 10s
- Error rate > 1%
- Vector store connectivity issues
- LLM service throttling

## Architecture Decisions

### Why Single Flexible Prompt?
- **Eliminates rigid classification** - LLM is smart enough to adapt
- **More natural responses** - No forced structure constraints
- **Easier maintenance** - One prompt to rule them all
- **Better user experience** - Handles edge cases gracefully

### Why Graceful Degradation?
- **AWS Bedrock has strict limits** - 10 requests/minute default
- **User experience continuity** - Always provide value
- **Transparency** - Users understand when system is limited
- **Operational resilience** - Service never completely fails

## Contributing

1. Create feature branch from `develop`
2. Implement changes with tests
3. Ensure response time < 5s target
4. Test graceful degradation scenarios
5. Submit PR with cultural cartographer review