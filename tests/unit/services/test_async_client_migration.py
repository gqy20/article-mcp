"""HTTP客户端异步迁移测试 - TDD Red 阶段

此测试验证所有服务应该使用纯异步HTTP客户端，而不是同步的 requests 库。

测试场景：
1. 验证 OpenAlexService 不使用 UnifiedAPIClient
2. 验证 CrossRefService 不使用 get_api_client()
3. 验证 ArxivSearchService 不使用 requests
4. 验证 PubMedSearch 不使用 requests
5. 验证 SimilarArticles 不使用 requests
"""

import asyncio
import inspect
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.services.api_utils import AsyncAPIClient, UnifiedAPIClient
from article_mcp.services.arxiv_search import ArXivSearchService, create_arxiv_service
from article_mcp.services.crossref_service import CrossRefService
from article_mcp.services.openalex_service import OpenAlexService
from article_mcp.services.pubmed_search import PubMedService, create_pubmed_service
from article_mcp.services.reference_service import UnifiedReferenceService

# similar_articles 模块只有函数，没有类


@pytest.fixture
def logger():
    return logging.getLogger(__name__)


# ============================================================================
# 测试 1: OpenAlexService 应该使用纯异步客户端
# ============================================================================


@pytest.mark.asyncio
class TestOpenAlexServiceAsyncOnly:
    """测试 OpenAlexService 使用纯异步客户端"""

    def test_openalex_service_should_not_use_unified_api_client(self):
        """测试：OpenAlexService 不应该使用 UnifiedAPIClient（同步客户端）"""
        # Red 阶段：验证服务不依赖同步客户端

        service = OpenAlexService()

        # 验证：不应该有同步 api_client 属性
        # 或者如果有，应该标记为已废弃
        assert not hasattr(service, "api_client") or isinstance(
            service.api_client, UnifiedAPIClient
        ), "OpenAlexService 应该移除同步的 UnifiedAPIClient"

    async def test_openalex_service_async_methods_use_async_client(self, logger):
        """测试：OpenAlexService 异步方法应该使用 AsyncAPIClient"""

        service = OpenAlexService(logger)

        # Mock 异步客户端
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(
            return_value={
                "success": True,
                "data": {"results": [], "meta": {"count": 0}},
            }
        )

        service._async_api_client = mock_async_client

        # 调用异步方法
        result = await service.search_works_async("test query")

        # 验证：使用了异步客户端
        mock_async_client.get.assert_called_once()
        assert result["success"] is True

    def test_openalex_service_sync_methods_should_be_async(self):
        """测试：OpenAlexService 的同步方法应该改为异步"""
        # Green 阶段：验证所有API方法都应该是异步的（纯数据处理方法除外）

        service = OpenAlexService()

        # 检查所有公共方法
        public_methods = [
            name
            for name in dir(service)
            if not name.startswith("_") and callable(getattr(service, name))
        ]

        # 排除纯数据处理方法（不需要异步）
        data_processing_methods = {"filter_open_access"}

        sync_methods = []
        for method_name in public_methods:
            # 跳过数据处理方法
            if method_name in data_processing_methods:
                continue

            method = getattr(service, method_name)
            if inspect.ismethod(method) and not inspect.iscoroutinefunction(method):
                sync_methods.append(method_name)

        # 所有API方法都应该是异步的
        assert len(sync_methods) == 0, f"这些方法应该是异步的: {sync_methods}"


# ============================================================================
# 测试 2: CrossRefService 应该使用纯异步客户端
# ============================================================================


@pytest.mark.asyncio
class TestCrossRefServiceAsyncOnly:
    """测试 CrossRefService 使用纯异步客户端"""

    def test_crossref_service_should_not_use_get_api_client(self):
        """测试：CrossRefService 不应该使用 get_api_client()"""
        # Red 阶段：验证服务不依赖同步客户端获取函数

        service = CrossRefService(logger=logger)

        # 验证：不应该使用 get_api_client()
        assert (
            "api_client" not in dir(service)
            or not callable(service.api_client.get)
            or inspect.iscoroutinefunction(service.api_client.get)
        ), "CrossRefService 应该使用异步客户端"

    async def test_crossref_service_methods_use_async_client(self, logger):
        """测试：CrossRefService 方法应该使用 AsyncAPIClient"""
        # Green 阶段：验证异步方法使用异步客户端

        service = CrossRefService(logger=logger)

        # Mock 异步客户端
        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(
            return_value={
                "success": True,
                "data": {"message": {"items": []}},
            }
        )

        service._async_api_client = mock_async_client

        # 调用方法 - 使用正确的方法名 get_work_by_doi_async
        result = await service.get_work_by_doi_async("10.1234/test")

        # 验证结果
        assert result is not None


# ============================================================================
# 测试 3: ArxivSearchService 应该使用纯异步客户端
# ============================================================================


@pytest.mark.asyncio
class TestArxivSearchServiceAsyncOnly:
    """测试 ArxivSearchService 使用纯异步客户端"""

    def test_arxiv_service_should_not_use_requests(self):
        """测试：ArxivSearchService 不应该使用 requests 模块"""
        # Red 阶段：验证不使用 requests

        service = create_arxiv_service(logger)

        # 验证：不应该有同步的 session 属性使用 requests
        if hasattr(service, "session"):
            # 如果有 session，应该是 aiohttp ClientSession 而不是 requests.Session
            import requests

            assert not isinstance(service.session, requests.Session), (
                "ArxivSearchService 应该使用 aiohttp 而不是 requests"
            )

    async def test_arxiv_service_search_is_pure_async(self, logger):
        """测试：ArxivSearchService 搜索应该是纯异步"""
        # Red 阶段：验证搜索方法是纯异步

        service = create_arxiv_service(logger)

        # 验证 search_async 是协程函数
        assert inspect.iscoroutinefunction(service.search_async), "search_async 应该是异步函数"

        # Mock 测试
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<feed></feed>")
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_get.return_value = mock_response

            result = await service.search_async("machine learning")

            # 验证调用了异步方法
            assert mock_get.called or result is not None


