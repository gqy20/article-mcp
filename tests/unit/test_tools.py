#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具层单元测试
测试MCP工具注册和基本功能
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastmcp import FastMCP

# 导入要测试的工具注册函数
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from article_mcp.tools.core.search_tools import register_search_tools
from article_mcp.tools.core.article_tools import register_article_tools
from article_mcp.tools.core.reference_tools import register_reference_tools
from article_mcp.tools.core.quality_tools import register_quality_tools

from tests.utils.test_helpers import (
    MockDataGenerator,
    TestTimer,
    assert_valid_article_structure,
    assert_valid_search_results
)


class TestToolRegistration:
    """工具注册测试"""

    @pytest.fixture
    def mcp_server(self):
        """创建MCP服务器实例"""
        return FastMCP("Test Server")

    @pytest.fixture
    def mock_services(self):
        """创建模拟服务"""
        return {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock()
        }

    @pytest.fixture
    def mock_logger(self):
        """创建模拟日志器"""
        return Mock()

    @pytest.mark.unit
    def test_register_search_tools(self, mcp_server, mock_services, mock_logger):
        """测试搜索工具注册"""
        # 注册工具
        register_search_tools(mcp_server, mock_services, mock_logger)

        # 验证工具已注册
        assert hasattr(mcp_server, '_tools')
        assert len(mcp_server._tools) > 0

    @pytest.mark.unit
    def test_register_article_tools(self, mcp_server, mock_services, mock_logger):
        """测试文章工具注册"""
        # 注册工具
        register_article_tools(mcp_server, mock_services, mock_logger)

        # 验证工具已注册
        assert hasattr(mcp_server, '_tools')
        assert len(mcp_server._tools) > 0

    @pytest.mark.unit
    def test_register_reference_tools(self, mcp_server, mock_logger):
        """测试参考文献工具注册"""
        mock_reference_service = Mock()

        # 注册工具
        register_reference_tools(mcp_server, mock_reference_service, mock_logger)

        # 验证工具已注册
        assert hasattr(mcp_server, '_tools')
        assert len(mcp_server._tools) > 0

    @pytest.mark.unit
    def test_register_quality_tools(self, mcp_server, mock_services, mock_logger):
        """测试质量评估工具注册"""
        # 注册工具
        register_quality_tools(mcp_server, mock_services, mock_logger)

        # 验证工具已注册
        assert hasattr(mcp_server, '_tools')
        assert len(mcp_server._tools) > 0


class TestSearchTools:
    """搜索工具测试"""

    @pytest.fixture
    def mock_europe_pmc_service(self):
        """模拟Europe PMC服务"""
        service = Mock()
        service.search_articles = AsyncMock(return_value=MockDataGenerator.create_search_results(5))
        return service

    @pytest.fixture
    def mock_arxiv_service(self):
        """模拟ArXiv服务"""
        service = Mock()
        service.search_papers = AsyncMock(return_value=MockDataGenerator.create_search_results(3))
        return service

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_literature_tool(self, mock_europe_pmc_service, mock_arxiv_service):
        """测试文献搜索工具"""
        from article_mcp.tools.core.search_tools import _search_literature

        # 模拟服务调用
        mock_europe_pmc_service.search_articles.return_value = MockDataGenerator.create_search_results(5)
        mock_arxiv_service.search_papers.return_value = MockDataGenerator.create_search_results(3)

        # 调用搜索工具
        with patch('article_mcp.tools.core.search_tools._search_services', {
            'europe_pmc': mock_europe_pmc_service,
            'arxiv': mock_arxiv_service
        }):
            result = await _search_literature(
                keyword="machine learning",
                sources=["europe_pmc", "arxiv"],
                max_results=10,
                search_type="comprehensive"
            )

        # 验证结果
        assert "articles" in result
        assert isinstance(result["articles"], list)
        assert len(result["articles"]) > 0
        assert_valid_search_results(result)


class TestArticleTools:
    """文章工具测试"""

    @pytest.fixture
    def mock_europe_pmc_service(self):
        """模拟Europe PMC服务"""
        service = Mock()
        service.get_article_details = AsyncMock(return_value=MockDataGenerator.create_article())
        return service

    @pytest.fixture
    def mock_crossref_service(self):
        """模拟CrossRef服务"""
        service = Mock()
        service.resolve_doi = AsyncMock(return_value=MockDataGenerator.create_article())
        return service

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_article_details_tool(self, mock_europe_pmc_service, mock_crossref_service):
        """测试获取文章详情工具"""
        from article_mcp.tools.core.article_tools import _get_article_details

        # 模拟服务调用
        mock_article = MockDataGenerator.create_article(
            title="Test Article",
            doi="10.1000/test",
            pmid="12345678"
        )
        mock_europe_pmc_service.get_article_details.return_value = mock_article
        mock_crossref_service.resolve_doi.return_value = mock_article

        # 调用文章详情工具
        with patch('article_mcp.tools.core.article_tools._article_services', {
            'europe_pmc': mock_europe_pmc_service,
            'crossref': mock_crossref_service
        }):
            result = await _get_article_details(
                identifier="10.1000/test",
                id_type="doi",
                sources=["europe_pmc", "crossref"],
                include_quality_metrics=False
            )

        # 验证结果
        assert_valid_article_structure(result)
        assert result["doi"] == "10.1000/test"


