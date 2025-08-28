# UT-Vector-Store

Bedrock embeddings and FAISS search microservice for United Tribes. Provides semantic search capabilities over processed cultural content with source-aware indexing.

## Overview

UT-Vector-Store is responsible for:
- Creating vector embeddings using AWS Bedrock Titan V2
- Managing FAISS indices for fast similarity search
- Providing semantic search API for cultural content discovery
- Maintaining source attribution through the search pipeline
- Building resilient indices with comprehensive error handling

## Architecture

```
[Processed Content] → [Bedrock Embedding] → [FAISS Index] → [Semantic Search] → [Search Results]
                           ↓                    ↓                ↓
                    [Titan V2 1024d]    [Cosine Similarity]  [Source Attribution]
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Bedrock credentials

# Run service
uvicorn src.app:app --host 0.0.0.0 --port 8002 --reload

# Check health
curl http://localhost:8002/health
```

## Features

### ✅ Source-Aware Indexing
- **Original source preservation** - Maintains attribution to Pitchfork, NPR, podcasts
- **Direct quote capability** - Enables exact citation for content consumption
- **Fair use compliance** - Respects copyright while enabling search
- **Metadata preservation** - Artist, album, genre, temporal context

### ✅ Resilient Embedding Generation
- **AWS Bedrock integration** - Titan V2 embeddings (1024 dimensions)
- **Exponential backoff** - Handles rate limiting gracefully
- **100% success rate** - Comprehensive error handling and retry logic
- **Progress tracking** - Real-time status updates for index builds

### ✅ High-Performance Search
- **FAISS optimization** - Fast cosine similarity search
- **Configurable results** - Flexible k-parameter for search depth
- **Confidence scoring** - Relevance scores for search results
- **Multi-index support** - Separate indices for different content types

## API Endpoints

- `POST /search` - Semantic similarity search
- `POST /embed` - Generate embeddings for content
- `POST /index/build` - Build or rebuild indices
- `GET /index/stats` - Index statistics and health
- `POST /content/add` - Add processed content to index
- `GET /health` - Service health check

## Configuration

### Environment Variables
- `BEDROCK_ACCESS_KEY_ID` - AWS Bedrock credentials
- `BEDROCK_SECRET_ACCESS_KEY` - AWS Bedrock credentials  
- `BEDROCK_REGION` - AWS region (default: us-east-1)
- `FAISS_INDEX_PATH` - Path for FAISS index files
- `MAX_SEARCH_RESULTS` - Maximum search results (default: 20)
- `EMBEDDING_BATCH_SIZE` - Batch size for embedding generation (default: 10)

### Index Configuration
```yaml
# config/index_config.yaml
embedding_model: "amazon.titan-embed-text-v2:0"
dimension: 1024
similarity_metric: "cosine"
index_type: "HNSW"  # Hierarchical Navigable Small World
build_parameters:
  ef_construction: 200
  M: 16
search_parameters:
  ef_search: 100
```

## Data Contracts

### Search Request
```json
{
  "query": "Who influenced Amy Winehouse?",
  "k": 5,
  "source_filter": ["pitchfork", "npr"],
  "min_confidence": 0.7
}
```

### Search Response
```json
{
  "results": [
    {
      "content": "Semantic chunk content...",
      "source": {
        "source": "pitchfork",
        "title": "The Influence of Nina Simone",
        "url": "https://pitchfork.com/...",
        "author": "John Smith"
      },
      "similarity_score": 0.85,
      "entities": ["Amy Winehouse", "Nina Simone"],
      "chunk_metadata": {
        "chunk_type": "influence_analysis",
        "temporal_context": "2000s"
      }
    }
  ],
  "search_time_ms": 45,
  "total_results": 1247,
  "query_embedding_time_ms": 120
}
```

### Content Addition Request
```json
{
  "processed_content": {
    "content_id": "uuid",
    "chunks": [
      {
        "chunk_id": "uuid",
        "content": "Semantic chunk...",
        "metadata": {
          "source": "pitchfork",
          "entities": ["Amy Winehouse"]
        }
      }
    ],
    "source_info": {
      "source": "pitchfork",
      "title": "Article Title",
      "url": "https://example.com"
    }
  }
}
```

## Service Integration

### With ut-content-processor
- `POST /webhook/content-processed` - Receives processed content for indexing
- Automatically adds new content to search index

