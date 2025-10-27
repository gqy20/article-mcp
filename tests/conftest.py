"""
pytest 配置和共享 fixtures
"""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# 延迟导入，只在需要时导入
def _import_services():
    try:
        from article_mcp.services.crossref_service import CrossRefService
        from article_mcp.services.europe_pmc import EuropePMCService
        from article_mcp.services.openalex_service import OpenAlexService
        from article_mcp.services.pubmed_search import PubMedService

        return CrossRefService, EuropePMCService, OpenAlexService, PubMedService
    except ImportError:
        # 测试环境下返回Mock类
        return Mock, Mock, Mock, Mock


@pytest.fixture
def logger():
    """提供测试用的 logger"""
    logger = logging.getLogger("test")
    logger.setLevel(logging.WARNING)
    return logger


@pytest.fixture
def mock_crossref_service(logger):
    """提供模拟的 CrossRef 服务"""
    CrossRefService, _, _, _ = _import_services()
    service = Mock(spec=CrossRefService)
    service.search_works.return_value = {
        "success": True,
        "articles": [
            {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test",
                "journal": "Test Journal",
                "publication_date": "2023-01-01",
                "source": "crossref",
            }
        ],
        "total_count": 1,
        "source": "crossref",
    }
    service.get_work_by_doi.return_value = {
        "success": True,
        "article": {
            "title": "Test Article",
            "authors": ["Test Author"],
            "doi": "10.1234/test",
            "journal": "Test Journal",
            "publication_date": "2023-01-01",
            "source": "crossref",
        },
        "source": "crossref",
    }
    return service


@pytest.fixture
def mock_openalex_service(logger):
    """提供模拟的 OpenAlex 服务"""
    _, _, OpenAlexService, _ = _import_services()
    service = Mock(spec=OpenAlexService)
    service.search_works.return_value = {
        "success": True,
        "articles": [
            {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test",
                "journal": "Test Journal",
                "publication_date": "2023",
                "source": "openalex",
            }
        ],
        "total_count": 1,
        "source": "openalex",
    }
    service.get_work_by_doi.return_value = {
        "success": True,
        "article": {
            "title": "Test Article",
            "authors": ["Test Author"],
            "doi": "10.1234/test",
            "journal": "Test Journal",
            "publication_date": "2023",
            "source": "openalex",
        },
        "source": "openalex",
    }
    return service


@pytest.fixture
def mock_europe_pmc_service(logger):
    """提供模拟的 Europe PMC 服务"""
    _, EuropePMCService, _, _ = _import_services()
    service = Mock(spec=EuropePMCService)
    service.search.return_value = {
        "articles": [
            {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test",
                "journal_name": "Test Journal",
                "publication_date": "2023-01-01",
                "pmid": "12345678",
            }
        ],
        "total_count": 1,
    }
    return service


@pytest.fixture
def mock_pubmed_service(logger):
    """提供模拟的 PubMed 服务"""
    _, _, _, PubMedService = _import_services()
    service = Mock(spec=PubMedService)
    service.search.return_value = {
        "articles": [
            {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test",
                "journal": "Test Journal",
                "publication_date": "2023-01-01",
                "pmid": "12345678",
            }
        ],
        "total_count": 1,
    }
    return service


@pytest.fixture
def sample_article_data():
    """提供示例文章数据"""
    return {
        "title": "Sample Article Title",
        "authors": ["Author One", "Author Two"],
        "doi": "10.1234/sample.2023",
        "journal": "Sample Journal",
        "publication_date": "2023-01-15",
        "abstract": "This is a sample abstract for testing purposes.",
        "pmid": "12345678",
        "pmcid": "PMC123456",
        "source": "test",
    }


@pytest.fixture
def sample_search_results():
    """提供示例搜索结果"""
    return {
        "success": True,
        "keyword": "machine learning",
        "sources_used": ["europe_pmc", "pubmed"],
        "results_by_source": {
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
                    "title": "Deep Learning Applications",
                    "authors": ["ML Specialist"],
                    "doi": "10.5678/dl.apps.2023",
                    "journal": "Machine Learning Today",
                    "publication_date": "2023-05-20",
                }
            ],
        },
        "merged_results": [
            {
                "title": "Machine Learning in Healthcare",
                "authors": ["AI Researcher"],
                "doi": "10.1234/ml.health.2023",
                "journal": "Health AI Journal",
                "publication_date": "2023-06-15",
            },
            {
                "title": "Deep Learning Applications",
                "authors": ["ML Specialist"],
                "doi": "10.5678/dl.apps.2023",
                "journal": "Machine Learning Today",
                "publication_date": "2023-05-20",
            },
        ],
        "total_count": 2,
        "search_time": 1.23,
    }


