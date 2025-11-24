#!/bin/bash
# 快速启动脚本

echo "🚀 Medical AI Platform 启动脚本"
echo "================================"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 未找到 .env 文件"
    echo "📝 正在创建 .env 文件..."
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
APP_NAME=Medical AI Platform
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production-32chars
ENCRYPTION_KEY=your-encryption-key-32-chars!!

DATABASE_URL=postgresql+asyncpg://medical_user:medical_pass@localhost:5432/medical_db
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

OPENAI_API_KEY=
DASHSCOPE_API_KEY=
DEEPSEEK_API_KEY=
SILICONFLOW_API_KEY=

CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
EOF
    echo "✅ .env 文件已创建"
    echo "⚠️  请编辑 .env 文件，填入你的 API Keys"
    echo ""
fi

# 选择启动方式
echo "请选择启动方式:"
echo "1) Docker Compose（推荐）"
echo "2) 本地开发模式"
echo "3) 仅启动数据库服务"
echo ""
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🐳 使用 Docker Compose 启动..."
        echo ""
        
        # 检查 Docker
        if ! command -v docker &> /dev/null; then
            echo "❌ 未安装 Docker，请先安装 Docker"
            exit 1
        fi
        
        # 启动服务
        echo "📦 启动所有服务..."
        docker-compose up -d
        
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 10
        
        # 运行迁移
        echo "🔄 运行数据库迁移..."
        docker-compose exec -T api alembic upgrade head
        
        echo ""
        echo "✅ 服务启动成功！"
        echo ""
        echo "📖 访问以下地址："
        echo "   - API 文档: http://localhost:8000/docs"
        echo "   - ReDoc: http://localhost:8000/redoc"
        echo "   - 健康检查: http://localhost:8000/health"
        echo ""
        echo "📝 查看日志："
        echo "   docker-compose logs -f api"
        echo ""
        ;;
        
    2)
        echo ""
        echo "💻 本地开发模式启动..."
        echo ""
        
        # 检查 Python
        if ! command -v python3 &> /dev/null; then
            echo "❌ 未安装 Python3"
            exit 1
        fi
        
        # 检查依赖
        if [ ! -d "venv" ]; then
            echo "📦 创建虚拟环境..."
            python3 -m venv venv
        fi
        
        echo "📦 激活虚拟环境..."
        source venv/bin/activate
        
        echo "📦 安装依赖..."
        pip install -r requirements.txt
        
        # 检查数据库连接
        echo ""
        echo "⚠️  请确保 PostgreSQL 和 Redis 已启动"
        echo "   如未启动，请运行选项 3 启动数据库服务"
        echo ""
        read -p "按 Enter 继续，或 Ctrl+C 退出..."
        
        # 运行迁移
        echo ""
        echo "🔄 运行数据库迁移..."
        alembic upgrade head
        
        # 启动服务
        echo ""
        echo "🚀 启动 FastAPI 服务..."
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
        
    3)
        echo ""
        echo "🗄️  启动数据库服务..."
        echo ""
        
        if ! command -v docker &> /dev/null; then
            echo "❌ 未安装 Docker"
            exit 1
        fi
        
        # 启动 PostgreSQL
        echo "🐘 启动 PostgreSQL..."
        docker run -d --name medical_postgres \
            -e POSTGRES_DB=medical_db \
            -e POSTGRES_USER=medical_user \
            -e POSTGRES_PASSWORD=medical_pass \
            -p 5432:5432 \
            postgres:15-alpine
        
        # 启动 Redis
        echo "🔴 启动 Redis..."
        docker run -d --name medical_redis \
            -p 6379:6379 \
            redis:7-alpine
        
        echo ""
        echo "✅ 数据库服务已启动"
        echo ""
        echo "📝 连接信息："
        echo "   PostgreSQL: localhost:5432"
        echo "   Redis: localhost:6379"
        echo ""
        ;;
        
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac

