# Medical AI Platform

类似 Dify 的 AI 应用管理和会话管理平台，支持多应用管理、多轮对话、提示词模板、模型配置等核心功能。

## 核心特性

- ✅ **独立会话架构**: 会话管理完全独立，不强制绑定应用
- ✅ **多平台模型支持**: OpenAI、通义千问、DeepSeek、硅基流动
- ✅ **灵活配置**: 三级配置优先级（请求级 > 应用级 > 用户默认级）
- ✅ **流式响应**: 支持 SSE 流式输出
- ✅ **知识库集成**: 基于 Milvus 的 RAG 检索增强（可选）

## 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **缓存**: Redis
- **向量数据库**: Milvus (可选)
- **AI SDK**: OpenAI、DashScope、多平台兼容

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 初始化数据库

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

## Docker 部署

```bash
docker-compose up -d
```

## 项目结构

```
medical_project/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 核心配置
│   ├── models/              # 数据库模型
│   ├── schemas/             # Pydantic 模型
│   ├── api/                 # API 路由
│   ├── services/            # 业务逻辑层
│   ├── utils/               # 工具函数
│   └── middleware/          # 中间件
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── requirements.txt         # 依赖包
└── docker-compose.yml       # Docker 配置
```

## API 文档

详见技术方案文档 `DESIGN_DOCUMENT.md`

## License

MIT

