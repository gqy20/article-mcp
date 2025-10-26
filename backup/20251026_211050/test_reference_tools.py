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
参考文献工具单元测试
"""

from unittest.mock import Mock

import pytest

from article_mcp.tools.reference_tools import register_reference_tools


class TestReferenceTools:
    """参考文献工具测试类"""

    @pytest.fixture
    def mock_mcp(self):
        """模拟 MCP 对象"""
        mcp = Mock()
        mcp.tool = Mock()
        return mcp

    @pytest.fixture
    def mock_reference_service(self):
        """模拟参考文献服务"""
        service = Mock()
        service.batch_search_europe_pmc_by_dois.return_value = {
            "10.1234/test1": {
                "title": "Test Article 1",
                "authors": ["Author 1"],
                "doi": "10.1234/test1",
            },
            "10.1234/test2": {
                "title": "Test Article 2",
                "authors": ["Author 2"],
                "doi": "10.1234/test2",
            },
        }
        service._format_europe_pmc_metadata.side_effect = lambda x: x
        return service

    @pytest.fixture
    def mock_literature_relation_service(self):
        """模拟文献关联服务"""
        service = Mock()
        service.get_references.return_value = {
            "references": [
                {
                    "title": "Reference Article",
                    "authors": ["Ref Author"],
                    "doi": "10.5678/ref",
                    "year": 2023,
                }
            ],
            "total_count": 1,
            "success": True,
        }
        return service

    @pytest.fixture
    def logger(self):
        """模拟日志记录器"""
        return Mock()

    def test_register_reference_tools(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试参考文献工具注册"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )

        assert len(tools) == 2
        assert mock_mcp.tool.call_count == 2

        # 获取注册的工具
        tool_names = [tool.__name__ for tool in tools]
        assert "get_references_by_doi" in tool_names
        assert "batch_enrich_references_by_dois" in tool_names

    def test_get_references_by_doi_success(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试成功获取参考文献"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        get_references_by_doi = tools[0]

        result = get_references_by_doi("10.1234/test")

        assert result["success"] is True
        assert len(result["references"]) == 1
        assert result["total_count"] == 1
        assert result["references"][0]["title"] == "Reference Article"
        mock_literature_relation_service.get_references.assert_called_once_with(
            "10.1234/test", id_type="doi"
        )

    def test_get_references_by_doi_empty(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试空DOI"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        get_references_by_doi = tools[0]

        result = get_references_by_doi("")

        assert result["total_count"] == 0
        assert "DOI不能为空" in result["message"]
        assert "请提供有效的DOI" in result["error"]

    def test_get_references_by_doi_whitespace_only(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试仅包含空白字符的DOI"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        get_references_by_doi = tools[0]

        result = get_references_by_doi("   ")

        assert result["total_count"] == 0
        assert "DOI不能为空" in result["message"]

    def test_get_references_by_doi_trim_whitespace(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试去除DOI前后空白字符"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        get_references_by_doi = tools[0]

        result = get_references_by_doi("  10.1234/test  ")

        assert result["success"] is True
        mock_literature_relation_service.get_references.assert_called_once_with(
            "10.1234/test", id_type="doi"
        )

    def test_get_references_by_doi_service_exception(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试服务调用异常"""
        mock_literature_relation_service.get_references.side_effect = Exception("Service Error")

        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        get_references_by_doi = tools[0]

        result = get_references_by_doi("10.1234/test")

        assert result["total_count"] == 0
        assert "Service Error" in result["error"]
        assert "获取参考文献失败" in result["message"]

    def test_batch_enrich_references_by_dois_success(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试批量补全参考文献成功"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        dois = ["10.1234/test1", "10.1234/test2"]
        result = batch_enrich_references_by_dois(dois)

        assert result["total_dois_processed"] == 2
        assert result["successful_enrichments"] == 2
        assert len(result["failed_dois"]) == 0
        assert len(result["enriched_references"]) == 2
        assert "10.1234/test1" in result["enriched_references"]
        assert "10.1234/test2" in result["enriched_references"]
        assert "processing_time" in result
        assert "performance_metrics" in result

    def test_batch_enrich_references_by_dois_empty_list(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试空DOI列表"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        result = batch_enrich_references_by_dois([])

        assert result["total_dois_processed"] == 0
        assert result["successful_enrichments"] == 0
        assert "DOI列表为空" in result["error"]

    def test_batch_enrich_references_by_dois_too_many(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试DOI数量超过限制"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        # 创建25个DOI（超过20个限制）
        dois = [f"10.1234/test{i}" for i in range(25)]
        result = batch_enrich_references_by_dois(dois)

        assert result["total_dois_processed"] == 0
        assert result["successful_enrichments"] == 0
        assert len(result["failed_dois"]) == 25
        assert "DOI数量超过最大限制(20个)" in result["error"]

    def test_batch_enrich_references_by_dois_partial_failure(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试部分DOI处理失败"""
        # 设置服务只返回一个DOI的结果
        mock_reference_service.batch_search_europe_pmc_by_dois.return_value = {
            "10.1234/test1": {"title": "Test Article 1", "authors": ["Author 1"]}
            # test2 不在结果中
        }

        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        dois = ["10.1234/test1", "10.1234/test2"]
        result = batch_enrich_references_by_dois(dois)

        assert result["total_dois_processed"] == 2
        assert result["successful_enrichments"] == 1
        assert len(result["failed_dois"]) == 1
        assert "10.1234/test2" in result["failed_dois"]
        assert "10.1234/test1" in result["enriched_references"]

    def test_batch_enrich_references_by_dois_service_exception(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试服务调用异常"""
        mock_reference_service.batch_search_europe_pmc_by_dois.side_effect = Exception(
            "Service Error"
        )

        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        dois = ["10.1234/test1", "10.1234/test2"]
        result = batch_enrich_references_by_dois(dois)

        assert result["total_dois_processed"] == 0
        assert result["successful_enrichments"] == 0
        assert "Service Error" in result["error"]
        assert len(result["failed_dois"]) == 2

    def test_batch_enrich_references_by_dois_with_email(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试带邮箱参数的批量补全"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        dois = ["10.1234/test1"]
        result = batch_enrich_references_by_dois(dois, email="test@example.com")

        assert result["successful_enrichments"] == 1
        # 注意：当前实现中没有使用email参数，但测试应该验证函数能正常处理

    def test_batch_enrich_references_performance_metrics(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试性能指标计算"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        dois = ["10.1234/test1", "10.1234/test2"]
        result = batch_enrich_references_by_dois(dois)

        assert "performance_metrics" in result
        metrics = result["performance_metrics"]
        assert "average_time_per_doi" in metrics
        assert "success_rate" in metrics
        assert "estimated_speedup" in metrics
        assert metrics["success_rate"] == "100.0%"

    def test_dependency_injection(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试依赖注入"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )

        # 验证依赖已正确注入
        from article_mcp.tools.reference_tools import reference_tools_deps

        assert reference_tools_deps["reference_service"] is mock_reference_service
        assert (
            reference_tools_deps["literature_relation_service"] is mock_literature_relation_service
        )
        assert reference_tools_deps["logger"] is logger

    def test_format_europe_pmc_metadata_called(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试格式化函数被调用"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        batch_enrich_references_by_dois = tools[1]

        dois = ["10.1234/test1"]
        batch_enrich_references_by_dois(dois)

        # 验证格式化函数被调用
        mock_reference_service._format_europe_pmc_metadata.assert_called_once()

    def test_multiple_tool_calls(
        self, mock_mcp, mock_reference_service, mock_literature_relation_service, logger
    ):
        """测试多次工具调用"""
        tools = register_reference_tools(
            mock_mcp, mock_reference_service, mock_literature_relation_service, logger
        )
        get_references_by_doi = tools[0]
        batch_enrich_references_by_dois = tools[1]

        # 多次调用不同工具
        for i in range(3):
            result = get_references_by_doi(f"10.1234/test{i}")
            assert result["success"] is True

        batch_result = batch_enrich_references_by_dois(["10.1234/batch1", "10.1234/batch2"])
        assert batch_result["successful_enrichments"] == 2

        # 验证服务被调用正确的次数
        assert mock_literature_relation_service.get_references.call_count == 3
        assert mock_reference_service.batch_search_europe_pmc_by_dois.call_count == 1
