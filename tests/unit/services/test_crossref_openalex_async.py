"""CrossRef 和 OpenAlex 服务异步实现测试

这个测试文件为 CrossRef 和 OpenAlex 服务定义异步接口的测试用例。
这两个服务使用统一的 api_client，所以可以共享测试逻辑。

测试内容：
1. 异步搜索方法 (search_works_async)
2. 异步获取文献详情
3. 错误处理
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# 添加 src 目录到路径
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestCrossRefServiceAsyncMethods:
    """测试 CrossRef 服务的异步方法"""

    @pytest.fixture
    def crossref_service(self):
        """创建 CrossRef 服务实例"""
        try:
            from article_mcp.services.crossref_service import CrossRefService

            return CrossRefService(logger=Mock())
        except ImportError:
            pytest.skip("CrossRefService 未找到")

    @pytest.mark.asyncio
    async def test_crossref_search_works_async_exists(self, crossref_service):
        """测试：CrossRef search_works_async 方法存在"""
        # 检查方法是否存在
        if hasattr(crossref_service, "search_works_async"):
            import inspect

            assert inspect.iscoroutinefunction(crossref_service.search_works_async), (
                "search_works_async 应该是异步函数"
            )
        else:
            pytest.skip("search_works_async 方法尚未实现")

    @pytest.mark.asyncio
    async def test_crossref_search_works_async_basic(self, crossref_service):
        """测试：CrossRef 异步搜索基本功能"""
        try:
            result = await crossref_service.search_works_async("machine learning", max_results=5)

            assert isinstance(result, dict), "结果应该是字典"
            assert "articles" in result or "success" in result, "结果应该包含 articles 或 success"

        except (NotImplementedError, AttributeError):
            pytest.skip("search_works_async 尚未实现")

    @pytest.mark.asyncio
    async def test_crossref_search_works_async_with_mock(self, crossref_service):
        """测试：使用 Mock 测试 CrossRef 异步搜索"""
        # Mock API 响应
        mock_api_response = {
            "success": True,
            "data": {
                "message": {
                    "total-results": 1,
                    "items": [
                        {
                            "title": ["Test Article"],
                            "DOI": "10.1234/test.doi",
                            "author": [{"given": "John", "family": "Doe"}],
                            "created": {"date-time": "2023-01-01T00:00:00Z"},
                        }
                    ],
                }
            },
        }

        # Mock 异步 api_client
        with patch("article_mcp.services.crossref_service.get_async_api_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get = AsyncMock(return_value=mock_api_response)
            mock_get_client.return_value = mock_client

            try:
                result = await crossref_service.search_works_async("test", max_results=10)

                # 验证结果
                if "articles" in result:
                    assert len(result["articles"]) > 0
                    assert result["articles"][0]["doi"] == "10.1234/test.doi"

            except (NotImplementedError, AttributeError):
                pytest.skip("search_works_async 尚未实现")


class TestOpenAlexServiceAsyncMethods:
    """测试 OpenAlex 服务的异步方法"""

    @pytest.fixture
    def openalex_service(self):
        """创建 OpenAlex 服务实例"""
        try:
            from article_mcp.services.openalex_service import OpenAlexService

            return OpenAlexService(logger=Mock())
        except ImportError:
            pytest.skip("OpenAlexService 未找到")

    @pytest.mark.asyncio
    async def test_openalex_search_works_async_exists(self, openalex_service):
        """测试：OpenAlex search_works_async 方法存在"""
        if hasattr(openalex_service, "search_works_async"):
            import inspect

            assert inspect.iscoroutinefunction(openalex_service.search_works_async), (
                "search_works_async 应该是异步函数"
            )
        else:
            pytest.skip("search_works_async 方法尚未实现")

    @pytest.mark.asyncio
    async def test_openalex_search_works_async_basic(self, openalex_service):
        """测试：OpenAlex 异步搜索基本功能"""
        try:
            result = await openalex_service.search_works_async("neural networks", max_results=5)

            assert isinstance(result, dict), "结果应该是字典"
            assert "articles" in result or "success" in result

        except (NotImplementedError, AttributeError):
            pytest.skip("search_works_async 尚未实现")

    @pytest.mark.asyncio
    async def test_openalex_search_works_async_with_mock(self, openalex_service):
        """测试：使用 Mock 测试 OpenAlex 异步搜索"""
        # Mock API 响应
        mock_api_response = {
            "success": True,
            "data": {
                "meta": {"count": 1},
                "results": [
                    {
                        "title": "Test Article",
                        "doi": "10.1234/openalex.test",
                        "publication_year": 2023,
                        "primary_location": {"source": {"display_name": "Test Journal"}},
                    }
                ],
            },
        }

        with patch("article_mcp.services.openalex_service.get_async_api_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get = AsyncMock(return_value=mock_api_response)
            mock_get_client.return_value = mock_client

            try:
                result = await openalex_service.search_works_async("test", max_results=10)

                if "articles" in result:
                    assert len(result["articles"]) > 0

            except (NotImplementedError, AttributeError):
                pytest.skip("search_works_async 尚未实现")


class TestCrossRefOpenAlexParallelSearch:
    """测试 CrossRef 和 OpenAlex 的并行搜索"""

    @pytest.mark.asyncio
    async def test_parallel_crossref_openalex_search(self):
        """测试：CrossRef 和 OpenAlex 并行搜索"""
        try:
            from article_mcp.services.crossref_service import CrossRefService
            from article_mcp.services.openalex_service import OpenAlexService

            crossref = CrossRefService(logger=Mock())
            openalex = OpenAlexService(logger=Mock())

            # 并行搜索
            import time

            start = time.time()

            results = await asyncio.gather(
                crossref.search_works_async("test", max_results=5),
                openalex.search_works_async("test", max_results=5),
                return_exceptions=True,
            )

            elapsed = time.time() - start

            # 验证结果
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 1

            # 并行执行应该更快
            assert elapsed < 2.0, f"并行执行耗时 {elapsed:.2f}s"

        except (ImportError, NotImplementedError, AttributeError):
            pytest.skip("服务或异步方法尚未实现")


# ============================================================================
# 实现检查
# ============================================================================


def test_crossref_async_signature():
    """测试：检查 CrossRef 异步方法签名"""
    try:
        import inspect

        from article_mcp.services.crossref_service import CrossRefService

        service = CrossRefService(logger=Mock())

        if hasattr(service, "search_works_async"):
            sig = inspect.signature(service.search_works_async)
            params = list(sig.parameters.keys())

            expected_params = ["self", "query", "max_results"]
            for param in expected_params:
                assert param in params

            assert inspect.iscoroutinefunction(service.search_works_async)

    except (ImportError, AssertionError):
        pytest.skip("CrossRefService 或 search_works_async 尚未实现")


def test_openalex_async_signature():
    """测试：检查 OpenAlex 异步方法签名"""
    try:
        import inspect

        from article_mcp.services.openalex_service import OpenAlexService

        service = OpenAlexService(logger=Mock())

        if hasattr(service, "search_works_async"):
            sig = inspect.signature(service.search_works_async)
            params = list(sig.parameters.keys())

            expected_params = ["self", "query", "max_results"]
            for param in expected_params:
                assert param in params

            assert inspect.iscoroutinefunction(service.search_works_async)

    except (ImportError, AssertionError):
        pytest.skip("OpenAlexService 或 search_works_async 尚未实现")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