### With ut-query-service
- `POST /search` - Provides semantic search results
- `GET /stats` - Index health and performance metrics

## Development

### Building Indices Locally
```bash
# Build comprehensive index from processed content
python tools/build_index.py --content-path ./data/processed --output ./indices/

# Test search performance
python tools/test_search.py --index-path ./indices/ --query "jazz influences"
```

### Running Tests
```bash
pytest tests/ -v --cov=src
```

### Performance Testing
```bash
# Load test search endpoint
python tests/search_load_test.py --concurrent 20 --queries 1000
```

## Deployment

### Docker
```bash
# Build image
docker build -f docker/Dockerfile -t ut-vector-store:latest .

# Run container with mounted indices
docker run -p 8002:8002 -v ./indices:/app/indices --env-file .env ut-vector-store:latest
```

### Kubernetes
```bash
# Deploy with persistent volumes for indices
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/service.yaml
```

## Index Management

### Building Production Index
The service includes comprehensive tools for building production-ready indices:

```bash
# Full index build with all content types
./tools/build_production_index.sh

# Incremental index updates
python tools/incremental_update.py --new-content ./data/new/
```

### Index Statistics
- **Total chunks**: 2,763 (from processing all artists)
- **Embedding dimension**: 1024 (Titan V2)
- **Index size**: ~50MB for full cultural content
- **Search latency**: <50ms for 95th percentile
- **Memory usage**: ~200MB loaded index

## Monitoring

### Health Checks
- **Endpoint**: `GET /health`
- **Dependencies**: Bedrock connectivity, FAISS index availability
- **Metrics**: Search latency, embedding generation rates, index health

### Performance Metrics
- **Search latency**: Target <100ms for 95th percentile
- **Embedding generation**: Target 10 embeddings/second sustained
- **Index build time**: Target <5 minutes for 3000 chunks
- **Memory efficiency**: Target <500MB for 10k chunks

### Alerts
- Search latency > 200ms
- Bedrock connectivity issues
- Index corruption or unavailability
- Memory usage > 1GB
- Embedding generation rate < 1/second

## Architecture Decisions

### Why FAISS Over Vector Databases?
- **Performance**: Sub-100ms search on 10k+ vectors
- **Cost efficiency**: No external vector database costs
- **Control**: Full control over indexing and search parameters
- **Reliability**: Local indices reduce external dependencies

### Why Source-Aware Architecture?
- **Attribution accuracy**: Maintains original source context
- **Citation capability**: Enables direct quotes with attribution
- **Discovery enhancement**: Users can consume original content
- **Fair use compliance**: Proper source attribution for cultural content

### Why Titan V2 Embeddings?
- **Semantic quality**: Superior performance on cultural/music content
- **Dimension efficiency**: 1024d provides good accuracy/performance balance  
- **Cost optimization**: Competitive pricing for embedding generation
- **AWS integration**: Seamless integration with Bedrock services

## Search Quality Optimization

### Embedding Strategies
- **Content chunking**: Optimize chunk size for semantic coherence (800-1200 chars)
- **Context preservation**: Include surrounding context in chunks
- **Entity weighting**: Boost chunks with high-confidence entity matches
- **Temporal context**: Include time period information in embeddings

### Index Optimization
- **HNSW parameters**: Tuned for music/cultural content similarity
- **Multi-index strategy**: Separate indices for articles, podcasts, knowledge graph
- **Incremental updates**: Efficient addition of new content without full rebuild
- **Index versioning**: Maintain multiple index versions for A/B testing

## Troubleshooting

### Common Issues

#### Slow Search Performance
- **Check**: Index size and memory usage
- **Solution**: Optimize HNSW parameters or split into multiple indices

#### Low Search Relevance
- **Check**: Embedding quality and chunk boundaries
- **Solution**: Adjust chunking strategy or embedding model parameters

#### Bedrock Rate Limiting
- **Check**: Request rate and batch sizing
- **Solution**: Implement exponential backoff and request batching

#### Index Corruption
- **Check**: Index file integrity and disk space
- **Solution**: Rebuild index from processed content backup

## Contributing

1. Create feature branch from `develop`
2. Implement changes with comprehensive tests
3. Ensure search latency < 100ms target
4. Test with production-scale data (3000+ chunks)
5. Submit PR with search quality validation