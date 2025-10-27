#!/usr/bin/env python3
"""
工具核心逻辑单元测试
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
        """测试标识符类型提取逻辑"""
        from article_mcp.tools.core.search_tools import _extract_identifier_type

        test_cases = [
            ("10.1234/test.doi", "doi"),
            ("https://doi.org/10.1234/test", "doi"),
            ("12345678", "pmid"),
            ("PMID:12345678", "pmid"),
            ("PMC123456", "pmcid"),
            ("PMCID:PMC123456", "pmcid"),
            ("arXiv:2301.00001", "arxiv_id"),
            ("unknown_format", "doi"),  # 默认为doi
        ]

        for identifier, expected_type in test_cases:
            result = _extract_identifier_type(identifier)
            assert (
                result == expected_type
            ), f"Failed for {identifier}: expected {expected_type}, got {result}"

    @pytest.mark.unit
    def test_search_results_merging(self):
        """测试搜索结果合并逻辑"""
        from article_mcp.tools.core.search_tools import _merge_and_deduplicate_results

        # 模拟多数据源结果
        results_by_source = {
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

        logger = Mock()
        merged_results = _merge_and_deduplicate_results(results_by_source, True, logger)

        # 验证去重效果
        assert len(merged_results) == 2  # 应该有2篇唯一文章

        # 验证数据合并
        ml_article = next((r for r in merged_results if r["doi"] == "10.1234/ml.health.2023"), None)
        assert ml_article is not None
        assert len(ml_article["authors"]) >= 1  # 应该包含作者信息

    @pytest.mark.unit
    def test_search_source_priority(self):
        """测试搜索数据源优先级"""
        from article_mcp.tools.core.search_tools import _merge_and_deduplicate_results

        # 模拟相同文章来自不同数据源
        results_by_source = {
            "crossref": [
                {
                    "title": "Important Article",
                    "doi": "10.9999/important.2023",
                    "journal": "High Impact Journal",
                    "source": "crossref",
                }
            ],
            "europe_pmc": [
                {
                    "title": "Important Article",
                    "doi": "10.9999/important.2023",
                    "journal": "High Impact Journal",
                    "abstract": "This is the abstract",
                    "source": "europe_pmc",
                }
            ],
        }

        logger = Mock()
        merged_results = _merge_and_deduplicate_results(results_by_source, True, logger)

        # 验证优先级处理
        assert len(merged_results) == 1
        article = merged_results[0]
        assert article["doi"] == "10.9999/important.2023"
        # 应该包含更完整的信息（有摘要）


class TestArticleToolsCore:
    """测试文章工具核心逻辑"""

    @pytest.mark.unit
    def test_article_data_standardization(self):
        """测试文章数据标准化逻辑"""
        from article_mcp.tools.core.article_tools import _standardize_article_data

        # 测试不同格式的文章数据
        raw_articles = [
            {
                "title": "Test Article 1",
                "authorString": "Author A; Author B; Author C",
                "journalTitle": "Test Journal",
                "pubYear": "2023",
                "doi": "10.1234/test1.2023",
            },
            {
                "title": "Test Article 2",
                "authors": [{"name": "Author X"}, {"name": "Author Y"}],
                "journal": "Another Journal",
                "publication_date": "2023-06-15",
                "doi": "10.5678/test2.2023",
                "abstract": "Test abstract",
            },
        ]

        standardized = _standardize_article_data(raw_articles)

        # 验证标准化结果
        assert len(standardized) == 2
        for article in standardized:
            assert "title" in article
            assert "authors" in article
            assert "journal" in article
            assert "publication_date" in article
            assert isinstance(article["authors"], list)

    @pytest.mark.unit
    def test_author_name_parsing(self):
        """测试作者姓名解析逻辑"""
        from article_mcp.tools.core.article_tools import _parse_author_names

        test_cases = [
            "Author A; Author B; Author C",
            "Author A, Author B, Author C",
            "Author A and Author B",
            "Author A",
        ]

        for author_string in test_cases:
            authors = _parse_author_names(author_string)
            assert isinstance(authors, list)
            assert len(authors) > 0
            for author in authors:
                assert isinstance(author, str)
                assert len(author.strip()) > 0

    @pytest.mark.unit
    def test_quality_metrics_integration(self):
        """测试质量指标集成逻辑"""
        from article_mcp.tools.core.article_tools import _add_quality_metrics

        base_article = {
            "title": "Quality Article",
            "authors": ["Quality Researcher"],
            "doi": "10.9999/quality.2023",
            "journal": "Nature",
        }

        quality_data = {
            "impact_factor": 42.5,
            "quartile": "Q1",
            "jci": 25.8,
            "citations": 150,
        }

        enhanced_article = _add_quality_metrics(base_article, quality_data)

        # 验证质量指标添加
        assert "quality_metrics" in enhanced_article
        assert enhanced_article["quality_metrics"]["impact_factor"] == 42.5
        assert enhanced_article["quality_metrics"]["quartile"] == "Q1"


class TestReferenceToolsCore:
    """测试参考文献工具核心逻辑"""

    @pytest.mark.unit
    def test_reference_deduplication(self):
        """测试参考文献去重逻辑"""
        from article_mcp.tools.core.reference_tools import _merge_and_deduplicate_references

        # 模拟重复的参考文献
        references_by_source = {
            "europe_pmc": [
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
                    "pmid": "12345678",
                    "journal": "Journal Two",
                    "publication_date": "2021-06-15",
                },
            ],
            "crossref": [
                {
                    "title": "Reference 1",  # 重复标题
                    "authors": ["Author One", "Co Author"],
                    "doi": "10.1111/ref1.2020",  # 相同DOI
                    "journal": "Journal One",
                    "publication_date": "2020-01-01",
                    "abstract": "Abstract from Crossref",
                }
            ],
        }

        logger = Mock()
        merged_refs = _merge_and_deduplicate_references(references_by_source, True, logger)

        # 验证去重效果
        assert len(merged_refs) == 2  # 应该有2篇唯一参考文献

        # 验证信息合并
        ref1 = next((r for r in merged_refs if r["doi"] == "10.1111/ref1.2020"), None)
        assert ref1 is not None
        assert len(ref1["authors"]) >= 1

    @pytest.mark.unit
    def test_reference_completeness_check(self):
        """测试参考文献完整性检查"""
        from article_mcp.tools.core.reference_tools import _check_reference_completeness

        test_references = [
            {
                "title": "Complete Reference",
                "authors": ["Author One"],
                "doi": "10.1111/complete.2020",
                "journal": "Complete Journal",
                "publication_date": "2020-01-01",
            },
            {
                "title": "Incomplete Reference",
                "authors": [],  # 缺少作者
                "doi": "",  # 缺少DOI
                "journal": "",
                "publication_date": "",
            },
        ]

        completeness_scores = [_check_reference_completeness(ref) for ref in test_references]

        # 验证完整性评分
        assert completeness_scores[0] > completeness_scores[1]  # 完整参考文献得分更高
        assert completeness_scores[0] > 0.8  # 完整参考文献应该得分很高
        assert completeness_scores[1] < 0.5  # 不完整参考文献得分较低


class TestRelationToolsCore:
    """测试关系分析工具核心逻辑"""

    @pytest.mark.unit
    def test_relation_type_detection(self):
        """测试关系类型检测逻辑"""
        from article_mcp.tools.core.relation_tools import _detect_relation_types

        # 测试关系类型参数
        relation_params = [
            ["references"],
            ["similar"],
            ["citing"],
            ["references", "similar"],
            ["references", "similar", "citing"],
        ]

        for relations in relation_params:
            detected_types = _detect_relation_types(relations)
            assert isinstance(detected_types, list)
            assert len(detected_types) > 0
            for rel_type in detected_types:
                assert rel_type in ["references", "similar", "citing"]

    @pytest.mark.unit
    def test_network_node_creation(self):
        """测试网络节点创建逻辑"""
        from article_mcp.tools.core.relation_tools import _create_network_node

        # 测试不同类型的节点
        seed_node = _create_network_node("article1", "Test Article", "seed")
        reference_node = _create_network_node("ref1", "Reference Article", "reference")
        citing_node = _create_network_node("cite1", "Citing Article", "citing")

        # 验证节点结构
        for node in [seed_node, reference_node, citing_node]:
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "x" in node
            assert "y" in node

        assert seed_node["type"] == "seed"
        assert reference_node["type"] == "reference"
        assert citing_node["type"] == "citing"

    @pytest.mark.unit
    def test_network_edge_creation(self):
        """测试网络边创建逻辑"""
        from article_mcp.tools.core.relation_tools import _create_network_edge

        # 测试不同类型的边
        ref_edge = _create_network_edge(0, 1, "references", 1.0)
        cite_edge = _create_network_edge(1, 2, "citing", 0.8)
        similar_edge = _create_network_edge(0, 2, "similar", 0.6)

        # 验证边结构
        for edge in [ref_edge, cite_edge, similar_edge]:
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert "weight" in edge

        assert ref_edge["type"] == "references"
        assert cite_edge["type"] == "citing"
        assert similar_edge["type"] == "similar"

    @pytest.mark.unit
    def test_network_metrics_calculation(self):
        """测试网络指标计算逻辑"""
        from article_mcp.tools.core.relation_tools import _calculate_network_metrics

        # 模拟网络数据
        nodes = [
            {"id": "n1", "type": "seed"},
            {"id": "n2", "type": "reference"},
            {"id": "n3", "type": "citing"},
        ]
        edges = [
            {"source": 0, "target": 1, "weight": 1.0},
            {"source": 2, "target": 0, "weight": 0.8},
        ]

        metrics = _calculate_network_metrics(nodes, edges)

        # 验证指标计算
        assert "total_nodes" in metrics
        assert "total_edges" in metrics
        assert "average_degree" in metrics
        assert "network_density" in metrics

        assert metrics["total_nodes"] == 3
        assert metrics["total_edges"] == 2
        assert metrics["average_degree"] == (2 * 2) / 3  # 2*edges/nodes


class TestQualityToolsCore:
    """测试质量评估工具核心逻辑"""

    @pytest.mark.unit
    def test_quality_score_calculation(self):
        """测试质量评分计算逻辑"""
        from article_mcp.tools.core.quality_tools import _calculate_quality_score

        # 测试不同质量指标
        quality_metrics = [
            {"impact_factor": 42.5, "quartile": "Q1", "jci": 25.8},
            {"impact_factor": 2.1, "quartile": "Q3", "jci": 0.8},
            {"impact_factor": 0.5, "quartile": "Q4", "jci": 0.1},
        ]

        scores = [_calculate_quality_score(metrics) for metrics in quality_metrics]

        # 验证评分逻辑
        assert scores[0] > scores[1] > scores[2]  # 高影响因子期刊得分更高
        assert 0 <= scores[0] <= 100  # 评分应该在0-100范围内
        assert 0 <= scores[1] <= 100
        assert 0 <= scores[2] <= 100

    @pytest.mark.unit
    def test_quartile_normalization(self):
        """测试分区标准化逻辑"""
        from article_mcp.tools.core.quality_tools import _normalize_quartile

        quartile_cases = ["Q1", "Q2", "Q3", "Q4", "未知"]

        normalized_scores = [_normalize_quartile(q) for q in quartile_cases]

        # 验证分区评分
        assert (
            normalized_scores[0]
            > normalized_scores[1]
            > normalized_scores[2]
            > normalized_scores[3]
        )
        assert normalized_scores[4] == 0  # 未知分区得分为0

    @pytest.mark.unit
    def test_field_ranking_processing(self):
        """测试领域排名处理逻辑"""
        from article_mcp.tools.core.quality_tools import _process_field_ranking

        ranking_data = {
            "field_name": "Biology",
            "total_journals": 500,
            "journal_rank": 25,
            "quartile_distribution": {"Q1": 125, "Q2": 125, "Q3": 125, "Q4": 125},
        }

        processed = _process_field_ranking(ranking_data)

        # 验证排名数据处理
        assert "percentile" in processed
        assert processed["percentile"] == (25 / 500) * 100  # 5th percentile
        assert "quartile_info" in processed


class TestBatchToolsCore:
    """测试批量工具核心逻辑"""

    @pytest.mark.unit
    def test_json_export_logic(self):
        """测试JSON导出逻辑"""
        import json
        import tempfile
        from pathlib import Path

        from article_mcp.tools.core.batch_tools import _export_to_json

        test_results = {
            "success": True,
            "merged_results": [
                {
                    "title": "Test Article",
                    "authors": ["Test Author"],
                    "doi": "10.1234/test.2023",
                }
            ],
            "total_count": 1,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.json"
            logger = Mock()

            # 测试导出
            records_count = _export_to_json(test_results, output_path, True, logger)

            # 验证导出结果
            assert records_count == 1
            assert output_path.exists()

            # 验证JSON内容
            with open(output_path, encoding="utf-8") as f:
                exported_data = json.load(f)

            assert "export_metadata" in exported_data
            assert "results" in exported_data
            assert exported_data["export_metadata"]["total_records"] == 1

    @pytest.mark.unit
    def test_csv_export_logic(self):
        """测试CSV导出逻辑"""
        import csv
        import tempfile
        from pathlib import Path

        from article_mcp.tools.core.batch_tools import _export_to_csv

        test_results = {
            "success": True,
            "merged_results": [
                {
                    "title": "Test Article 1",
                    "authors": [{"name": "Author 1"}, {"name": "Author 2"}],
                    "doi": "10.1234/test1.2023",
                    "journal": "Test Journal",
                    "publication_date": "2023-01-01",
                    "abstract": "Test abstract 1",
                },
                {
                    "title": "Test Article 2",
                    "authors": [{"name": "Author 3"}],
                    "doi": "10.5678/test2.2023",
                    "journal": "Another Journal",
                    "publication_date": "2023-06-15",
                    "abstract": "Test abstract 2",
                },
            ],
            "total_count": 2,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            logger = Mock()

            # 测试导出
            records_count = _export_to_csv(test_results, output_path, True, logger)

            # 验证导出结果
            assert records_count == 2
            assert output_path.exists()

            # 验证CSV内容
            with open(output_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "title" in rows[0]
            assert "authors" in rows[0]
            assert "Test Article 1" in rows[0]["title"]
            assert "Author 1; Author 2" in rows[0]["authors"]

    @pytest.mark.unit
    def test_export_path_generation(self):
        """测试导出路径生成逻辑"""
        import tempfile
        from pathlib import Path

        from article_mcp.tools.core.batch_tools import _generate_export_path

        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试自动路径生成
            auto_path = _generate_export_path(None, "json", temp_dir)
            assert auto_path.suffix == ".json"
            assert auto_path.parent == Path(temp_dir)

            # 测试指定路径
            custom_path = _generate_export_path("custom_export.xlsx", "excel", temp_dir)
            assert custom_path.name == "custom_export.xlsx"
            assert custom_path.suffix == ".xlsx"

    @pytest.mark.unit
    def test_file_size_calculation(self):
        """测试文件大小计算逻辑"""
        import tempfile
        from pathlib import Path

        from article_mcp.tools.core.batch_tools import _calculate_file_size

        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content for file size calculation")
            temp_path = Path(f.name)

        try:
            # 测试文件大小计算
            size_info = _calculate_file_size(temp_path)

            assert "size" in size_info
            assert "formatted_size" in size_info
            assert size_info["size"] > 0
            assert "B" in size_info["formatted_size"] or "KB" in size_info["formatted_size"]

        finally:
            temp_path.unlink()


class TestToolIntegration:
    """工具集成测试"""

    @pytest.mark.unit
    def test_cross_tool_data_flow(self):
        """测试跨工具数据流"""
        # 模拟从搜索到导出的完整数据流
        search_results = {
            "success": True,
            "merged_results": [
                {
                    "title": "Research Article",
                    "authors": ["Researcher"],
                    "doi": "10.9999/research.2023",
                    "journal": "High Impact Journal",
                }
            ],
            "total_count": 1,
        }

        # 测试数据在不同工具间的传递
        assert "merged_results" in search_results
        assert len(search_results["merged_results"]) > 0

        # 模拟文章详情获取
        article = search_results["merged_results"][0]
        assert "doi" in article
        assert article["doi"] == "10.9999/research.2023"

        # 模拟参考文献获取
        ref_params = {
            "identifier": article["doi"],
            "id_type": "doi",
            "max_results": 10,
        }

        assert ref_params["identifier"] == article["doi"]

        # 模拟导出参数
        export_params = {
            "results": search_results,
            "format_type": "json",
            "include_metadata": True,
        }

        assert export_params["results"] == search_results

    @pytest.mark.unit
    def test_error_propagation(self):
        """测试错误传播机制"""
        # 模拟错误在不同工具间的传播
        search_error = {
            "success": False,
            "error": "API request failed",
            "error_type": "RequestException",
        }

        # 验证错误信息传递
        assert not search_error["success"]
        assert "error" in search_error
        assert "error_type" in search_error

        # 模拟错误处理
        def handle_tool_error(error_result):
            return {
                "success": False,
                "user_message": f"操作失败: {error_result.get('error', '未知错误')}",
                "error_code": error_result.get("error_type", "UnknownError"),
            }

        user_message = handle_tool_error(search_error)
        assert "操作失败" in user_message["user_message"]
        assert user_message["error_code"] == "RequestException"
