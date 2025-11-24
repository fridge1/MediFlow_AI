# 故障排查指南

## 常见问题及解决方案

### 1. ❌ 安装依赖时提示需要 Rust 编译器

**错误信息**：
```
error: failed to download file from 'https://static.rust-lang.org/dist/...'
Cargo, the Rust package manager, is not installed or is not on PATH.
This package requires Rust and Cargo to compile extensions.
```

**原因**：
`cryptography` 包需要 Rust 编译器来编译，但由于网络问题无法下载 Rust。

**解决方案（按推荐顺序）**：

#### 方案 1：使用国内镜像源（最简单，推荐）✅

```bash
# 使用新的安装脚本
./install_dependencies.sh
# 选择选项 1（使用国内镜像源）
```

或者直接使用清华镜像：

```bash
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 方案 2：使用 Docker（最推荐，无需本地配置）✅

```bash
# Docker 内已包含所有依赖
docker-compose up -d
docker-compose exec api alembic upgrade head
```

#### 方案 3：手动安装 Rust（如果必须本地运行）

```bash
# 配置 Rust 使用国内镜像
export RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static
export RUSTUP_UPDATE_ROOT=https://mirrors.ustc.edu.cn/rust-static/rustup

# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 然后重新安装依赖
pip install -r requirements.txt
```

#### 方案 4：使用预编译的 wheel 包

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像安装，会自动下载预编译包
pip install cryptography -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### 2. ❌ 数据库连接失败

**错误信息**：
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**：

```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 如果没有运行，启动数据库
docker-compose up -d postgres

# 或使用 start.sh 选项 3
./start.sh  # 选择选项 3
```

---

### 3. ❌ Redis 连接失败

**错误信息**：
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决方案**：

```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 启动 Redis
docker-compose up -d redis
```

---

### 4. ❌ Alembic 迁移失败

**错误信息**：
```
alembic.util.exc.CommandError: Can't locate revision identified by...
```

**解决方案**：

```bash
# 方案 1：重新生成迁移
rm -rf alembic/versions/*.py  # 删除旧迁移文件
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 方案 2：使用 Docker（推荐）
docker-compose up -d
docker-compose exec api alembic upgrade head
```

---

### 5. ❌ 导入错误（ModuleNotFoundError）

**错误信息**：
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案**：

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### 6. ❌ 端口已被占用

**错误信息**：
```
OSError: [Errno 48] Address already in use
```

**解决方案**：

```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
uvicorn app.main:app --port 8001
```

---

### 7. ⚠️ 网络问题（国内用户）

**问题**：下载速度慢或超时

**解决方案**：

#### Python 包镜像

创建或编辑 `~/.pip/pip.conf`：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

#### Docker 镜像加速

创建或编辑 `~/.docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com"
  ]
}
```

重启 Docker：
```bash
# macOS
killall Docker && open /Applications/Docker.app

# Linux
sudo systemctl restart docker
```

---

## 推荐的安装流程

### 对于国内用户（最佳实践）

```bash
# 1. 使用 Docker（强烈推荐）
docker-compose up -d
docker-compose exec api alembic upgrade head

# 2. 如果必须本地运行
./install_dependencies.sh  # 选择选项 1（国内镜像）
alembic upgrade head
uvicorn app.main:app --reload
```

### 对于海外用户

```bash
# 1. 使用 Docker（推荐）
docker-compose up -d
docker-compose exec api alembic upgrade head

# 2. 本地运行
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

---

## 验证安装

### 1. 检查服务状态

```bash
# Docker 方式
docker-compose ps

# 本地方式
curl http://localhost:8000/health
```

### 2. 访问 API 文档

打开浏览器访问：
- http://localhost:8000/docs （Swagger UI）
- http://localhost:8000/redoc （ReDoc）

### 3. 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 注册用户
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

---

## 获取帮助

### 查看日志

```bash
# Docker 日志
docker-compose logs -f api

# 本地日志
tail -f logs/app_*.log
tail -f logs/error_*.log
```

### 调试模式

在 `.env` 文件中设置：
```bash
DEBUG=true
```

### 数据库状态

```bash
# 连接数据库
docker-compose exec postgres psql -U medical_user -d medical_db

# 查看表
\dt

# 退出
\q
```

---

## 清理与重置

### 重置数据库

```bash
# Docker 方式
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head

# 本地方式
dropdb medical_db
createdb medical_db
alembic upgrade head
```

### 清理 Python 缓存

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 重新安装依赖

```bash
# 删除虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate
./install_dependencies.sh
```

---

## 性能优化建议

### 1. 生产环境配置

在 `.env` 文件中：
```bash
DEBUG=false
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### 2. 数据库连接池

已在 `app/core/database.py` 中配置：
- pool_size=10
- max_overflow=20

### 3. Redis 缓存

确保 Redis 正常运行以提升性能。

---

如果以上方案都无法解决问题，请查看：
- 完整日志文件
- 系统环境信息
- 详细错误堆栈

