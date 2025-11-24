# 类似 Dify 的应用管理和会话管理系统 - 技术方案

## 一、项目概述

本项目旨在构建一个类似 Dify 的 AI 应用管理和会话管理平台，支持多应用管理、多轮对话、提示词模板、模型配置等核心功能。

### 🔑 核心设计理念

**独立会话架构**: 本系统采用解耦设计，会话管理完全独立，不强制绑定应用或模型配置。

- ✅ **会话独立**: 会话是通用的对话容器，可在任何场景使用
- ✅ **灵活配置**: 每次对话可动态选择模型和参数
- ✅ **可选模板**: 应用作为配置模板存在，提供便捷性但不强制使用
- ✅ **三级配置**: 请求级 > 应用级（可选）> 用户默认级

这种设计使系统更加灵活，易于集成到各种业务场景中。

### 1.1 核心功能模块

1. **用户管理模块**
   - 用户注册、登录、认证
   - JWT Token 认证机制
   - 用户权限管理

2. **应用管理模块**
   - 应用创建、编辑、删除
   - 应用配置（模型选择、参数设置）
   - 提示词模板管理
   - 应用发布/草稿状态管理
   - **注意**: 应用是可选的配置模板，不强制与会话绑定

3. **会话管理模块（独立）**
   - 通用的多轮对话管理，不依赖应用
   - 会话历史记录
   - 上下文维护
   - 会话列表查询
   - 支持灵活指定模型和参数

4. **消息管理模块**
   - 消息发送与接收
   - 流式响应支持（SSE）
   - 消息历史查询
   - 消息评价反馈

5. **模型管理模块**
   - 多模型支持（OpenAI、Claude、本地模型等）
   - 模型参数配置
   - API Key 管理

6. **知识库模块（可选扩展）**
   - 文档上传与管理
   - 向量化存储
   - RAG 检索增强

## 二、技术架构

### 2.1 技术栈

#### 后端技术
- **Web 框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+ (主数据库)
- **缓存**: Redis 7+ (会话缓存、Token 缓存)
- **向量数据库**: Milvus (知识库功能)
- **ORM**: SQLAlchemy 2.0+ with Alembic (数据库迁移)
- **认证**: python-jose (JWT), passlib (密码加密)
- **异步任务**: Celery + Redis
- **AI SDK**: 
  - OpenAI SDK (OpenAI 模型)
  - DashScope SDK (通义千问)
  - OpenAI-Compatible API (DeepSeek、硅基流动)
  - 统一适配层封装

#### 开发工具
- **API 文档**: Swagger/OpenAPI (FastAPI 自动生成)
- **代码质量**: Black, Flake8, Pylint
- **测试**: Pytest, pytest-asyncio
- **容器化**: Docker, Docker Compose

### 2.2 项目结构

```
medical_project/
├── alembic/                    # 数据库迁移
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── core/                   # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py          # 配置管理
│   │   ├── security.py        # 安全相关（JWT、密码）
│   │   ├── database.py        # 数据库连接
│   │   ├── redis_client.py    # Redis 连接
│   │   └── milvus_client.py   # Milvus 连接
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── application.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── model_config.py
│   ├── schemas/                # Pydantic 模型（请求/响应）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── application.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── common.py
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py            # 依赖项（认证、数据库会话）
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── applications.py
│   │       ├── conversations.py
│   │       ├── messages.py
│   │       └── models.py
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── app_service.py
│   │   ├── conversation_service.py
│   │   ├── message_service.py
│   │   ├── ai_service.py      # AI 模型调用（多平台适配）
│   │   ├── embedding_service.py  # Embedding 服务
│   │   └── vector_service.py  # 向量存储与检索（Milvus）
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── exceptions.py
│   └── middleware/             # 中间件
│       ├── __init__.py
│       └── error_handler.py
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_applications.py
│   └── test_conversations.py
├── scripts/                    # 脚本
│   └── init_db.py
├── .env.example                # 环境变量示例
├── .gitignore
├── requirements.txt            # 依赖包
├── Dockerfile
├── docker-compose.yml
├── alembic.ini                 # Alembic 配置
└── README.md
```

## 三、数据库设计

### 3.1 核心表结构

