# United Tribes API - Current Deployment Status

**Last Updated**: August 29, 2025  
**Status**: Production Ready - Query Service Active

## 🚀 Production Deployment

### AWS Infrastructure
- **Service**: AWS ECS (Elastic Container Service) with Fargate
- **Load Balancer**: Application Load Balancer (ALB)
- **Region**: us-east-1
- **Cluster**: `ut-api-cluster`

### Service Endpoints
- **Production API**: `http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com`
- **Query Service**: `/query` - Cultural Cartographer with Claude integration ✅
- **Vector Store**: `/search` - Semantic search backend ⚠️

### Service Status

#### Query Service (Cultural Cartographer) ✅ ACTIVE
- **Container**: `ut-query-service-service`
- **Status**: Running and healthy
- **Features**: 
  - Claude 3 Haiku integration for cultural context
  - Source attribution and citation generation
  - Discovery pathways for exploration
  - Graceful degradation during rate limits
- **Health Check**: `GET /health` - Passing
- **Test**: 
  ```bash
  curl -X POST "http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "jazz influences on hip hop", "k": 5}'
  ```

#### Vector Store (Semantic Search) ⚠️ DEGRADED
- **Container**: `ut-vector-store-service`
- **Status**: Service running, data loading in progress
- **Issues**: 
  - Enhanced knowledge graph data not fully loaded
  - Some endpoints returning 500 errors during data loading
  - Health checks intermittently failing
- **Data Source**: S3 bucket `ut-processed-content/enhanced-knowledge-graph/`
- **Expected Resolution**: Service should stabilize once S3 data loading completes

### Load Balancer Routing
- **Port**: 80 (HTTP)
- **Rules**:
  - `/query*` → Query Service (Cultural Cartographer)
  - `/search*` → Vector Store (Semantic Search)
  - Default → Query Service

## 📊 System Architecture

```
Internet
    ↓
[Application Load Balancer]
    ↓
┌─────────────────────────────┐
│        ECS Cluster          │
│     (ut-api-cluster)        │
│                             │
│  ┌─────────────────────┐    │
│  │   Query Service     │    │ ← Claude Integration ✅
│  │   (Port 8000)       │    │
│  └─────────────────────┘    │
│                             │
│  ┌─────────────────────┐    │
│  │   Vector Store      │    │ ← Data Loading ⚠️
│  │   (Port 8000)       │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
    ↓
[S3: ut-processed-content]
```

## 🔧 Deployment Commands

### Check Service Status
```bash
aws ecs describe-services \
  --cluster ut-api-cluster \
  --services ut-query-service-service ut-vector-store-service
```

### View Service Logs
```bash
# Query service logs
aws logs tail /ecs/ut-query-service --follow

# Vector store logs  
aws logs tail /ecs/ut-vector-store --follow
```

### Update Services
```bash
# Force new deployment with latest images
aws ecs update-service \
  --cluster ut-api-cluster \
  --service ut-query-service-service \
  --force-new-deployment

aws ecs update-service \
  --cluster ut-api-cluster \
  --service ut-vector-store-service \
  --force-new-deployment
```

## 📋 Next Steps

### High Priority
1. **Vector Store Data Loading**: Complete S3 enhanced knowledge graph data loading
2. **Health Check Stability**: Resolve intermittent 500 errors in vector store
3. **Performance Testing**: Validate production load capacity

### Medium Priority
1. **HTTPS Setup**: Configure SSL certificate for production domain
2. **Custom Domain**: Set up production domain instead of ALB DNS name
3. **Monitoring**: CloudWatch dashboards and alerting
4. **Auto-scaling**: Configure ECS service auto-scaling policies

### Low Priority
1. **API Keys**: Implement authentication for production access
2. **Rate Limiting**: Add request throttling for public endpoints
3. **Documentation**: API documentation site with examples

## 🏗️ Repository Structure

**ut-api (this repository)** - Production API services
- `services/query-service/` - Cultural Cartographer with Claude
- `services/vector-store/` - Semantic search backend
- `scripts/deploy.sh` - ECS deployment automation

**ut-microservices** - Content processing pipeline
- Content scraping and processing
- Knowledge graph generation
- S3 data pipeline management

## 🚨 Known Issues

1. **Vector Store Instability**: Service experiencing health check failures during data loading
2. **Data Pipeline**: Enhanced knowledge graph loading process needs optimization
3. **Error Handling**: Some endpoints returning generic 500 errors instead of specific error messages

## 🎯 Success Metrics

- **Query Service Uptime**: 99.9% (currently meeting SLA)
- **Claude Integration**: Fully operational with context-aware responses
- **Response Times**: Query service < 5 seconds average
- **Knowledge Graph**: 2,787+ relationships available in enhanced format