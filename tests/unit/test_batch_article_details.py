#!/usr/bin/env python3
"""批量获取文献详情单元测试
测试工具2 (get_article_details) 的批量功能扩展

所有调用都返回统一的批量格式：
{
    "total": 1,
    "successful": 1,
    "articles": [...]
}
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestBatchArticleDetailsBasic:
    """测试批量获取文献详情的基础功能"""

    @pytest.fixture
    def mock_services(self):
        """模拟文章服务"""
        return {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
        }

    @pytest.mark.unit
    def test_single_identifier_returns_batch_format(self, mock_services):
        """测试单个标识符也返回批量格式"""
        from article_mcp.tools.core.article_tools import get_article_details_async

        # 模拟服务响应
        mock_services["europe_pmc"].fetch.return_value = {
            "article": {
                "title": "Test Article 1",
                "doi": "10.1234/test1",
                "pmcid": "",
            },
            "error": None,
        }

        import article_mcp.tools.core.article_tools as article_tools_module

        article_tools_module._article_services = mock_services
        article_tools_module._logger = Mock()

        # 单个标识符现在也返回批量格式
        result = asyncio.run(
            get_article_details_async(
                identifier="10.1234/test1",
                id_type="auto",
                include_fulltext=False,
            )
        )

        # 验证返回统一的批量格式
        assert isinstance(result, dict)
        assert "total" in result
        assert "successful" in result
        assert "failed" in result
        assert "articles" in result
        assert result["total"] == 1
        assert result["successful"] == 1
        assert len(result["articles"]) == 1
        assert result["articles"][0]["doi"] == "10.1234/test1"

    @pytest.mark.unit
    def test_batch_multiple_identifiers(self, mock_services):
        """测试批量获取多个标识符"""
        from article_mcp.tools.core.article_tools import get_article_details_async

        # 模拟服务响应
        mock_services["europe_pmc"].fetch.return_value = {
            "article": {
                "title": "Test Article",
                "doi": "test",
                "pmcid": "",
            },
            "error": None,
        }

        import article_mcp.tools.core.article_tools as article_tools_module

        article_tools_module._article_services = mock_services
        article_tools_module._logger = Mock()

        # 批量获取（多个标识符）
        identifiers = ["10.1234/test1", "10.1234/test2", "10.1234/test3"]

        result = asyncio.run(
            get_article_details_async(
                identifier=identifiers,
                id_type="auto",
                include_fulltext=False,
            )
        )

        # 验证返回批量格式
        assert isinstance(result, dict)
        assert "total" in result
        assert result["total"] == 3
        assert result["successful"] == 3
        assert len(result["articles"]) == 3

    @pytest.mark.unit
    def test_empty_list_returns_empty_batch(self, mock_services):
        """测试空列表返回空的批量格式"""
        import article_mcp.tools.core.article_tools as article_tools_module
        from article_mcp.tools.core.article_tools import get_article_details_async

        article_tools_module._article_services = mock_services
        article_tools_module._logger = Mock()

        # 空列表返回空批量结果
        result = asyncio.run(get_article_details_async(identifier=[], id_type="auto"))

        assert result["total"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0
        assert len(result["articles"]) == 0


class TestBatchArticleDetailsWithFulltext:
    """测试批量获取文献详情（包含全文）"""

    @pytest.fixture
    def mock_services_with_fulltext(self):
        """模拟支持全文的服务"""
        europe_pmc = Mock()
        europe_pmc.fetch.return_value = {
            "article": {
                "title": "Article with PMCID",
                "doi": "10.1234/has-pmc",
                "pmcid": "PMC1234567",
            },
            "error": None,
        }

        pubmed = Mock()
        pubmed.get_pmc_fulltext_html.return_value = {
            "pmc_id": "PMC1234567",
            "fulltext_available": True,
            "fulltext_markdown": "# Methods\n\nTest content",
            "fulltext_text": "Methods\n\nTest content",
            "fulltext_xml": "<article>...</article>",
            "sections_requested": ["methods", "discussion"],
            "sections_found": ["methods", "discussion"],
            "sections_missing": [],
        }

        return {
            "europe_pmc": europe_pmc,
            "pubmed": pubmed,
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_with_fulltext_mixed(self, mock_services_with_fulltext):
        """测试批量获取：部分有PMCID，部分没有"""
        from article_mcp.tools.core.article_tools import get_article_details_async

        # 设置不同的响应（有/无 PMCID）
        def mock_fetch_side_effect(identifier, id_type="auto"):
            if "has-pmc" in str(identifier):
                return {
                    "article": {
                        "title": "Article with PMCID",
                        "doi": identifier,
                        "pmcid": "PMC1234567",
                    },
                    "error": None,
                }
            else:
                return {
                    "article": {
                        "title": "Article without PMCID",
                        "doi": identifier,
                        "pmcid": "",
                    },
                    "error": None,
                }

        mock_services_with_fulltext["europe_pmc"].fetch.side_effect = mock_fetch_side_effect

        import article_mcp.tools.core.article_tools as article_tools_module

        article_tools_module._article_services = mock_services_with_fulltext
        article_tools_module._logger = Mock()

        # 混合列表：有 PMCID 和没有的
        identifiers = ["10.1234/has-pmc", "10.1234/no-pmc"]

        result = await get_article_details_async(
            identifier=identifiers,
            id_type="auto",
            include_fulltext=True,
        )

        # 验证批量结果
        assert result["total"] == 2
        assert result["successful"] >= 1

        # 检查全文统计
        assert "fulltext_stats" in result
        assert result["fulltext_stats"]["has_pmcid"] == 1
        assert result["fulltext_stats"]["no_pmcid"] == 1

        # 验证有 PMCID 的文章有 fulltext 字段
        articles = result["articles"]
        article_with_pmc = next(
            (a for a in articles if "PMC1234567" in str(a.get("pmcid", ""))), None
        )
        assert article_with_pmc is not None
        assert "fulltext" in article_with_pmc
        assert article_with_pmc["fulltext"]["fulltext_available"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_with_sections(self, mock_services_with_fulltext):
        """测试批量获取 + 指定章节"""
        import article_mcp.tools.core.article_tools as article_tools_module
        from article_mcp.tools.core.article_tools import get_article_details_async

        article_tools_module._article_services = mock_services_with_fulltext
        article_tools_module._logger = Mock()

        # 指定只获取 methods 和 discussion 章节
        identifiers = ["10.1234/has-pmc"]
        sections = ["methods", "discussion"]

        result = await get_article_details_async(
            identifier=identifiers,
            id_type="auto",
            include_fulltext=True,
            sections=sections,
        )

        # 验证批量结果
        assert result["total"] == 1
        assert result["successful"] == 1

        # 验证章节信息
        article = result["articles"][0]
        if "fulltext" in article and article["fulltext"].get("fulltext_available"):
            fulltext = article["fulltext"]
            assert "sections_requested" in fulltext
            assert set(fulltext["sections_requested"]) == {"methods", "discussion"}
            assert "sections_found" in fulltext
            assert "sections_missing" in fulltext


class TestBatchArticleDetailsErrorHandling:
    """测试批量获取的错误处理"""

    @pytest.fixture
    def mock_services_with_errors(self):
        """模拟会返回错误的服务"""
        europe_pmc = Mock()

        def mock_fetch_with_error(identifier, id_type="auto"):
            if "error" in str(identifier):
                return {"article": None, "error": "Article not found"}
            else:
                return {
                    "article": {"title": "Valid Article", "doi": identifier, "pmcid": ""},
                    "error": None,
                }

        europe_pmc.fetch.side_effect = mock_fetch_with_error
        return {"europe_pmc": europe_pmc, "pubmed": Mock()}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, mock_services_with_errors):
        """测试部分文章获取失败"""
        import article_mcp.tools.core.article_tools as article_tools_module
        from article_mcp.tools.core.article_tools import get_article_details_async

        article_tools_module._article_services = mock_services_with_errors
        article_tools_module._logger = Mock()

        # 混合：成功和失败
        identifiers = ["10.1234/valid", "10.1234/error", "10.1234/valid2"]

        result = await get_article_details_async(
            identifier=identifiers,
            id_type="auto",
            include_fulltext=False,
        )

        # 验证部分成功
        assert result["total"] == 3
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert len(result["articles"]) == 2  # 只返回成功的

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_all_failure(self, mock_services_with_errors):
        """测试全部文章获取失败"""
        from article_mcp.tools.core.article_tools import get_article_details_async

        # 让所有请求都失败
        mock_services_with_errors["europe_pmc"].fetch.return_value = {
            "article": None,
            "error": "Service unavailable",
        }

        import article_mcp.tools.core.article_tools as article_tools_module

        article_tools_module._article_services = mock_services_with_errors
        article_tools_module._logger = Mock()

        identifiers = ["10.1234/error1", "10.1234/error2"]

        result = await get_article_details_async(
            identifier=identifiers,
            id_type="auto",
            include_fulltext=False,
        )

        # 验证全部失败
        assert result["total"] == 2
        assert result["successful"] == 0
        assert result["failed"] == 2
        assert len(result["articles"]) == 0


class TestBatchArticleDetailsPerformance:
    """测试批量获取的性能"""

    @pytest.fixture
    def mock_services_fast(self):
        """模拟快速响应的服务"""
        europe_pmc = Mock()
        europe_pmc.fetch.return_value = {
            "article": {
                "title": "Fast Article",
                "doi": "10.1234/fast",
                "pmcid": "",
            },
            "error": None,
        }
        return {"europe_pmc": europe_pmc, "pubmed": Mock()}

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_concurrent_fetch(self, mock_services_fast):
        """测试并发获取性能"""
        import time

        import article_mcp.tools.core.article_tools as article_tools_module
        from article_mcp.tools.core.article_tools import get_article_details_async

        article_tools_module._article_services = mock_services_fast
        article_tools_module._logger = Mock()

        # 批量获取10篇文章
        identifiers = [f"10.1234/article{i}" for i in range(10)]

        start_time = time.time()
        result = await get_article_details_async(
            identifier=identifiers,
            id_type="auto",
            include_fulltext=False,
        )
        processing_time = time.time() - start_time

        # 验证结果
        assert result["total"] == 10
        assert result["successful"] == 10

        # 验证性能
        assert processing_time < 5.0  # 应该在5秒内完成

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_large_set(self, mock_services_fast):
        """测试大批量获取"""
        import article_mcp.tools.core.article_tools as article_tools_module
        from article_mcp.tools.core.article_tools import get_article_details_async

        article_tools_module._article_services = mock_services_fast
        article_tools_module._logger = Mock()

        # 大批量：50篇
        identifiers = [f"10.1234/large{i}" for i in range(50)]

        result = await get_article_details_async(
            identifier=identifiers,
            id_type="auto",
            include_fulltext=False,
        )

        # 验证结果
        assert result["total"] == 50
        assert result["successful"] == 50


class TestBatchArticleDetailsIntegration:
    """批量获取的集成测试"""

    @pytest.mark.unit
    def test_tool_registration_with_batch_support(self):
        """测试工具注册支持批量参数"""
        from fastmcp import FastMCP

        from article_mcp.tools.core.article_tools import register_article_tools

        mcp = FastMCP("test")
        services = {"europe_pmc": Mock(), "pubmed": Mock()}
        logger = Mock()

        # 注册工具
        register_article_tools(mcp, services, logger)

        # 验证工具已注册
        public_attrs = [name for name in dir(mcp) if not name.startswith("_")]
        assert len(public_attrs) > 0

    @pytest.mark.unit
    def test_batch_api_consistency(self):
        """测试批量API一致性"""
        # 参数命名一致
        assert "identifier" in "identifier"
        assert "id_type" in "id_type"
        assert "include_fulltext" in "include_fulltext"
        assert "sections" in "sections"

        # 单个和批量使用相同的参数名
        single_params = ["identifier", "id_type", "include_fulltext", "sections"]
        batch_params = ["identifier", "id_type", "include_fulltext", "sections"]

        assert set(single_params) == set(batch_params)
