#!/usr/bin/env python3
"""Article Tools 异步测试 - 核心任务版本

核心任务：有 PMCID 时获取全文
章节提取：支持按章节提取全文内容
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

SAMPLE_ARTICLE_WITHOUT_PMCID = {
    "title": "Article Without PMCID",
    "authors": [{"name": "Alice"}],
    "doi": "10.5678/test.2023",
    "journal": "Science",
    "publication_date": "2023-03-20",
    "abstract": "No PMCID.",
    "pmid": "87654321",
    "pmcid": None,
}

SAMPLE_FULLTEXT = {
    "pmc_id": "PMC1234567",
    "fulltext_xml": "<article><body>Content</body></article>",
    "fulltext_markdown": "# Introduction\nContent",
    "fulltext_text": "Introduction\nContent",
    "fulltext_available": True,
    "error": None,
}

# 章节提取的全文
SAMPLE_FULLTEXT_WITH_SECTIONS = {
    "pmc_id": "PMC1234567",
    "fulltext_xml": "<body><sec sec-type='methods'><title>Methods</title><p>Methods content</p></sec></body>",
    "fulltext_markdown": "## Methods\n\nMethods content",
    "fulltext_text": "Methods\n\nMethods content",
    "fulltext_available": True,
    "sections_requested": ["methods"],
    "sections_found": ["methods"],
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
# 核心任务测试
# ============================================================================


@pytest.mark.asyncio
class TestGetArticleDetails:
    """核心任务测试：有 PMCID 时获取全文"""

    async def test_with_pmcid_fetches_fulltext(self, mock_services, logger):
        """测试：有 PMCID 时自动获取全文"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("PMC1234567", "pmcid")

        # 验证返回文章
        assert result is not None
        assert result["title"] == "Machine Learning in Healthcare"
        assert result["pmcid"] == "PMC1234567"

        # 验证包含全文
        assert "fulltext" in result
        assert result["fulltext"]["fulltext_available"] is True
        assert result["fulltext"]["fulltext_markdown"] is not None

        # 验证调用了全文获取（默认 sections=None）
        mock_services["pubmed"].get_pmc_fulltext_html.assert_called_once_with(
            "PMC1234567", sections=None
        )

    async def test_without_pmcid_no_fulltext(self, mock_services, logger):
        """测试：无 PMCID 时不获取全文"""
        # 设置返回无 PMCID 的文章
        mock_services["europe_pmc"].fetch = Mock(
            return_value={"article": SAMPLE_ARTICLE_WITHOUT_PMCID.copy(), "error": None}
        )

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("10.5678/test.2023", "doi")

        # 验证返回文章
        assert result is not None
        assert result["pmcid"] is None

        # 验证不包含全文
        assert "fulltext" not in result

        # 验证没有调用全文获取
        mock_services["pubmed"].get_pmc_fulltext_html.assert_not_called()

    async def test_fulltext_fetch_failed_continues(self, mock_services, logger):
        """测试：全文获取失败时仍返回文章"""
        # 设置全文获取失败
        mock_services["pubmed"].get_pmc_fulltext_html = Mock(
            return_value={"fulltext_available": False, "error": "Not found"}
        )

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("PMC1234567", "pmcid")

        # 验证仍返回文章（只是没有 fulltext）
        assert result is not None
        assert result["title"] == "Machine Learning in Healthcare"
        assert "fulltext" not in result

    async def test_empty_identifier_returns_none(self, mock_services, logger):
        """测试：空标识符返回 None"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("", "doi")
        assert result is None

    async def test_article_not_found_returns_none(self, mock_services, logger):
        """测试：文献未找到返回 None"""
        mock_services["europe_pmc"].fetch = Mock(
            return_value={"article": None, "error": "未找到文献"}
        )

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("notfound", "doi")
        assert result is None


# ============================================================================
# 章节提取测试
# ============================================================================


@pytest.mark.asyncio
class TestArticleDetailsSectionExtraction:
    """章节提取功能测试"""

    async def test_with_sections_extracts_only_methods(self, mock_services, logger):
        """测试：指定 sections 时只提取指定章节"""
        # 设置返回章节提取结果
        mock_services["pubmed"].get_pmc_fulltext_html = Mock(
            return_value=SAMPLE_FULLTEXT_WITH_SECTIONS.copy()
        )

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            "PMC1234567", "pmcid", sections=["methods"]
        )

        # 验证返回文章
        assert result is not None
        assert result["pmcid"] == "PMC1234567"

        # 验证包含全文和章节信息
        assert "fulltext" in result
        assert result["fulltext"]["fulltext_available"] is True
        assert result["fulltext"]["sections_requested"] == ["methods"]
        assert result["fulltext"]["sections_found"] == ["methods"]
        assert result["fulltext"]["sections_missing"] == []

        # 验证调用了章节提取
        mock_services["pubmed"].get_pmc_fulltext_html.assert_called_once_with(
            "PMC1234567", sections=["methods"]
        )

    async def test_empty_sections_list_skips_fulltext(self, mock_services, logger):
        """测试：空章节列表跳过全文获取"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("PMC1234567", "pmcid", sections=[])

        # 验证返回文章但无全文
        assert result is not None
        assert result["pmcid"] == "PMC1234567"
        assert "fulltext" not in result

        # 验证没有调用全文获取
        mock_services["pubmed"].get_pmc_fulltext_html.assert_not_called()

    async def test_sections_none_gets_all_sections(self, mock_services, logger):
        """测试：sections=None 获取全部章节"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async("PMC1234567", "pmcid", sections=None)

        # 验证返回文章和全文
        assert result is not None
        assert "fulltext" in result

        # 验证不包含章节信息字段（全部章节时不标记）
        assert "sections_requested" not in result.get("fulltext", {})

        # 验证调用全文获取时 sections=None
        mock_services["pubmed"].get_pmc_fulltext_html.assert_called_once_with(
            "PMC1234567", sections=None
        )


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
