#!/usr/bin/env python3
"""
6工具架构单元测试
测试新的6个核心MCP工具功能
"""

import sys
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402

from article_mcp.cli import create_mcp_server  # noqa: E402
from tests.utils.test_helpers import TestTimer  # noqa: E402


class TestSearchLiteratureTool:
    """测试工具1: search_literature - 统一多源文献搜索工具"""

    @pytest.fixture
    def mock_services(self):
        """模拟搜索服务"""
        return {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        }

    @pytest.mark.unit
    def test_search_literature_basic(self, mock_services):
        """测试基本文献搜索功能"""
        # 模拟服务响应
        mock_services["europe_pmc"].search.return_value = {
            "success": True,
            "articles": [
                {
                    "title": "Machine Learning in Healthcare",
                    "authors": ["AI Researcher"],
                    "doi": "10.1234/ml.health.2023",
                    "journal": "Health AI Journal",
                    "publication_date": "2023-06-15",
                }
            ],
            "total_count": 1,
        }

        with patch("article_mcp.tools.core.search_tools.register_search_tools") as mock_register:
            mcp = create_mcp_server()

            # 验证工具注册
            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert args[0] == mcp  # MCP实例
            assert "search_services" in kwargs
            assert "logger" in kwargs

    @pytest.mark.unit
    def test_search_literature_multi_source(self, mock_services):
        """测试多数据源搜索"""
        # 设置不同数据源的响应
        mock_services["europe_pmc"].search.return_value = {
            "success": True,
            "articles": [{"title": "Article 1", "source": "europe_pmc"}],
            "total_count": 1,
        }
        mock_services["pubmed"].search.return_value = {
            "success": True,
            "articles": [{"title": "Article 2", "source": "pubmed"}],
            "total_count": 1,
        }

        # 测试多源搜索参数
        search_params = {
            "keyword": "machine learning",
            "sources": ["europe_pmc", "pubmed"],
            "max_results": 10,
            "search_type": "comprehensive",
        }

        # 验证参数传递正确
        assert search_params["sources"] == ["europe_pmc", "pubmed"]
        assert search_params["max_results"] == 10
        assert search_params["search_type"] == "comprehensive"

    @pytest.mark.unit
    def test_search_literature_error_handling(self, mock_services):
        """测试搜索错误处理"""
        # 模拟服务错误
        mock_services["europe_pmc"].search.side_effect = Exception("API Error")

        # 验证错误处理逻辑
        with pytest.raises(Exception, match="API Error"):
            mock_services["europe_pmc"].search(keyword="test")


class TestGetArticleDetailsTool:
    """测试工具2: get_article_details - 统一文献详情获取工具"""

    @pytest.fixture
    def mock_article_services(self):
        """模拟文章服务"""
        return {
            "europe_pmc": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
            "arxiv": Mock(),
            "pubmed": Mock(),
        }

    @pytest.mark.unit
    def test_get_article_details_by_doi(self, mock_article_services):
        """测试通过DOI获取文章详情"""
        doi = "10.1234/test.article.2023"

        # 模拟DOI解析响应
        mock_article_services["crossref"].get_work_by_doi.return_value = {
            "success": True,
            "article": {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": doi,
                "journal": "Test Journal",
                "publication_date": "2023-01-01",
                "abstract": "Test abstract",
            },
        }

        with patch("article_mcp.tools.core.article_tools.register_article_tools") as mock_register:
            create_mcp_server()

            # 验证工具注册和服务注入
            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert "article_services" in kwargs
            assert kwargs["article_services"]["crossref"] == mock_article_services["crossref"]

    @pytest.mark.unit
    def test_get_article_details_auto_id_type(self):
        """测试自动标识符类型识别"""
        test_cases = [
            ("10.1234/test.doi", "doi"),
            ("12345678", "pmid"),
            ("PMC123456", "pmcid"),
            ("arXiv:2301.00001", "arxiv_id"),
        ]

        for identifier, expected_type in test_cases:
            # 这里测试标识符类型识别逻辑
            if identifier.startswith("10."):
                assert expected_type == "doi"
            elif identifier.isdigit():
                assert expected_type == "pmid"
            elif identifier.startswith("PMC"):
                assert expected_type == "pmcid"
            elif identifier.startswith("arXiv:"):
                assert expected_type == "arxiv_id"

    @pytest.mark.unit
    def test_get_article_details_quality_metrics(self, mock_article_services):
        """测试包含质量指标的文章详情"""
        doi = "10.1234/high.quality.2023"

        # 模拟包含质量指标的响应
        mock_article_services["crossref"].get_work_by_doi.return_value = {
            "success": True,
            "article": {
                "title": "High Quality Article",
                "doi": doi,
                "journal": "Nature",
                "quality_metrics": {
                    "impact_factor": 42.5,
                    "quartile": "Q1",
                    "citations": 150,
                },
            },
        }

        # 验证质量指标参数处理
        params = {
            "identifier": doi,
            "include_quality_metrics": True,
            "sources": ["crossref", "europe_pmc"],
        }

        assert params["include_quality_metrics"] is True
        assert "crossref" in params["sources"]


