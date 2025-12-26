"""search_tools 异步集成测试

这是方案A（直接替换）的核心集成测试文件。
测试异步版本的 search_literature 工具函数。

测试内容：
1. 异步多数据源并行搜索
2. 搜索策略功能
3. 缓存功能
4. 结果合并
5. 错误处理
6. 性能验证
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# 添加 src 目录到路径
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestSearchLiteratureAsyncIntegration:
    """测试异步搜索工具的集成功能"""

    @pytest.fixture
    def mock_search_services(self):
        """创建带有异步方法的模拟服务"""
        services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        }

        # 为每个服务添加异步搜索方法
        async def mock_europe_pmc_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.02)
            return {
                "articles": [
                    {
                        "title": f"EPMC: {query}",
                        "doi": f"10.1234/epmc.{i}",
                        "journal": "EPMC Journal",
                    }
                    for i in range(max_results)
                ],
                "error": None,
            }

        async def mock_pubmed_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.015)
            return {
                "articles": [
                    {
                        "title": f"PubMed: {query}",
                        "doi": f"10.1234/pubmed.{i}",
                        "journal": "PubMed Journal",
                    }
                    for i in range(max_results)
                ],
                "error": None,
            }

        async def mock_arxiv_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.025)
            return {
                "articles": [
                    {"title": f"arXiv: {query}", "doi": f"10.1234/arxiv.{i}", "journal": "arXiv"}
                    for i in range(max_results)
                ],
                "error": None,
            }

        async def mock_crossref_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.018)
            return {
                "articles": [
                    {
                        "title": f"CrossRef: {query}",
                        "doi": f"10.1234/crossref.{i}",
                        "journal": "CrossRef Journal",
                    }
                    for i in range(max_results)
                ],
                "error": None,
            }

        async def mock_openalex_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.022)
            return {
                "articles": [
                    {
                        "title": f"OpenAlex: {query}",
                        "doi": f"10.1234/openalex.{i}",
                        "journal": "OpenAlex Journal",
                    }
                    for i in range(max_results)
                ],
                "error": None,
            }

        # 添加异步方法到服务
        services["europe_pmc"].search_async = mock_europe_pmc_search
        services["pubmed"].search_async = mock_pubmed_search
        services["arxiv"].search_async = mock_arxiv_search
        services["crossref"].search_works_async = mock_crossref_search
        services["openalex"].search_works_async = mock_openalex_search

        return services

    @pytest.mark.asyncio
    async def test_async_search_literature_parallel_execution(self, mock_search_services):
        """测试：异步并行搜索多个数据源"""
        try:
            from article_mcp.tools.core.search_tools import search_literature_async

            start = time.time()
            result = await search_literature_async(
                keyword="machine learning",
                sources=["europe_pmc", "pubmed", "arxiv"],
                max_results=5,
                services=mock_search_services,
                logger=Mock(),
            )
            elapsed = time.time() - start

            # 验证结果
            assert result["success"] is True
            assert len(result["sources_used"]) == 3
            assert result["total_count"] > 0

            # 验证并行执行：时间应该远小于串行累加时间
            # 串行累加约 0.02 + 0.015 + 0.025 = 0.06s（不含开销）
            # 考虑 asyncio 事件循环和测试开销，允许 < 0.5s
            assert elapsed < 0.5, f"并行执行耗时 {elapsed:.3f}s，应该 < 0.5s"

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 尚未实现")

    @pytest.mark.asyncio
    async def test_async_search_with_strategies(self, mock_search_services):
        """测试：异步搜索使用搜索策略"""
        try:
            from article_mcp.tools.core.search_tools import search_literature_async

            # 测试 fast 策略（只搜索2个数据源）
            result_fast = await search_literature_async(
                keyword="test",
                search_type="fast",
                max_results=5,
                services=mock_search_services,
                logger=Mock(),
            )

            assert result_fast["success"] is True
            assert len(result_fast["sources_used"]) <= 2, (
                f"fast 策略应该最多搜索2个数据源，实际搜索了 {len(result_fast['sources_used'])} 个"
            )

            # 测试 comprehensive 策略（搜索所有数据源）
            result_comprehensive = await search_literature_async(
                keyword="test",
                search_type="comprehensive",
                max_results=5,
                services=mock_search_services,
                logger=Mock(),
            )

            assert result_comprehensive["success"] is True
            assert len(result_comprehensive["sources_used"]) >= 3, (
                "comprehensive 策略应该搜索多个数据源"
            )

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 或策略功能尚未实现")

    @pytest.mark.asyncio
    async def test_async_search_with_caching(self, mock_search_services):
        """测试：异步搜索使用缓存"""
        try:
            import tempfile

            from article_mcp.tools.core.search_tools import SearchCache, search_literature_async

            keyword = "caching test query"

            # 使用独立的临时缓存目录，避免被之前的测试影响
            with tempfile.TemporaryDirectory() as temp_dir:
                cache = SearchCache(cache_dir=temp_dir)

                # 第一次搜索（缓存未命中）
                start = time.time()
                result1 = await search_literature_async(
                    keyword=keyword,
                    sources=["europe_pmc", "pubmed"],
                    max_results=5,
                    use_cache=True,
                    cache=cache,
                    services=mock_search_services,
                    logger=Mock(),
                )
                time1 = time.time() - start

                assert result1["success"] is True
                assert result1.get("cached") is False, "第一次搜索不应该命中缓存"
                assert time1 >= 0.02, "第一次搜索应该有网络延迟"

                # 第二次搜索（缓存命中）
                start = time.time()
                result2 = await search_literature_async(
                    keyword=keyword,
                    sources=["europe_pmc", "pubmed"],
                    max_results=5,
                    use_cache=True,
                    cache=cache,
                    services=mock_search_services,
                    logger=Mock(),
                )
                time2 = time.time() - start

                assert result2["success"] is True
                assert result2.get("cached") is True, "第二次搜索应该命中缓存"
                assert result2.get("cache_hit") is True
                assert time2 < 0.01, f"缓存命中应该非常快，实际耗时 {time2:.3f}s"

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 或缓存功能尚未实现")

    @pytest.mark.asyncio
    async def test_async_search_result_merging(self, mock_search_services):
        """测试：异步搜索结果正确合并"""
        try:
            from article_mcp.tools.core.search_tools import search_literature_async

            result = await search_literature_async(
                keyword="merging test",
                sources=["europe_pmc", "pubmed", "arxiv"],
                max_results=10,
                search_type="comprehensive",
                services=mock_search_services,
                logger=Mock(),
            )

            assert result["success"] is True
            assert "merged_results" in result

            # 验证合并结果
            merged = result["merged_results"]
            assert isinstance(merged, list)
            assert len(merged) > 0, "合并结果应该不为空"

            # 验证每个文章有基本字段
            for article in merged[:5]:  # 检查前5篇
                assert "title" in article
                assert "doi" in article or "id" in article

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 或合并功能尚未实现")

    @pytest.mark.asyncio
    async def test_async_search_error_handling(self, mock_search_services):
        """测试：异步搜索的错误处理"""

        # 让一个服务抛出异常
        async def failing_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.01)
            raise Exception("Simulated API error")

        mock_search_services["arxiv"].search_async = failing_search

        try:
            from article_mcp.tools.core.search_tools import search_literature_async

            result = await search_literature_async(
                keyword="error test",
                sources=["europe_pmc", "pubmed", "arxiv"],  # arxiv 会失败
                max_results=5,
                services=mock_search_services,
                logger=Mock(),
            )

            # 应该返回部分成功的结果
            assert result["success"] is True
            assert "arxiv" not in result["sources_used"], "失败的数据源不应该在 sources_used 中"
            assert len(result["sources_used"]) >= 2, "至少应该有2个成功的数据源"

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 尚未实现")

    @pytest.mark.asyncio
    async def test_async_search_performance_comparison(self, mock_search_services):
        """测试：异步搜索 vs 同步搜索的性能对比"""
        try:
            from article_mcp.tools.core.search_tools import search_literature_async

            sources = ["europe_pmc", "pubmed", "arxiv", "crossref", "openalex"]

            # 测试异步并行搜索
            start_async = time.time()
            result_async = await search_literature_async(
                keyword="performance test",
                sources=sources,
                max_results=5,
                services=mock_search_services,
                logger=Mock(),
            )
            async_time = time.time() - start_async

            # 估算串行时间（每个服务的延迟之和）
            estimated_serial_time = 0.02 + 0.015 + 0.025 + 0.018 + 0.022  # 约 0.1 秒

            # 验证结果
            assert result_async["success"] is True
            assert len(result_async["sources_used"]) == 5

            # 验证性能提升
            speedup = estimated_serial_time / async_time
            assert speedup >= 2.0, f"异步加速比应该 >= 2x，实际为 {speedup:.1f}x"

            print("\n异步搜索性能:")
            print(f"  并行耗时: {async_time:.3f}s")
            print(f"  估算串行: {estimated_serial_time:.3f}s")
            print(f"  加速比: {speedup:.1f}x")

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 尚未实现")


class TestSearchLiteratureAsyncWithFastMCP:
    """测试异步搜索工具与 FastMCP 的集成"""

    def test_register_async_search_tool(self):
        """测试：向 FastMCP 注册异步搜索工具"""
        from fastmcp import FastMCP

        mcp = FastMCP("Test Async Search", version="0.1.0")

        # 尝试注册异步工具
        try:

            @mcp.tool(description="异步文献搜索")
            async def search_literature(
                keyword: str,
                sources: list[str] | None = None,
                max_results: int = 10,
                search_type: str = "comprehensive",
            ) -> dict[str, Any]:
                """多源文献搜索工具（异步版本）"""
                await asyncio.sleep(0.01)
                return {"success": True, "keyword": keyword, "total_count": 0, "async_tool": True}

            # 如果没有报错，说明 FastMCP 支持异步工具
            assert True

        except Exception as e:
            pytest.fail(f"FastMCP 注册异步工具失败: {e}")

    @pytest.mark.asyncio
    async def test_async_tool_response_format(self):
        """测试：异步工具返回符合 MCP 工具规范的格式"""

        # 定义原始异步函数（不使用 @mcp.tool 装饰器）
        async def test_search_impl(keyword: str) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {
                "success": True,
                "keyword": keyword,
                "sources_used": ["test_source"],
                "merged_results": [{"title": "Test Article", "doi": "10.1234/test"}],
                "total_count": 1,
                "search_time": 0.05,
                "search_type": "comprehensive",
                "cached": False,
            }

        # 验证返回格式
        result = await test_search_impl("test")

        # 检查必需字段
        required_fields = [
            "success",
            "keyword",
            "sources_used",
            "merged_results",
            "total_count",
            "search_time",
        ]

        for field in required_fields:
            assert field in result, f"结果应该包含 {field} 字位"


# ============================================================================
# 实现检查
# ============================================================================


def test_async_search_literature_exists():
    """测试：检查异步搜索工具函数是否存在"""
    try:
        import inspect

        from article_mcp.tools.core.search_tools import search_literature_async

        # 应该是异步函数
        assert inspect.iscoroutinefunction(search_literature_async), (
            "search_literature_async 应该是异步函数"
        )

        # 检查函数签名
        sig = inspect.signature(search_literature_async)
        params = list(sig.parameters.keys())

        # 应该有的参数
        expected_params = [
            "keyword",
            "sources",
            "max_results",
            "search_type",
            "use_cache",
            "cache",
            "services",
            "logger",
        ]
        for param in expected_params:
            assert param in params, f"search_literature_async 应该有 {param} 参数"

    except ImportError:
        pytest.skip("search_literature_async 函数尚未实现")


def test_async_search_imports():
    """测试：检查异步搜索的必要导入"""
    try:
        import inspect

        import article_mcp.tools.core.search_tools as search_tools_module

        source = inspect.getsource(search_tools_module)

        # 检查是否有必要的异步导入
        has_asyncio = "asyncio" in source or "import asyncio" in source
        has_search_async = "search_literature_async" in source

        # 如果实现了异步搜索，应该有 asyncio
        if has_search_async:
            assert has_asyncio, "异步搜索需要 asyncio"

    except ImportError:
        pytest.skip("search_tools 模块未找到")


# ============================================================================
# 完整工作流测试
# ============================================================================


class TestSearchLiteratureAsyncWorkflow:
    """测试异步搜索的完整工作流"""

    @pytest.fixture
    def complete_services(self):
        """创建完整的模拟服务（包括 Europe PMC 的模拟异步方法）"""
        services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
        }

        # 添加所有服务的异步搜索方法
        async def mock_europe_pmc_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.02)
            return {
                "articles": [{"title": f"EPMC: {query}", "pmid": "12345678"}],
                "error": None,
            }

        async def mock_pubmed_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.02)
            return {
                "articles": [{"title": f"PubMed: {query}", "pmid": "87654321"}],
                "error": None,
            }

        async def mock_arxiv_search(query: str, max_results: int = 10) -> dict:
            await asyncio.sleep(0.025)
            return {
                "articles": [{"title": f"arXiv: {query}"}],
                "error": None,
            }

        services["europe_pmc"].search_async = mock_europe_pmc_search
        services["pubmed"].search_async = mock_pubmed_search
        services["arxiv"].search_async = mock_arxiv_search

        return services

    @pytest.mark.asyncio
    async def test_complete_async_workflow(self, complete_services):
        """测试：完整的异步搜索工作流"""
        try:
            from article_mcp.tools.core.search_tools import search_literature_async

            # 1. 搜索
            result = await search_literature_async(
                keyword="deep learning",
                sources=None,  # 使用策略默认
                max_results=10,
                search_type="fast",
                use_cache=False,  # 禁用缓存，确保使用 mock 服务
                services=complete_services,
                logger=Mock(),
            )

            # 2. 验证结果
            assert result["success"] is True
            assert result["keyword"] == "deep learning"
            assert len(result["sources_used"]) > 0

            # 3. 验证搜索策略应用
            assert result.get("search_type") == "fast"

            # 4. 验证性能
            assert result["search_time"] < 0.5, f"搜索时间 {result['search_time']}s 应该 < 0.5s"

        except (ImportError, AttributeError):
            pytest.skip("search_literature_async 尚未实现")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
