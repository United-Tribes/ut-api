#!/bin/bash

# Deployment Script with Automated Regression Testing
# Ensures no functionality is lost during deployments
# Usage: ./deploy-with-tests.sh [service-name]

set -e

SERVICE_NAME=${1:-"query-service"}
API_URL="http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🚀 UT-API Deployment with Regression Testing"
echo "Service: $SERVICE_NAME"
echo "Timestamp: $TIMESTAMP"
echo "=============================================="

# Pre-deployment regression test
echo -e "\n📋 STEP 1: Pre-deployment regression test"
if ./test-regression.sh "$API_URL"; then
    echo "✅ Pre-deployment tests passed"
else
    echo "❌ Pre-deployment tests failed - aborting deployment"
    exit 1
fi

# Build and push new image
echo -e "\n🔨 STEP 2: Building and pushing new image"
cd "services/$SERVICE_NAME"
docker build --platform linux/amd64 -t "ut-$SERVICE_NAME" .
docker tag "ut-$SERVICE_NAME:latest" "805187821622.dkr.ecr.us-east-1.amazonaws.com/ut-$SERVICE_NAME-development:latest"
docker push "805187821622.dkr.ecr.us-east-1.amazonaws.com/ut-$SERVICE_NAME-development:latest"
cd ../..

# Deploy new version
echo -e "\n🚀 STEP 3: Deploying new version"
# Register new task definition
TASK_DEF_FILE="/tmp/$SERVICE_NAME-task-def-new.json"
NEW_REVISION=$(aws ecs register-task-definition --cli-input-json "file://$TASK_DEF_FILE" --query 'taskDefinition.revision' --output text)
echo "Registered task definition revision: $NEW_REVISION"

# Update service
aws ecs update-service --cluster ut-api-cluster --service "ut-$SERVICE_NAME-service" --task-definition "ut-$SERVICE_NAME:$NEW_REVISION"
echo "Service update initiated"

# Wait for deployment
echo -e "\n⏳ STEP 4: Waiting for deployment to complete"
echo "Waiting 3 minutes for service to stabilize..."
sleep 180

# Post-deployment regression test
echo -e "\n🧪 STEP 5: Post-deployment regression test"
RETRY_COUNT=0
MAX_RETRIES=3

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ./test-regression.sh "$API_URL"; then
        echo "✅ Post-deployment tests passed"
        break
    else
        echo "⚠️  Post-deployment tests failed (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        if [ $RETRY_COUNT -eq $((MAX_RETRIES - 1)) ]; then
            echo "❌ Deployment validation failed - consider rollback"
            exit 1
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Retrying in 60 seconds..."
        sleep 60
    fi
done

# Success
echo -e "\n🎉 DEPLOYMENT SUCCESSFUL"
echo "================================"
echo "✅ Service: $SERVICE_NAME"
echo "✅ Revision: $NEW_REVISION" 
echo "✅ All regression tests passed"
echo "✅ Deployment timestamp: $TIMESTAMP"

# Optional: Tag the successful deployment
git tag "deploy-$SERVICE_NAME-$TIMESTAMP" || echo "Note: Git tagging failed (non-critical)"

echo -e "\nDeployment completed successfully! 🚀"