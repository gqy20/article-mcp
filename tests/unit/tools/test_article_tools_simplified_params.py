#!/usr/bin/env python3
"""Article Tools 简化参数测试 - TDD

简化设计：移除冗余的 include_fulltext 参数，只保留 sections 参数

sections 参数语义：
- sections=None (默认) → 获取全部章节（全文）
- sections=["xxx"] → 获取指定章节
- sections=[] → 不获取全文（只要元数据）
"""

import logging
from unittest.mock import Mock

import pytest

from article_mcp.tools.core import article_tools

# ============================================================================
# 测试数据
# ============================================================================

SAMPLE_ARTICLE_WITH_PMCID = {
    "title": "Machine Learning in Healthcare",
    "authors": [{"name": "John Smith"}, {"name": "Jane Doe"}],
    "doi": "10.1234/test.2023",
    "journal": "Nature Medicine",
    "publication_date": "2023-01-15",
    "abstract": "This study explores machine learning.",
    "pmid": "12345678",
    "pmcid": "PMC1234567",
}

SAMPLE_FULLTEXT = {
    "pmc_id": "PMC1234567",
    "fulltext_xml": "<article><body>Content</body></article>",
    "fulltext_markdown": "# Introduction\nContent",
    "fulltext_text": "Introduction\nContent",
    "fulltext_available": True,
    "error": None,
}

SAMPLE_FULLTEXT_SECTIONS = {
    "pmc_id": "PMC1234567",
    "fulltext_xml": "<body><sec>Conclusion content</sec></body>",
    "fulltext_markdown": "## Conclusion\n\nConclusion content",
    "fulltext_text": "Conclusion\n\nConclusion content",
    "fulltext_available": True,
    "sections_requested": ["conclusion"],
    "sections_found": ["conclusion"],
    "sections_missing": [],
    "error": None,
}


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def logger():
    return logging.getLogger(__name__)


@pytest.fixture
def mock_services():
    """模拟服务"""
    europe_pmc = Mock()
    europe_pmc.fetch = Mock(
        return_value={"article": SAMPLE_ARTICLE_WITH_PMCID.copy(), "error": None}
    )

    pubmed = Mock()
    pubmed.get_pmc_fulltext_html = Mock(return_value=SAMPLE_FULLTEXT.copy())

    return {"europe_pmc": europe_pmc, "pubmed": pubmed}


# ============================================================================
# 简化参数测试
# ============================================================================


@pytest.mark.asyncio
class TestSimplifiedParameters:
    """简化参数设计测试：移除 include_fulltext，只保留 sections"""

    async def test_sections_none_gets_fulltext(self, mock_services, logger):
        """测试：sections=None（默认）获取全部全文"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        # 不传 sections 参数，默认为 None
        result = await article_tools.get_article_details_async("PMC1234567", "pmcid", sections=None)

        # 验证返回批量结果格式，提取第一篇文章
        assert result is not None
        assert "articles" in result
        assert len(result["articles"]) == 1
        article = result["articles"][0]

        # 验证包含全文
        assert "fulltext" in article
        assert article["fulltext"]["fulltext_available"] is True

        # 验证调用全文获取（sections=None 表示全部）
        mock_services["pubmed"].get_pmc_fulltext_html.assert_called_once_with(
            "PMC1234567", sections=None
        )

    async def test_sections_list_gets_specific_chapter(self, mock_services, logger):
        """测试：sections=["conclusion"] 只获取结论章节"""
        mock_services["pubmed"].get_pmc_fulltext_html = Mock(
            return_value=SAMPLE_FULLTEXT_SECTIONS.copy()
        )

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            "PMC1234567", "pmcid", sections=["conclusion"]
        )

        # 验证返回批量结果格式，提取第一篇文章
        assert result is not None
        assert "articles" in result
        article = result["articles"][0]

        # 验证包含指定章节
        assert "fulltext" in article
        assert article["fulltext"]["sections_requested"] == ["conclusion"]

        mock_services["pubmed"].get_pmc_fulltext_html.assert_called_once_with(
            "PMC1234567", sections=["conclusion"]
        )

    async def test_sections_empty_skips_fulltext(self, mock_services, logger):
        """测试：sections=[] 跳过全文获取，只返回元数据"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("PMC1234567", "pmcid", sections=[])

        # 验证返回批量结果格式，提取第一篇文章
        assert result is not None
        assert "articles" in result
        article = result["articles"][0]

        # 验证无全文
        assert "fulltext" not in article

        # 验证没有调用全文获取
        mock_services["pubmed"].get_pmc_fulltext_html.assert_not_called()

    async def test_default_parameters_gets_fulltext(self, mock_services, logger):
        """测试：不传任何参数，默认获取全文（sections=None）"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        # 使用默认参数
        result = await article_tools.get_article_details_async("PMC1234567", "pmcid")

        # 验证返回批量结果格式，提取第一篇文章
        assert result is not None
        assert "articles" in result
        article = result["articles"][0]

        # 验证包含全文
        assert "fulltext" in article
        assert article["fulltext"]["fulltext_available"] is True

    async def test_no_include_fulltext_parameter(self, mock_services, logger):
        """测试：新的 API 不应该有 include_fulltext 参数

        这个测试确保函数签名已经简化，不再包含 include_fulltext
        """
        import inspect

        # 检查函数签名
        sig = inspect.signature(article_tools.get_article_details_async)
        params = list(sig.parameters.keys())

        # 不应该包含 include_fulltext 参数
        assert "include_fulltext" not in params, (
            "include_fulltext 参数应该被移除，只保留 sections 参数"
        )

        # 应该包含 sections 参数
        assert "sections" in params, "必须保留 sections 参数"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
