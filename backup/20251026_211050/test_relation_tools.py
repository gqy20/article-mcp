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
文献关系工具单元测试
"""

from unittest.mock import Mock

import pytest

from article_mcp.tools.relation_tools import register_relation_tools


class TestRelationTools:
    """文献关系工具测试类"""

    @pytest.fixture
    def mock_mcp(self):
        """模拟 MCP 对象"""
        mcp = Mock()
        mcp.tool = Mock()
        return mcp

    @pytest.fixture
    def mock_literature_relation_service(self):
        """模拟文献关联服务"""
        service = Mock()
        service.get_similar_articles.return_value = {
            "original_article": {
                "title": "Original Article",
                "authors": ["Original Author"],
                "pmid": "12345678",
                "doi": "10.1234/original",
                "journal": "Test Journal",
                "abstract": "Original abstract",
            },
            "similar_articles": [
                {
                    "title": "Similar Article 1",
                    "authors": ["Similar Author 1"],
                    "pmid": "87654321",
                    "doi": "10.1234/similar1",
                },
                {
                    "title": "Similar Article 2",
                    "authors": ["Similar Author 2"],
                    "pmid": "11223344",
                    "doi": "10.1234/similar2",
                },
            ],
            "total_similar_count": 2,
            "retrieved_count": 2,
        }
        service.get_citing_articles.return_value = {
            "citing_articles": [
                {
                    "title": "Citing Article 1",
                    "authors": ["Citing Author 1"],
                    "pmid": "55556666",
                    "doi": "10.1234/citing1",
                }
            ],
            "total_count": 1,
        }
        service.get_all_relations.return_value = {
            "references": {"total_count": 5},
            "similar_articles": {"total_count": 2},
            "citing_articles": {"total_count": 1},
        }
        return service

    @pytest.fixture
    def logger(self):
        """模拟日志记录器"""
        return Mock()

    def test_register_relation_tools(self, mock_mcp, mock_literature_relation_service, logger):
        """测试文献关系工具注册"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)

        assert len(tools) == 3
        assert mock_mcp.tool.call_count == 3

        # 获取注册的工具
        tool_names = [tool.__name__ for tool in tools]
        assert "get_similar_articles" in tool_names
        assert "get_citing_articles" in tool_names
        assert "get_literature_relations" in tool_names

    def test_get_similar_articles_success(self, mock_mcp, mock_literature_relation_service, logger):
        """测试成功获取相似文章"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("10.1234/test")

        assert result["original_article"]["title"] == "Original Article"
        assert len(result["similar_articles"]) == 2
        assert result["total_similar_count"] == 2
        assert result["retrieved_count"] == 2
        assert result["similar_articles"][0]["title"] == "Similar Article 1"
        mock_literature_relation_service.get_similar_articles.assert_called_once_with(
            "10.1234/test", id_type="doi", max_results=20
        )

    def test_get_similar_articles_with_pmid(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试使用PMID获取相似文章"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("12345678", id_type="pmid")

        assert result["original_article"]["title"] == "Original Article"
        mock_literature_relation_service.get_similar_articles.assert_called_once_with(
            "12345678", id_type="pmid", max_results=20
        )

    def test_get_similar_articles_with_pmcid(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试使用PMCID获取相似文章"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("PMC12345678", id_type="pmcid")

        assert result["original_article"]["title"] == "Original Article"
        mock_literature_relation_service.get_similar_articles.assert_called_once_with(
            "PMC12345678", id_type="pmcid", max_results=20
        )

    def test_get_similar_articles_with_max_results(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试自定义最大结果数"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("10.1234/test", max_results=10)

        assert result["original_article"]["title"] == "Original Article"
        mock_literature_relation_service.get_similar_articles.assert_called_once_with(
            "10.1234/test", id_type="doi", max_results=10
        )

    def test_get_similar_articles_with_email(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试带邮箱参数"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("10.1234/test", email="test@example.com")

        assert result["original_article"]["title"] == "Original Article"
        # 注意：当前实现中没有使用email参数，但测试应该验证函数能正常处理

    def test_get_similar_articles_empty_identifier(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试空标识符"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("")

        assert result["original_article"] is None
        assert result["similar_articles"] == []
        assert result["total_similar_count"] == 0
        assert result["retrieved_count"] == 0
        assert "文献标识符不能为空" in result["error"]

    def test_get_similar_articles_whitespace_only(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试仅包含空白字符的标识符"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("   ")

        assert result["original_article"] is None
        assert "文献标识符不能为空" in result["error"]

    def test_get_similar_articles_trim_whitespace(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试去除标识符前后空白字符"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("  10.1234/test  ")

        assert result["original_article"]["title"] == "Original Article"
        mock_literature_relation_service.get_similar_articles.assert_called_once_with(
            "10.1234/test", id_type="doi", max_results=20
        )

    def test_get_similar_articles_service_exception(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试服务调用异常"""
        mock_literature_relation_service.get_similar_articles.side_effect = Exception(
            "Service Error"
        )

        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        result = get_similar_articles("10.1234/test")

        assert result["original_article"] is None
        assert result["similar_articles"] == []
        assert "Service Error" in result["error"]
        logger.error.assert_called_once()

    def test_get_citing_articles_success(self, mock_mcp, mock_literature_relation_service, logger):
        """测试成功获取引用文章"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_citing_articles = tools[1]

        result = get_citing_articles("12345678", id_type="pmid")

        assert len(result["citing_articles"]) == 1
        assert result["total_count"] == 1
        assert result["citing_articles"][0]["title"] == "Citing Article 1"
        mock_literature_relation_service.get_citing_articles.assert_called_once_with(
            "12345678", id_type="pmid", max_results=20
        )

    def test_get_citing_articles_empty_identifier(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试空标识符"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_citing_articles = tools[1]

        result = get_citing_articles("")

        assert result["citing_articles"] == []
        assert result["total_count"] == 0
        assert "文献标识符不能为空" in result["error"]

    def test_get_citing_articles_service_exception(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试服务调用异常"""
        mock_literature_relation_service.get_citing_articles.side_effect = Exception(
            "Network Error"
        )

        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_citing_articles = tools[1]

        result = get_citing_articles("12345678")

        assert result["citing_articles"] == []
        assert result["total_count"] == 0
        assert "Network Error" in result["error"]
        logger.error.assert_called_once()

    def test_get_literature_relations_success(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试成功获取文献关联信息"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_literature_relations = tools[2]

        result = get_literature_relations("10.1234/test")

        assert "references" in result
        assert "similar_articles" in result
        assert "citing_articles" in result
        assert "processing_time" in result
        assert result["references"]["total_count"] == 5
        assert result["similar_articles"]["total_count"] == 2
        assert result["citing_articles"]["total_count"] == 1
        mock_literature_relation_service.get_all_relations.assert_called_once_with(
            "10.1234/test", id_type="doi", max_results=20
        )

    def test_get_literature_relations_empty_identifier(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试空标识符"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_literature_relations = tools[2]

        result = get_literature_relations("")

        assert result["references"] == {}
        assert result["similar_articles"] == {}
        assert result["citing_articles"] == {}
        assert "文献标识符不能为空" in result["error"]
        assert "processing_time" in result

    def test_get_literature_relations_service_exception(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试服务调用异常"""
        mock_literature_relation_service.get_all_relations.side_effect = Exception("Database Error")

        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_literature_relations = tools[2]

        result = get_literature_relations("10.1234/test")

        assert result["references"] == {}
        assert result["similar_articles"] == {}
        assert result["citing_articles"] == {}
        assert "Database Error" in result["error"]
        assert "processing_time" in result
        logger.error.assert_called_once()

    def test_get_literature_relations_processing_time(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试处理时间计算"""
        import time

        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_literature_relations = tools[2]

        start_time = time.time()
        result = get_literature_relations("10.1234/test")
        end_time = time.time()

        assert "processing_time" in result
        assert 0 <= result["processing_time"] <= (end_time - start_time + 0.1)

    def test_dependency_injection(self, mock_mcp, mock_literature_relation_service, logger):
        """测试依赖注入"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)

        # 验证依赖已正确注入
        from article_mcp.tools.relation_tools import relation_tools_deps

        assert (
            relation_tools_deps["literature_relation_service"] is mock_literature_relation_service
        )
        assert relation_tools_deps["logger"] is logger

    def test_multiple_tool_calls(self, mock_mcp, mock_literature_relation_service, logger):
        """测试多次工具调用"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]
        get_citing_articles = tools[1]
        get_literature_relations = tools[2]

        # 多次调用不同工具
        for i in range(3):
            result = get_similar_articles(f"10.1234/test{i}")
            assert result["original_article"]["title"] == "Original Article"

        citing_result = get_citing_articles("12345678")
        assert citing_result["total_count"] == 1

        relations_result = get_literature_relations("10.1234/comprehensive")
        assert "processing_time" in relations_result

        # 验证服务被调用正确的次数
        assert mock_literature_relation_service.get_similar_articles.call_count == 3
        assert mock_literature_relation_service.get_citing_articles.call_count == 1
        assert mock_literature_relation_service.get_all_relations.call_count == 1

    def test_id_type_case_conversion(self, mock_mcp, mock_literature_relation_service, logger):
        """测试ID类型大小写转换"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)
        get_similar_articles = tools[0]

        # 使用大写的ID类型
        result = get_similar_articles("10.1234/test", id_type="DOI")

        assert result["original_article"]["title"] == "Original Article"
        mock_literature_relation_service.get_similar_articles.assert_called_once_with(
            "10.1234/test", id_type="doi", max_results=20
        )

    def test_max_results_parameter_propagation(
        self, mock_mcp, mock_literature_relation_service, logger
    ):
        """测试max_results参数传递"""
        tools = register_relation_tools(mock_mcp, mock_literature_relation_service, logger)

        # 测试不同工具的max_results参数
        get_similar_articles = tools[0]
        get_citing_articles = tools[1]
        get_literature_relations = tools[2]

        get_similar_articles("10.1234/test", max_results=5)
        mock_literature_relation_service.get_similar_articles.assert_called_with(
            "10.1234/test", id_type="doi", max_results=5
        )

        get_citing_articles("10.1234/test", max_results=15)
        mock_literature_relation_service.get_citing_articles.assert_called_with(
            "10.1234/test", id_type="doi", max_results=15
        )

        get_literature_relations("10.1234/test", max_results=8)
        mock_literature_relation_service.get_all_relations.assert_called_with(
            "10.1234/test", id_type="doi", max_results=8
        )
