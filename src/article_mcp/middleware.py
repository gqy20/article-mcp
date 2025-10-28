"""
MCP服务器中间件模块
提供错误处理、日志记录和性能监控中间件
"""

import time
import traceback
from typing import Any, Callable

from fastmcp import FastMCP


class MCPErrorHandlingMiddleware:
    """MCP错误处理中间件"""

    def __init__(self, logger: Any):
        self.logger = logger

    async def __call__(self, handler: Callable, request: Any) -> Any:
        """处理工具调用异常"""
        try:
            return await handler(request)
        except Exception as e:
            self.logger.error(f"工具调用异常: {type(e).__name__}: {str(e)}")
            self.logger.debug(f"异常详情:\n{traceback.format_exc()}")

            # 抛出MCP标准错误
            from mcp import McpError
            from mcp.types import ErrorData

            raise McpError(ErrorData(
                code=-32603,
                message=f"工具执行失败: {type(e).__name__}: {str(e)}"
            ))


class LoggingMiddleware:
    """MCP日志记录中间件"""

    def __init__(self, logger: Any):
        self.logger = logger

    async def __call__(self, handler: Callable, request: Any) -> Any:
        """记录工具调用日志"""
        start_time = time.time()

        # 获取工具名称
        tool_name = getattr(request, 'method', 'unknown_tool')
        self.logger.info(f"开始调用工具: {tool_name}")

        try:
            result = await handler(request)
            end_time = time.time()

            self.logger.info(f"工具 {tool_name} 执行成功，耗时: {end_time - start_time:.2f}秒")
            return result

        except Exception as e:
            end_time = time.time()
            self.logger.error(f"工具 {tool_name} 执行失败，耗时: {end_time - start_time:.2f}秒，错误: {str(e)}")
            raise


class TimingMiddleware:
    """MCP性能监控中间件"""

    def __init__(self):
        self.call_stats = {}

    async def __call__(self, handler: Callable, request: Any) -> Any:
        """监控工具调用性能"""
        start_time = time.time()

        # 获取工具名称
        tool_name = getattr(request, 'method', 'unknown_tool')

        try:
            result = await handler(request)
            end_time = time.time()
            execution_time = end_time - start_time

            # 更新统计信息
            if tool_name not in self.call_stats:
                self.call_stats[tool_name] = {
                    'total_calls': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'success_count': 0,
                    'error_count': 0
                }

            stats = self.call_stats[tool_name]
            stats['total_calls'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['total_calls']
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['success_count'] += 1

            return result

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            # 更新错误统计
            if tool_name not in self.call_stats:
                self.call_stats[tool_name] = {
                    'total_calls': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'success_count': 0,
                    'error_count': 0
                }

            self.call_stats[tool_name]['error_count'] += 1
            raise

    def get_stats(self) -> dict[str, Any]:
        """获取性能统计信息"""
        return self.call_stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.call_stats.clear()


# 便捷函数，用于创建中间件实例
def create_error_handling_middleware(logger: Any) -> MCPErrorHandlingMiddleware:
    """创建错误处理中间件"""
    return MCPErrorHandlingMiddleware(logger)


def create_logging_middleware(logger: Any) -> LoggingMiddleware:
    """创建日志记录中间件"""
    return LoggingMiddleware(logger)


def create_timing_middleware() -> TimingMiddleware:
    """创建性能监控中间件"""
    return TimingMiddleware()


# 全局性能监控实例
_global_timing_middleware = None


def get_global_timing_middleware() -> TimingMiddleware:
    """获取全局性能监控中间件实例"""
    global _global_timing_middleware
    if _global_timing_middleware is None:
        _global_timing_middleware = TimingMiddleware()
    return _global_timing_middleware


def get_global_performance_stats() -> dict[str, Any]:
    """获取全局性能统计"""
    return get_global_timing_middleware().get_stats()


def reset_global_performance_stats() -> None:
    """重置全局性能统计"""
    get_global_timing_middleware().reset_stats()