#### users (用户表)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### applications (应用表)
```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    icon VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',  -- draft, published
    app_type VARCHAR(50) DEFAULT 'chatbot',  -- chatbot, completion, agent
    
    -- 模型配置
    model_provider VARCHAR(50) DEFAULT 'openai',  -- openai, qwen, deepseek, siliconflow
    model_name VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    model_config JSONB DEFAULT '{}',  -- temperature, max_tokens, etc.
    
    -- 提示词配置
    system_prompt TEXT,
    user_prompt_template TEXT,
    opening_statement TEXT,  -- 开场白
    
    -- 其他配置
    max_conversation_length INTEGER DEFAULT 10,
    enable_context BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

#### conversations (会话表)
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',  -- active, archived, deleted
    summary TEXT,
    
    -- 会话元数据（可存储关联的应用ID等扩展信息）
    metadata JSONB DEFAULT '{}',
    message_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_last_message (last_message_at DESC)
);
```

**说明**: 
- 移除了 `application_id` 外键约束，会话不再强制关联应用
- 会话是独立的对话容器，可以在任何场景使用
- 如需关联应用，可通过 `metadata` 字段灵活存储（可选）
- 这样设计使会话管理更加通用和灵活

#### messages (消息表)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- 消息内容
    role VARCHAR(50) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    
    -- 模型信息（每条消息可使用不同模型）
    model_provider VARCHAR(50),  -- openai, qwen, deepseek, siliconflow
    model_name VARCHAR(100),     -- gpt-4, qwen-max, deepseek-chat, etc.
    model_config JSONB DEFAULT '{}',  -- 本次使用的模型参数
    
    -- Token 统计
    token_count INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    
    -- 反馈
    feedback VARCHAR(50),  -- like, dislike, null
    feedback_comment TEXT,
    
    -- 时间
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_role (role)
);
```

**说明**:
- 每条消息记录使用的模型信息，支持同一会话使用不同模型
- `model_config` 存储本次消息使用的具体参数（temperature、max_tokens 等）
- 便于后续分析不同模型的效果和成本

#### model_configs (模型配置表)
```sql
CREATE TABLE model_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- openai, qwen, deepseek, siliconflow
    model_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,  -- 加密存储
    api_base VARCHAR(255),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, provider, model_name),
    INDEX idx_user_id (user_id),
    INDEX idx_provider (provider)
);
```

**支持的模型提供商**:
- `openai`: OpenAI 官方（gpt-4, gpt-3.5-turbo 等）
- `qwen`: 阿里云通义千问（qwen-turbo, qwen-plus, qwen-max 等）
- `deepseek`: DeepSeek（deepseek-chat, deepseek-coder 等）
- `siliconflow`: 硅基流动（支持多种开源模型）

### 3.2 Redis 缓存设计

```python
# 会话缓存（保存最近的消息上下文）
conversation:{conversation_id}:messages  # List, 保存最近 N 条消息
conversation:{conversation_id}:context   # String, JSON 格式的上下文
conversation:{conversation_id}:model     # Hash, 当前会话最近使用的模型信息

# Token 缓存
user:{user_id}:token                     # String, JWT Token
token_blacklist:{token_jti}              # String, 已废弃的 Token

# 用户配置缓存
user:{user_id}:default_model             # Hash, 用户默认模型配置
application:{app_id}:config              # Hash, 应用配置缓存（可选）

# 限流
rate_limit:{user_id}:{endpoint}          # String, 请求计数