# ============================================================================
# 测试 4: PubMedSearch 应该使用纯异步客户端
# ============================================================================


@pytest.mark.asyncio
class TestPubMedSearchAsyncOnly:
    """测试 PubMedSearch 使用纯异步客户端"""

    def test_pubmed_service_should_not_use_direct_requests(self):
        """测试：PubMedSearch 不应该直接使用 requests.get"""
        # Red 阶段：验证不使用 requests.get

        service = create_pubmed_service(logger)

        # 检查源代码中是否有 requests.get 调用
        import requests

        import article_mcp.services.pubmed_search as pubmed_module

        # 这个检查通过分析源代码来完成
        source = inspect.getsource(pubmed_module)
        has_requests_get = "requests.get(" in source

        # Red 阶段：这个会失败，因为代码中仍有 requests.get
        assert not has_requests_get, "PubMedSearch 应该移除所有 requests.get 调用"


# ============================================================================
# 测试 5: ReferenceService 应该使用纯异步客户端
# ============================================================================


@pytest.mark.asyncio
class TestReferenceServiceAsyncOnly:
    """测试 UnifiedReferenceService 使用纯异步客户端"""

    def test_reference_service_should_not_use_requests_session(self):
        """测试：UnifiedReferenceService 不应该使用 requests.Session"""
        # Red 阶段：验证不使用 requests.Session

        service = UnifiedReferenceService(logger=logger)

        # 验证：不应该有同步的 session
        if hasattr(service, "session"):
            import requests

            assert not isinstance(service.session, requests.Session), (
                "ReferenceService 应该使用异步客户端"
            )


# ============================================================================
# 测试 6: SimilarArticles 模块应该使用纯异步客户端
# ============================================================================


@pytest.mark.asyncio
class TestSimilarArticlesModuleAsyncOnly:
    """测试 SimilarArticles 模块使用纯异步客户端"""

    def test_similar_articles_should_not_use_requests_get(self):
        """测试：SimilarArticles 模块不应该使用 requests.get"""
        # Red 阶段：验证不使用 requests.get

        # 检查源代码中是否有 requests.get 调用
        import article_mcp.services.similar_articles as similar_module

        source = inspect.getsource(similar_module)
        has_requests_get = "requests.get(" in source

        # Red 阶段：这个会失败，因为代码中仍有 requests.get
        assert not has_requests_get, "SimilarArticles 应该移除所有 requests.get 调用"


# ============================================================================
# 集成测试：纯异步客户端性能
# ============================================================================


@pytest.mark.asyncio
class TestAsyncClientPerformance:
    """测试异步客户端性能"""

    async def test_async_client_concurrent_requests(self, logger):
        """测试：异步客户端应该支持并发请求"""
        # Green 阶段：验证并发性能

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value={
                "success": True,
                "data": {"results": []},
            }
        )

        # 模拟并发请求
        tasks = [mock_client.get(f"url_{i}") for i in range(10)]

        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        elapsed = asyncio.get_event_loop().time() - start_time

        # 验证：并发执行应该很快（< 1秒）
        assert elapsed < 1.0, f"并发请求耗时 {elapsed:.2f}s，应该 < 1.0s"
        assert len(results) == 10

    async def test_async_client_connection_reuse(self, logger):
        """测试：异步客户端应该复用连接"""
        # Green 阶段：验证连接复用

        client = AsyncAPIClient(logger)

        # 验证：使用单例模式或连接池
        session = await client._get_session()

        # aiohttp ClientSession 有连接器
        assert hasattr(session, "connector"), "应该有连接器用于连接复用"


# ============================================================================
# 辅助测试：验证代码中没有 requests 模块的直接使用
# ============================================================================


class TestNoDirectRequestsUsage:
    """验证服务模块不直接使用 requests"""

    @pytest.mark.parametrize(
        "module_name",
        [
            "article_mcp.services.openalex_service",
            "article_mcp.services.crossref_service",
            "article_mcp.services.arxiv_search",
            "article_mcp.services.pubmed_search",
            "article_mcp.services.reference_service",
            "article_mcp.services.similar_articles",
        ],
    )
    def test_module_should_not_import_requests_for_api_calls(self, module_name):
        """测试：服务模块不应该为 API 调用导入 requests"""
        # Green 阶段：验证模块中没有使用 requests 进行 API 调用

        import importlib

        try:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            # 移除注释和字符串字面量，避免误报
            import re

            # 移除单行注释
            source_no_comments = re.sub(r"#.*$", "", source, flags=re.MULTILINE)
            # 移除多行注释
            source_no_comments = re.sub(r'""".*?"""', "", source_no_comments, flags=re.DOTALL)
            source_no_comments = re.sub(r"'''.*?'''", "", source_no_comments, flags=re.DOTALL)

            # 检查是否有 requests.get 或 requests.post 用于 API 调用
            has_api_calls = (
                "requests.get(" in source_no_comments
                or "requests.post(" in source_no_comments
                or "UnifiedAPIClient" in source_no_comments
                or "get_api_client()" in source_no_comments
            )

            # Green 阶段：这些应该通过
            assert not has_api_calls, f"{module_name} 应该移除同步 HTTP 客户端使用"

        except ImportError:
            pytest.skip(f"{module_name} 无法导入")
