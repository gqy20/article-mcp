#!/usr/bin/env python3
"""
测试辅助工具和模拟数据生成器
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class MockDataGenerator:
    """模拟数据生成器"""

    @staticmethod
    def create_article(
        title: str = "Test Article",
        authors: list[str] = None,
        doi: str = "10.1000/test",
        pmid: str = "12345678",
        pmcid: str = "PMC1234567",
        **kwargs,
    ) -> dict[str, Any]:
        """创建模拟文章数据"""
        if authors is None:
            authors = ["Test Author", "Second Author"]

        article = {
            "title": title,
            "authors": authors,
            "doi": doi,
            "pmid": pmid,
            "pmcid": pmcid,
            "journal": kwargs.get("journal", "Test Journal"),
            "publication_date": kwargs.get("publication_date", "2023-01-01"),
            "abstract": kwargs.get("abstract", "This is a test article abstract."),
            "keywords": kwargs.get("keywords", ["test", "article"]),
            "url": kwargs.get("url", f"https://doi.org/{doi}"),
            "source": kwargs.get("source", "test"),
        }

        # 添加额外字段
        article.update(kwargs)
        return article

    @staticmethod
    def create_search_results(count: int = 5, **kwargs) -> dict[str, Any]:
        """创建模拟搜索结果"""
        articles = []
        for i in range(count):
            article = MockDataGenerator.create_article(
                title=f"Test Article {i + 1}",
                doi=f"10.1000/test-{i + 1}",
                pmid=f"{12345678 + i}",
                **kwargs,
            )
            articles.append(article)

        return {
            "articles": articles,
            "total_count": count,
            "query": kwargs.get("query", "test query"),
            "search_time": kwargs.get("search_time", 1.5),
        }

    @staticmethod
    def create_reference_list(count: int = 10, **kwargs) -> list[dict[str, Any]]:
        """创建模拟参考文献列表"""
        references = []
        for i in range(count):
            ref = MockDataGenerator.create_article(
                title=f"Reference Article {i + 1}",
                doi=f"10.1000/ref-{i + 1}",
                pmid=f"{20000000 + i}",
                **kwargs,
            )
            references.append(ref)
        return references


class TestTimer:
    """测试计时器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    def stop(self) -> float:
        """停止计时并返回耗时"""
        if self.end_time is None:
            self.end_time = time.time()
        return self.end_time - self.start_time

    def elapsed(self) -> float:
        """获取已经过的时间"""
        current_time = time.time()
        return current_time - self.start_time if self.start_time else 0


class MockResponse:
    """模拟HTTP响应"""

    def __init__(
        self,
        json_data: dict[str, Any] = None,
        status_code: int = 200,
        text: str = "",
        ok: bool = True,
    ):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.ok = ok

    def json(self) -> dict[str, Any]:
        return self.json_data


def create_mock_service(service_class, **method_returns):
    """创建模拟服务实例"""
    service = Mock(spec=service_class)

    for method_name, return_value in method_returns.items():
        mock_method = Mock(return_value=return_value)
        if asyncio.iscoroutinefunction(return_value) or hasattr(return_value, "__await__"):
            mock_method = asyncio.coroutine(lambda r=return_value: r)()
        setattr(service, method_name, mock_method)

    return service


def assert_valid_article_structure(article: dict[str, Any]) -> None:
    """验证文章结构的有效性"""
    required_fields = ["title", "authors"]
    for field in required_fields:
        assert field in article, f"文章缺少必需字段: {field}"
        assert article[field], f"文章字段 {field} 不能为空"

    # 验证作者字段
    assert isinstance(article["authors"], list), "作者字段必须是列表"
    assert len(article["authors"]) > 0, "作者列表不能为空"

    # 验证可选的标识符字段
    for id_field in ["doi", "pmid", "pmcid"]:
        if id_field in article and article[id_field]:
            assert isinstance(article[id_field], str), f"{id_field} 必须是字符串"


def assert_valid_search_results(results: dict[str, Any]) -> None:
    """验证搜索结果结构的有效性"""
    required_fields = ["articles", "total_count"]
    for field in required_fields:
        assert field in results, f"搜索结果缺少必需字段: {field}"

    assert isinstance(results["articles"], list), "articles 字段必须是列表"
    assert isinstance(results["total_count"], int), "total_count 必须是整数"
    assert results["total_count"] >= 0, "total_count 不能为负数"

    # 验证文章数量一致性
    if "articles" in results:
        actual_count = len(results["articles"])
        assert results["total_count"] >= actual_count, "total_count 应该大于等于实际文章数量"

    # 验证每篇文章的结构
    for i, article in enumerate(results["articles"]):
        try:
            assert_valid_article_structure(article)
        except AssertionError as e:
            raise AssertionError(f"第 {i + 1} 篇文章结构无效: {e}") from e