# 会话锁（防止并发）
conversation:{conversation_id}:lock      # String, 分布式锁
```

## 四、API 设计

### 4.1 认证相关 API

```
POST   /api/v1/auth/register          # 用户注册
POST   /api/v1/auth/login             # 用户登录
POST   /api/v1/auth/refresh           # 刷新 Token
POST   /api/v1/auth/logout            # 退出登录
GET    /api/v1/auth/me                # 获取当前用户信息
```

### 4.2 应用管理 API（可选配置模板）

```
POST   /api/v1/applications                  # 创建应用配置模板
GET    /api/v1/applications                  # 获取应用列表
GET    /api/v1/applications/{id}             # 获取应用详情
GET    /api/v1/applications/{id}/config      # 获取应用的模型配置
PUT    /api/v1/applications/{id}             # 更新应用
DELETE /api/v1/applications/{id}             # 删除应用
POST   /api/v1/applications/{id}/publish     # 发布应用
```

**说明**:
- 应用是可复用的配置模板（提示词、模型参数等）
- 不强制要求创建应用，会话可独立使用
- 应用配置可在消息发送时作为模板引用

### 4.3 会话管理 API

```
POST   /api/v1/conversations                      # 创建会话（独立，无需关联应用）
GET    /api/v1/conversations                      # 获取会话列表
GET    /api/v1/conversations/{id}                 # 获取会话详情
PUT    /api/v1/conversations/{id}                 # 更新会话（标题、状态等）
DELETE /api/v1/conversations/{id}                 # 删除会话
GET    /api/v1/conversations/{id}/messages        # 获取会话消息列表
POST   /api/v1/conversations/{id}/messages        # 发送消息到会话
POST   /api/v1/conversations/{id}/messages/stream # 发送消息（流式响应）
```

**说明**:
- 会话创建时只需提供基本信息（标题、元数据等），不需要关联应用
- 消息发送时可在请求体中指定使用的模型和参数（临时配置）
- 也可以使用用户默认的模型配置
- 会话管理完全独立，可灵活应用于各种场景

### 4.4 消息管理 API

```
GET    /api/v1/messages/{id}                      # 获取单条消息详情
PUT    /api/v1/messages/{id}/feedback             # 消息反馈（点赞/点踩）
DELETE /api/v1/messages/{id}                      # 删除消息
```

**消息发送请求示例**:
```json
POST /api/v1/conversations/{id}/messages
{
  "content": "用户消息内容",
  "model_provider": "openai",          // 可选，指定模型提供商
  "model_name": "gpt-4",               // 可选，指定模型
  "model_config": {                     // 可选，临时模型参数
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "你是一个医疗助手..."
  }
}
```

**说明**:
- 如不指定模型参数，使用用户的默认模型配置
- 支持每次对话临时指定不同的模型和参数
- 会话不绑定特定模型，灵活性更高

### 4.5 模型配置 API

```
POST   /api/v1/models                 # 添加模型配置
GET    /api/v1/models                 # 获取模型配置列表
PUT    /api/v1/models/{id}            # 更新模型配置
DELETE /api/v1/models/{id}            # 删除模型配置
```

## 五、应用与会话的关系设计

### 5.1 独立会话架构

本系统采用**解耦设计**，会话管理完全独立，不强制依赖应用：

1. **独立会话模式**（推荐）
   - 会话创建时无需关联应用
   - 每次发送消息时可灵活指定模型参数
   - 适用于自由对话、临时咨询等场景

2. **应用模板模式**（可选）
   - 应用作为可复用的配置模板存在
   - 用户可创建"医疗问诊助手"、"健康咨询"等应用模板
   - 发送消息时可引用应用配置（通过 metadata 或请求参数）
   - 客户端层面实现应用与会话的关联

3. **灵活组合**
   ```json
   // 场景1: 完全独立的会话
   POST /api/v1/conversations
   {
     "title": "今日咨询",
     "metadata": {}
   }
   
   // 场景2: 会话可选关联应用配置（客户端逻辑）
   POST /api/v1/conversations
   {
     "title": "医疗问诊",
     "metadata": {
       "application_id": "xxx",  // 可选，客户端记录
       "source": "medical_app"
     }
   }
   
   // 发送消息时引用应用配置
   POST /api/v1/conversations/{id}/messages
   {
     "content": "我头疼",
     "use_application_config": "application_id_xxx"  // 可选
   }
   ```

### 5.2 设计优势

- ✅ **高度解耦**: 会话不依赖应用，可以在任何场景使用
- ✅ **灵活配置**: 支持每次对话使用不同的模型参数
- ✅ **可选模板**: 应用作为配置模板，提供便捷性但不强制
- ✅ **易于扩展**: 未来可轻松集成到其他系统中

### 5.3 典型使用场景示例

#### 场景1: 完全独立的临时会话
```bash
# 1. 创建会话（无需关联任何应用）
POST /api/v1/conversations
{
  "title": "临时咨询"
}
# 返回: { "id": "conv_123", ... }