@pytest.fixture
def invalid_identifier_data():
    """提供无效标识符数据"""
    return {
        "empty": "",
        "whitespace_only": "   ",
        "invalid_format": "not-a-valid-identifier",
        "nonexistent_doi": "10.9999/nonexistent",
        "nonexistent_pmid": "99999999",
    }


@pytest.fixture
def error_response_data():
    """提供错误响应数据"""
    return {
        "success": False,
        "error": "API request failed",
        "error_type": "RequestException",
        "context": {"url": "https://example.com/api", "params": {"query": "test"}},
        "timestamp": 1234567890.0,
    }


@pytest.fixture
def six_tool_services(logger):
    """提供6工具架构的完整服务集合"""
    return {
        "search_services": {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        },
        "article_services": {
            "europe_pmc": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
            "arxiv": Mock(),
            "pubmed": Mock(),
        },
        "reference_service": Mock(),
        "relation_services": {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
        },
        "quality_services": {
            "pubmed": Mock(),
        },
        "batch_services": {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        },
    }


@pytest.fixture
def mock_mcp_tools():
    """模拟6个MCP工具"""
    tools = {}

    # 工具1: search_literature
    tools["search_literature"] = Mock()
    tools["search_literature"].return_value = {
        "success": True,
        "keyword": "test query",
        "merged_results": [
            {
                "title": "Test Article",
                "authors": ["Test Author"],
                "doi": "10.1234/test.2023",
                "journal": "Test Journal",
                "publication_date": "2023-01-01",
            }
        ],
        "total_count": 1,
        "search_time": 1.0,
    }

    # 工具2: get_article_details
    tools["get_article_details"] = Mock()
    tools["get_article_details"].return_value = {
        "success": True,
        "identifier": "10.1234/test.2023",
        "article": {
            "title": "Test Article",
            "authors": ["Test Author"],
            "doi": "10.1234/test.2023",
            "journal": "Test Journal",
            "publication_date": "2023-01-01",
            "abstract": "Test abstract",
        },
    }

    # 工具3: get_references
    tools["get_references"] = Mock()
    tools["get_references"].return_value = {
        "success": True,
        "identifier": "10.1234/test.2023",
        "merged_references": [
            {
                "title": "Reference Article",
                "authors": ["Reference Author"],
                "doi": "10.5678/ref.2020",
                "journal": "Reference Journal",
                "publication_date": "2020-01-01",
            }
        ],
        "total_count": 1,
        "processing_time": 0.5,
    }

    # 工具4: get_literature_relations
    tools["get_literature_relations"] = Mock()
    tools["get_literature_relations"].return_value = {
        "success": True,
        "identifier": "10.1234/test.2023",
        "relations": {
            "references": [],
            "similar": [],
            "citing": [],
        },
        "statistics": {
            "references_count": 0,
            "similar_count": 0,
            "citing_count": 0,
            "total_relations": 0,
        },
    }

    # 工具5: get_journal_quality
    tools["get_journal_quality"] = Mock()
    tools["get_journal_quality"].return_value = {
        "success": True,
        "journal_name": "Test Journal",
        "quality_metrics": {
            "impact_factor": 2.5,
            "quartile": "Q2",
            "jci": 1.0,
        },
    }

    # 工具6: export_batch_results
    tools["export_batch_results"] = Mock()
    tools["export_batch_results"].return_value = {
        "success": True,
        "export_path": "/tmp/test_export.json",
        "format_type": "json",
        "records_exported": 1,
        "file_size": "1.2KB",
        "processing_time": 0.1,
    }

    return tools


