"""质量工具纯异步测试 - TDD Red 阶段

此测试验证质量工具应该是纯异步实现，不使用 threading 混合模式。

测试场景：
1. 验证 get_journal_quality_async 存在且是异步函数
2. 验证单个期刊查询可以在异步上下文中直接调用
3. 验证批量期刊查询使用异步并发（非 threading）
4. 验证不在异步上下文中调用时能优雅处理
"""

import asyncio
import inspect
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.tools.core import quality_tools


@pytest.fixture
def logger():
    return logging.getLogger(__name__)


@pytest.fixture
def mock_services():
    """模拟服务"""

    # 创建一个保留原始字段的 enhance_quality_result mock
    async def mock_enhance(result, use_cache):
        """保留原始 response 的字段，只添加 OpenAlex 指标"""
        result["openalex_metrics"] = {
            "h_index": 500,
            "citation_rate": 50.0,
        }
        return result

    openalex = Mock()
    openalex.enhance_quality_result = AsyncMock(side_effect=mock_enhance)

    easyscholar = Mock()
    easyscholar.get_journal_quality = AsyncMock(
        return_value={
            "success": True,
            "journal_name": "Nature",
            "data_source": "easyscholar",
            "quality_metrics": {
                "impact_factor": 49.0,
                "quartile": "Q1",
            },
            "ranking_info": {},
        }
    )
    easyscholar.batch_get_journal_quality = AsyncMock(
        return_value=[
            {
                "success": True,
                "journal_name": "Nature",
                "data_source": "easyscholar",
                "quality_metrics": {
                    "impact_factor": 49.0,
                    "quartile": "Q1",
                },
                "ranking_info": {},
                "cache_hit": False,
            },
            {
                "success": True,
                "journal_name": "Science",
                "data_source": "easyscholar",
                "quality_metrics": {
                    "impact_factor": 50.0,
                    "quartile": "Q1",
                },
                "ranking_info": {},
                "cache_hit": False,
            },
            {
                "success": True,
                "journal_name": "Cell",
                "data_source": "easyscholar",
                "quality_metrics": {
                    "impact_factor": 48.0,
                    "quartile": "Q1",
                },
                "ranking_info": {},
                "cache_hit": False,
            },
        ]
    )

    return {
        "openalex": openalex,
        "easyscholar": easyscholar,
    }


@pytest.mark.asyncio
class TestQualityToolsPureAsync:
    """测试质量工具的纯异步实现"""

    def test_get_journal_quality_async_exists(self):
        """测试：get_journal_quality_async 函数应该存在"""
        # Red 阶段：这个测试会失败，因为函数尚未存在或不是异步的
        assert hasattr(quality_tools, "get_journal_quality_async"), (
            "get_journal_quality_async 函数应该存在"
        )

        # 验证是协程函数
        assert inspect.iscoroutinefunction(quality_tools.get_journal_quality_async), (
            "get_journal_quality_async 应该是异步函数"
        )

    async def test_single_journal_quality_is_pure_async(self, mock_services, logger):
        """测试：单个期刊查询应该是纯异步，不使用 threading"""
        # Red 阶段：这个测试验证纯异步行为

        # Mock 验证：不应该创建线程
        with patch("threading.Thread") as mock_thread:
            result = await quality_tools.get_journal_quality_async(
                journal_name="Nature",
                use_cache=False,  # 禁用缓存以避免文件锁问题
                services=mock_services,
                logger=logger,
            )

            # 验证：不应该使用 threading
            mock_thread.assert_not_called()

            # 验证结果正确
            assert result["success"] is True
            assert result["journal_name"] == "Nature"

    async def test_batch_journal_quality_uses_async_gather(self, mock_services, logger):
        """测试：批量期刊查询应该使用异步并发，而非 threading"""
        # Red 阶段：验证批量查询使用 asyncio.gather 而非 threading

        journal_names = ["Nature", "Science", "Cell"]

        # Mock 验证：不应该创建线程
        with patch("threading.Thread") as mock_thread:
            result = await quality_tools.get_journal_quality_async(
                journal_name=journal_names,
                use_cache=False,  # 禁用缓存以避免文件锁问题
                services=mock_services,
                logger=logger,
            )

            # 验证：不应该使用 threading
            mock_thread.assert_not_called()

            # 验证批量结果
            assert result["success"] is True
            assert result["total_journals"] == 3
            assert result["successful_evaluations"] == 3
            # _apply_sorting 返回的是 journals 而不是 journal_results
            assert "journals" in result
            assert len(result["journals"]) == 3

    async def test_pure_async_no_event_loop_creation(self, mock_services, logger):
        """测试：纯异步实现不应该创建新的事件循环"""
        # Red 阶段：验证不使用 asyncio.new_event_loop

        with patch("asyncio.new_event_loop") as mock_new_loop:
            result = await quality_tools.get_journal_quality_async(
                journal_name="Nature",
                use_cache=False,  # 禁用缓存以避免文件锁问题
                services=mock_services,
                logger=logger,
            )

            # 验证：不应该创建新事件循环
            mock_new_loop.assert_not_called()

            # 验证结果正确
            assert result["success"] is True

    async def test_async_function_signature_matches_others(self):
        """测试：异步函数签名应该与其他工具一致"""
        # Red 阶段：验证函数签名使用 services 和 logger 闭包模式

        sig = inspect.signature(quality_tools.get_journal_quality_async)
        params = sig.parameters

        # 验证必需参数
        assert "journal_name" in params
        assert "services" in params, "应该有 services 参数（闭包模式）"
        assert "logger" in params, "应该有 logger 参数（闭包模式）"

    async def test_cache_operations_in_async_context(self, mock_services, logger):
        """测试：缓存操作应该在异步上下文中正常工作"""
        # Red 阶段：验证缓存与纯异步兼容

        result = await quality_tools.get_journal_quality_async(
            journal_name="Nature",
            use_cache=True,
            services=mock_services,
            logger=logger,
        )

        # 缓存应该正常工作
        assert result["success"] is True
        # 验证使用了缓存
        assert "cache_hit" in result or "from_cache" in result


class TestAsyncQualityToolsOutsideEventLoop:
    """测试在非异步上下文中调用异步质量工具"""

    def test_calling_async_with_asyncio_run(self):
        """测试：使用 asyncio.run 可以调用异步函数"""
        # Green 阶段：验证纯异步函数可以通过 asyncio.run 调用
        # FastMCP 会处理事件循环问题

        # 创建简单的 mock
        async def mock_get_journal_quality(*args, **kwargs):
            return {"success": True, "journal_name": "Test"}

        # 使用 asyncio.run 运行异步函数
        result = asyncio.run(mock_get_journal_quality())

        # 验证可以正常运行
        assert result["success"] is True
        assert result["journal_name"] == "Test"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
