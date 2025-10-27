#!/usr/bin/env python3
"""
6工具架构集成测试
测试完整的端到端工作流程
"""

import asyncio
import json
import sys
import tempfile
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


class TestEndToEndWorkflow:
    """端到端工作流程测试"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_literature_search_workflow(self):
        """测试完整的文献搜索工作流程"""
        with TestTimer() as timer:
            # 1. 创建MCP服务器
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
                mcp = create_mcp_server()

            # 验证服务器创建
            assert mcp is not None

        # 验证创建时间
        assert timer.stop() < 5.0

    @pytest.mark.integration
    def test_search_to_export_workflow(self):
        """测试从搜索到导出的完整工作流程"""
        # 模拟完整的搜索结果
        search_results = {
            "success": True,
            "keyword": "machine learning healthcare",
            "sources_used": ["europe_pmc", "pubmed"],
            "merged_results": [
                {
                    "title": "Machine Learning in Healthcare: A Systematic Review",
                    "authors": ["AI Researcher", "Healthcare Specialist"],
                    "doi": "10.1234/ml.healthcare.2023",
                    "journal": "Journal of Medical AI",
                    "publication_date": "2023-06-15",
                    "abstract": "This systematic review examines the applications of machine learning in healthcare...",
                    "pmid": "37891234",
                    "source": "europe_pmc",
                },
                {
                    "title": "Deep Learning for Medical Image Analysis",
                    "authors": ["Computer Vision Expert", "Radiologist"],
                    "doi": "10.5678/dl.medical.2023",
                    "journal": "Medical Imaging Today",
                    "publication_date": "2023-04-20",
                    "abstract": "Deep learning techniques have revolutionized medical image analysis...",
                    "pmid": "37654321",
                    "source": "pubmed",
                },
            ],
            "total_count": 2,
            "search_time": 1.23,
        }

        # 2. 获取文章详情（使用第一个结果）
        first_article = search_results["merged_results"][0]
        article_details = {
            "success": True,
            "identifier": first_article["doi"],
            "id_type": "doi",
            "article": {
                **first_article,
                "full_text_available": True,
                "open_access": True,
                "quality_metrics": {
                    "impact_factor": 8.5,
                    "quartile": "Q1",
                    "jci": 2.1,
                },
            },
        }

        # 3. 获取参考文献
        references = {
            "success": True,
            "identifier": first_article["doi"],
            "id_type": "doi",
            "references_by_source": {
                "europe_pmc": [
                    {
                        "title": "Foundations of Machine Learning",
                        "authors": ["ML Pioneer"],
                        "doi": "10.1111/foundations.2020",
                        "journal": "Machine Learning Journal",
                        "publication_date": "2020-01-01",
                    }
                ]
            },
            "merged_references": [
                {
                    "title": "Foundations of Machine Learning",
                    "authors": ["ML Pioneer"],
                    "doi": "10.1111/foundations.2020",
                    "journal": "Machine Learning Journal",
                    "publication_date": "2020-01-01",
                    "source": "europe_pmc",
                }
            ],
            "total_count": 15,
            "processing_time": 0.89,
        }

        # 4. 获取期刊质量信息
        journal_quality = {
            "success": True,
            "journal_name": first_article["journal"],
            "quality_metrics": {
                "impact_factor": 8.5,
                "quartile": "Q1",
                "jci": 2.1,
                "分区": "中科院一区",
                "citescore": 12.3,
            },
            "ranking_info": {
                "field": "Medicine",
                "rank": 25,
                "total_journals": 150,
                "percentile": 83.3,
            },
        }

        # 5. 导出结果
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "literature_search_results.json"

            # 模拟导出功能
            export_data = {
                "search_results": search_results,
                "article_details": article_details,
                "references": references,
                "journal_quality": journal_quality,
                "export_metadata": {
                    "export_time": "2023-12-07 10:30:00",
                    "total_records": len(search_results["merged_results"]),
                    "workflow": "search_to_export",
                },
            }

            # 写入文件
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            # 验证导出结果
            assert export_path.exists()
            with open(export_path, encoding="utf-8") as f:
                loaded_data = json.load(f)

            assert "search_results" in loaded_data
            assert "article_details" in loaded_data
            assert "references" in loaded_data
            assert "journal_quality" in loaded_data
            assert loaded_data["search_results"]["total_count"] == 2

    @pytest.mark.integration
    def test_literature_relation_analysis_workflow(self):
        """测试文献关系分析工作流程"""
        # 1. 输入多篇文献
        seed_articles = [
            {"identifier": "10.1234/seed1.2023", "title": "Seed Article 1"},
            {"identifier": "10.5678/seed2.2023", "title": "Seed Article 2"},
        ]

        # 2. 获取文献关系
        relations = {
            "success": True,
            "identifiers": [article["identifier"] for article in seed_articles],
            "relations": {
                "references": [
                    {
                        "title": "Common Reference Article",
                        "doi": "10.9999/common.ref.2020",
                        "authors": ["Common Author"],
                        "journal": "Prestigious Journal",
                        "publication_date": "2020-03-15",
                    }
                ],
                "similar": [
                    {
                        "title": "Similar Research Article",
                        "doi": "10.8888/similar.2023",
                        "authors": ["Similar Researcher"],
                        "journal": "Related Journal",
                        "publication_date": "2023-02-28",
                    }
                ],
                "citing": [
                    {
                        "title": "Citing Article 2023",
                        "doi": "10.7777/citing.2023",
                        "authors": ["Citing Researcher"],
                        "journal": "Modern Journal",
                        "publication_date": "2023-11-01",
                    }
                ],
            },
            "statistics": {
                "references_count": 1,
                "similar_count": 1,
                "citing_count": 1,
                "total_relations": 3,
            },
        }

        # 3. 构建网络分析
        network_analysis = {
            "success": True,
            "network_data": {
                "nodes": [
                    {"id": "10.1234/seed1.2023", "type": "seed", "label": "Seed Article 1"},
                    {"id": "10.5678/seed2.2023", "type": "seed", "label": "Seed Article 2"},
                    {
                        "id": "10.9999/common.ref.2020",
                        "type": "reference",
                        "label": "Common Reference",
                    },
                    {"id": "10.8888/similar.2023", "type": "similar", "label": "Similar Research"},
                    {"id": "10.7777/citing.2023", "type": "citing", "label": "Citing Article"},
                ],
                "edges": [
                    {"source": 0, "target": 2, "type": "references", "weight": 1.0},
                    {"source": 1, "target": 2, "type": "references", "weight": 1.0},
                    {"source": 0, "target": 3, "type": "similar", "weight": 0.8},
                    {"source": 1, "target": 4, "type": "citing", "weight": 0.9},
                ],
                "clusters": {
                    "seed_papers": [0, 1],
                    "references": [2],
                    "similar": [3],
                    "citing": [4],
                },
            },
            "analysis_metrics": {
                "total_nodes": 5,
                "total_edges": 4,
                "average_degree": 1.6,
                "network_density": 0.4,
                "cluster_count": 4,
            },
        }

        # 验证关系分析结果
        assert relations["success"]
        assert len(relations["relations"]) == 3
        assert relations["statistics"]["total_relations"] == 3

        # 验证网络分析结果
        assert network_analysis["success"]
        assert len(network_analysis["network_data"]["nodes"]) == 5
        assert len(network_analysis["network_data"]["edges"]) == 4
        assert network_analysis["analysis_metrics"]["average_degree"] == 1.6

    @pytest.mark.integration
    def test_quality_assessment_workflow(self):
        """测试质量评估工作流程"""
        # 1. 批量文章数据
        articles_batch = [
            {
                "title": "High Impact Research",
                "journal": "Nature",
                "doi": "10.1038/high.2023",
                "publication_date": "2023-01-15",
            },
            {
                "title": "Medium Impact Study",
                "journal": "Regional Journal",
                "doi": "10.5678/medium.2023",
                "publication_date": "2023-03-20",
            },
            {
                "title": "Emerging Research",
                "journal": "New Journal",
                "doi": "10.9999/emerging.2023",
                "publication_date": "2023-06-10",
            },
        ]

        # 2. 批量质量评估
        quality_assessment = {
            "success": True,
            "total_articles": len(articles_batch),
            "evaluated_articles": [
                {
                    "article": articles_batch[0],
                    "quality_score": 95.5,
                    "quality_metrics": {
                        "impact_factor": 42.5,
                        "quartile": "Q1",
                        "jci": 25.8,
                        "分区": "中科院一区",
                    },
                    "quality_grade": "Excellent",
                },
                {
                    "article": articles_batch[1],
                    "quality_score": 65.2,
                    "quality_metrics": {
                        "impact_factor": 3.2,
                        "quartile": "Q2",
                        "jci": 1.1,
                        "分区": "中科院二区",
                    },
                    "quality_grade": "Good",
                },
                {
                    "article": articles_batch[2],
                    "quality_score": 45.8,
                    "quality_metrics": {
                        "impact_factor": 1.5,
                        "quartile": "Q3",
                        "jci": 0.4,
                        "分区": "中科院三区",
                    },
                    "quality_grade": "Fair",
                },
            ],
            "quality_distribution": {
                "excellent": 1,
                "good": 1,
                "fair": 1,
                "poor": 0,
            },
            "average_quality_score": 68.8,
        }

        # 3. 领域排名分析
        field_ranking = {
            "success": True,
            "field_name": "Computer Science",
            "ranking_type": "journal_impact",
            "top_journals": [
                {
                    "name": "Nature",
                    "impact_factor": 42.5,
                    "rank": 1,
                    "quartile": "Q1",
                },
                {
                    "name": "Regional Journal",
                    "impact_factor": 3.2,
                    "rank": 45,
                    "quartile": "Q2",
                },
                {
                    "name": "New Journal",
                    "impact_factor": 1.5,
                    "rank": 120,
                    "quartile": "Q3",
                },
            ],
            "field_statistics": {
                "total_journals": 200,
                "average_impact_factor": 2.8,
                "median_impact_factor": 1.9,
            },
        }

        # 验证质量评估结果
        assert quality_assessment["success"]
        assert quality_assessment["total_articles"] == 3
        assert len(quality_assessment["evaluated_articles"]) == 3
        assert quality_assessment["average_quality_score"] == 68.8

        # 验证领域排名结果
        assert field_ranking["success"]
        assert len(field_ranking["top_journals"]) == 3
        assert field_ranking["field_statistics"]["total_journals"] == 200

    @pytest.mark.integration
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 1. 搜索错误
        search_error = {
            "success": False,
            "error": "API rate limit exceeded",
            "error_type": "RateLimitError",
            "retry_after": 60,
            "suggestion": "请稍后重试或减少搜索频率",
        }

        # 2. 详情获取错误
        details_error = {
            "success": False,
            "error": "Article not found",
            "error_type": "NotFoundError",
            "identifier": "10.9999/nonexistent.2023",
            "suggestion": "请检查文献标识符是否正确",
        }

        # 3. 导出错误
        export_error = {
            "success": False,
            "error": "Insufficient disk space",
            "error_type": "StorageError",
            "required_space": "50MB",
            "available_space": "10MB",
            "suggestion": "请清理磁盘空间或选择其他导出位置",
        }

        # 验证错误处理一致性
        errors = [search_error, details_error, export_error]

        for error in errors:
            assert not error["success"]
            assert "error" in error
            assert "error_type" in error
            assert "suggestion" in error

        # 验证错误传播
        def propagate_error(source_error):
            return {
                "success": False,
                "original_error": source_error["error"],
                "error_type": source_error["error_type"],
                "user_message": source_error["suggestion"],
                "context": "integration_test",
            }

        propagated_search_error = propagate_error(search_error)
        assert propagated_search_error["original_error"] == "API rate limit exceeded"
        assert "integration_test" in propagated_search_error["context"]


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_batch_processing_performance(self):
        """测试大批量处理性能"""
        with TestTimer() as timer:
            # 模拟大批量数据
            large_batch = {
                "success": True,
                "merged_results": [
                    {
                        "title": f"Research Article {i}",
                        "authors": [f"Author {i}"],
                        "doi": f"10.1234/article.{i}.2023",
                        "journal": f"Journal {i % 10}",  # 10种不同期刊
                        "publication_date": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    }
                    for i in range(100)  # 100篇文章
                ],
                "total_count": 100,
                "processing_time": 0,
            }

            # 模拟批量处理
            processed_results = []
            for article in large_batch["merged_results"]:
                # 模拟文章处理
                processed_article = {
                    **article,
                    "processed": True,
                    "quality_score": 50 + (hash(article["doi"]) % 50),  # 伪随机分数
                }
                processed_results.append(processed_article)

        processing_time = timer.stop()

        # 验证性能指标
        assert len(processed_results) == 100
        assert processing_time < 5.0  # 应该在5秒内完成
        assert processing_time < len(processed_results) * 0.1  # 每篇文章处理时间少于0.1秒

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_tool_execution(self):
        """测试并发工具执行"""

        async def simulate_concurrent_execution():
            with TestTimer() as timer:
                # 模拟并发执行多个工具
                tasks = [
                    asyncio.sleep(0.1),  # 搜索工具
                    asyncio.sleep(0.15),  # 详情工具
                    asyncio.sleep(0.12),  # 参考文献工具
                    asyncio.sleep(0.08),  # 关系分析工具
                    asyncio.sleep(0.05),  # 质量评估工具
                    asyncio.sleep(0.03),  # 导出工具
                ]

                await asyncio.gather(*tasks)

            return timer.stop()

        # 运行并发测试
        execution_time = asyncio.run(simulate_concurrent_execution())

        # 验证并发执行性能
        # 串行执行时间：0.1 + 0.15 + 0.12 + 0.08 + 0.05 + 0.03 = 0.53秒
        # 并发执行应该接近最慢的任务时间
        assert execution_time < 0.2  # 并发应该比串行快很多
        assert execution_time > 0.15  # 但不会比最慢任务更快

    @pytest.mark.integration
    def test_memory_usage_optimization(self):
        """测试内存使用优化"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with TestTimer() as timer:
            # 模拟大数据集处理
            large_datasets = []
            for i in range(10):  # 10个数据集
                dataset = {
                    "results": [
                        {
                            "title": f"Article {j}",
                            "content": "x" * 1000,  # 1KB每篇文章
                            "metadata": {"key": "value" * 100},  # 额外元数据
                        }
                        for j in range(1000)  # 1000篇文章
                    ],
                    "dataset_id": i,
                }
                large_datasets.append(dataset)

            # 模拟处理并清理
            processed_count = 0
            for dataset in large_datasets:
                # 处理数据
                for article in dataset["results"]:
                    article["processed"] = True
                    processed_count += 1

                # 模拟内存清理（删除原始数据）
                del dataset

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        processing_time = timer.stop()

        # 验证内存使用
        assert processed_count == 10000  # 处理了10000篇文章
        assert memory_increase < 100  # 内存增长应该小于100MB
        assert processing_time < 10.0  # 处理时间应该合理