def run_async_with_timeout(coro, timeout: float = 10.0):
    """运行异步协程并设置超时"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
    except asyncio.TimeoutError:
        raise TimeoutError(f"操作在 {timeout} 秒后超时") from None
    finally:
        if not loop.is_running():
            loop.close()


# 测试标记
pytest_plugins = ["pytest_asyncio"]

# 默认配置
DEFAULT_TEST_CONFIG = {
    "test_keyword": "machine learning",
    "test_doi": "10.1000/test-article",
    "test_pmid": "12345678",
    "max_results": 10,
    "timeout": 30.0,
}


@pytest.fixture
def mock_logger():
    """模拟日志记录器fixture"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def test_config():
    """测试配置fixture"""
    return DEFAULT_TEST_CONFIG.copy()


@pytest.fixture
def mock_search_results():
    """模拟搜索结果fixture"""
    return MockDataGenerator.create_search_results(5)


@pytest.fixture
def mock_article_details():
    """模拟文章详情fixture"""
    return MockDataGenerator.create_article()


@pytest.fixture
def mock_reference_list():
    """模拟参考文献列表fixture"""
    return MockDataGenerator.create_reference_list(10)


class SixToolTestHelper:
    """6工具架构专用测试辅助工具"""

    @staticmethod
    def create_six_tool_test_data() -> dict[str, Any]:
        """创建完整的6工具测试数据"""
        return {
            # 工具1搜索数据
            "search_data": {
                "keyword": "machine learning healthcare",
                "sources": ["europe_pmc", "pubmed", "arxiv"],
                "max_results": 20,
                "search_type": "comprehensive",
            },
            # 工具2文章详情数据
            "article_details_data": {
                "identifier": "10.1234/ml.health.2023",
                "id_type": "doi",
                "sources": ["crossref", "europe_pmc"],
                "include_quality_metrics": True,
            },
            # 工具3参考文献数据
            "references_data": {
                "identifier": "10.1234/ml.health.2023",
                "id_type": "doi",
                "sources": ["europe_pmc"],
                "max_results": 25,
                "include_metadata": True,
            },
            # 工具4关系分析数据
            "relations_data": {
                "identifiers": ["10.1234/ml.health.2023"],
                "relation_types": ["references", "similar", "citing"],
                "max_depth": 2,
                "max_results": 15,
            },
            # 工具5质量评估数据
            "quality_data": {
                "journals": ["Nature", "Science", "Cell"],
                "operation": "quality",
                "evaluation_criteria": ["journal_quality", "citation_count"],
                "include_metrics": ["impact_factor", "quartile", "jci"],
            },
            # 工具6导出数据
            "export_data": {
                "format_type": "json",
                "output_path": None,
                "include_metadata": True,
            },
        }

    @staticmethod
    def create_workflow_scenarios() -> dict[str, dict[str, Any]]:
        """创建真实工作流程场景"""
        return {
            "researcher_review": {
                "description": "研究者文献综述工作流程",
                "steps": [
                    {
                        "tool": "search_literature",
                        "params": {"keyword": "AI healthcare", "max_results": 50},
                    },
                    {
                        "tool": "get_article_details",
                        "params": {
                            "identifier": "doi_from_search",
                            "include_quality_metrics": True,
                        },
                    },
                    {
                        "tool": "get_references",
                        "params": {"identifier": "selected_articles", "max_results": 20},
                    },
                    {
                        "tool": "get_journal_quality",
                        "params": {"journals": "all_journals", "operation": "quality"},
                    },
                    {"tool": "export_batch_results", "params": {"format_type": "excel"}},
                ],
                "expected_tools_used": 5,
            },
            "student_assignment": {
                "description": "学生作业工作流程",
                "steps": [
                    {
                        "tool": "search_literature",
                        "params": {"keyword": "ethics AI", "max_results": 15},
                    },
                    {"tool": "get_article_details", "params": {"identifier": "top_3_articles"}},
                    {"tool": "export_batch_results", "params": {"format_type": "csv"}},
                ],
                "expected_tools_used": 3,
            },
            "clinical_evidence": {
                "description": "临床证据搜索工作流程",
                "steps": [
                    {
                        "tool": "search_literature",
                        "params": {"keyword": "immunotherapy lung cancer", "sources": ["pubmed"]},
                    },
                    {
                        "tool": "get_article_details",
                        "params": {
                            "identifier": "clinical_trials",
                            "include_quality_metrics": True,
                        },
                    },
                    {
                        "tool": "get_journal_quality",
                        "params": {"journals": "relevant_journals", "operation": "ranking"},
                    },
                    {
                        "tool": "export_batch_results",
                        "params": {"format_type": "json", "include_metadata": True},
                    },
                ],
                "expected_tools_used": 4,
            },
        }

    @staticmethod
    def create_performance_benchmarks() -> dict[str, dict[str, Any]]:
        """创建性能基准测试数据"""
        return {
            "search_performance": {
                "small_query": {"expected_time": 2.0, "max_memory": 20},
                "medium_query": {"expected_time": 5.0, "max_memory": 50},
                "large_query": {"expected_time": 15.0, "max_memory": 100},
            },
            "details_performance": {
                "single_article": {"expected_time": 1.0, "max_memory": 10},
                "batch_articles": {"expected_time": 8.0, "max_memory": 80},
            },
            "export_performance": {
                "json_export": {"expected_time": 0.5, "max_memory": 15},
                "csv_export": {"expected_time": 1.0, "max_memory": 25},
                "excel_export": {"expected_time": 2.0, "max_memory": 40},
            },
        }

    @staticmethod
    def assert_valid_six_tool_response(tool_name: str, response: dict[str, Any]) -> None:
        """验证6工具响应格式的有效性"""
        # 通用验证
        assert isinstance(response, dict), f"{tool_name} 响应必须是字典"
        assert "success" in response, f"{tool_name} 响应缺少 success 字段"
        assert isinstance(response["success"], bool), f"{tool_name} success 必须是布尔值"

        if response["success"]:
            # 成功响应的特定验证
            if tool_name == "search_literature":
                assert "merged_results" in response, f"{tool_name} 缺少 merged_results"
                assert "total_count" in response, f"{tool_name} 缺少 total_count"
                assert isinstance(
                    response["merged_results"], list
                ), f"{tool_name} merged_results 必须是列表"

            elif tool_name == "get_article_details":
                assert "article" in response, f"{tool_name} 缺少 article"
                assert isinstance(response["article"], dict), f"{tool_name} article 必须是字典"

            elif tool_name == "get_references":
                assert "merged_references" in response, f"{tool_name} 缺少 merged_references"
                assert "total_count" in response, f"{tool_name} 缺少 total_count"

            elif tool_name == "get_literature_relations":
                assert "relations" in response, f"{tool_name} 缺少 relations"
                assert "statistics" in response, f"{tool_name} 缺少 statistics"

            elif tool_name == "get_journal_quality":
                assert "quality_metrics" in response, f"{tool_name} 缺少 quality_metrics"

            elif tool_name == "export_batch_results":
                assert "export_path" in response, f"{tool_name} 缺少 export_path"
                assert "records_exported" in response, f"{tool_name} 缺少 records_exported"
        else:
            # 失败响应的验证
            assert "error" in response, f"{tool_name} 失败响应缺少 error 字段"

    @staticmethod
    def create_error_response(tool_name: str, error_type: str, message: str) -> dict[str, Any]:
        """创建标准化的错误响应"""
        return {
            "success": False,
            "error": message,
            "error_type": error_type,
            "tool": tool_name,
            "timestamp": time.time(),
            "suggestion": SixToolTestHelper._get_error_suggestion(error_type),
        }

    @staticmethod
    def _get_error_suggestion(error_type: str) -> str:
        """根据错误类型提供建议"""
        suggestions = {
            "NetworkError": "请检查网络连接",
            "RateLimitError": "请稍后重试或减少请求频率",
            "AuthenticationError": "请检查API配置",
            "ValidationError": "请检查输入参数",
            "NotFoundError": "请检查标识符是否正确",
            "TimeoutError": "请稍后重试",
            "StorageError": "请检查磁盘空间",
        }
        return suggestions.get(error_type, "请联系技术支持")