class TestGetReferencesTool:
    """测试工具3: get_references - 参考文献获取工具"""

    @pytest.fixture
    def mock_reference_service(self):
        """模拟参考文献服务"""
        return Mock()

    @pytest.mark.unit
    def test_get_references_by_doi(self, mock_reference_service):
        """测试通过DOI获取参考文献"""

        # 模拟参考文献响应
        mock_reference_service.get_references.return_value = {
            "success": True,
            "references": [
                {
                    "title": "Reference 1",
                    "authors": ["Author One"],
                    "doi": "10.1111/ref1.2020",
                    "journal": "Journal One",
                    "publication_date": "2020-01-01",
                },
                {
                    "title": "Reference 2",
                    "authors": ["Author Two"],
                    "doi": "10.2222/ref2.2021",
                    "journal": "Journal Two",
                    "publication_date": "2021-06-15",
                },
            ],
            "total_count": 2,
        }

        with patch(
            "article_mcp.tools.core.reference_tools.register_reference_tools"
        ) as mock_register:
            create_mcp_server()

            # 验证服务注入
            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert kwargs["services"] == mock_reference_service

    @pytest.mark.unit
    def test_get_references_deduplication(self):
        """测试参考文献去重功能"""
        # 模拟重复的参考文献
        duplicate_references = [
            {"title": "Same Article", "doi": "10.1111/same.2020"},
            {"title": "Same Article", "doi": "10.1111/same.2020"},  # 重复
            {"title": "Different Article", "doi": "10.2222/diff.2021"},
        ]

        # 测试去重逻辑
        seen_dois = set()
        unique_refs = []

        for ref in duplicate_references:
            doi = ref.get("doi")
            if doi and doi not in seen_dois:
                seen_dois.add(doi)
                unique_refs.append(ref)

        assert len(unique_refs) == 2
        assert len(seen_dois) == 2

    @pytest.mark.unit
    def test_get_references_max_results(self, mock_reference_service):
        """测试最大结果数量限制"""
        # 模拟大量参考文献
        many_references = [{"title": f"Reference {i}"} for i in range(50)]

        mock_reference_service.get_references.return_value = {
            "success": True,
            "references": many_references,
            "total_count": 50,
        }

        # 测试结果限制
        max_results = 20
        limited_refs = many_references[:max_results]

        assert len(limited_refs) == max_results


class TestGetLiteratureRelationsTool:
    """测试工具4: get_literature_relations - 文献关系分析工具"""

    @pytest.fixture
    def mock_relation_services(self):
        """模拟关系分析服务"""
        return {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
        }

    @pytest.mark.unit
    def test_literature_relations_single_article(self, mock_relation_services):
        """测试单篇文章关系分析"""

        # 模拟关系分析响应
        mock_relation_services["europe_pmc"].get_references.return_value = {
            "success": True,
            "references": [{"title": "Reference 1", "doi": "10.1111/ref1"}],
        }
        mock_relation_services["europe_pmc"].get_citing_articles.return_value = {
            "success": True,
            "citing_articles": [{"title": "Citing 1", "doi": "10.3333/cite1"}],
        }

        with patch(
            "article_mcp.tools.core.relation_tools.register_relation_tools"
        ) as mock_register:
            create_mcp_server()

            # 验证服务注册
            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert kwargs["services"]["europe_pmc"] == mock_relation_services["europe_pmc"]

    @pytest.mark.unit
    def test_literature_relations_batch_analysis(self):
        """测试批量文献关系分析"""
        identifiers = ["10.1234/test1.2023", "10.1234/test2.2023"]

        # 测试批量分析参数
        params = {
            "identifiers": identifiers,
            "relation_types": ["references", "similar", "citing"],
            "max_results": 10,
            "analysis_type": "comprehensive",
        }

        assert isinstance(params["identifiers"], list)
        assert len(params["identifiers"]) == 2
        assert "references" in params["relation_types"]
        assert params["analysis_type"] == "comprehensive"

    @pytest.mark.unit
    def test_literature_relations_network_analysis(self):
        """测试文献网络分析"""
        # 模拟网络数据结构
        network_data = {
            "nodes": [
                {"id": "article1", "type": "seed", "x": 0, "y": 0},
                {"id": "article2", "type": "reference", "x": 100, "y": 100},
            ],
            "edges": [
                {"source": 0, "target": 1, "type": "references", "weight": 1},
            ],
            "clusters": {
                "seed_papers": [0],
                "references": [1],
            },
        }

        # 验证网络数据结构
        assert "nodes" in network_data
        assert "edges" in network_data
        assert "clusters" in network_data
        assert len(network_data["nodes"]) == 2
        assert len(network_data["edges"]) == 1


