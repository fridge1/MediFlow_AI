"""
日志工具
"""
import sys
from loguru import logger

from app.core.config import settings


# 配置日志
logger.remove()  # 移除默认处理器

# 添加控制台输出
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO"
)

# 添加文件输出
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩
    encoding="utf-8",
    level="INFO"
)

# 错误日志单独记录
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    level="ERROR"
)


__all__ = ["logger"]