@pytest.fixture
def workflow_test_data():
    """提供完整工作流程测试数据"""
    return {
        "search_query": "machine learning healthcare",
        "search_results": {
            "success": True,
            "keyword": "machine learning healthcare",
            "merged_results": [
                {
                    "title": "ML in Healthcare: A Review",
                    "authors": ["AI Expert", "Medical Researcher"],
                    "doi": "10.1234/ml.health.2023",
                    "journal": "Health AI Journal",
                    "publication_date": "2023-06-15",
                    "pmid": "37891234",
                },
                {
                    "title": "Deep Learning for Medical Diagnosis",
                    "authors": ["DL Specialist"],
                    "doi": "10.5678/dl.medical.2023",
                    "journal": "Medical Imaging Today",
                    "publication_date": "2023-04-20",
                    "pmid": "37654321",
                },
            ],
            "total_count": 2,
        },
        "article_details": {
            "success": True,
            "identifier": "10.1234/ml.health.2023",
            "article": {
                "title": "ML in Healthcare: A Review",
                "authors": ["AI Expert", "Medical Researcher"],
                "doi": "10.1234/ml.health.2023",
                "journal": "Health AI Journal",
                "publication_date": "2023-06-15",
                "abstract": "This review examines machine learning applications in healthcare...",
                "pmid": "37891234",
                "pmcid": "PMC1234567",
                "quality_metrics": {
                    "impact_factor": 4.2,
                    "quartile": "Q1",
                    "jci": 1.8,
                },
            },
        },
        "references": {
            "success": True,
            "identifier": "10.1234/ml.health.2023",
            "merged_references": [
                {
                    "title": "Foundations of Machine Learning",
                    "authors": ["ML Pioneer"],
                    "doi": "10.1111/foundations.2020",
                    "journal": "ML Journal",
                    "publication_date": "2020-01-01",
                },
                {
                    "title": "Healthcare Data Analytics",
                    "authors": ["Data Scientist"],
                    "doi": "10.2222/health.analytics.2021",
                    "journal": "Health Informatics",
                    "publication_date": "2021-03-15",
                },
            ],
            "total_count": 25,
        },
        "relations": {
            "success": True,
            "identifier": "10.1234/ml.health.2023",
            "relations": {
                "references": [
                    {
                        "title": "Foundations of Machine Learning",
                        "doi": "10.1111/foundations.2020",
                        "publication_date": "2020-01-01",
                    }
                ],
                "similar": [
                    {
                        "title": "AI in Clinical Practice",
                        "doi": "10.3333/ai.clinical.2023",
                        "publication_date": "2023-05-10",
                    }
                ],
                "citing": [
                    {
                        "title": "Recent Advances in Health AI",
                        "doi": "10.4444/recent.healthai.2023",
                        "publication_date": "2023-11-20",
                    }
                ],
            },
            "statistics": {
                "references_count": 1,
                "similar_count": 1,
                "citing_count": 1,
                "total_relations": 3,
            },
        },
        "journal_quality": {
            "success": True,
            "journal_name": "Health AI Journal",
            "quality_metrics": {
                "impact_factor": 4.2,
                "quartile": "Q1",
                "jci": 1.8,
                "分区": "中科院二区",
                "citescore": 6.5,
            },
            "ranking_info": {
                "field": "Medical Informatics",
                "rank": 15,
                "total_journals": 80,
                "percentile": 81.25,
            },
        },
        "export_data": {
            "success": True,
            "export_path": "/tmp/health_ai_literature_review.json",
            "format_type": "json",
            "records_exported": 2,
            "file_size": "15.3KB",
        },
    }


@pytest.fixture
def performance_test_data():
    """提供性能测试数据"""
    return {
        "small_batch": {
            "size": 10,
            "expected_time": 1.0,
            "expected_memory": 10,  # MB
        },
        "medium_batch": {
            "size": 100,
            "expected_time": 5.0,
            "expected_memory": 50,  # MB
        },
        "large_batch": {
            "size": 1000,
            "expected_time": 30.0,
            "expected_memory": 200,  # MB
        },
        "concurrent_operations": {
            "tools_count": 6,
            "expected_parallel_time": 2.0,
            "expected_serial_time": 8.0,
        },
    }


@pytest.fixture
def error_scenarios():
    """提供错误场景测试数据"""
    return {
        "network_errors": [
            {
                "error_type": "ConnectionError",
                "message": "Failed to connect to API",
                "retry_possible": True,
            },
            {
                "error_type": "TimeoutError",
                "message": "Request timed out",
                "retry_possible": True,
            },
            {
                "error_type": "DNSResolutionError",
                "message": "Could not resolve hostname",
                "retry_possible": False,
            },
        ],
        "api_errors": [
            {
                "error_type": "RateLimitError",
                "message": "API rate limit exceeded",
                "retry_after": 60,
                "suggestion": "Reduce request frequency",
            },
            {
                "error_type": "AuthenticationError",
                "message": "Invalid API credentials",
                "retry_possible": False,
                "suggestion": "Check API configuration",
            },
            {
                "error_type": "InvalidRequestError",
                "message": "Invalid request parameters",
                "retry_possible": True,
                "suggestion": "Validate request parameters",
            },
        ],
        "data_errors": [
            {
                "error_type": "NotFoundError",
                "message": "Requested resource not found",
                "suggestion": "Check identifier validity",
            },
            {
                "error_type": "ParseError",
                "message": "Failed to parse response data",
                "retry_possible": True,
                "suggestion": "Check data format",
            },
            {
                "error_type": "ValidationError",
                "message": "Data validation failed",
                "retry_possible": False,
                "suggestion": "Check input data format",
            },
        ],
    }


@pytest.fixture(autouse=True)
def test_environment():
    """设置测试环境变量"""

    os.environ["PYTHONUNBUFFERED"] = "1"
    # 设置测试模式，避免实际API调用
    os.environ["TESTING"] = "1"
    # 设置缓存测试模式
    os.environ["CACHE_TEST_MODE"] = "1"
    # 禁用网络请求
    os.environ["DISABLE_NETWORK_CALLS"] = "1"
