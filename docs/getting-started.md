# Getting Started with United Tribes API

Welcome to the United Tribes API! This guide will help you get up and running quickly.

## 🚀 Quick Setup

### 1. Local Development

```bash
# Clone the repository
git clone https://github.com/United-Tribes/united-tribes-api.git
cd united-tribes-api

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Verify services are running
curl http://localhost:8002/health  # Vector Store
curl http://localhost:8001/health  # Query Service
```

### 2. Test Your First Query

```bash
# Cultural Cartographer Query
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "jazz influences on modern music",
    "k": 3
  }' | jq .

# Direct Entity Search  
curl -X POST "http://localhost:8002/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bob Dylan",
    "k": 5,
    "source_filter": ["Rolling Stone"]
  }' | jq .
```

## 📋 API Overview

### Cultural Cartographer (`/query`)
**Primary customer-facing API** - Rich cultural analysis with source attribution.

**Key Features:**
- Contextual cultural analysis
- Discovery pathways for exploration  
- 100% source attribution with citations
- Quality metrics and confidence scoring

### Semantic Search (`/search`)
**Direct entity search** - Fast lookup of cultural entities and relationships.

**Key Features:**
- Source filtering by publication
- Entity-specific searches
- Similarity scoring
- Direct access to enhanced knowledge graph

## 🎯 Common Use Cases

### Research & Academia
```bash
# Get citation-ready cultural analysis
curl -X POST "http://localhost:8001/query" \
  -d '{"query": "influence of blues on rock music", "citation_ready_only": true}'
```

### Content Creation
```bash
# Discover cultural connections for storytelling
curl -X POST "http://localhost:8001/query" \
  -d '{"query": "unexpected musical influences", "k": 10}'
```

### Music Discovery
```bash
# Find related artists and influences
curl -X POST "http://localhost:8002/search" \
  -d '{"query": "Joni Mitchell", "entity_filter": ["artists"], "k": 8}'
```

## 🔑 Understanding Responses

### Enhanced Attribution
Every response includes detailed source information:

```json
{
  "sources": [
    {
      "source": "Rolling Stone",
      "evidence_text": "Dylan's impact on folk music cannot be overstated",
      "citation": "\"Dylan's impact on folk music cannot be overstated\" from Dylan's Legacy by Music Historian, Rolling Stone",
      "confidence": 0.92,
      "paragraph_number": 2,
      "url": "https://rollingstone.com/dylan-legacy"
    }
  ]
}
```

### Quality Metrics
Understand the reliability of your results:

```json
{
  "attribution_quality": 0.95,      // How complete is the source attribution
  "citation_readiness": 1.0,        // Percentage of citation-ready sources  
  "source_verification_score": 0.85 // How many sources are verifiable
}
```

### Discovery Pathways
Get suggestions for deeper exploration:

```json
{
  "discovery_pathways": [
    "Explore verified connections between Bob Dylan and Joan Baez",
    "Find well-documented influences on Bob Dylan",
    "Discover more insights from Rolling Stone"
  ]
}
```

## ⚙️ Configuration Options

### Query Parameters

**For `/query` (Cultural Cartographer):**
- `query` (required): Your cultural question
- `k` (optional, default: 5): Number of results
- `source_filter` (optional): Filter by publications
- `entity_filter` (optional): Filter by specific entities

**For `/search` (Direct Search):**
- `query` (required): Search term
- `k` (optional, default: 5): Number of results  
- `source_filter` (optional): Filter by publications
- `min_confidence` (optional, default: 0.7): Minimum confidence score
- `citation_ready_only` (optional): Only citation-ready results

### Source Filtering
Available sources include:
- `Rolling Stone`
- `Pitchfork` 
- `Billboard`
- `NPR`
- `The Guardian`

```bash
# Filter by specific sources
curl -X POST "http://localhost:8001/query" \
  -d '{"query": "punk rock history", "source_filter": ["Rolling Stone", "Pitchfork"]}'
```

## 🐛 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check if ports are already in use
lsof -i :8001
lsof -i :8002

# Use different ports if needed
docker-compose -f docker-compose.dev.yml up
```

**Empty responses:**
```bash
# Check if vector store has data
curl http://localhost:8002/data/summary

# Trigger index build if needed
curl -X POST "http://localhost:8002/index/build" \
  -d '{"index_name": "enhanced_main", "force_rebuild": true}'
```

**Authentication errors (production):**
```bash
# Verify your API key
export UT_API_KEY="your-api-key"
curl -H "Authorization: Bearer $UT_API_KEY" https://api.unitedtribes.com/health
```

## 🔗 Next Steps

- **[API Reference](api-reference.md)** - Complete endpoint documentation
- **[Examples](examples/)** - Code samples in multiple languages
- **[Authentication](authentication.md)** - Production API access
- **[Rate Limits](rate-limits.md)** - Usage guidelines

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/United-Tribes/united-tribes-api/issues)
- **Documentation**: [docs.unitedtribes.com](https://docs.unitedtribes.com)
- **Email**: api-support@unitedtribes.com

Happy exploring! 🎵