# 2. 发送消息（直接指定模型）
POST /api/v1/conversations/conv_123/messages
{
  "content": "请帮我分析一下这个症状",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "model_config": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

#### 场景2: 使用用户默认配置
```bash
# 1. 用户预先设置默认模型
POST /api/v1/models
{
  "provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "api_key": "sk-xxx",
  "is_default": true,
  "config": {
    "temperature": 0.8
  }
}

# 2. 创建会话并发送消息（不指定模型，自动使用默认）
POST /api/v1/conversations
{ "title": "日常咨询" }

POST /api/v1/conversations/conv_456/messages
{
  "content": "你好"
  // 自动使用用户的默认模型配置
}
```

#### 场景3: 引用应用模板配置（可选）
```bash
# 1. 创建应用模板（可复用的配置）
POST /api/v1/applications
{
  "name": "医疗问诊助手",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "model_config": {
    "temperature": 0.3,
    "max_tokens": 3000
  },
  "system_prompt": "你是一名专业的医疗助手，请谨慎回答问题..."
}
# 返回: { "id": "app_789", ... }

# 2. 创建会话（可选在 metadata 中记录）
POST /api/v1/conversations
{
  "title": "医疗问诊",
  "metadata": {
    "application_id": "app_789",  // 客户端记录，方便管理
    "scene": "medical"
  }
}

# 3. 发送消息时引用应用配置
POST /api/v1/conversations/conv_789/messages
{
  "content": "我最近头痛",
  "use_application_config": "app_789"  // 引用应用的模型配置
}
```

#### 场景4: 同一会话使用多个模型
```bash
# 创建会话
POST /api/v1/conversations
{ "title": "模型对比测试" }

# 第一条消息使用 GPT-4
POST /api/v1/conversations/conv_999/messages
{
  "content": "请分析这个问题",
  "model_name": "gpt-4"
}

# 第二条消息使用 Claude
POST /api/v1/conversations/conv_999/messages
{
  "content": "同样的问题",
  "model_provider": "anthropic",
  "model_name": "claude-3-opus"
}

# 每条消息都会记录使用的模型信息
```

## 六、多平台模型适配方案

### 6.1 支持的模型平台

#### 1. OpenAI
- **API 地址**: `https://api.openai.com/v1`
- **认证方式**: Bearer Token (API Key)
- **支持模型**: gpt-4, gpt-4-turbo, gpt-3.5-turbo 等
- **SDK**: `openai` Python 官方库

#### 2. 通义千问（阿里云 DashScope）
- **API 地址**: `https://dashscope.aliyuncs.com/api/v1`
- **认证方式**: API Key (X-DashScope-API-Key)
- **支持模型**: qwen-turbo, qwen-plus, qwen-max, qwen-vl-plus 等
- **SDK**: `dashscope` Python 官方库

#### 3. DeepSeek
- **API 地址**: `https://api.deepseek.com/v1`
- **认证方式**: Bearer Token (API Key)
- **支持模型**: deepseek-chat, deepseek-coder 等
- **SDK**: OpenAI-Compatible API（使用 `openai` 库）

#### 4. 硅基流动（SiliconFlow）
- **API 地址**: `https://api.siliconflow.cn/v1`
- **认证方式**: Bearer Token (API Key)
- **支持模型**: Qwen系列、DeepSeek系列、ChatGLM系列等开源模型
- **SDK**: OpenAI-Compatible API（使用 `openai` 库）

### 6.2 统一适配层设计

```python
# app/services/ai_service.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any
import openai
from dashscope import Generation
import dashscope

class BaseModelProvider(ABC):
    """模型提供商基类"""
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: list, 
        model: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """同步聊天完成"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self, 
        messages: list, 
        model: str, 
        **kwargs
    ) -> AsyncIterator[str]:
        """流式聊天完成"""
        pass


class OpenAIProvider(BaseModelProvider):
    """OpenAI 模型提供商"""
    
    def __init__(self, api_key: str, api_base: str = None):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=api_base or "https://api.openai.com/v1"
        )
    
    async def chat_completion(self, messages: list, model: str, **kwargs):
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class QwenProvider(BaseModelProvider):
    """通义千问模型提供商"""
    
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
    
    async def chat_completion(self, messages: list, model: str, **kwargs):
        response = Generation.call(
            model=model,
            messages=messages,
            result_format='message',
            **kwargs
        )
        return {
            "content": response.output.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        responses = Generation.call(
            model=model,
            messages=messages,
            result_format='message',
            stream=True,
            **kwargs
        )
        for response in responses:
            if response.output.choices[0].message.content:
                yield response.output.choices[0].message.content


class DeepSeekProvider(BaseModelProvider):
    """DeepSeek 模型提供商（OpenAI 兼容）"""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
    
    async def chat_completion(self, messages: list, model: str, **kwargs):
        # 与 OpenAI 实现相同
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class SiliconFlowProvider(BaseModelProvider):
    """硅基流动模型提供商（OpenAI 兼容）"""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
    
    async def chat_completion(self, messages: list, model: str, **kwargs):
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def chat_completion_stream(self, messages: list, model: str, **kwargs):
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AIModelService:
    """AI 模型服务统一入口"""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "qwen": QwenProvider,
        "deepseek": DeepSeekProvider,
        "siliconflow": SiliconFlowProvider,
    }
    
    @classmethod
    def get_provider(cls, provider: str, api_key: str, api_base: str = None) -> BaseModelProvider:
        """获取模型提供商实例"""
        provider_class = cls.PROVIDERS.get(provider)
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider}")
        
        if provider == "openai" and api_base:
            return provider_class(api_key, api_base)
        return provider_class(api_key)
    
    @classmethod
    async def chat(
        cls, 
        provider: str,
        api_key: str,
        model: str,
        messages: list,
        stream: bool = False,
        **kwargs
    ):
        """统一的聊天接口"""
        provider_instance = cls.get_provider(provider, api_key)
        
        if stream:
            return provider_instance.chat_completion_stream(messages, model, **kwargs)
        else:
            return await provider_instance.chat_completion(messages, model, **kwargs)
```

### 6.3 各平台配置示例

```python
# OpenAI 配置
{
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "sk-xxx",
    "config": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0
    }
}

# 通义千问配置
{
    "provider": "qwen",
    "model_name": "qwen-max",
    "api_key": "sk-xxx",
    "config": {
        "temperature": 0.8,
        "top_p": 0.8,
        "repetition_penalty": 1.1
    }
}

# DeepSeek 配置
{
    "provider": "deepseek",
    "model_name": "deepseek-chat",
    "api_key": "sk-xxx",
    "config": {
        "temperature": 0.7,
        "max_tokens": 4000
    }
}

# 硅基流动配置
{
    "provider": "siliconflow",
    "model_name": "Qwen/Qwen2-7B-Instruct",
    "api_key": "sk-xxx",
    "config": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9
    }
}
```

## 七、核心功能实现

### 7.1 会话上下文管理

```python
# 策略：
1. 使用 Redis 缓存最近的 N 条消息（如 20 条）
2. 超过限制时，自动摘要或裁剪旧消息
3. 支持滑动窗口和摘要策略
4. Token 计数控制，避免超出模型限制
```

### 7.2 流式响应（SSE）

```python
# 使用 FastAPI 的 StreamingResponse
# 支持实时流式输出 AI 响应
# 客户端使用 EventSource 接收
```

### 7.3 并发控制

```python
# 使用 Redis 分布式锁
# 同一会话同时只能有一个消息在处理
# 防止上下文混乱
```

### 7.4 动态模型选择与配置优先级

```python
# 模型配置三级优先级机制
# 1. 请求级别（最高优先级）- 发送消息时指定
# 2. 应用模板级别（中优先级）- 引用应用配置（可选）
# 3. 用户默认级别（最低优先级）- 用户的默认模型配置

# 示例实现逻辑
def get_model_config(request_config, app_config_id, user_id):
    # 优先使用请求中直接指定的配置
    if request_config:
        return request_config
    
    # 其次使用应用模板配置（如果指定）
    if app_config_id:
        app_config = get_application_config(app_config_id)
        if app_config:
            return app_config.model_config
    
    # 最后使用用户默认配置
    return get_user_default_model_config(user_id)

# 支持运行时切换模型而不影响会话
# 同一会话内可使用多个不同的模型
```

### 7.5 错误处理与重试

```python
# AI 调用失败自动重试（指数退避）
# 全局异常处理中间件
# 详细的错误日志记录
```

## 八、安全设计

### 8.1 认证授权
- JWT Token 认证，有效期 7 天
- Refresh Token 机制
- Token 黑名单（用户登出时）

### 8.2 数据安全
- API Key 加密存储（支持多平台密钥管理）
- 密码使用 bcrypt 加密
- HTTPS 强制（生产环境）
- SQL 注入防护（使用 ORM）

### 8.3 访问控制
- 基于用户 ID 的资源隔离
- 会话和消息的所有权验证
- 应用配置的所有权验证
- 模型配置的所有权验证
- API 限流（每用户每分钟限制请求数）

## 九、性能优化

### 9.1 数据库优化
- 合理的索引设计
- 连接池配置（10-20 连接）
- 查询优化（避免 N+1 问题）
- 分页查询（默认 20 条/页）

### 9.2 缓存策略
- 热点数据 Redis 缓存
- 会话上下文缓存
- 应用配置缓存（1 小时）
- 用户模型配置缓存
- 向量检索结果缓存（Milvus）

### 9.3 异步处理
- 使用 FastAPI 的异步特性
- 数据库异步驱动（asyncpg）
- 长时间任务使用 Celery 异步
- 向量化任务异步处理

## 十、部署方案

### 10.1 开发环境
```bash
# 使用 Docker Compose 一键启动
docker-compose up -d
```

### 10.2 生产环境
```
- Nginx 反向代理
- Gunicorn + Uvicorn workers
- PostgreSQL 主从复制
- Redis 主从 + 哨兵
- Milvus 集群部署
- Docker + Kubernetes（可选）
```

## 十一、开发计划

### Phase 1: 基础架构（1-2 周）
- [x] 项目初始化
- [ ] 数据库设计与迁移
- [ ] 用户认证系统
- [ ] 基础 API 框架

### Phase 2: 核心功能（2-3 周）
- [ ] 独立会话管理模块
- [ ] 消息处理与 AI 集成
- [ ] 流式响应支持
- [ ] 动态模型选择机制

### Phase 3: 完善功能（1-2 周）
- [ ] 应用配置模板（可选）
- [ ] 模型配置管理
- [ ] 会话上下文优化
- [ ] 错误处理与重试
- [ ] API 文档完善

### Phase 4: 优化与测试（1 周）
- [ ] 性能优化
- [ ] 单元测试与集成测试
- [ ] 安全加固
- [ ] 部署文档

## 十二、技术难点与解决方案

### 12.1 上下文管理
**难点**: 长对话的上下文维护，Token 限制
**方案**: 
- 实现智能摘要算法
- 滑动窗口 + 重要信息提取
- 支持手动固定重要消息

### 12.2 并发处理
**难点**: 同一会话的并发消息处理
**方案**:
- Redis 分布式锁
- 消息队列排队处理
- WebSocket 连接状态管理

### 12.3 流式响应
**难点**: SSE 连接管理，错误处理
**方案**:
- 心跳机制
- 连接超时处理
- 断线重连支持

### 12.4 多平台模型统一适配
**难点**: 四个平台 API 不完全兼容
**方案**:
- 统一的 Provider 抽象基类
- 适配器模式封装不同平台差异
- OpenAI-Compatible 协议优先（DeepSeek、硅基流动）
- 通义千问使用官方 SDK（DashScope）
- 统一的响应格式和错误处理

### 12.5 独立会话的模型配置
**难点**: 会话不绑定应用，如何管理模型配置
**方案**:
- 请求级别指定模型参数（最高优先级）
- 用户级别默认模型配置
- 可选引用应用模板配置
- 三级配置优先级机制

### 12.6 多平台 API Key 管理
**难点**: 用户可能配置多个平台的密钥
**方案**:
- 支持每个平台配置多个模型
- API Key 加密存储
- 支持设置默认模型
- 请求时自动选择对应平台的 API Key

## 十三、扩展功能（可选）

1. **知识库集成（基于 Milvus）**
   - 文档上传与解析（PDF、Word、TXT、Markdown）
   - 文本分块与向量化（使用 Embedding 模型）
   - Milvus 向量存储与检索
   - RAG（检索增强生成）集成
   - 相似度搜索与重排序

2. **插件系统**
   - 自定义工具调用
   - Function Calling
   - Agent 模式

3. **多租户支持**
   - 团队/组织管理
   - 权限分级
   - 资源配额

4. **监控与分析**
   - Token 使用统计
   - 对话质量分析
   - 用户行为分析

---

## 附录

### A. 依赖包列表（requirements.txt）
```
# Web 框架
fastapi==0.104.1
uvicorn[standard]==0.24.0

# 数据库
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1

# 数据验证
pydantic==2.5.0
pydantic-settings==2.1.0

# 认证安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 缓存与异步任务
redis==5.0.1
celery==5.3.4

# AI 模型 SDK
openai==1.3.0                    # OpenAI、DeepSeek、硅基流动
dashscope==1.14.0                # 阿里云通义千问
httpx==0.25.2

# 向量数据库
pymilvus==2.3.4                  # Milvus Python SDK

# 文本处理与 Embedding
langchain==0.1.0
langchain-community==0.0.10
sentence-transformers==2.2.2     # 本地 Embedding 模型

# 文档解析
pypdf==3.17.0
python-docx==1.1.0
python-pptx==0.6.23
markdown==3.5.1

# 工具
python-dotenv==1.0.0
loguru==0.7.2
tenacity==8.2.3                  # 重试机制
cryptography==41.0.7             # API Key 加密
```

### B. 环境变量配置（.env.example）
```env
# 应用配置
APP_NAME=Medical AI Platform
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-for-api-keys

# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/medical_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Milvus 向量数据库
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AI 模型平台配置（默认配置，用户可在系统中覆盖）
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1

# 通义千问（阿里云 DashScope）
DASHSCOPE_API_KEY=sk-xxx

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# 硅基流动
SILICONFLOW_API_KEY=sk-xxx
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1

# Embedding 模型配置
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5  # 本地模型
# EMBEDDING_PROVIDER=openai              # 或使用 OpenAI 的 Embedding

# 其他
CORS_ORIGINS=["http://localhost:3000"]
MAX_UPLOAD_SIZE=10485760  # 10MB
RATE_LIMIT_PER_MINUTE=60
```

### C. Docker Compose 配置示例

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: medical_postgres
    environment:
      POSTGRES_DB: medical_db
      POSTGRES_USER: medical_user
      POSTGRES_PASSWORD: medical_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: medical_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  # Milvus Etcd (Milvus 依赖)
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    container_name: milvus_etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  # Milvus MinIO (对象存储)
  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: milvus_minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"

  # Milvus Standalone
  milvus:
    image: milvusdb/milvus:v2.3.3
    container_name: medical_milvus
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    restart: unless-stopped

  # FastAPI 应用
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: medical_api
    environment:
      - DATABASE_URL=postgresql+asyncpg://medical_user:medical_pass@postgres:5432/medical_db
      - REDIS_URL=redis://redis:6379/0
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
    volumes:
      - ./app:/app/app
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - milvus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  etcd_data:
  minio_data:
  milvus_data:
```

### D. 支持的模型列表参考

#### OpenAI
- gpt-4-turbo
- gpt-4
- gpt-3.5-turbo
- gpt-3.5-turbo-16k

#### 通义千问（阿里云）
- qwen-max (最强)
- qwen-plus (增强)
- qwen-turbo (标准)
- qwen-vl-plus (视觉)
- qwen-long (长文本)

#### DeepSeek
- deepseek-chat (对话)
- deepseek-coder (代码)

#### 硅基流动（部分开源模型）
- Qwen/Qwen2-7B-Instruct
- Qwen/Qwen2-72B-Instruct
- THUDM/chatglm3-6b
- deepseek-ai/DeepSeek-V2-Chat
- meta-llama/Meta-Llama-3-8B-Instruct

---

**注意**: 此方案为初步设计，具体实现时可根据实际需求调整。