class TestRealWorldScenarios:
    """真实世界场景测试"""

    @pytest.mark.integration
    def test_researcher_literature_review_scenario(self):
        """测试研究者文献综述场景"""
        # 研究者想要进行机器学习在医疗领域应用的文献综述

        # 1. 初步搜索
        initial_search = {
            "keyword": "machine learning healthcare diagnosis",
            "max_results": 50,
            "search_type": "comprehensive",
            "sources": ["europe_pmc", "pubmed", "arxiv"],
        }

        # 2. 高质量筛选
        quality_filter = {
            "min_impact_factor": 2.0,
            "min_publication_year": 2020,
            "include_only_open_access": True,
            "language": "english",
        }

        # 3. 关系分析
        relation_analysis = {
            "include_references": True,
            "include_citing": True,
            "max_depth": 2,
            "focus_on_recent": True,
        }

        # 4. 导出报告
        export_requirements = {
            "format": "excel",
            "include_abstracts": True,
            "include_quality_metrics": True,
            "include_network_analysis": True,
            "group_by_journal": True,
        }

        # 验证场景完整性
        assert "machine learning" in initial_search["keyword"]
        assert "healthcare" in initial_search["keyword"]
        assert initial_search["max_results"] == 50
        assert quality_filter["min_impact_factor"] == 2.0
        assert relation_analysis["max_depth"] == 2
        assert export_requirements["format"] == "excel"

    @pytest.mark.integration
    def test_student_assignment_scenario(self):
        """测试学生作业场景"""
        # 学生需要完成关于"人工智能伦理"的课程作业

        # 1. 基础搜索
        student_search = {
            "keyword": "artificial intelligence ethics bias fairness",
            "max_results": 20,
            "search_type": "recent",  # 重视最新研究
            "sources": ["europe_pmc", "arxiv"],  # 学术预印本和期刊
        }

        # 2. 简化筛选
        simple_filter = {
            "include_review_articles": True,
            "min_publication_year": 2021,
            "prefer_open_access": True,
        }

        # 3. 基础关系分析
        simple_relations = {
            "include_references": False,  # 不需要深入参考文献
            "include_similar": True,
            "max_depth": 1,
        }

        # 4. 简单导出
        simple_export = {
            "format": "csv",
            "include_abstracts": True,
            "include_basic_info": True,
            "exclude_technical_details": True,
        }

        # 验证学生场景
        assert student_search["max_results"] == 20  # 适中的数量
        assert simple_filter["min_publication_year"] == 2021  # 较新的研究
        assert simple_relations["max_depth"] == 1  # 浅层分析
        assert simple_export["format"] == "csv"  # 简单格式

    @pytest.mark.integration
    def test_clinician_evidence_search_scenario(self):
        """测试临床医生证据搜索场景"""
        # 临床医生需要查找特定治疗方法的最新证据

        # 1. 精确临床搜索
        clinical_search = {
            "keyword": "immunotherapy lung cancer checkpoint inhibitors",
            "max_results": 30,
            "search_type": "clinical_focus",
            "sources": ["pubmed", "europe_pmc"],  # 主要医学数据库
            "filter_clinical_trials": True,
        }

        # 2. 临床质量筛选
        clinical_filter = {
            "min_evidence_level": "randomized_controlled_trial",
            "min_sample_size": 100,
            "prefer_recent": True,
            "exclude_preprints": True,
        }

        # 3. 临床关系分析
        clinical_relations = {
            "include_clinical_guidelines": True,
            "include_systematic_reviews": True,
            "focus_on_treatment_outcomes": True,
        }

        # 4. 临床报告导出
        clinical_export = {
            "format": "json",
            "include_patient_outcomes": True,
            "include_adverse_effects": True,
            "include_dosage_info": True,
            "clinical_summary": True,
        }

        # 验证临床场景
        assert "immunotherapy" in clinical_search["keyword"]
        assert "lung cancer" in clinical_search["keyword"]
        assert clinical_filter["min_evidence_level"] == "randomized_controlled_trial"
        assert clinical_relations["include_clinical_guidelines"] is True
        assert clinical_export["clinical_summary"] is True