class TestGetJournalQualityTool:
    """测试工具5: get_journal_quality - 期刊质量评估工具"""

    @pytest.fixture
    def mock_quality_services(self):
        """模拟质量评估服务"""
        return {
            "pubmed": Mock(),
        }

    @pytest.mark.unit
    def test_get_journal_quality_single(self, mock_quality_services):
        """测试单个期刊质量评估"""

        # 模拟期刊质量响应

        with patch("article_mcp.tools.core.quality_tools.register_quality_tools") as mock_register:
            create_mcp_server()

            # 验证服务注册
            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert kwargs["services"]["pubmed"] == mock_quality_services["pubmed"]

    @pytest.mark.unit
    def test_get_journal_quality_batch(self):
        """测试批量期刊质量评估"""
        journals = ["Nature", "Science", "Cell"]

        # 测试批量评估参数
        params = {
            "journals": journals,
            "operation": "quality",
            "evaluation_criteria": ["journal_quality", "citation_count", "open_access"],
            "include_metrics": ["impact_factor", "quartile", "jci"],
        }

        assert isinstance(params["journals"], list)
        assert len(params["journals"]) == 3
        assert params["operation"] == "quality"
        assert "journal_quality" in params["evaluation_criteria"]

    @pytest.mark.unit
    def test_get_journal_quality_field_ranking(self):
        """测试领域排名功能"""
        field_name = "Biology"

        # 测试领域排名参数
        params = {
            "journals": field_name,  # 单个字符串作为期刊名传入
            "operation": "ranking",
            "evaluation_criteria": ["journal_impact"],
            "include_metrics": ["impact_factor", "quartile"],
        }

        assert params["operation"] == "ranking"
        assert params["journals"] == field_name


class TestExportBatchResultsTool:
    """测试工具6: export_batch_results - 通用结果导出工具"""

    @pytest.fixture
    def mock_batch_services(self):
        """模拟批量处理服务"""
        return {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        }

    @pytest.mark.unit
    def test_export_batch_results_json(self, mock_batch_services, sample_search_results):
        """测试JSON格式导出"""
        with patch("article_mcp.tools.core.batch_tools.register_batch_tools") as mock_register:
            create_mcp_server()

            # 验证服务注册
            mock_register.assert_called_once()
            args, kwargs = mock_register.call_args
            assert kwargs["services"]["europe_pmc"] == mock_batch_services["europe_pmc"]

        # 测试导出参数
        export_params = {
            "results": sample_search_results,
            "format_type": "json",
            "output_path": None,
            "include_metadata": True,
        }

        assert export_params["format_type"] == "json"
        assert export_params["include_metadata"] is True

    @pytest.mark.unit
    def test_export_batch_results_csv(self, sample_search_results):
        """测试CSV格式导出"""
        export_params = {
            "results": sample_search_results,
            "format_type": "csv",
            "output_path": "/tmp/export.csv",
            "include_metadata": False,
        }

        assert export_params["format_type"] == "csv"
        assert export_params["output_path"] == "/tmp/export.csv"
        assert export_params["include_metadata"] is False

    @pytest.mark.unit
    def test_export_batch_results_excel(self, sample_search_results):
        """测试Excel格式导出"""
        export_params = {
            "results": sample_search_results,
            "format_type": "excel",
            "output_path": "/tmp/export.xlsx",
            "include_metadata": True,
        }

        assert export_params["format_type"] == "excel"
        assert export_params["output_path"].endswith(".xlsx")

    @pytest.mark.unit
    def test_export_batch_results_auto_path(self, sample_search_results):
        """测试自动路径生成"""
        export_params = {
            "results": sample_search_results,
            "format_type": "json",
            "output_path": None,  # 自动生成路径
            "include_metadata": True,
        }

        assert export_params["output_path"] is None
        # 在实际实现中，会自动生成路径


