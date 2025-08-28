#!/bin/bash

# United Tribes API Health Check Script
# Monitors the health of both vector-store and query-service

ENVIRONMENT=${1:-production}
QUERY_INTERVAL=${2:-60}  # seconds

echo "🔍 Starting health monitoring for $ENVIRONMENT environment"
echo "📊 Check interval: ${QUERY_INTERVAL}s"

# Function to check service health
check_service_health() {
    local service_name=$1
    local service_url=$2
    local endpoint=$3
    
    echo -n "Checking $service_name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$service_url$endpoint" --max-time 10)
    
    if [ "$response" = "200" ]; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Unhealthy (HTTP $response)"
        return 1
    fi
}

# Function to get App Runner service URL
get_service_url() {
    local service_name=$1
    
    aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='$service_name'].ServiceUrl" \
        --output text 2>/dev/null
}

# Function to test API functionality
test_api_functionality() {
    local query_service_url=$1
    
    echo "🧪 Testing API functionality..."
    
    # Test basic query
    response=$(curl -s -X POST "https://$query_service_url/query" \
        -H "Content-Type: application/json" \
        -d '{"query": "test", "k": 1}' \
        --max-time 30)
    
    if echo "$response" | jq -e '.response' > /dev/null 2>&1; then
        echo "✅ Query endpoint functional"
        return 0
    else
        echo "❌ Query endpoint not responding correctly"
        echo "Response: $response"
        return 1
    fi
}

# Main health check loop
while true; do
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Health Check"
    echo "============================================"
    
    # Get service URLs
    VECTOR_STORE_URL=$(get_service_url "ut-vector-store-$ENVIRONMENT")
    QUERY_SERVICE_URL=$(get_service_url "ut-query-service-$ENVIRONMENT")
    
    if [ -z "$VECTOR_STORE_URL" ] || [ -z "$QUERY_SERVICE_URL" ]; then
        echo "❌ Could not retrieve service URLs. Check AWS credentials and service deployment."
        sleep $QUERY_INTERVAL
        continue
    fi
    
    echo "📊 Vector Store: https://$VECTOR_STORE_URL"
    echo "💬 Query Service: https://$QUERY_SERVICE_URL"
    echo ""
    
    # Check services
    vector_healthy=false
    query_healthy=false
    
    if check_service_health "Vector Store" "https://$VECTOR_STORE_URL" "/health"; then
        vector_healthy=true
    fi
    
    if check_service_health "Query Service" "https://$QUERY_SERVICE_URL" "/health"; then
        query_healthy=true
    fi
    
    # Test functionality if both services are healthy
    if [ "$vector_healthy" = true ] && [ "$query_healthy" = true ]; then
        test_api_functionality "$QUERY_SERVICE_URL"
        
        echo ""
        echo "🎉 All systems operational!"
        
        # Get some basic stats
        echo ""
        echo "📈 Quick Stats:"
        stats_response=$(curl -s "https://$QUERY_SERVICE_URL/health" --max-time 10)
        if [ $? -eq 0 ]; then
            echo "$stats_response" | jq -r '.dependencies' 2>/dev/null || echo "Stats unavailable"
        fi
        
    else
        echo ""
        echo "⚠️  System degraded - some services unhealthy"
        
        # Send alert (you can integrate with your monitoring system here)
        echo "🚨 Alert: United Tribes API ($ENVIRONMENT) has unhealthy services"
    fi
    
    # Sleep until next check
    echo ""
    echo "⏰ Next check in ${QUERY_INTERVAL}s..."
    sleep $QUERY_INTERVAL
done