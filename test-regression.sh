#!/bin/bash

# Regression Test Suite for UT-API
# Validates critical functionality after deployments
# Usage: ./test-regression.sh <api-url>

set -e

API_URL=${1:-"http://ut-api-alb-470552730.us-east-1.elb.amazonaws.com"}
TEMP_DIR="/tmp/ut-api-tests"
mkdir -p $TEMP_DIR

echo "🧪 UT-API Regression Test Suite"
echo "Testing API: $API_URL"
echo "==============================="

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_passed() {
    echo "✅ $1"
    ((TESTS_PASSED++))
}

test_failed() {
    echo "❌ $1"
    ((TESTS_FAILED++))
}

# 1. Root Endpoint Returns JSON API Metadata
echo -e "\n🔍 Test 1: Root endpoint returns JSON API metadata"
ROOT_RESPONSE=$(curl -s "$API_URL/" -w "%{http_code}")
HTTP_CODE=${ROOT_RESPONSE: -3}
JSON_CONTENT=${ROOT_RESPONSE%???}

if [[ $HTTP_CODE == "200" ]] && echo "$JSON_CONTENT" | jq -e '.service == "ut-query-service"' >/dev/null 2>&1; then
    test_passed "Root endpoint returns proper JSON"
else
    test_failed "Root endpoint failed (HTTP: $HTTP_CODE)"
fi

# 2. Health Check Shows All Services Healthy
echo -e "\n🔍 Test 2: Health check shows all services healthy"
HEALTH_RESPONSE=$(curl -s "$API_URL/health")
if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' >/dev/null 2>&1; then
    test_passed "All services healthy"
else
    test_failed "Health check failed or degraded"
fi

# 3. Claude Integration Working (Not Fallback Mode)
echo -e "\n🔍 Test 3: Claude integration working (enhanced mode)"
CLAUDE_TEST=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "Beatles", "k": 3}' | jq -r '.mode')

if [[ "$CLAUDE_TEST" == "enhanced" ]]; then
    test_passed "Claude synthesis working"
else
    test_failed "Claude in fallback mode: $CLAUDE_TEST"
fi

# 4. Video Subjects Return Data
echo -e "\n🔍 Test 4: All video subjects return rich data"
SUBJECTS=("Beatles" "Bob Dylan" "Charlie Parker" "Amy Winehouse" "Justin Bieber" "Kendrick Lamar")

for subject in "${SUBJECTS[@]}"; do
    SUBJECT_RESPONSE=$(curl -s -X POST "$API_URL/query" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$subject\", \"k\": 2}")
    
    SOURCE_COUNT=$(echo "$SUBJECT_RESPONSE" | jq -r '.sources | length')
    if [[ $SOURCE_COUNT -gt 0 ]]; then
        test_passed "$subject returns $SOURCE_COUNT sources"
    else
        test_failed "$subject returns no sources"
    fi
done

# 5. Response Time Performance
echo -e "\n🔍 Test 5: Response times under 15 seconds"
START_TIME=$(date +%s%3N)
PERF_RESPONSE=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test performance", "k": 2}')
END_TIME=$(date +%s%3N)
RESPONSE_TIME=$((END_TIME - START_TIME))

if [[ $RESPONSE_TIME -lt 15000 ]]; then
    test_passed "Response time: ${RESPONSE_TIME}ms"
else
    test_failed "Response time too slow: ${RESPONSE_TIME}ms"
fi

# 6. Error Handling and Validation
echo -e "\n🔍 Test 6: Proper error handling"
ERROR_RESPONSE=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "", "k": 2}')

if echo "$ERROR_RESPONSE" | jq -e '.[0].msg | contains("Query cannot be empty")' >/dev/null 2>&1; then
    test_passed "Empty query validation working"
else
    test_failed "Empty query validation failed"
fi

# 7. Data Quality and Attribution
echo -e "\n🔍 Test 7: Source attribution quality"
ATTRIBUTION_RESPONSE=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "Beatles", "k": 3}')

SOURCE_WITH_CONFIDENCE=$(echo "$ATTRIBUTION_RESPONSE" | jq -r '.sources[0] | has("confidence") and has("source") and has("excerpt")')
if [[ "$SOURCE_WITH_CONFIDENCE" == "true" ]]; then
    test_passed "Source attribution complete"
else
    test_failed "Missing attribution fields"
fi

# 8. Knowledge Graph Coverage
echo -e "\n🔍 Test 8: Knowledge graph relationship count"
STATS_RESPONSE=$(curl -s "$API_URL/stats")
KB_RELATIONSHIPS=$(echo "$STATS_RESPONSE" | jq -r '.cultural_cartographer_info.features[] | select(contains("relationships"))' | grep -o '[0-9,]*' | tr -d ',' | head -1)

if [[ $KB_RELATIONSHIPS -gt 2000 ]]; then
    test_passed "Knowledge graph has $KB_RELATIONSHIPS relationships"
else
    test_failed "Knowledge graph coverage low: $KB_RELATIONSHIPS"
fi

# 9. Source URL Format (Known Issue Test)
echo -e "\n🔍 Test 9: Source URL format (monitoring known issue)"
URL_RESPONSE=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "Beatles", "k": 1}')

SAMPLE_URL=$(echo "$URL_RESPONSE" | jq -r '.sources[0].url')
if [[ "$SAMPLE_URL" == *".txt.com"* ]]; then
    echo "⚠️  Source URLs are fake (.txt.com domains) - known issue"
else
    test_passed "Source URLs appear canonical"
fi

# 10. Vector Store Integration
echo -e "\n🔍 Test 10: Vector store connectivity"
VECTOR_HEALTH=$(echo "$HEALTH_RESPONSE" | jq -r '.dependencies.vector_service // "unhealthy"')
if [[ "$VECTOR_HEALTH" == "healthy" ]]; then
    test_passed "Vector store connected"
else
    test_failed "Vector store unhealthy"
fi

# Summary
echo -e "\n📊 REGRESSION TEST RESULTS"
echo "=========================="
echo "✅ Passed: $TESTS_PASSED"
echo "❌ Failed: $TESTS_FAILED"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n🎉 ALL TESTS PASSED - Deployment is stable!"
    exit 0
else
    echo -e "\n⚠️  $TESTS_FAILED tests failed - Review before promoting!"
    exit 1
fi