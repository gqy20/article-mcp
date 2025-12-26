"""测试工具函数使用闭包捕获服务（不使用全局变量）

这是 TDD 第一阶段：消除全局变量状态管理问题
验证工具函数能够通过闭包捕获服务实例，而不是依赖全局变量。
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest


class TestClosureServicesSearchTools:
    """测试 search_tools 使用闭包捕获服务"""

    @pytest.mark.asyncio
    async def test_search_literature_async_uses_closure_services(self):
        """测试：search_literature_async 函数通过闭包参数使用服务，不依赖全局变量"""

        # Arrange: 创建模拟服务
        async def mock_search(query, max_results=10):
            await asyncio.sleep(0.01)
            return {
                "articles": [
                    {"title": f"Test: {query}", "doi": f"10.1234/test.{i}"} for i in range(3)
                ],
                "error": None,
            }

        mock_services = {
            "europe_pmc": Mock(search_async=mock_search),
            "pubmed": Mock(search_async=mock_search),
        }

        # Act: 调用函数并传入 services 参数
        from article_mcp.tools.core.search_tools import search_literature_async

        result = await search_literature_async(
            keyword="test query",
            sources=["europe_pmc", "pubmed"],
            max_results=5,
            services=mock_services,  # 通过参数传入，不使用全局变量
            logger=Mock(),
        )

        # Assert: 验证结果
        assert result["success"] is True
        assert result["keyword"] == "test query"
        assert len(result["merged_results"]) > 0

    def test_search_literature_async_fails_without_services(self):
        """测试：search_literature_async 在没有 services 参数时应该返回错误"""
        # Arrange: 不提供 services 参数，让函数使用全局变量
        # （但全局变量未初始化，应该返回错误）

        # Act: 调用函数不传入 services
        # 由于全局变量未初始化，应该抛出异常或返回错误
        # 当前实现会抛出 ToolError
        import asyncio

        from article_mcp.tools.core.search_tools import search_literature_async

        async def call_without_services():
            try:
                result = await search_literature_async(
                    keyword="test",
                    services=None,  # 不传入 services
                    logger=Mock(),
                )
                return result
            except Exception as e:
                return {"error": str(e)}

        result = asyncio.run(call_without_services())

        # Assert: 应该返回错误
        assert "error" in result or result.get("success") is False


class TestClosureServicesArticleTools:
    """测试 article_tools 使用闭包捕获服务"""

    @pytest.mark.asyncio
    async def test_get_article_details_async_uses_closure_services(self):
        """测试：get_article_details_async 通过闭包参数使用服务"""

        # Arrange: 创建模拟服务
        def mock_fetch(pmcid, id_type="pmcid"):
            return {
                "article": {
                    "pmcid": pmcid,
                    "title": "Test Article",
                },
                "error": None,
            }

        def mock_fulltext(pmcid, sections=None):
            return {
                "fulltext_xml": "<xml>content</xml>",
                "fulltext_markdown": "# content",
                "fulltext_text": "content",
                "fulltext_available": True,
            }

        mock_services = {
            "europe_pmc": Mock(fetch=mock_fetch),
            "pubmed": Mock(get_pmc_fulltext_html=mock_fulltext),
        }

        # Act: 调用函数并传入 services 参数
        from article_mcp.tools.core.article_tools import get_article_details_async

        result = await get_article_details_async(
            pmcid="PMC1234567",
            services=mock_services,  # 通过参数传入
            logger=Mock(),
        )

        # Assert: 验证结果
        assert result["successful"] == 1
        assert result["total"] == 1
        assert len(result["articles"]) > 0
        assert result["articles"][0]["fulltext"]["fulltext_available"] is True


class TestClosureServicesReferenceTools:
    """测试 reference_tools 使用闭包捕获服务"""

    @pytest.mark.asyncio
    async def test_get_references_async_uses_closure_services(self):
        """测试：get_references_async 通过闭包参数使用服务"""

        # Arrange: 创建模拟服务 - reference_tools.py 调用 reference 服务
        async def mock_get_refs_by_doi(identifier):
            await asyncio.sleep(0.01)
            return {
                "references": [{"title": f"Ref {i}", "doi": f"10.1234/ref.{i}"} for i in range(5)],
                "success": True,
            }

        mock_reference_service = Mock(get_references_by_doi_async=mock_get_refs_by_doi)
        mock_services = {
            "reference": mock_reference_service,
        }

        # Act: 调用函数并传入 services 参数
        from article_mcp.tools.core.reference_tools import get_references_async

        result = await get_references_async(
            identifier="10.1234/test",
            id_type="doi",
            sources=["europe_pmc"],
            services=mock_services,
            logger=Mock(),
        )

        # Assert: 验证结果
        assert result["success"] is True
        assert len(result["merged_references"]) > 0


class TestClosureServicesRelationTools:
    """测试 relation_tools 使用闭包捕获服务"""

    @pytest.mark.asyncio
    async def test_single_literature_relations_uses_closure_services(self):
        """测试：_single_literature_relations 通过闭包参数使用服务"""

        # Arrange: 创建模拟服务
        async def mock_get_refs(ident, id_type, max_results, sources, logger):
            await asyncio.sleep(0.01)
            return [{"title": f"Ref {i}", "doi": f"10.1234/ref.{i}"} for i in range(3)]

        mock_services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
        }

        # Act: 调用函数并传入 services 参数
        from article_mcp.tools.core.relation_tools import _single_literature_relations

        result = await _single_literature_relations(
            identifier="10.1234/test",
            id_type="doi",
            relation_types=["references"],
            max_results=20,
            sources=["europe_pmc"],
            services=mock_services,
            logger=Mock(),
        )

        # Assert: 验证结果
        assert result["success"] is True
        assert "relations" in result
        assert "references" in result["relations"]


class TestClosureServicesQualityTools:
    """测试 quality_tools 使用闭包捕获服务"""

    @pytest.mark.asyncio
    async def test_single_journal_quality_uses_closure_services(self):
        """测试：_single_journal_quality 通过闭包参数使用服务"""

        # Arrange: 创建模拟服务
        async def mock_get_quality(journal_name):
            await asyncio.sleep(0.01)
            return {
                "journal": journal_name,
                "impact_factor": 5.0,
                "quartile": "Q1",
            }

        mock_services = {
            "pubmed": Mock(get_journal_quality_async=mock_get_quality),
        }

        # Act: 调用函数并传入 services 参数
        from article_mcp.tools.core.quality_tools import _single_journal_quality

        result = await _single_journal_quality(
            journal_name="Nature",
            include_metrics=["impact_factor", "quartile"],
            use_cache=False,
            services=mock_services,
            logger=Mock(),
        )

        # Assert: 验证结果
        assert result["success"] is True
        assert result["journal_name"] == "Nature"
        assert "quality_metrics" in result
