# 快速开始指南

本指南将帮助你快速搭建和运行 Medical AI Platform。

## 前置要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- 或者使用 Docker 和 Docker Compose

## 方式一：使用 Docker Compose（推荐）

### 1. 克隆项目

```bash
cd /Users/zhulang/work/medical_project
```

### 2. 配置环境变量

编辑 `.env` 文件，填入你的 API Keys：

```bash
# 配置你的 AI 模型 API Key
OPENAI_API_KEY=sk-your-openai-key
DASHSCOPE_API_KEY=sk-your-qwen-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
SILICONFLOW_API_KEY=sk-your-siliconflow-key
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 运行数据库迁移

```bash
docker-compose exec api alembic upgrade head
```

### 5. 访问服务

- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 方式二：本地开发环境

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 启动 PostgreSQL 和 Redis

```bash
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=medical_db \
  -e POSTGRES_USER=medical_user \
  -e POSTGRES_PASSWORD=medical_pass \
  -p 5432:5432 \
  postgres:15-alpine

# Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 4. 运行数据库迁移

```bash
# 创建迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 5. 启动应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 使用示例

### 1. 注册用户

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### 2. 登录获取 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

### 3. 配置模型

```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8000/api/v1/models" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "api_key": "sk-your-openai-key",
    "is_default": true,
    "config": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }'
```

### 4. 创建会话

```bash
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "医疗咨询",
    "metadata": {}
  }'
```

响应示例：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "医疗咨询",
  "status": "active",
  ...
}
```

### 5. 发送消息（同步）

```bash
CONV_ID="your_conversation_id"

curl -X POST "http://localhost:8000/api/v1/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好，我想咨询一下健康问题"
  }'
```

### 6. 发送消息（流式）

```bash
curl -X POST "http://localhost:8000/api/v1/conversations/$CONV_ID/messages/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下健康饮食的重要性",
    "model_provider": "openai",
    "model_name": "gpt-3.5-turbo"
  }'
```

### 7. 创建应用模板（可选）

```bash
curl -X POST "http://localhost:8000/api/v1/applications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "医疗问诊助手",
    "description": "专业的医疗问诊AI助手",
    "model_provider": "openai",
    "model_name": "gpt-4",
    "model_config": {
      "temperature": 0.3,
      "max_tokens": 3000
    },
    "system_prompt": "你是一名专业的医疗助手，请谨慎回答问题，并建议用户咨询专业医生。"
  }'
```

## API 文档

访问 http://localhost:8000/docs 查看完整的 API 文档。

## 核心功能

### ✅ 独立会话架构
- 会话管理完全独立，不强制绑定应用
- 支持灵活的模型配置

### ✅ 多平台模型支持
- OpenAI (GPT-3.5, GPT-4)
- 通义千问 (Qwen)
- DeepSeek
- 硅基流动 (SiliconFlow)

### ✅ 三级配置优先级
1. **请求级别**（最高）：发送消息时直接指定模型参数
2. **应用模板级别**（中）：引用应用配置
3. **用户默认级别**（最低）：使用用户的默认模型配置

### ✅ 流式响应
- 支持 SSE (Server-Sent Events) 流式输出
- 实时获取 AI 响应

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      客户端应用                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    FastAPI 应用层                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │  用户    │  │  应用    │  │  会话    │  │  消息   ││
│  │  认证    │  │  管理    │  │  管理    │  │  管理   ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     服务层 (Services)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │          多平台 AI 模型适配层                     │  │
│  │  OpenAI │ Qwen │ DeepSeek │ SiliconFlow         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┐    ┌──────────────────┐
│   PostgreSQL     │    │      Redis       │
│   (主数据库)     │    │   (缓存/队列)    │
└──────────────────┘    └──────────────────┘
```

## 故障排查

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 查看日志
docker logs medical_postgres
```

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 测试连接
redis-cli ping
```

### API 调用失败

```bash
# 查看应用日志
docker logs medical_api

# 或本地运行时查看
tail -f logs/app_*.log
```

## 下一步

- 查看完整的 API 文档
- 阅读 [技术方案文档](DESIGN_DOCUMENT.md)
- 配置更多的模型提供商
- 创建应用模板
- 集成到你的业务系统

## 支持

如有问题，请查看项目文档或提交 Issue。

