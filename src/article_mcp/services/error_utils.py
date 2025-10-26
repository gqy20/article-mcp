"""
统一的错误处理工具 - Linus风格：简单直接
"""

import logging
import time
from typing import Any


def format_error(operation: str, error: Exception, context: dict | None = None) -> dict[str, Any]:
    """
    统一的错误格式 - 一个函数搞定所有错误

    Args:
        operation: 操作名称
        error: 异常对象
        context: 额外的上下文信息

    Returns:
        标准化的错误响应
    """
    return {
        "success": False,
        "error": str(error),
        "operation": operation,
        "error_type": type(error).__name__,
        "context": context or {},
        "timestamp": time.time(),
    }


def format_response(
    success: bool,
    data: Any = None,
    operation: str = "",
    message: str = "",
    context: dict | None = None,
) -> dict[str, Any]:
    """
    统一的响应格式 - 一个函数搞定所有响应

    Args:
        success: 是否成功
        data: 返回数据
        operation: 操作名称
        message: 响应消息
        context: 额外的上下文信息

    Returns:
        标准化的响应
    """
    response = {"success": success, "operation": operation, "timestamp": time.time()}

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    if context:
        response["context"] = context

    return response


def safe_execute(operation: str, func, *args, **kwargs):
    """
    安全执行函数 - 自动处理异常

    Args:
        operation: 操作名称
        func: 要执行的函数
        *args, **kwargs: 函数参数

    Returns:
        格式化的响应
    """
    try:
        result = func(*args, **kwargs)
        return format_response(True, result, operation, "操作成功")
    except Exception as e:
        return format_error(operation, e)


class ErrorHandler:
    """错误处理器类 - 简单直接"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    def handle(
        self, operation: str, error: Exception, context: dict | None = None
    ) -> dict[str, Any]:
        """处理错误"""
        self.logger.error(f"{operation} 失败: {error}")
        return format_error(operation, error, context)

    def log_and_return(self, operation: str, message: str, data: Any = None) -> dict[str, Any]:
        """记录日志并返回响应"""
        self.logger.info(f"{operation}: {message}")
        return format_response(True, data, operation, message)


# 全局错误处理器实例
_default_handler = ErrorHandler()


def get_error_handler(logger: logging.Logger | None = None) -> ErrorHandler:
    """获取错误处理器"""
    if logger:
        return ErrorHandler(logger)
    return _default_handler
