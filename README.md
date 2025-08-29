# United Tribes API

**Cultural discovery through enhanced knowledge graphs and semantic search**

![API Status](https://img.shields.io/badge/API-Production%20Ready-brightgreen) ![Citations](https://img.shields.io/badge/Citations-100%25%20Coverage-blue) ![Sources](https://img.shields.io/badge/Sources-Verified-green)

## 🌟 Overview

The United Tribes API provides **read-only access** to our curated cultural knowledge graph, featuring music artists, influences, and relationships with comprehensive source attribution and citation tracking.

### **Production-Grade Capabilities**
- 🔍 **Query Cultural Entities**: Search artists, influences, and musical relationships
- 🤖 **Claude-Powered Analysis**: Cultural Cartographer provides contextual insights
- 📚 **Enhanced Answers**: Responses include citations, confidence scores, and source verification
- 🕸️ **Network Browsing**: Discovery pathways to explore entity connections
- 📖 **Academic Citations**: APA, MLA, Chicago format citations ready for research

### **User Experience Flow**
1. **Ask Cultural Questions**: "How did blues influence rock music?"
2. **Receive AI Analysis**: Claude processes your query with cultural context
3. **Get Sourced Answers**: Every claim backed by exact quotes and citations
4. **Explore Connections**: Follow discovery pathways to related entities
5. **Browse the Network**: Navigate relationships between artists and influences

**What makes us different:**
- **100% Source Attribution**: Every entity includes exact quotes and citations
- **Cultural Cartographer**: AI-powered cultural analysis and discovery pathways  
- **Enhanced Search**: Semantic search with confidence scoring and source filtering
- **Production Ready**: Always-on cloud deployment with auto-scaling

## 🚀 Quick Start

### Start Services Locally
```bash
# Clone and setup
git clone https://github.com/United-Tribes/united-tribes-api.git
cd united-tribes-api

# Start both services
docker-compose up -d

# Test the API
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "jazz influences on hip hop", "k": 5}'
```

### Production API Access
```bash
# Production endpoint (currently deployed on AWS ECS)
export API_BASE_URL="http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com"

# Query the Cultural Cartographer
curl -X POST "$API_BASE_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Bob Dylan folk music influences", "k": 5}'
```

## 📋 API Services

### Cultural Cartographer API (`query-service`) 🎯
**Primary customer-facing API** - Your gateway to cultural discovery

**Endpoint**: `POST /query`

**What it does:**
- 🤖 **Claude-Powered Analysis**: Contextual cultural insights and interpretation
- 🔍 **Entity Discovery**: Finds relevant artists, influences, and relationships
- 📚 **Source Attribution**: Every response includes citations and evidence
- 🗺️ **Discovery Pathways**: Suggests related queries and exploration paths

**Perfect for:**
- Cultural research and academic work
- Content creation and storytelling
- Music discovery and exploration
- Understanding artistic influences and connections

### Semantic Search API (`vector-store`) 🔍
**High-performance search backend** - Direct access to entity relationships

**Endpoint**: `POST /search`

**What it does:**
- ⚡ **Fast Entity Lookup**: Direct search of cultural entities and relationships
- 🎨 **Source Filtering**: Filter by specific publications (Rolling Stone, Pitchfork, etc.)
- 📊 **Similarity Scoring**: Confidence-based result ranking
- 🔗 **Relationship Mapping**: Direct access to entity connections

**Perfect for:**
- Building cultural applications
- Direct entity and relationship queries
- High-volume search operations
- Custom cultural discovery interfaces

### **Read-Only Design 🔒**
Both APIs are **read-only** - no data modification, completely safe for public access.

## 🌆 Example User Journeys

### **Researcher**: "I need to understand jazz influences on modern music"

1. **Query**: `POST /query` with "jazz influences on modern music"
2. **AI Analysis**: Cultural Cartographer analyzes the cultural context
3. **Sourced Response**: Detailed analysis with exact quotes from music historians
4. **Citations**: Academic-ready citations from Rolling Stone, NPR, Billboard
5. **Discovery**: "Explore Miles Davis connections to hip-hop producers"
6. **Network Browsing**: Follow pathways to discover unexpected connections

### **Content Creator**: "I want to write about unexpected musical connections"

1. **Query**: `POST /query` with "unexpected musical influences"
2. **Cultural Insights**: Claude identifies surprising artist relationships
3. **Story Material**: Rich narratives with source attribution for fact-checking
4. **Exploration Paths**: Multiple angles for content development
5. **Verification**: All claims backed by credible music journalism sources

### **Music App Developer**: "I need artist relationship data for my app"

1. **Direct Search**: `POST /search` with specific artist names
2. **Fast Results**: Entity relationships with confidence scores
3. **Source Filtering**: Results from trusted music publications only
4. **Integration**: Clean JSON responses for application integration
5. **Scalable**: High-performance search for user-facing features

## 🎯 Technical Features

### Enhanced Attribution System
```json
{
  "sources": [
    {
      "source": "Rolling Stone",
      "evidence_text": "Dylan revolutionized folk music in the 1960s",
      "citation": "\"Dylan revolutionized folk music in the 1960s\" from Bob Dylan: The Revolution by Music Critic, Rolling Stone",
      "confidence": 0.95,
      "paragraph_number": 2,
      "source_verification_score": 1.0
    }
  ]
}
```

### Discovery Pathways
```json
{
  "discovery_pathways": [
    "Explore verified connections between Bob Dylan and Joan Baez",
    "Find well-documented influences on Bob Dylan",
    "Discover cited collaborations of Bob Dylan"
  ]
}
```

### Quality Metrics
```json
{
  "attribution_quality": 0.95,
  "citation_readiness": 1.0,
  "source_verification_score": 0.85
}
```

## 📚 Documentation

- **[API Reference](docs/api-reference.md)** - Complete endpoint documentation
- **[Getting Started](docs/getting-started.md)** - Developer onboarding guide
- **[Examples](docs/examples/)** - Code samples and use cases
- **[Authentication](docs/authentication.md)** - API keys and rate limits

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐
│ Query Service   │───▶│ Vector Store     │
│ (Port 8001)     │    │ (Port 8002)      │
│                 │    │                  │
│ Cultural        │    │ Semantic Search  │
│ Cartographer    │    │ FAISS + S3       │
└─────────────────┘    └──────────────────┘
         │                       │
         ▼                       ▼
    [Customer API]          [S3 Knowledge Base]
```

**Always-On Services:**
- **Query Service**: Customer-facing Cultural Cartographer API
- **Vector Store**: Search backend with enhanced attribution data

**Data Pipeline** (separate repository):
- Content scraping and processing runs on schedule
- Updates knowledge base with fresh cultural content

## 🚀 Deployment

### Current Production Status
**Deployed on AWS ECS (Fargate) with Application Load Balancer**

- **Query Service**: ✅ Running - Claude-powered Cultural Cartographer
- **Vector Store**: ⚠️  Service available, data loading in progress
- **Load Balancer**: `ut-api-alb-470552730.us-east-1.elb.amazonaws.com`
- **ECS Cluster**: `ut-api-cluster`

### Production Deployment
```bash
# Deploy to AWS ECS via ECR
./scripts/deploy.sh development

# Check service status
aws ecs describe-services --cluster ut-api-cluster --services ut-query-service-service ut-vector-store-service
```

### Development Environment
```bash
# Local development with Docker
docker-compose -f docker-compose.dev.yml up

# With hot reload
docker-compose -f docker-compose.dev.yml up --build
```

## 📊 Monitoring & Health

### Health Checks
```bash
# Query Service health
curl http://localhost:8001/health

# Vector Store health  
curl http://localhost:8002/health
```

### Metrics Available
- Response times and throughput
- Citation quality scores
- Source verification rates
- API usage analytics

## 🤝 Contributing

We welcome contributions to improve the United Tribes API experience:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.unitedtribes.com](https://docs.unitedtribes.com)
- **Issues**: [GitHub Issues](https://github.com/United-Tribes/united-tribes-api/issues)
- **API Support**: api-support@unitedtribes.com

---

**Built with ❤️ by the United Tribes team**

*Connecting cultures through enhanced knowledge graphs and semantic understanding*