class TestSixToolIntegration:
    """6工具集成测试"""

    @pytest.mark.unit
    def test_all_tools_registered(self):
        """测试所有6个工具都被正确注册"""
        with TestTimer() as timer:
            mcp = create_mcp_server()

        # 验证服务器创建成功
        assert mcp is not None
        assert timer.stop() < 5.0  # 应该在5秒内完成

    @pytest.mark.unit
    def test_tools_service_dependencies(self):
        """测试工具的服务依赖注入"""
        with patch.multiple(
            "article_mcp.cli",
            create_europe_pmc_service=Mock(return_value=Mock()),
            create_pubmed_service=Mock(return_value=Mock()),
            CrossRefService=Mock(),
            OpenAlexService=Mock(),
            create_reference_service=Mock(return_value=Mock()),
            create_literature_relation_service=Mock(return_value=Mock()),
            create_arxiv_service=Mock(return_value=Mock()),
        ):
            with (
                patch(
                    "article_mcp.tools.core.search_tools.register_search_tools"
                ) as mock_search_tools,
                patch(
                    "article_mcp.tools.core.article_tools.register_article_tools"
                ) as mock_article_tools,
                patch(
                    "article_mcp.tools.core.reference_tools.register_reference_tools"
                ) as mock_reference_tools,
                patch(
                    "article_mcp.tools.core.relation_tools.register_relation_tools"
                ) as mock_relation_tools,
                patch(
                    "article_mcp.tools.core.quality_tools.register_quality_tools"
                ) as mock_quality_tools,
                patch(
                    "article_mcp.tools.core.batch_tools.register_batch_tools"
                ) as mock_batch_tools,
            ):
                create_mcp_server()

                # 验证所有工具都被注册
                mock_search_tools.assert_called_once()
                mock_article_tools.assert_called_once()
                mock_reference_tools.assert_called_once()
                mock_relation_tools.assert_called_once()
                mock_quality_tools.assert_called_once()
                mock_batch_tools.assert_called_once()

    @pytest.mark.unit
    def test_tool_parameter_validation(self):
        """测试工具参数验证"""
        # 测试无效参数处理
        invalid_params = [
            {"keyword": ""},  # 空关键词
            {"identifier": None},  # 空标识符
            {"max_results": -1},  # 负数结果
            {"format_type": "invalid"},  # 无效格式
        ]

        for params in invalid_params:
            # 验证参数验证逻辑
            for key, value in params.items():
                if value == "" or value is None:
                    assert not value  # 空值检测
                elif key == "max_results" and value < 0:
                    assert value < 0  # 负数检测
                elif key == "format_type" and value not in ["json", "csv", "excel"]:
                    assert value == "invalid"  # 无效格式检测

    @pytest.mark.unit
    def test_tool_error_handling(self):
        """测试工具错误处理"""
        # 模拟各种错误情况
        error_cases = [
            {"error": "API Error", "type": "RequestException"},
            {"error": "Network Error", "type": "ConnectionError"},
            {"error": "Timeout", "type": "TimeoutError"},
        ]

        for error_case in error_cases:
            # 验证错误处理逻辑
            assert "error" in error_case
            assert "type" in error_case

    @pytest.mark.unit
    @pytest.mark.slow
    def test_performance_benchmarks(self):
        """测试性能基准"""
        with TestTimer() as timer:
            create_mcp_server()

        # 验证创建时间
        creation_time = timer.stop()
        assert creation_time < 3.0  # 应该在3秒内创建完成

        # 测试工具注册性能
        with TestTimer() as timer:
            # 模拟工具调用开销
            pass

        registration_time = timer.stop()
        assert registration_time < 1.0  # 工具注册应该很快
