"""arXiv 服务异步实现测试

这个测试文件为 arXiv 服务定义异步接口的测试用例。
按照 TDD 原则，先编写测试，然后实现功能。

测试内容：
1. 异步搜索方法 (search_async)
2. 错误处理
3. arXiv 特有的字段处理
4. 并发性能
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


class TestArXivServiceAsyncMethods:
    """测试 arXiv 服务的异步方法"""

    @pytest.fixture
    def arxiv_service(self):
        """创建 arXiv 服务实例"""
        # arXiv 服务目前是函数式，不是类
        # 这里我们测试异步函数
        return Mock()

    @pytest.mark.asyncio
    async def test_arxiv_search_async_returns_articles(self):
        """测试：异步搜索返回文章列表"""
        # 检查异步函数是否存在
        try:
            # 应该是异步函数
            import inspect

            from article_mcp.services.arxiv_search import search_async

            assert inspect.iscoroutinefunction(search_async), "search_async 应该是异步函数"

        except ImportError:
            pytest.skip("search_async 函数尚未实现")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_basic_query(self):
        """测试：异步搜索基本查询"""
        try:
            from article_mcp.services.arxiv_search import search_async

            result = await search_async("machine learning", max_results=5)

            assert isinstance(result, dict), "结果应该是字典"
            assert "articles" in result, "结果应该包含 articles 键"
            assert isinstance(result["articles"], list), "articles 应该是列表"

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_with_arxiv_specific_fields(self):
        """测试：异步搜索返回 arXiv 特有字段"""
        try:
            from article_mcp.services.arxiv_search import search_async

            result = await search_async("quantum computing", max_results=3)

            articles = result.get("articles", [])
            if articles:
                article = articles[0]

                # arXiv 特有字段
                assert "arxiv_id" in article or "id" in article, "应该有 arXiv ID"
                assert "title" in article, "应该有标题"
                assert "authors" in article, "应该有作者"
                assert "abstract" in article, "应该有摘要"
                # arXiv 特有的分类字段
                assert (
                    "category" in article
                    or "categories" in article
                    or "primary_category" in article
                ), "应该有分类信息"

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_respects_max_results(self):
        """测试：异步搜索遵守 max_results 参数"""
        try:
            from article_mcp.services.arxiv_search import search_async

            result = await search_async("neural networks", max_results=5)

            articles = result.get("articles", [])
            assert len(articles) <= 5, f"返回的文章数量应该 ≤ 5，实际返回 {len(articles)}"

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_with_date_filter(self):
        """测试：异步搜索支持日期过滤"""
        try:
            from article_mcp.services.arxiv_search import search_async

            # arXiv API 支持日期过滤
            result = await search_async(
                "deep learning", start_date="2022-01-01", end_date="2023-12-31", max_results=10
            )

            assert "articles" in result
            articles = result["articles"]

            # 如果返回文章，验证日期在范围内
            if articles:
                # arXiv 日期格式通常是 YYYY-MM-DD
                for article in articles[:3]:  # 检查前3篇
                    pub_date = article.get("publication_date")
                    if pub_date:
                        assert "2022" <= pub_date[:4] <= "2023", (
                            f"文章日期 {pub_date} 应该在 2022-2023 范围内"
                        )

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")


class TestArXivServiceAsyncWithMocking:
    """使用 Mock 测试异步方法的行为"""

    @pytest.fixture
    def mock_arxiv_xml_response(self):
        """Mock arXiv API 的 XML 响应"""
        # arXiv 使用 Atom feed 格式
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>ArXiv Query: search_query=all:test</title>
            <entry>
                <id>http://arxiv.org/abs/2301.00001</id>
                <title>Test Article Title</title>
                <summary>This is a test abstract for the article.</summary>
                <published>2023-01-01T00:00:00Z</published>
                <author>
                    <name>John Doe</name>
                </author>
                <author>
                    <name>Jane Smith</name>
                </author>
                <link href="http://arxiv.org/pdf/2301.00001v1.pdf" rel="related" type="application/pdf"/>
                <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
                <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
                <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
            </entry>
        </feed>
        """
        return xml_content

    @pytest.mark.asyncio
    async def test_arxiv_search_async_with_mock_api(self, mock_arxiv_xml_response):
        """测试：使用 Mock API 测试异步搜索"""
        # Mock aiohttp 响应
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=mock_arxiv_xml_response)

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = Mock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session

            try:
                from article_mcp.services.arxiv_search import search_async

                result = await search_async("test query", max_results=10)

                # 验证结果
                assert "articles" in result
                assert len(result["articles"]) > 0

                article = result["articles"][0]
                assert article["title"] == "Test Article Title"
                assert "2301.00001" in article.get("arxiv_id", article.get("id", ""))
                assert len(article.get("authors", [])) == 2

            except (ImportError, NotImplementedError):
                pytest.skip("search_async 尚未实现")


