#!/bin/bash
# 自动部署脚本

set -e  # 遇到错误立即退出

echo "🚀 Medical AI Platform 自动部署脚本"
echo "========================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未安装 Docker，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 未安装 docker-compose，请先安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down 2>/dev/null || true
echo ""

# 清理旧数据（可选）
read -p "是否清理旧数据？(y/N): " clean_data
if [ "$clean_data" = "y" ] || [ "$clean_data" = "Y" ]; then
    echo "🧹 清理旧数据..."
    docker-compose down -v
    echo "✅ 数据已清理"
fi
echo ""

# 构建并启动服务
echo "📦 构建并启动服务..."
docker-compose up -d --build

echo ""
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "📊 检查服务健康状态..."

# 等待 PostgreSQL
echo -n "等待 PostgreSQL 启动..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U medical_user -d medical_db > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 1
done

# 等待 Redis
echo -n "等待 Redis 启动..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 1
done

# 等待 API 服务
echo -n "等待 API 服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "🔄 运行数据库迁移..."
docker-compose exec -T api alembic upgrade head

echo ""
echo "✅ 部署完成！"
echo ""
echo "📖 服务访问地址："
echo "   - API 文档: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo "   - 健康检查: http://localhost:8000/health"
echo ""
echo "📝 查看日志："
echo "   docker-compose logs -f api"
echo ""
echo "🛑 停止服务："
echo "   docker-compose down"
echo ""

