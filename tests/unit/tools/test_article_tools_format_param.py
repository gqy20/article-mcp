#!/usr/bin/env python3
"""Article Tools format 参数测试

测试优化后的按需转换功能：
1. format 参数控制返回格式
2. 默认返回 markdown 格式
3. 支持 "markdown" | "xml" | "text" 三种格式
4. 只返回请求的格式，不返回其他格式
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

# 服务层返回的三种格式（当前实现）
SAMPLE_FULLTEXT_ALL_FORMATS = {
    "pmc_id": "PMC1234567",
    "fulltext_xml": "<article><body><p>XML Content</p></body></article>",
    "fulltext_markdown": "# Markdown Content\n\nParagraph",
    "fulltext_text": "Markdown Content\n\nParagraph",
    "fulltext_available": True,
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
    # 使用异步 mock
    from unittest.mock import AsyncMock

    pubmed.get_pmc_fulltext_html_async = AsyncMock(return_value=SAMPLE_FULLTEXT_ALL_FORMATS.copy())

    return {"europe_pmc": europe_pmc, "pubmed": pubmed}


# ============================================================================
# format 参数测试
# ============================================================================


@pytest.mark.asyncio
class TestArticleToolsFormatParam:
    """测试 format 参数功能"""

    async def test_format_defaults_to_markdown(self, mock_services, logger):
        """测试：默认 format="markdown" 返回 markdown 格式"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", services=mock_services, logger=logger
        )

        assert result is not None
        assert result["successful"] == 1
        article = result["articles"][0]

        # 新的返回结构
        assert "fulltext" in article
        fulltext = article["fulltext"]

        # 应该有 format 字段
        assert "format" in fulltext
        assert fulltext["format"] == "markdown"

        # 应该只有 content 字段，没有三种格式的字段
        assert "content" in fulltext
        assert fulltext["content"] == SAMPLE_FULLTEXT_ALL_FORMATS["fulltext_markdown"]

        # 不应该有旧的字段
        assert "fulltext_xml" not in fulltext
        assert "fulltext_markdown" not in fulltext
        assert "fulltext_text" not in fulltext

    async def test_format_markdown_returns_only_markdown(self, mock_services, logger):
        """测试：format="markdown" 只返回 markdown 格式"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", format="markdown", services=mock_services, logger=logger
        )

        assert result is not None
        article = result["articles"][0]
        fulltext = article["fulltext"]

        assert fulltext["format"] == "markdown"
        assert fulltext["content"] == SAMPLE_FULLTEXT_ALL_FORMATS["fulltext_markdown"]
        assert "fulltext_xml" not in fulltext
        assert "fulltext_text" not in fulltext

    async def test_format_xml_returns_only_xml(self, mock_services, logger):
        """测试：format="xml" 只返回 XML 格式"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", format="xml", services=mock_services, logger=logger
        )

        assert result is not None
        article = result["articles"][0]
        fulltext = article["fulltext"]

        assert fulltext["format"] == "xml"
        assert fulltext["content"] == SAMPLE_FULLTEXT_ALL_FORMATS["fulltext_xml"]
        assert "fulltext_markdown" not in fulltext
        assert "fulltext_text" not in fulltext

    async def test_format_text_returns_only_text(self, mock_services, logger):
        """测试：format="text" 只返回纯文本格式"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", format="text", services=mock_services, logger=logger
        )

        assert result is not None
        article = result["articles"][0]
        fulltext = article["fulltext"]

        assert fulltext["format"] == "text"
        assert fulltext["content"] == SAMPLE_FULLTEXT_ALL_FORMATS["fulltext_text"]
        assert "fulltext_xml" not in fulltext
        assert "fulltext_markdown" not in fulltext

    async def test_format_invalid_raises_error(self, mock_services, logger):
        """测试：无效的 format 值应该返回错误"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", format="invalid", services=mock_services, logger=logger
        )

        # 应该失败
        assert result["successful"] == 0
        assert result["failed"] == 1
        assert "error" in result

    async def test_format_preserves_fulltext_available(self, mock_services, logger):
        """测试：format 参数保留 fulltext_available 字段"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", format="markdown", services=mock_services, logger=logger
        )

        article = result["articles"][0]
        fulltext = article["fulltext"]

        # fulltext_available 应该保留
        assert "fulltext_available" in fulltext
        assert fulltext["fulltext_available"] is True


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