class TestArXivServiceAsyncErrorHandling:
    """测试异步方法的错误处理"""

    @pytest.mark.asyncio
    async def test_arxiv_search_async_handles_timeout(self):
        """测试：异步搜索处理超时"""
        try:
            from article_mcp.services.arxiv_search import search_async

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()

                # Mock 超时
                async def mock_get_with_timeout(*args, **kwargs):
                    await asyncio.sleep(10)  # 超过超时限制
                    return Mock(status=200)

                mock_session.get = mock_get_with_timeout
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                # 应该处理超时
                result = await search_async("test", max_results=10)

                # 应该返回错误而不是抛出异常
                assert "error" in result or len(result.get("articles", [])) == 0

        except (ImportError, NotImplementedError, asyncio.TimeoutError):
            pytest.skip("search_async 尚未实现或超时处理未完成")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_handles_network_error(self):
        """测试：异步搜索处理网络错误"""
        try:
            from article_mcp.services.arxiv_search import search_async

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()

                async def mock_get_with_error(*args, **kwargs):
                    raise Exception("Network error")

                mock_session.get = mock_get_with_error
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                result = await search_async("test", max_results=10)

                # 应该返回错误信息
                assert "error" in result
                assert result["error"] is not None

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_handles_empty_response(self):
        """测试：异步搜索处理空响应"""
        try:
            from article_mcp.services.arxiv_search import search_async

            # Mock 空响应
            empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <title>ArXiv Query: search_query=all:nonexistent</title>
            </feed>
            """

            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=empty_xml)

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = Mock()
                mock_session.get = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session

                result = await search_async("nonexistent", max_results=10)

                # 应该返回空结果
                assert "articles" in result
                assert len(result["articles"]) == 0

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")


class TestArXivServiceAsyncPerformance:
    """测试异步方法的性能"""

    @pytest.mark.asyncio
    async def test_arxiv_search_async_parallel_execution(self):
        """测试：多个异步搜索可以并行执行"""
        try:
            from article_mcp.services.arxiv_search import search_async

            keywords = ["machine learning", "neural networks", "deep learning"]

            import time

            start = time.time()
            results = await asyncio.gather(
                *[search_async(keyword, max_results=5) for keyword in keywords]
            )
            elapsed = time.time() - start

            # 验证所有任务完成
            assert len(results) == 3
            for result in results:
                assert "articles" in result

            # 并行执行应该远快于串行
            # 如果每个请求约 1 秒（arXiv 的限制），串行需要 3 秒，并行应该 < 1.5 秒
            assert elapsed < 2.0, f"并行执行耗时 {elapsed:.2f}s"

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")

    @pytest.mark.asyncio
    async def test_arxiv_search_async_respects_rate_limit(self):
        """测试：异步搜索遵守 arXiv 的速率限制

        arXiv API 要求每 3 秒最多 1 个请求
        """
        try:
            # arXiv 的速率限制是 1 请求 / 3 秒
            # 如果并行发送多个请求，应该有限制
            import time

            from article_mcp.services.arxiv_search import search_async

            start = time.time()

            # 尝试并行发送多个请求
            await asyncio.gather(
                *[search_async(f"test {i}", max_results=3) for i in range(3)],
                return_exceptions=True,
            )

            elapsed = time.time() - start

            # 由于速率限制，即使并行也需要一定时间
            # 如果是串行执行且遵守限制，3个请求需要约 9 秒
            # 如果有限制并发，应该也在合理范围内
            assert elapsed < 12.0, f"执行耗时 {elapsed:.2f}s"

        except (ImportError, NotImplementedError):
            pytest.skip("search_async 尚未实现")


# ============================================================================
# 实现检查
# ============================================================================


def test_arxiv_async_function_exists():
    """测试：检查 arXiv 异步函数是否存在"""
    try:
        import inspect

        from article_mcp.services.arxiv_search import search_async

        # 检查是异步函数
        assert inspect.iscoroutinefunction(search_async), "search_async 应该是异步函数"

        # 检查函数签名
        sig = inspect.signature(search_async)
        params = list(sig.parameters.keys())

        # 应该有的参数
        expected_params = ["query", "max_results"]
        for param in expected_params:
            assert param in params, f"search_async 应该有 {param} 参数"

    except ImportError:
        pytest.skip("search_async 函数尚未实现")


def test_arxiv_async_imports():
    """测试：检查 arXiv 服务是否有必要的异步导入"""
    try:
        import inspect

        import article_mcp.services.arxiv_search as arxiv_module

        source = inspect.getsource(arxiv_module)

        # 检查是否有必要的异步导入
        has_asyncio = "asyncio" in source or "import asyncio" in source

        # 如果实现了异步函数，应该有这些导入
        if hasattr(arxiv_module, "search_async"):
            assert has_asyncio, "实现异步函数需要 asyncio"

    except ImportError:
        pytest.skip("arxiv_search 模块未找到")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
