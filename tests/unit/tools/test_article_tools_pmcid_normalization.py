"""测试 pmcid 参数规范化功能 - TDD Phase 1

测试场景：
1. 正常 JSON 数组 → 保持不变
2. 字符串化的数组 → 自动解析为数组
3. 单个字符串 → 保持不变
4. 无效的字符串化数组 → 返回友好错误
5. 空数组 → 返回空结果
6. 超过20个 PMCID → 返回错误
"""

import pytest

from article_mcp.tools.core.article_tools import get_article_details_async


class TestPmcidNormalization:
    """测试 pmcid 参数规范化"""

    @pytest.mark.asyncio
    async def test_json_array_unchanged(self, mock_services, mock_logger):
        """正常 JSON 数组应保持不变"""
        pmcids = ["PMC12700438", "PMC12705824"]

        result = await get_article_details_async(
            pmcid=pmcids,
            sections=None,
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        # 验证参数被正确处理（未修改）
        # 这里我们通过检查是否正确调用了服务来验证
        assert "total" in result
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_stringified_array_auto_parsed(self, mock_services, mock_logger):
        """字符串化的数组应自动解析为数组"""
        # 这是用户报告的错误格式
        stringified_array = '["PMC12700438", "PMC12705824"]'

        result = await get_article_details_async(
            pmcid=stringified_array,
            sections=None,
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        # 应自动解析为2个 PMCID，而不是失败
        assert "total" in result
        assert result["total"] == 2
        assert result["successful"] > 0

    @pytest.mark.asyncio
    async def test_single_string_unchanged(self, mock_services, mock_logger):
        """单个字符串应保持不变"""
        result = await get_article_details_async(
            pmcid="PMC12700438",
            sections=None,
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        assert "total" in result
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_invalid_stringified_array_friendly_error(self, mock_services, mock_logger):
        """无效的字符串化数组应返回友好错误"""
        # 语法错误的 JSON
        invalid_stringified = "[PMC12700438, PMC12705824]"  # 缺少引号

        result = await get_article_details_async(
            pmcid=invalid_stringified,
            sections=None,
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        # 应返回友好的错误信息
        assert "error" in result or result["failed"] > 0

    @pytest.mark.asyncio
    async def test_empty_array_returns_empty(self, mock_services, mock_logger):
        """空数组应返回空结果"""
        result = await get_article_details_async(
            pmcid=[],
            sections=None,
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        assert result["total"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_exceeds_limit_returns_error(self, mock_services, mock_logger):
        """超过20个 PMCID 应返回错误"""
        # 创建21个 PMCID
        pmcids = [f"PMC{i:07d}" for i in range(1, 22)]

        result = await get_article_details_async(
            pmcid=pmcids,
            sections=None,
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        assert "error" in result
        assert "超过限制" in result["error"] or "20" in result["error"]

    @pytest.mark.asyncio
    async def test_sections_string_auto_converted_to_list(self, mock_services, mock_logger):
        """sections 字符串应自动转换为数组"""
        result = await get_article_details_async(
            pmcid="PMC12700438",
            sections="methods",  # 字符串而不是数组
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        # 应该成功处理，自动将 "methods" 转换为 ["methods"]
        assert "total" in result
        assert result["total"] == 1
        assert result["successful"] > 0

    @pytest.mark.asyncio
    async def test_sections_list_unchanged(self, mock_services, mock_logger):
        """sections 数组应保持不变"""
        result = await get_article_details_async(
            pmcid="PMC12700438",
            sections=["methods", "results"],  # 已经是数组
            format="markdown",
            services=mock_services,
            logger=mock_logger,
        )

        assert "total" in result
        assert result["total"] == 1
        assert result["successful"] > 0


# ===== Fixtures =====
import asyncio
from unittest.mock import AsyncMock, Mock, patch


@pytest.fixture
def mock_logger():
    """模拟 logger"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_services():
    """模拟服务"""

    europe_pmc = Mock()
    europe_pmc.fetch = Mock(
        return_value={
            "article": {
                "pmid": "12345678",
                "title": "Test Article",
                "authors": ["Author A", "Author B"],
                "journal_name": "Test Journal",
                "publication_date": "2025-01-01",
                "abstract": "Test abstract",
                "doi": "10.1234/test",
                "pmcid": "PMC12700438",
            },
            "error": None,
        }
    )

    pubmed = Mock()
    pubmed.get_pmc_fulltext_html_async = AsyncMock(
        return_value={
            "fulltext_xml": "<xml>content</xml>",
            "fulltext_markdown": "# content",
            "fulltext_text": "content",
            "fulltext_available": True,
        }
    )

    return {"europe_pmc": europe_pmc, "pubmed": pubmed}
