#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n# 添加src目录到Python路径
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
文章详情工具单元测试
"""

from unittest.mock import Mock

import pytest

from article_mcp.tools.article_detail_tools import register_article_detail_tools


class TestArticleDetailTools:
    """文章详情工具测试类"""

    @pytest.fixture
    def mock_mcp(self):
        """模拟 MCP 对象"""
        mcp = Mock()
        mcp.tool = Mock()
        return mcp

    @pytest.fixture
    def mock_europe_pmc_service(self):
        """模拟 Europe PMC 服务"""
        service = Mock()
        service.fetch.return_value = {
            "success": True,
            "article": {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test",
                "pmid": "12345678",
                "abstract": "Test abstract",
            },
            "processing_time": 0.5,
            "cache_hit": False,
        }
        return service

    @pytest.fixture
    def logger(self):
        """模拟日志记录器"""
        return Mock()

    def test_register_article_detail_tools(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试文章详情工具注册"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)

        assert len(tools) == 1
        mock_mcp.tool.assert_called_once()

        # 获取注册的工具
        article_tool = tools[0]
        assert article_tool.__name__ == "get_article_details"

    def test_get_article_details_success(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试成功获取文章详情"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(
            identifier="12345678", id_type="pmid", mode="sync", include_fulltext=False
        )

        assert result["success"] is True
        assert result["article"]["title"] == "Test Article"
        assert result["article"]["doi"] == "10.1234/test"
        assert "processing_time" in result
        assert "cache_hit" in result

    def test_get_article_details_with_doi(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试使用DOI获取文章详情"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="10.1234/test", id_type="doi", mode="sync")

        assert result["success"] is True
        mock_europe_pmc_service.fetch.assert_called_with(
            "10.1234/test", id_type="doi", mode="sync", include_fulltext=False
        )

    def test_get_article_details_with_pmcid(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试使用PMCID获取文章详情"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="PMC12345678", id_type="pmcid")

        assert result["success"] is True
        mock_europe_pmc_service.fetch.assert_called_with(
            "PMC12345678", id_type="pmcid", mode="sync", include_fulltext=False
        )

    def test_get_article_details_async_mode(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试异步模式获取文章详情"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="12345678", mode="async")

        assert result["success"] is True
        mock_europe_pmc_service.fetch.assert_called_with(
            "12345678", id_type="pmid", mode="async", include_fulltext=False
        )

    def test_get_article_details_with_fulltext(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试包含全文的获取"""
        # 设置服务返回包含全文信息
        mock_europe_pmc_service.fetch.return_value = {
            "success": True,
            "article": {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test",
                "pmid": "12345678",
                "abstract": "Test abstract",
            },
            "fulltext": {
                "html": "<html>Full text content</html>",
                "available": True,
                "title": "Test Article",
                "authors": ["Test Author"],
                "abstract": "Test abstract",
            },
            "processing_time": 0.8,
            "cache_hit": True,
        }

        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="12345678", include_fulltext=True)

        assert result["success"] is True
        assert "fulltext" in result
        assert result["fulltext"]["available"] is True
        assert result["fulltext"]["html"] == "<html>Full text content</html>"
        assert result["cache_hit"] is True

    def test_get_article_details_service_failure(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试服务调用失败"""
        mock_europe_pmc_service.fetch.return_value = {
            "success": False,
            "error": "Article not found",
            "processing_time": 0.3,
        }

        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="invalid_id")

        assert result["success"] is False
        assert result["error"] == "Article not found"

    def test_get_article_details_service_exception(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试服务调用异常"""
        mock_europe_pmc_service.fetch.side_effect = Exception("Network Error")

        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        with pytest.raises(Exception, match="Network Error"):
            get_article_details(identifier="12345678")

    def test_get_article_details_default_parameters(
        self, mock_mcp, mock_europe_pmc_service, logger
    ):
        """测试默认参数"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="12345678")

        # 验证使用了默认参数
        mock_europe_pmc_service.fetch.assert_called_with(
            "12345678", id_type="pmid", mode="sync", include_fulltext=False
        )
        assert result["success"] is True

    def test_get_article_details_empty_identifier(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试空标识符"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="")

        assert result["success"] is True  # 服务层处理验证

    def test_get_article_details_performance_metrics(
        self, mock_mcp, mock_europe_pmc_service, logger
    ):
        """测试性能指标"""
        mock_europe_pmc_service.fetch.return_value = {
            "success": True,
            "article": {"title": "Test Article"},
            "processing_time": 1.23,
            "cache_hit": True,
            "performance_info": {"cache_size": 1000, "hit_rate": 0.85},
            "retry_count": 2,
        }

        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        result = get_article_details(identifier="12345678")

        assert result["processing_time"] == 1.23
        assert result["cache_hit"] is True
        assert "performance_info" in result
        assert result["retry_count"] == 2

    def test_dependency_injection(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试依赖注入"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        # 验证依赖已正确注入
        from article_mcp.tools.article_detail_tools import article_detail_tools_deps

        assert article_detail_tools_deps["europe_pmc_service"] is mock_europe_pmc_service
        assert article_detail_tools_deps["logger"] is logger

        # 调用工具函数
        get_article_details(identifier="12345678")

        # 验证服务被正确调用
        mock_europe_pmc_service.fetch.assert_called_once()

    def test_multiple_tool_calls(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试多次工具调用"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        # 多次调用
        for i in range(3):
            result = get_article_details(identifier=f"1234567{i}")
            assert result["success"] is True

        # 验证服务被调用多次
        assert mock_europe_pmc_service.fetch.call_count == 3

    def test_different_id_types(self, mock_mcp, mock_europe_pmc_service, logger):
        """测试不同的标识符类型"""
        tools = register_article_detail_tools(mock_mcp, mock_europe_pmc_service, logger)
        get_article_details = tools[0]

        test_cases = [("12345678", "pmid"), ("10.1234/test", "doi"), ("PMC12345678", "pmcid")]

        for identifier, id_type in test_cases:
            result = get_article_details(identifier=identifier, id_type=id_type)
            assert result["success"] is True
            mock_europe_pmc_service.fetch.assert_called_with(
                identifier, id_type=id_type, mode="sync", include_fulltext=False
            )