class WorkflowTester:
    """工作流程测试器"""

    def __init__(self):
        self.helper = SixToolTestHelper()

    def test_workflow(self, scenario_name: str, mock_tools: dict[str, Mock]) -> dict[str, Any]:
        """测试完整工作流程"""
        scenarios = self.helper.create_workflow_scenarios()
        if scenario_name not in scenarios:
            raise ValueError(f"未知的工作流程场景: {scenario_name}")

        scenario = scenarios[scenario_name]
        results = []

        for step in scenario["steps"]:
            tool_name = step["tool"]
            params = step["params"]

            if tool_name in mock_tools:
                # 模拟工具调用
                mock_tool = mock_tools[tool_name]
                result = mock_tool.return_value
                results.append(
                    {
                        "tool": tool_name,
                        "params": params,
                        "result": result,
                        "success": True,
                    }
                )
            else:
                results.append(
                    {
                        "tool": tool_name,
                        "params": params,
                        "result": None,
                        "success": False,
                        "error": f"工具 {tool_name} 不可用",
                    }
                )

        return {
            "scenario": scenario_name,
            "description": scenario["description"],
            "steps_completed": len(results),
            "steps_successful": sum(1 for r in results if r["success"]),
            "expected_tools": scenario["expected_tools_used"],
            "actual_tools_used": len([r for r in results if r["success"]]),
            "results": results,
            "workflow_success": all(r["success"] for r in results),
        }


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.measurements = {}

    def start_measurement(self, name: str) -> None:
        """开始测量"""
        self.measurements[name] = {"start_time": time.time()}

    def end_measurement(self, name: str) -> float:
        """结束测量并返回耗时"""
        if name not in self.measurements:
            raise ValueError(f"测量 {name} 未开始")

        measurement = self.measurements[name]
        measurement["end_time"] = time.time()
        measurement["duration"] = measurement["end_time"] - measurement["start_time"]
        return measurement["duration"]

    def get_measurement(self, name: str) -> dict[str, Any]:
        """获取测量结果"""
        return self.measurements.get(name, {})

    def assert_performance_within_limits(self, name: str, max_time: float) -> None:
        """断言性能在限制内"""
        measurement = self.get_measurement(name)
        if "duration" not in measurement:
            raise AssertionError(f"测量 {name} 未完成")

        actual_time = measurement["duration"]
        assert (
            actual_time <= max_time
        ), f"性能测试失败: {name} 耗时 {actual_time:.2f}s 超过限制 {max_time:.2f}s"

    def reset(self) -> None:
        """重置所有测量"""
        self.measurements.clear()


