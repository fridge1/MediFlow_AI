"""
初始化数据库脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db, engine
from app.utils.logger import logger


async def main():
    """初始化数据库表"""
    logger.info("开始初始化数据库...")
    
    try:
        await init_db()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