class TestReferenceTools:
    """参考文献工具测试"""

    @pytest.fixture
    def mock_reference_service(self):
        """模拟参考文献服务"""
        service = Mock()
        service.get_references = AsyncMock(return_value={
            "references": MockDataGenerator.create_reference_list(10),
            "total_count": 10
        })
        return service

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_references_tool(self, mock_reference_service):
        """测试获取参考文献工具"""
        from article_mcp.tools.core.reference_tools import _get_references

        # 模拟服务调用
        mock_reference_service.get_references.return_value = {
            "references": MockDataGenerator.create_reference_list(5),
            "total_count": 5,
            "processing_time": 0.5
        }

        # 调用参考文献工具
        with patch('article_mcp.tools.core.reference_tools._reference_service',
                  mock_reference_service):
            result = await _get_references(
                identifier="10.1000/test",
                id_type="doi",
                sources=["europe_pmc"],
                max_results=10
            )

        # 验证结果
        assert "references" in result
        assert isinstance(result["references"], list)
        assert len(result["references"]) == 5
        assert "processing_time" in result


class TestQualityTools:
    """质量评估工具测试"""

    @pytest.fixture
    def mock_pubmed_service(self):
        """模拟PubMed服务"""
        service = Mock()
        service.get_journal_quality = AsyncMock(return_value={
            "journal_name": "Test Journal",
            "impact_factor": 5.0,
            "quartile": "Q1",
            "jci": 1.2,
            "rank": 100
        })
        return service

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_journal_quality_tool(self, mock_pubmed_service):
        """测试获取期刊质量工具"""
        from article_mcp.tools.core.quality_tools import _get_journal_quality

        # 模拟服务调用
        mock_pubmed_service.get_journal_quality.return_value = {
            "journal_name": "Test Journal",
            "impact_factor": 5.0,
            "quartile": "Q1",
            "jci": 1.2,
            "rank": 100
        }

        # 调用期刊质量工具
        with patch('article_mcp.tools.core.quality_tools._quality_services', {
            'pubmed': mock_pubmed_service
        }):
            result = await _get_journal_quality(
                journal_name="Test Journal",
                include_metrics=True,
                evaluation_criteria="standard"
            )

        # 验证结果
        assert "journal_name" in result
        assert result["journal_name"] == "Test Journal"
        assert "impact_factor" in result
        assert result["impact_factor"] == 5.0


class TestToolPerformance:
    """工具性能测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tool_performance(self):
        """测试工具性能"""
        from article_mcp.tools.core.search_tools import _search_literature

        # 模拟搜索结果
        mock_results = MockDataGenerator.create_search_results(100)  # 大量结果

        with patch('article_mcp.tools.core.search_tools._search_services') as mock_services:
            mock_service = Mock()
            mock_service.search_articles = AsyncMock(return_value=mock_results)
            mock_services.__getitem__ = Mock(return_value=mock_service)

            # 测量性能
            with TestTimer() as timer:
                result = await _search_literature(
                    keyword="test query",
                    sources=["europe_pmc"],
                    max_results=100,
                    search_type="comprehensive"
                )

        # 验证性能要求
        assert timer.stop() < 10.0  # 应该在10秒内完成
        assert len(result["articles"]) == 100

    @pytest.mark.unit
    def test_tool_error_handling(self):
        """测试工具错误处理"""
        from article_mcp.tools.core.search_tools import _search_literature

        # 模拟服务错误
        with patch('article_mcp.tools.core.search_tools._search_services') as mock_services:
            mock_service = Mock()
            mock_service.search_articles = AsyncMock(side_effect=Exception("Service error"))
            mock_services.__getitem__ = Mock(return_value=mock_service)

            # 测试错误处理
            with pytest.raises(Exception):
                # 这里需要使用实际的异步调用
                import asyncio
                asyncio.run(_search_literature(
                    keyword="test query",
                    sources=["europe_pmc"],
                    max_results=10,
                    search_type="comprehensive"
                ))