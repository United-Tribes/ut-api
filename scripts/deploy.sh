#!/bin/bash

# United Tribes API Deployment Script
# Deploys both vector-store and query-service to AWS App Runner

set -e

ENVIRONMENT=${1:-development}
REGION=${AWS_REGION:-us-east-1}

echo "🚀 Deploying United Tribes API to $ENVIRONMENT environment"
echo "📍 Region: $REGION"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Build and push Docker images
echo "🔨 Building Docker images..."

# Get AWS account ID for ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Create ECR repositories if they don't exist
echo "📦 Creating ECR repositories..."
aws ecr describe-repositories --repository-names ut-vector-store-$ENVIRONMENT &> /dev/null || \
  aws ecr create-repository --repository-name ut-vector-store-$ENVIRONMENT --region $REGION

aws ecr describe-repositories --repository-names ut-query-service-$ENVIRONMENT &> /dev/null || \
  aws ecr create-repository --repository-name ut-query-service-$ENVIRONMENT --region $REGION

# Build and push vector store
echo "🔍 Building and pushing vector store..."
docker build -t ut-vector-store-$ENVIRONMENT ./services/vector-store/
docker tag ut-vector-store-$ENVIRONMENT:latest $ECR_REGISTRY/ut-vector-store-$ENVIRONMENT:latest
docker push $ECR_REGISTRY/ut-vector-store-$ENVIRONMENT:latest

# Build and push query service  
echo "💬 Building and pushing query service..."
docker build -t ut-query-service-$ENVIRONMENT ./services/query-service/
docker tag ut-query-service-$ENVIRONMENT:latest $ECR_REGISTRY/ut-query-service-$ENVIRONMENT:latest
docker push $ECR_REGISTRY/ut-query-service-$ENVIRONMENT:latest

echo "✅ Docker images pushed successfully"

# Deploy with App Runner
echo "🚀 Deploying to AWS App Runner..."

# Deploy vector store first (query service depends on it)
echo "📊 Deploying Vector Store..."
VECTOR_STORE_SERVICE_ARN=$(aws apprunner create-service \
  --service-name "ut-vector-store-$ENVIRONMENT" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR_REGISTRY'/ut-vector-store-'$ENVIRONMENT':latest",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "AWS_REGION": "'$REGION'",
          "UT_PROCESSED_BUCKET": "ut-processed-content",
          "USE_MOCK": "false",
          "SERVICE_NAME": "ut-vector-store-'$ENVIRONMENT'"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }' \
  --query 'Service.ServiceArn' --output text)

echo "📊 Vector Store deployed: $VECTOR_STORE_SERVICE_ARN"

# Wait for vector store to be ready
echo "⏳ Waiting for vector store to be running..."
aws apprunner wait service-operation-succeeded --service-arn "$VECTOR_STORE_SERVICE_ARN"

# Get vector store URL
VECTOR_STORE_URL=$(aws apprunner describe-service --service-arn "$VECTOR_STORE_SERVICE_ARN" --query 'Service.ServiceUrl' --output text)
echo "✅ Vector Store URL: https://$VECTOR_STORE_URL"

# Deploy query service
echo "💬 Deploying Query Service..."
QUERY_SERVICE_ARN=$(aws apprunner create-service \
  --service-name "ut-query-service-$ENVIRONMENT" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR_REGISTRY'/ut-query-service-'$ENVIRONMENT':latest",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "VECTOR_STORE_URL": "https://'$VECTOR_STORE_URL'",
          "SERVICE_NAME": "ut-query-service-'$ENVIRONMENT'"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU", 
    "Memory": "2 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }' \
  --query 'Service.ServiceArn' --output text)

echo "💬 Query Service deployed: $QUERY_SERVICE_ARN"

# Wait for query service to be ready
echo "⏳ Waiting for query service to be running..."
aws apprunner wait service-operation-succeeded --service-arn "$QUERY_SERVICE_ARN"

# Get query service URL
QUERY_SERVICE_URL=$(aws apprunner describe-service --service-arn "$QUERY_SERVICE_ARN" --query 'Service.ServiceUrl' --output text)

echo ""
echo "🎉 Deployment Complete!"
echo "=================="
echo "Vector Store: https://$VECTOR_STORE_URL"
echo "Query Service (API): https://$QUERY_SERVICE_URL"
echo ""
echo "Test your deployment:"
echo "curl https://$QUERY_SERVICE_URL/health"
echo ""
echo "Query the Cultural Cartographer:"
echo 'curl -X POST "https://'$QUERY_SERVICE_URL'/query" \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '"'"'{"query": "jazz influences on hip hop", "k": 3}'"'"''