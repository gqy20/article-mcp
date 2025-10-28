"""
MCP标准错误处理中间件
"""

import logging as std_logging
import time
from typing import Any

from mcp import McpError
from mcp.types import ErrorData
from fastmcp.exceptions import ToolError

from fastmcp.server.middleware import Middleware, MiddlewareContext

# 导入具体的中间件实现
from .logging import LoggingMiddleware, TimingMiddleware


class MCPErrorHandlingMiddleware(Middleware):
    """MCP标准错误处理中间件"""

    def __init__(self, logger: std_logging.Logger | None = None):
        self.logger = logger or std_logging.getLogger(__name__)

    async def on_message(self, context: MiddlewareContext, call_next):
        """处理所有消息的错误"""
        try:
            return await call_next(context)
        except McpError:
            # 已经是MCP标准错误，直接重新抛出
            raise
        except ToolError:
            # ToolError会自动发送给客户端，直接重新抛出
            raise
        except Exception as e:
            # 转换为MCP标准错误
            self.logger.error(f"Error in {context.method}: {type(e).__name__}: {e}")

            # 根据异常类型确定错误处理方式
            if self._is_user_input_error(e):
                # 用户输入错误，重新抛出为ToolError
                raise ToolError(f"输入错误: {str(e)}")
            else:
                # 系统错误，转换为MCP标准错误
                error_code = self._get_error_code(e)
                raise McpError(ErrorData(
                    code=error_code,
                    message=f"系统错误: {type(e).__name__}: {str(e)}"
                ))

    def _is_user_input_error(self, error: Exception) -> bool:
        """判断是否为用户输入错误"""
        user_error_types = (
            ValueError, TypeError, AttributeError,
            KeyError, IndexError, AssertionError
        )
        return isinstance(error, user_error_types)

    def _get_error_code(self, error: Exception) -> int:
        """根据异常类型确定MCP错误码"""
        # 网络相关错误
        if "connection" in str(type(error).__name__).lower():
            return -32603  # Internal error
        # 超时错误
        if "timeout" in str(type(error).__name__).lower():
            return -32603  # Internal error
        # 参数错误
        if "value" in str(type(error).__name__).lower() or "type" in str(type(error).__name__).lower():
            return -32602  # Invalid params
        # 默认内部错误
        return -32603


class StandardErrorWrapper:
    """标准错误包装器 - 用于工具函数"""

    @staticmethod
    def wrap_tool_function(tool_func):
        """包装工具函数以提供标准错误处理"""
        async def wrapper(*args, **kwargs):
            try:
                return await tool_func(*args, **kwargs)
            except McpError:
                raise
            except Exception as e:
                raise McpError(ErrorData(
                    code=-32603,
                    message=f"{type(e).__name__}: {str(e)}"
                ))
        return wrapper

    @staticmethod
    def wrap_sync_tool_function(tool_func):
        """包装同步工具函数以提供标准错误处理"""
        def wrapper(*args, **kwargs):
            try:
                return tool_func(*args, **kwargs)
            except McpError:
                raise
            except Exception as e:
                raise McpError(ErrorData(
                    code=-32603,
                    message=f"{type(e).__name__}: {str(e)}"
                ))
        return wrapper