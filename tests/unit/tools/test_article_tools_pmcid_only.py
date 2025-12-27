#!/usr/bin/env python3
"""Article Tools 简化版测试 - 只支持 PMCID

简化设计：
1. 只接受 PMCID 作为输入
2. 移除 id_type 参数
3. 移除 sections=[]（不获取全文）的选项
4. sections=None 表示获取全部章节（默认）
5. sections=["xxx"] 表示获取指定章节
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

SAMPLE_FULLTEXT_CONCLUSION = {
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
    # 使用异步 mock
    from unittest.mock import AsyncMock

    pubmed.get_pmc_fulltext_html_async = AsyncMock(return_value=SAMPLE_FULLTEXT.copy())

    return {"europe_pmc": europe_pmc, "pubmed": pubmed}


# ============================================================================
# 简化版测试
# ============================================================================


@pytest.mark.asyncio
class TestArticleDetailsPMCidOnly:
    """简化版测试：只支持 PMCID"""

    async def test_accepts_pmcid_only(self, mock_services, logger):
        """测试：只接受 PMCID 作为输入"""
        # 使用 PMCID 应该成功
        result = await article_tools.get_article_details_async(
            "PMC1234567", services=mock_services, logger=logger
        )

        assert result is not None
        assert result["total"] == 1
        assert result["successful"] == 1
        assert len(result["articles"]) == 1
        assert result["articles"][0]["pmcid"] == "PMC1234567"

    async def test_no_id_type_parameter(self, mock_services, logger):
        """测试：函数签名不应该有 id_type 参数"""
        import inspect

        sig = inspect.signature(article_tools.get_article_details_async)
        params = list(sig.parameters.keys())

        # 不应该有 id_type 参数
        assert "id_type" not in params, "id_type 参数应该被移除"
        # 应该只有 pmcid 参数
        assert "pmcid" in params, "必须有 pmcid 参数"

    async def test_sections_default_gets_all(self, mock_services, logger):
        """测试：默认 sections=None 获取全部章节"""
        result = await article_tools.get_article_details_async(
            "PMC1234567", services=mock_services, logger=logger
        )

        assert result is not None
        assert result["successful"] == 1
        article = result["articles"][0]
        assert "fulltext" in article
        assert article["fulltext"]["fulltext_available"] is True

        # 验证调用时 sections=None（获取全部）
        mock_services["pubmed"].get_pmc_fulltext_html_async.assert_called_once_with(
            "PMC1234567", sections=None
        )

    async def test_sections_list_gets_specific(self, mock_services, logger):
        """测试：sections=["conclusion"] 获取指定章节"""
        from unittest.mock import AsyncMock

        mock_services["pubmed"].get_pmc_fulltext_html_async = AsyncMock(
            return_value=SAMPLE_FULLTEXT_CONCLUSION.copy()
        )

        result = await article_tools.get_article_details_async(
            "PMC1234567", sections=["conclusion"], services=mock_services, logger=logger
        )

        assert result is not None
        article = result["articles"][0]
        assert article["fulltext"]["sections_requested"] == ["conclusion"]

        mock_services["pubmed"].get_pmc_fulltext_html_async.assert_called_once_with(
            "PMC1234567", sections=["conclusion"]
        )

    async def test_sections_empty_list_not_allowed(self, mock_services, logger):
        """测试：sections=[] 不应该被允许（这是全文获取工具）"""
        # sections=[] 应该报错或被忽略
        # 根据新设计，这应该被视为无效参数
        result = await article_tools.get_article_details_async(
            "PMC1234567", sections=[], services=mock_services, logger=logger
        )

        # 既然是全文获取工具，sections=[] 应该被当作无效输入
        # 返回错误或者直接当作 sections=None 处理都可以
        # 这里我们验证：即使传 []，也应该获取全文（因为是全文工具）
        assert result is not None
        article = result["articles"][0]
        assert "fulltext" in article, "作为全文获取工具，不应该允许不获取全文"

    async def test_non_pmcid_input_returns_error(self, mock_services, logger):
        """测试：非 PMCID 输入应该返回明确的错误"""
        # PMID 输入应该失败
        result = await article_tools.get_article_details_async(
            "12345678", services=mock_services, logger=logger
        )

        assert result is not None
        assert result["successful"] == 0
        assert result["failed"] == 1
        assert "error" in result or len(result["articles"]) == 0

    async def test_doi_input_returns_error(self, mock_services, logger):
        """测试：DOI 输入应该返回明确的错误"""
        # DOI 输入应该失败
        result = await article_tools.get_article_details_async(
            "10.1234/test.2023", services=mock_services, logger=logger
        )

        assert result is not None
        assert result["successful"] == 0
        assert result["failed"] == 1
        assert "error" in result or len(result["articles"]) == 0


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
