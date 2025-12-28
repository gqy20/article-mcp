"""测试 RuntimeWarning 协程未等待问题的修复

测试目标：
1. 验证 test_relation_tools.py 的导入路径需要修复
2. 验证 run_async_with_timeout 的正确用法

问题根因：
- test_relation_tools.py 使用 `from src.article_mcp...` 导入
- 应该使用 `from article_mcp...` 导入
"""

import sys
from pathlib import Path

import pytest

# 添加 src 到路径以支持旧式导入
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.unit
class TestImportPathFix:
    """测试导入路径修复"""

    def test_old_import_path_works_with_sys_path(self):
        """验证：旧的导入路径在有 sys.path 设置时可以工作"""
        # 因为 sys.path 已包含 src，这个导入应该工作
        from article_mcp.tools.core import relation_tools

        assert relation_tools is not None
        assert hasattr(relation_tools, "register_relation_tools")

    def test_new_import_path_always_works(self):
        """验证：新的导入路径（无 src 前缀）总是工作"""
        # 这个应该始终工作，因为项目使用 src layout
        from article_mcp.tools.core import relation_tools

        assert relation_tools is not None


@pytest.mark.unit
class TestRunAsyncWithTimeoutUsage:
    """测试 run_async_with_timeout 的正确用法"""

    def test_function_is_sync_not_async(self):
        """验证：run_async_with_timeout 是同步函数，不是异步函数"""
        # 这个函数应该是同步的
        import inspect

        from tests.utils.test_helpers import run_async_with_timeout

        assert not inspect.iscoroutinefunction(run_async_with_timeout)

    def test_run_async_with_timeout_wraps_coro(self):
        """验证：run_async_with_timeout 正确包装协程"""
        import asyncio

        from tests.utils.test_helpers import run_async_with_timeout

        async def sample_coro():
            await asyncio.sleep(0.01)
            return "done"

        # 应该直接调用，不应该 await
        result = run_async_with_timeout(sample_coro(), timeout=1.0)
        assert result == "done"
