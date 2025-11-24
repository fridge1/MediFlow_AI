#!/bin/bash
# 安装依赖脚本（带镜像源支持）

echo "📦 开始安装 Python 依赖..."
echo ""

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  建议在虚拟环境中安装"
    read -p "是否创建虚拟环境？(y/n): " create_venv
    
    if [ "$create_venv" = "y" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
        echo "✅ 虚拟环境已创建并激活"
    fi
fi

echo ""
echo "选择安装方式："
echo "1) 使用国内镜像源（推荐国内用户，速度快）"
echo "2) 使用官方源"
echo "3) 手动指定镜像源"
echo ""
read -p "请选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📥 使用清华大学镜像源..."
        pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        ;;
    2)
        echo ""
        echo "📥 使用官方源..."
        pip install --upgrade pip
        pip install -r requirements.txt
        ;;
    3)
        echo ""
        echo "可用的镜像源："
        echo "  - 清华: https://pypi.tuna.tsinghua.edu.cn/simple"
        echo "  - 阿里: https://mirrors.aliyun.com/pypi/simple/"
        echo "  - 腾讯: https://mirrors.cloud.tencent.com/pypi/simple"
        echo "  - 豆瓣: https://pypi.douban.com/simple"
        echo ""
        read -p "请输入镜像源 URL: " mirror_url
        pip install --upgrade pip -i $mirror_url
        pip install -r requirements.txt -i $mirror_url
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 依赖安装成功！"
    echo ""
    echo "下一步："
    echo "1. 配置 .env 文件"
    echo "2. 运行数据库迁移: alembic upgrade head"
    echo "3. 启动服务: uvicorn app.main:app --reload"
else
    echo ""
    echo "❌ 安装失败"
    echo ""
    echo "如果遇到 cryptography 需要 Rust 的问题："
    echo "1. 尝试使用国内镜像源（选项 1）"
    echo "2. 或手动安装 Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "3. 或使用 Docker 方式部署（推荐）"
fi

