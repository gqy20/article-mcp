#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期刊质量工具单元测试
"""

import pytest
from unittest.mock import Mock, patch

# 添加src目录到Python路径
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from article_mcp.tools.quality_tools import register_quality_tools


class TestQualityTools:
    """期刊质量工具测试类"""

    @pytest.fixture
    def mock_mcp(self):
        """模拟 MCP 对象"""
        mcp = Mock()
        mcp.tool = Mock()
        return mcp

    @pytest.fixture
    def mock_pubmed_service(self):
        """模拟 PubMed 服务"""
        service = Mock()
        service.get_journal_quality.return_value = {
            "journal_name": "Test Journal",
            "source": "easyscholar_api",
            "quality_metrics": {
                "impact_factor": 5.123,
                "sci_quartile": "Q1",
                "sci_zone": "医学1区",
                "jci": 2.456,
                "impact_factor_5year": 4.789,
            },
        }
        service.evaluate_articles_quality.return_value = [
            {
                "title": "Article 1",
                "journal": "Test Journal",
                "journal_quality": {"impact_factor": 5.123, "sci_quartile": "Q1"},
            },
            {
                "title": "Article 2",
                "journal": "Another Journal",
                "journal_quality": {"impact_factor": 3.456, "sci_quartile": "Q2"},
            },
        ]
        return service

    @pytest.fixture
    def logger(self):
        """模拟日志记录器"""
        return Mock()

    def test_register_quality_tools(self, mock_mcp, mock_pubmed_service, logger):
        """测试期刊质量工具注册"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)

        assert len(tools) == 2
        assert mock_mcp.tool.call_count == 2

        # 获取注册的工具
        tool_names = [tool.__name__ for tool in tools]
        assert "get_journal_quality" in tool_names
        assert "evaluate_articles_quality" in tool_names

    def test_get_journal_quality_success(self, mock_mcp, mock_pubmed_service, logger):
        """测试成功获取期刊质量"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]

        result = get_journal_quality("Test Journal")

        assert result["journal_name"] == "Test Journal"
        assert result["source"] == "easyscholar_api"
        assert "quality_metrics" in result
        assert result["quality_metrics"]["impact_factor"] == 5.123
        assert result["quality_metrics"]["sci_quartile"] == "Q1"
        mock_pubmed_service.get_journal_quality.assert_called_once()

    @pytest.mark.parametrize("journal_name", ["Nature", "Science", "Cell", "The Lancet"])
    def test_get_journal_quality_different_journals(
        self, mock_mcp, mock_pubmed_service, logger, journal_name
    ):
        """测试不同期刊的查询"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]

        result = get_journal_quality(journal_name)

        assert result["journal_name"] == journal_name
        mock_pubmed_service.get_journal_quality.assert_called_once()

    def test_get_journal_quality_with_secret_key(self, mock_mcp, mock_pubmed_service, logger):
        """测试带密钥的期刊质量查询"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]

        secret_key = "test_secret_key_12345"
        result = get_journal_quality("Test Journal", secret_key=secret_key)

        assert result["journal_name"] == "Test Journal"
        mock_pubmed_service.get_journal_quality.assert_called_once()

    def test_get_journal_quality_service_error(self, mock_mcp, mock_pubmed_service, logger):
        """测试服务调用错误"""
        mock_pubmed_service.get_journal_quality.return_value = {
            "journal_name": "Test Journal",
            "error": "Journal not found",
            "quality_metrics": None,
        }

        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]

        result = get_journal_quality("Unknown Journal")

        assert result["journal_name"] == "Test Journal"
        assert result["error"] == "Journal not found"
        assert result["quality_metrics"] is None

    def test_get_journal_quality_service_exception(self, mock_mcp, mock_pubmed_service, logger):
        """测试服务调用异常"""
        mock_pubmed_service.get_journal_quality.side_effect = Exception("API Error")

        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]

        # 异常应该向上传播，因为工具层没有try-catch
        with pytest.raises(Exception, match="API Error"):
            get_journal_quality("Test Journal")

    def test_evaluate_articles_quality_success(self, mock_mcp, mock_pubmed_service, logger):
        """测试成功批量评估文献质量"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        articles = [
            {"title": "Article 1", "journal": "Test Journal"},
            {"title": "Article 2", "journal": "Another Journal"},
        ]

        result = evaluate_articles_quality(articles)

        assert result["total_count"] == 2
        assert len(result["evaluated_articles"]) == 2
        assert "成功评估 2 篇文献的期刊质量" in result["message"]
        assert result["error"] is None
        assert result["evaluated_articles"][0]["journal_quality"]["impact_factor"] == 5.123
        assert result["evaluated_articles"][1]["journal_quality"]["sci_quartile"] == "Q2"
        mock_pubmed_service.evaluate_articles_quality.assert_called_once()

    def test_evaluate_articles_quality_empty_list(self, mock_mcp, mock_pubmed_service, logger):
        """测试空文献列表"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        result = evaluate_articles_quality([])

        assert result["total_count"] == 0
        assert len(result["evaluated_articles"]) == 0
        assert "没有文献需要评估" in result["message"]
        assert result["error"] is None
        mock_pubmed_service.evaluate_articles_quality.assert_not_called()

    def test_evaluate_articles_quality_with_secret_key(self, mock_mcp, mock_pubmed_service, logger):
        """测试带密钥的批量评估"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        articles = [{"title": "Article 1", "journal": "Test Journal"}]
        secret_key = "test_api_key_67890"

        result = evaluate_articles_quality(articles, secret_key=secret_key)

        assert result["total_count"] == 1
        assert "成功评估 1 篇文献的期刊质量" in result["message"]
        mock_pubmed_service.evaluate_articles_quality.assert_called_once()

    def test_evaluate_articles_quality_service_exception(
        self, mock_mcp, mock_pubmed_service, logger
    ):
        """测试服务调用异常"""
        mock_pubmed_service.evaluate_articles_quality.side_effect = Exception("Service Error")

        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        articles = [{"title": "Article 1", "journal": "Test Journal"}]

        result = evaluate_articles_quality(articles)

        assert result["total_count"] == 0
        assert len(result["evaluated_articles"]) == 0
        assert result["message"] is None
        assert "Service Error" in result["error"]
        assert "期刊质量评估失败" in result["error"]
        logger.error.assert_called_once()

    def test_evaluate_articles_quality_large_batch(self, mock_mcp, mock_pubmed_service, logger):
        """测试大批量文献评估"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        # 创建100篇文献
        articles = [{"title": f"Article {i}", "journal": f"Journal {i}"} for i in range(100)]
        mock_pubmed_service.evaluate_articles_quality.return_value = [
            {
                "title": f"Article {i}",
                "journal": f"Journal {i}",
                "journal_quality": {"impact_factor": i + 1},
            }
            for i in range(100)
        ]

        result = evaluate_articles_quality(articles)

        assert result["total_count"] == 100
        assert len(result["evaluated_articles"]) == 100
        assert "成功评估 100 篇文献的期刊质量" in result["message"]
        mock_pubmed_service.evaluate_articles_quality.assert_called_once()

    def test_evaluate_articles_quality_varied_article_formats(
        self, mock_mcp, mock_pubmed_service, logger
    ):
        """测试不同格式的文献"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        articles = [
            {"title": "Article 1", "journal": "Journal A", "doi": "10.1234/1"},
            {"title": "Article 2", "journal_name": "Journal B", "pmid": "12345678"},
            {"title": "Article 3", "journal": "Journal C", "authors": ["Author 1", "Author 2"]},
            {"title": "Article 4", "journal": ""},  # 空期刊名
        ]

        result = evaluate_articles_quality(articles)

        assert result["total_count"] == 4
        assert len(result["evaluated_articles"]) == 4
        mock_pubmed_service.evaluate_articles_quality.assert_called_once_with(articles, None)

    @patch("tool_modules.quality_tools.get_easyscholar_key")
    def test_easyscholar_key_integration(self, mock_get_key, mock_mcp, mock_pubmed_service, logger):
        """测试EasyScholar密钥集成"""
        mock_get_key.return_value = "integrated_key_12345"

        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]
        evaluate_articles_quality = tools[1]

        # 测试期刊质量查询
        get_journal_quality("Test Journal")
        mock_get_key.assert_called_with(None, logger)

        # 测试批量评估
        mock_get_key.reset_mock()
        evaluate_articles_quality([{"title": "Article 1"}])
        mock_get_key.assert_called_with(None, logger)

        # 测试带参数密钥
        mock_get_key.reset_mock()
        user_key = "user_provided_key"
        get_journal_quality("Test Journal", secret_key=user_key)
        mock_get_key.assert_called_with(user_key, logger)

    def test_dependency_injection(self, mock_mcp, mock_pubmed_service, logger):
        """测试依赖注入"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)

        # 验证依赖已正确注入
        from article_mcp.tools.quality_tools import quality_tools_deps

        assert quality_tools_deps["pubmed_service"] is mock_pubmed_service
        assert quality_tools_deps["logger"] is logger

    def test_multiple_tool_calls(self, mock_mcp, mock_pubmed_service, logger):
        """测试多次工具调用"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]
        evaluate_articles_quality = tools[1]

        # 多次调用期刊质量查询
        for i in range(3):
            result = get_journal_quality(f"Journal {i}")
            assert result["journal_name"] == f"Journal {i}"

        # 多次调用批量评估
        for i in range(2):
            articles = [{"title": f"Article {i}", "journal": f"Journal {i}"}]
            result = evaluate_articles_quality(articles)
            assert result["total_count"] == 1

        # 验证服务被调用正确的次数
        assert mock_pubmed_service.get_journal_quality.call_count == 3
        assert mock_pubmed_service.evaluate_articles_quality.call_count == 2

    def test_quality_metrics_structure(self, mock_mcp, mock_pubmed_service, logger):
        """测试质量指标结构"""
        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        get_journal_quality = tools[0]

        result = get_journal_quality("Test Journal")

        quality_metrics = result["quality_metrics"]
        expected_keys = ["impact_factor", "sci_quartile", "sci_zone", "jci", "impact_factor_5year"]

        for key in expected_keys:
            assert key in quality_metrics
            assert quality_metrics[key] is not None

    def test_error_handling_in_evaluation(self, mock_mcp, mock_pubmed_service, logger):
        """测试评估中的错误处理"""
        # 设置服务返回部分成功的结果
        mock_pubmed_service.evaluate_articles_quality.return_value = [
            {"title": "Article 1", "journal_quality": {"impact_factor": 5.0}},
            None,  # 失败的文章
            {"title": "Article 3", "journal_quality": {"impact_factor": 3.0}},
        ]

        tools = register_quality_tools(mock_mcp, mock_pubmed_service, logger)
        evaluate_articles_quality = tools[1]

        articles = [{"title": f"Article {i}"} for i in range(3)]
        result = evaluate_articles_quality(articles)

        # 应该返回服务提供的结果，即使包含None
        assert result["total_count"] == 3
        assert len(result["evaluated_articles"]) == 3
        assert result["evaluated_articles"][0] is not None
        assert result["evaluated_articles"][1] is None
        assert result["evaluated_articles"][2] is not None