# 新的fixture
@pytest.fixture
def six_tool_helper():
    """6工具测试辅助工具fixture"""
    return SixToolTestHelper()


@pytest.fixture
def workflow_tester():
    """工作流程测试器fixture"""
    return WorkflowTester()


@pytest.fixture
def performance_monitor():
    """性能监控器fixture"""
    return PerformanceMonitor()


@pytest.fixture
def workflow_scenarios():
    """工作流程场景fixture"""
    return SixToolTestHelper.create_workflow_scenarios()


@pytest.fixture
def performance_benchmarks():
    """性能基准测试数据fixture"""
    return SixToolTestHelper.create_performance_benchmarks()


@pytest.fixture
def mock_six_tool_responses():
    """模拟6工具响应fixture"""
    return {
        "search_literature": {
            "success": True,
            "keyword": "test query",
            "merged_results": [MockDataGenerator.create_article()],
            "total_count": 1,
            "search_time": 1.0,
        },
        "get_article_details": {
            "success": True,
            "identifier": "10.1234/test.2023",
            "article": MockDataGenerator.create_article(),
        },
        "get_references": {
            "success": True,
            "identifier": "10.1234/test.2023",
            "merged_references": [MockDataGenerator.create_article(title="Reference Article")],
            "total_count": 1,
            "processing_time": 0.5,
        },
        "get_literature_relations": {
            "success": True,
            "identifier": "10.1234/test.2023",
            "relations": {"references": [], "similar": [], "citing": []},
            "statistics": {"total_relations": 0},
        },
        "get_journal_quality": {
            "success": True,
            "journal_name": "Test Journal",
            "quality_metrics": {"impact_factor": 2.5, "quartile": "Q2"},
        },
        "export_batch_results": {
            "success": True,
            "export_path": "/tmp/test_export.json",
            "format_type": "json",
            "records_exported": 1,
            "file_size": "1.2KB",
        },
    }
