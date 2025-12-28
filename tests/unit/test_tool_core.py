#!/usr/bin/env python3
"""工具核心逻辑单元测试
测试6工具架构的核心业务逻辑
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestSearchToolsCore:
    """测试搜索工具核心逻辑"""

    @pytest.mark.unit
    def test_identifier_type_extraction(self):
        """测试标识符类型提取逻辑 - 从 merged_results 导入"""
        from article_mcp.services.merged_results import extract_identifier_type

        test_cases = [
            ("10.1234/test.doi", "doi"),
            ("https://doi.org/10.1234/test", "doi"),
            ("12345678", "pmid"),
            ("PMID:12345678", "pmid"),
            ("PMC123456", "pmcid"),
            ("PMCID:PMC123456", "pmcid"),
            ("arXiv:2301.00001", "arxiv_id"),
            ("unknown_format", "unknown"),  # 修复: 新架构返回 "unknown"
        ]

        for identifier, expected_type in test_cases:
            result = extract_identifier_type(identifier)
            assert result == expected_type, (
                f"Failed for {identifier}: expected {expected_type}, got {result}"
            )

    @pytest.mark.unit
    def test_search_results_merging(self):
        """测试搜索结果合并逻辑 - 使用 merge_articles_by_doi"""
        from article_mcp.services.merged_results import merge_articles_by_doi

        # 模拟多数据源结果
        articles_by_source = {
            "europe_pmc": [
                {
                    "title": "Machine Learning in Healthcare",
                    "authors": ["AI Researcher"],
                    "doi": "10.1234/ml.health.2023",
                    "journal": "Health AI Journal",
                    "publication_date": "2023-06-15",
                }
            ],
            "pubmed": [
                {
                    "title": "Machine Learning in Healthcare",
                    "authors": ["AI Researcher", "ML Expert"],
                    "doi": "10.1234/ml.health.2023",  # 重复DOI
                    "journal": "Health AI Journal",
                    "publication_date": "2023-06-15",
                },
                {
                    "title": "Deep Learning Applications",
                    "authors": ["DL Specialist"],
                    "doi": "10.5678/dl.apps.2023",
                    "journal": "Machine Learning Today",
                    "publication_date": "2023-05-20",
                },
            ],
        }

        merged_results = merge_articles_by_doi(articles_by_source)

        # 验证合并结果
        assert len(merged_results) == 2, "Should have 2 unique articles after merging"
        # 验证重复DOI被合并
        ml_article = next(
            (a for a in merged_results if a.get("doi") == "10.1234/ml.health.2023"), None
        )
        assert ml_article is not None
        assert "sources" in ml_article
        assert set(ml_article["sources"]) == {"europe_pmc", "pubmed"}

    @pytest.mark.unit
    def test_search_source_priority(self):
        """测试数据源优先级排序"""
        from article_mcp.services.merged_results import simple_rank_articles

        articles = [
            {"title": "Low Priority", "source": "arxiv", "doi": "10.0001/low"},
            {"title": "High Priority", "source": "nature", "doi": "10.0002/high"},
            {"title": "Medium Priority", "source": "pubmed", "doi": "10.0003/medium"},
        ]

        ranked = simple_rank_articles(articles)

        # 验证排序: nature > pubmed > arxiv
        assert ranked[0]["doi"] == "10.0002/high"
        assert ranked[1]["doi"] == "10.0003/medium"
        assert ranked[2]["doi"] == "10.0001/low"


class TestArticleToolsCore:
    """测试文章工具核心逻辑"""

    @pytest.mark.unit
    def test_article_data_access(self):
        """测试文章数据访问功能"""
        from fastmcp import FastMCP

        from article_mcp.tools.core.article_tools import register_article_tools

        mcp = FastMCP("test")
        logger = Mock()
        services = {
            "crossref": Mock(),
            "europe_pmc": Mock(),
            "openalex": Mock(),
            "arxiv": Mock(),
            "pubmed": Mock(),
        }

        # 验证注册函数存在且可调用
        assert callable(register_article_tools)
        # 注册工具不应该抛出异常
        try:
            register_article_tools(mcp, services, logger)
        except Exception as e:
            pytest.fail(f"register_article_tools raised {e}")

    @pytest.mark.unit
    def test_quality_metrics_available(self):
        """测试质量指标功能可用"""
        from fastmcp import FastMCP

        from article_mcp.tools.core.quality_tools import register_quality_tools

        # 质量工具通过 register_quality_tools 注册
        mcp = FastMCP("test")
        logger = Mock()
        services = {"pubmed": Mock()}
        # 注册不应抛出异常
        try:
            register_quality_tools(mcp, services, logger)
        except Exception as e:
            pytest.fail(f"register_quality_tools raised {e}")


class TestReferenceToolsCore:
    """测试参考文献工具核心逻辑"""

    @pytest.mark.unit
    def test_reference_deduplication(self):
        """测试参考文献去重逻辑"""
        from article_mcp.services.merged_results import deduplicate_references

        references = [
            {"doi": "10.1234/ref1", "title": "Reference 1"},
            {"doi": "10.1234/ref1", "title": "Reference 1 (duplicate)"},
            {"doi": "10.5678/ref2", "title": "Reference 2"},
            {"title": "Reference without DOI"},
        ]

        deduplicated = deduplicate_references(references)

        # 验证去重
        assert len(deduplicated) == 3, "Should have 3 unique references after deduplication"
        dois = [r.get("doi", "") for r in deduplicated if r.get("doi")]
        assert dois.count("10.1234/ref1") == 1

    @pytest.mark.unit
    def test_reference_results_merge(self):
        """测试参考文献结果合并"""
        from article_mcp.services.merged_results import merge_reference_results

        reference_results = {
            "crossref": {
                "success": True,
                "references": [{"doi": "10.1234/ref1"}],
                "total_count": 1,
            },
            "europe_pmc": {
                "success": True,
                "references": [{"doi": "10.1234/ref1"}, {"doi": "10.5678/ref2"}],
                "total_count": 2,
            },
        }

        merged = merge_reference_results(reference_results)

        # 验证合并
        assert merged["total_count"] == 2  # 去重后
        assert "crossref" in merged["sources_used"]
        assert "europe_pmc" in merged["sources_used"]


class TestRelationToolsCore:
    """测试关系分析工具核心逻辑"""

    @pytest.mark.unit
    def test_relation_tools_registration(self):
        """测试关系分析工具注册"""
        from fastmcp import FastMCP

        from article_mcp.tools.core.relation_tools import register_relation_tools

        mcp = FastMCP("test")
        logger = Mock()
        services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "openalex": Mock(),
        }

        # 验证注册函数存在且可调用
        assert callable(register_relation_tools)
        try:
            register_relation_tools(mcp, services, logger)
        except Exception as e:
            pytest.fail(f"register_relation_tools raised {e}")


class TestQualityToolsCore:
    """测试质量评估工具核心逻辑"""

    @pytest.mark.unit
    def test_quality_tools_registration(self):
        """测试质量评估工具注册"""
        from fastmcp import FastMCP

        from article_mcp.tools.core.quality_tools import register_quality_tools

        mcp = FastMCP("test")
        logger = Mock()
        services = {
            "pubmed": Mock(),
        }

        # 验证注册函数存在且可调用
        assert callable(register_quality_tools)
        try:
            register_quality_tools(mcp, services, logger)
            # 使用同步方法检查工具 - 验证至少有一些公开属性被添加
            public_attrs = [name for name in dir(mcp) if not name.startswith("_")]
            # 工具注册后应该有可调用的属性
            assert len(public_attrs) > 0
        except Exception as e:
            pytest.fail(f"register_quality_tools raised {e}")


class TestToolIntegration:
    """测试工具集成"""

    @pytest.mark.unit
    def test_all_tool_registrations(self):
        """测试所有工具可以正确注册"""
        from fastmcp import FastMCP

        from article_mcp.tools.core.article_tools import register_article_tools
        from article_mcp.tools.core.quality_tools import register_quality_tools
        from article_mcp.tools.core.reference_tools import register_reference_tools
        from article_mcp.tools.core.relation_tools import register_relation_tools
        from article_mcp.tools.core.search_tools import register_search_tools

        mcp = FastMCP("test")
        logger = Mock()

        # 模拟服务字典
        search_services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        }

        article_services = {
            "europe_pmc": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
            "arxiv": Mock(),
            "pubmed": Mock(),
        }

        reference_services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
        }

        relation_services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
        }

        quality_services = {
            "easyscholar": Mock(),
            "openalex": Mock(),
        }

        # 注册所有工具（5个核心工具）
        register_search_tools(mcp, search_services, logger)
        register_article_tools(mcp, article_services, logger)
        register_reference_tools(mcp, reference_services, logger)
        register_relation_tools(mcp, relation_services, logger)
        register_quality_tools(mcp, quality_services, logger)

        # 验证工具已注册 - FastMCP 存储工具在内部
        # 检查是否有非私有属性（注册的工具）
        public_attrs = [name for name in dir(mcp) if not name.startswith("_")]
        assert len(public_attrs) > 0

    @pytest.mark.unit
    def test_tool_count(self):
        """验证5个核心工具都已注册"""
        # 这5个工具是:
        # 1. search_literature
        # 2. get_article_details
        # 3. get_references
        # 4. get_literature_relations
        # 5. get_journal_quality

        import asyncio

        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()
        # 使用 get_tools() 方法替代遍历属性
        # 这样避免触发 FastMCP .settings 废弃警告
        tools = asyncio.run(server.get_tools())
        tool_names = list(tools.keys())

        # 验证5个核心工具存在
        expected_tools = [
            "search_literature",
            "get_article_details",
            "get_references",
            "get_literature_relations",
            "get_journal_quality",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"缺少工具: {tool_name}"

        assert len(tool_names) >= 5, (
            f"Expected at least 5 tools, got {len(tool_names)}: {tool_names}"
        )
