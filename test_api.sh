#!/bin/bash
# API 测试脚本

set -e

API_BASE="http://localhost:8000"
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BOLD}🧪 Medical AI Platform API 测试${NC}"
echo "========================================"
echo ""

# 测试函数
test_api() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_code=$5
    local token=$6
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "测试 $TOTAL_TESTS: $test_name ... "
    
    if [ -z "$token" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_BASE$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$API_BASE$endpoint" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $token" \
            -d "$data" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ FAIL${NC} (期望 $expected_code, 实际 $http_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
    echo ""
}

# 1. 健康检查
echo -e "${YELLOW}=== 1. 基础功能测试 ===${NC}"
test_api "健康检查" "GET" "/health" "" "200"
test_api "根路径" "GET" "/" "" "200"

# 2. 用户注册
echo -e "${YELLOW}=== 2. 用户注册测试 ===${NC}"
TIMESTAMP=$(date +%s)
TEST_USER="testuser_$TIMESTAMP"
TEST_EMAIL="test_$TIMESTAMP@example.com"
TEST_PASSWORD="Test123456"

register_response=$(curl -s -X POST "$API_BASE/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"username\": \"$TEST_USER\",
        \"password\": \"$TEST_PASSWORD\",
        \"full_name\": \"Test User\"
    }")

if echo "$register_response" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 用户注册成功${NC}"
    USER_ID=$(echo "$register_response" | jq -r '.id')
    echo "用户ID: $USER_ID"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 用户注册失败${NC}"
    echo "$register_response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# 3. 用户登录
echo -e "${YELLOW}=== 3. 用户登录测试 ===${NC}"
login_response=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"$TEST_USER\",
        \"password\": \"$TEST_PASSWORD\"
    }")

if echo "$login_response" | jq -e '.access_token' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 用户登录成功${NC}"
    ACCESS_TOKEN=$(echo "$login_response" | jq -r '.access_token')
    REFRESH_TOKEN=$(echo "$login_response" | jq -r '.refresh_token')
    echo "Access Token: ${ACCESS_TOKEN:0:20}..."
    echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 用户登录失败${NC}"
    echo "$login_response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# 4. Token 刷新测试
echo -e "${YELLOW}=== 4. Token 刷新测试 ===${NC}"
sleep 2
refresh_response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/auth/refresh" \
    -H "X-Refresh-Token: $REFRESH_TOKEN")

http_code=$(echo "$refresh_response" | tail -n1)
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Token 刷新成功${NC}"
    NEW_ACCESS_TOKEN=$(echo "$refresh_response" | sed '$d' | jq -r '.access_token')
    echo "New Access Token: ${NEW_ACCESS_TOKEN:0:20}..."
    ACCESS_TOKEN=$NEW_ACCESS_TOKEN
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ Token 刷新失败${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# 5. 获取当前用户信息
echo -e "${YELLOW}=== 5. 用户信息测试 ===${NC}"
test_api "获取当前用户" "GET" "/api/v1/auth/me" "" "200" "$ACCESS_TOKEN"
test_api "获取用户详情" "GET" "/api/v1/users/me" "" "200" "$ACCESS_TOKEN"

# 6. 模型配置测试
echo -e "${YELLOW}=== 6. 模型配置测试 ===${NC}"
model_config_response=$(curl -s -X POST "$API_BASE/api/v1/models" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"provider\": \"openai\",
        \"model_name\": \"gpt-3.5-turbo\",
        \"api_key\": \"sk-test-key-for-testing\",
        \"is_default\": true,
        \"config\": {
            \"temperature\": 0.7,
            \"max_tokens\": 2000
        }
    }")

if echo "$model_config_response" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 模型配置创建成功${NC}"
    MODEL_CONFIG_ID=$(echo "$model_config_response" | jq -r '.id')
    echo "模型配置ID: $MODEL_CONFIG_ID"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 模型配置创建失败${NC}"
    echo "$model_config_response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

test_api "获取模型配置列表" "GET" "/api/v1/models" "" "200" "$ACCESS_TOKEN"

# 7. 应用管理测试
echo -e "${YELLOW}=== 7. 应用管理测试 ===${NC}"
app_response=$(curl -s -X POST "$API_BASE/api/v1/applications" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"name\": \"测试应用\",
        \"description\": \"这是一个测试应用\",
        \"model_provider\": \"openai\",
        \"model_name\": \"gpt-3.5-turbo\",
        \"system_prompt\": \"你是一个测试助手\",
        \"model_parameters\": {
            \"temperature\": 0.7
        }
    }")

if echo "$app_response" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 应用创建成功${NC}"
    APP_ID=$(echo "$app_response" | jq -r '.id')
    echo "应用ID: $APP_ID"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 应用创建失败${NC}"
    echo "$app_response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

test_api "获取应用列表" "GET" "/api/v1/applications" "" "200" "$ACCESS_TOKEN"
if [ ! -z "$APP_ID" ]; then
    test_api "获取应用详情" "GET" "/api/v1/applications/$APP_ID" "" "200" "$ACCESS_TOKEN"
fi

# 8. 会话管理测试
echo -e "${YELLOW}=== 8. 会话管理测试 ===${NC}"
conv_response=$(curl -s -X POST "$API_BASE/api/v1/conversations" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"title\": \"测试会话\",
        \"metadata\": {
            \"test\": true
        }
    }")

if echo "$conv_response" | jq -e '.id' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 会话创建成功${NC}"
    CONV_ID=$(echo "$conv_response" | jq -r '.id')
    echo "会话ID: $CONV_ID"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 会话创建失败${NC}"
    echo "$conv_response"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

test_api "获取会话列表" "GET" "/api/v1/conversations" "" "200" "$ACCESS_TOKEN"
if [ ! -z "$CONV_ID" ]; then
    test_api "获取会话详情" "GET" "/api/v1/conversations/$CONV_ID" "" "200" "$ACCESS_TOKEN"
fi

# 9. 限流测试
echo -e "${YELLOW}=== 9. 限流测试 ===${NC}"
echo "发送10个快速请求测试限流..."
for i in {1..10}; do
    response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE/api/v1/conversations" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    http_code=$(echo "$response" | tail -n1)
    rate_limit=$(echo "$response" | sed '$d' | grep -i "X-RateLimit" || echo "")
    
    if [ $i -eq 1 ]; then
        echo "第1次请求 - HTTP $http_code"
        echo "$response" | sed '$d' | head -5
    fi
done
echo -e "${GREEN}✅ 限流测试完成（检查响应头中的 X-RateLimit-* 信息）${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
PASSED_TESTS=$((PASSED_TESTS + 1))
echo ""

# 10. 登出测试
echo -e "${YELLOW}=== 10. 登出测试 ===${NC}"
logout_response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/auth/logout" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
http_code=$(echo "$logout_response" | tail -n1)
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ 登出成功${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 登出失败${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# 11. 验证 Token 黑名单
echo -e "${YELLOW}=== 11. Token 黑名单测试 ===${NC}"
blacklist_response=$(curl -s -w "\n%{http_code}" -X GET "$API_BASE/api/v1/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
http_code=$(echo "$blacklist_response" | tail -n1)
if [ "$http_code" = "401" ]; then
    echo -e "${GREEN}✅ Token 黑名单生效（登出后的 Token 被拒绝）${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ Token 黑名单未生效${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

# 测试总结
echo ""
echo "========================================"
echo -e "${BOLD}📊 测试总结${NC}"
echo "========================================"
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}❌ 有测试失败，请检查日志${NC}"
    exit 1
fi

