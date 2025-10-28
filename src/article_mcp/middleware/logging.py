"""
日志和计时中间件
"""

import logging
import time
from typing import Any

from fastmcp.server.middleware import Middleware, MiddlewareContext


class LoggingMiddleware(Middleware):
    """日志中间件"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    async def on_message(self, context: MiddlewareContext, call_next):
        """记录请求日志"""
        start_time = time.time()

        self.logger.info(f"开始处理 {context.method}")

        try:
            result = await call_next(context)
            processing_time = round(time.time() - start_time, 2)

            self.logger.info(f"{context.method} 处理成功，耗时 {processing_time}s")
            return result

        except Exception as e:
            processing_time = round(time.time() - start_time, 2)
            self.logger.error(f"{context.method} 处理失败，耗时 {processing_time}s，错误: {e}")
            raise


class TimingMiddleware(Middleware):
    """计时中间件 - 自动添加性能统计"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def on_message(self, context: MiddlewareContext, call_next):
        """自动添加计时信息"""
        start_time = time.time()

        result = await call_next(context)

        processing_time = round(time.time() - start_time, 2)

        # 如果结果是字典，添加计时信息
        if isinstance(result, dict):
            result["processing_time"] = processing_time
            result["timestamp"] = time.time()

        return result