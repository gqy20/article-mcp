"""
pytest 配置和共享 fixtures
"""

import logging
from unittest.mock import Mock

import pytest

from src.crossref_service import CrossRefService
from src.europe_pmc import EuropePMCService
from src.openalex_service import OpenAlexService
from src.pubmed_search import PubMedService


@pytest.fixture
def logger():
    """提供测试用的 logger"""
    logger = logging.getLogger("test")
    logger.setLevel(logging.WARNING)
    return logger


@pytest.fixture
def mock_crossref_service(logger):
    """提供模拟的 CrossRef 服务"""
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


@pytest.fixture(autouse=True)
def test_environment():
    """设置测试环境变量"""
    import os

    os.environ["PYTHONUNBUFFERED"] = "1"
    # 设置测试模式，避免实际API调用
    os.environ["TESTING"] = "1"
