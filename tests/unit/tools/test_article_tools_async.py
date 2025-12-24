#!/usr/bin/env python3
"""
Article Tools 异步测试
测试 get_article_details 工具的异步版本
"""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.tools.core import article_tools


@pytest.fixture
def logger():
    """提供测试用的 logger"""
    return logging.getLogger(__name__)


@pytest.fixture
def mock_europe_pmc_service():
    """模拟 Europe PMC 服务"""
    service = Mock()
    # 异步方法
    service.fetch = Mock(return_value={
        "success": True,
        "article": {
            "title": "Test Article from Europe PMC",
            "authors": ["Author One", "Author Two"],
            "doi": "10.1234/test.article.2023",
            "journal": "Test Journal",
            "publication_date": "2023-01-01",
            "abstract": "Test abstract",
        }
    })
    return service


@pytest.fixture
def mock_crossref_service():
    """模拟 CrossRef 服务"""
    service = Mock()
    service.get_work_by_doi = Mock(return_value={
        "success": True,
        "article": {
            "title": "Test Article from CrossRef",
            "authors": ["Author One"],
            "doi": "10.1234/test.article.2023",
            "journal": "Test Journal",
        }
    })
    return service


@pytest.fixture
def mock_openalex_service():
    """模拟 OpenAlex 服务"""
    service = Mock()
    service.get_work_by_doi = Mock(return_value={
        "success": True,
        "article": {
            "title": "Test Article from OpenAlex",
            "authors": ["Author One"],
            "doi": "10.1234/test.article.2023",
            "journal": "Test Journal",
        }
    })
    return service


@pytest.fixture
def mock_arxiv_service():
    """模拟 arXiv 服务"""
    service = Mock()
    service.fetch = Mock(return_value={
        "success": True,
        "article": {
            "title": "Test Article from arXiv",
            "authors": ["Author One"],
            "arxiv_id": "2301.00001",
            "abstract": "Test abstract",
        }
    })
    return service


@pytest.fixture
def mock_services(mock_europe_pmc_service, mock_crossref_service, mock_openalex_service, mock_arxiv_service):
    """模拟服务字典"""
    return {
        "europe_pmc": mock_europe_pmc_service,
        "crossref": mock_crossref_service,
        "openalex": mock_openalex_service,
        "arxiv": mock_arxiv_service,
    }


@pytest.mark.asyncio
class TestGetArticleDetailsAsync:
    """测试异步 get_article_details 工具"""

    async def test_get_article_details_by_doi_success(
        self, mock_services, mock_europe_pmc_service, logger
    ):
        """测试通过 DOI 成功获取文献详情"""
        # 注册服务
        article_tools._article_services = mock_services
        article_tools._logger = logger

        # 调用工具
        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            sources=["europe_pmc"],
            include_quality_metrics=False,
        )

        # 验证结果
        assert result["success"] is True
        assert result["total_count"] == 1
        assert len(result["sources_found"]) == 1
        assert "europe_pmc" in result["sources_found"]
        assert result["merged_detail"]["title"] == "Test Article from Europe PMC"
        assert result["processing_time"] >= 0

        # 验证服务方法被调用
        mock_europe_pmc_service.fetch.assert_called_once()

    async def test_get_article_details_multiple_sources(
        self, mock_services, mock_europe_pmc_service, mock_crossref_service, logger
    ):
        """测试从多个数据源获取文献详情"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            sources=["europe_pmc", "crossref"],
        )

        # 验证结果
        assert result["success"] is True
        assert len(result["sources_found"]) == 2
        assert "europe_pmc" in result["sources_found"]
        assert "crossref" in result["sources_found"]
        assert result["total_count"] == 2

    async def test_get_article_details_auto_id_type(self, mock_services, logger):
        """测试自动标识符类型识别"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        test_cases = [
            ("10.1234/test.doi", "doi"),
            ("12345678", "pmid"),
            ("PMC123456", "pmcid"),
            ("arXiv:2301.00001", "arxiv_id"),
        ]

        for identifier, expected_type in test_cases:
            # 测试标识符类型提取
            from article_mcp.services.merged_results import extract_identifier_type
            extracted_type = extract_identifier_type(identifier)
            assert extracted_type == expected_type

    async def test_get_article_details_empty_identifier(self, mock_services, logger):
        """测试空标识符错误处理"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="",
            id_type="doi",
        )

        # 验证错误处理
        assert result["success"] is False
        assert "文献标识符不能为空" in result.get("error", "")
        assert result["total_count"] == 0

    async def test_get_article_details_no_data_source_error(
        self, mock_services, mock_europe_pmc_service, logger
    ):
        """测试数据源返回无数据时的处理"""
        # 设置返回空结果
        mock_europe_pmc_service.fetch.return_value = {
            "success": True,
            "article": None,
        }

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
        )

        # 验证空结果处理
        assert result["success"] is False
        assert result["total_count"] == 0
        assert result["sources_found"] == []

    async def test_get_article_details_service_error_handling(
        self, mock_services, mock_europe_pmc_service, logger
    ):
        """测试服务异常处理"""
        # 设置服务抛出异常
        mock_europe_pmc_service.fetch.side_effect = Exception("API Error")

        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
        )

        # 验证错误处理 - 应该优雅地处理异常，返回空结果
        assert result["total_count"] == 0
        assert result["sources_found"] == []

    async def test_get_article_details_default_sources(
        self, mock_services, logger
    ):
        """测试默认数据源"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            # 不指定 sources，应该使用默认值
        )

        # 验证默认使用 europe_pmc 和 crossref
        assert "europe_pmc" in result["sources_found"] or "crossref" in result["sources_found"]

    async def test_get_article_details_parallel_execution(
        self, mock_services, logger
    ):
        """测试并行执行多个数据源"""
        # 设置延迟以验证并行执行
        import time

        original_europe_pmc_fetch = mock_services["europe_pmc"].fetch
        original_crossref_fetch = mock_services["crossref"].get_work_by_doi

        def delayed_europe_pmc(identifier, id_type):
            time.sleep(0.05)
            return original_europe_pmc_fetch(identifier, id_type=id_type)

        def delayed_crossref(doi):
            time.sleep(0.05)
            return original_crossref_fetch(doi)

        mock_services["europe_pmc"].fetch = delayed_europe_pmc
        mock_services["crossref"].get_work_by_doi = delayed_crossref

        article_tools._article_services = mock_services
        article_tools._logger = logger

        start = time.time()
        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc", "crossref"],
        )
        elapsed = time.time() - start

        # 并行执行应该比串行快（两个0.05秒的延迟并行执行应该 < 0.12秒）
        assert elapsed < 0.12, f"Parallel execution took {elapsed}s, expected < 0.12s"
        assert result["total_count"] == 2

    async def test_get_article_details_arxiv_id(
        self, mock_services, mock_arxiv_service, logger
    ):
        """测试通过 arXiv ID 获取文献详情"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="2301.00001",
            id_type="arxiv_id",
            sources=["arxiv"],
        )

        # 验证结果
        assert result["success"] is True
        assert "arxiv" in result["sources_found"]
        assert result["merged_detail"]["title"] == "Test Article from arXiv"

    async def test_get_article_details_crossref_only(
        self, mock_services, mock_crossref_service, logger
    ):
        """测试仅从 CrossRef 获取文献详情"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            sources=["crossref"],
        )

        # 验证结果
        assert result["success"] is True
        assert "crossref" in result["sources_found"]
        assert result["merged_detail"]["title"] == "Test Article from CrossRef"

    async def test_get_article_details_openalex_only(
        self, mock_services, mock_openalex_service, logger
    ):
        """测试仅从 OpenAlex 获取文献详情"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            sources=["openalex"],
        )

        # 验证结果
        assert result["success"] is True
        assert "openalex" in result["sources_found"]
        assert result["merged_detail"]["title"] == "Test Article from OpenAlex"

    async def test_get_article_details_pmid_type(
        self, mock_services, mock_europe_pmc_service, logger
    ):
        """测试 PMID 类型标识符"""
        article_tools._article_services = mock_services
        article_tools._logger = logger

        result = await article_tools.get_article_details_async(
            identifier="12345678",
            id_type="pmid",
            sources=["europe_pmc"],
        )

        # 验证结果
        assert result["success"] is True
        assert result["id_type"] == "pmid"


# 测试辅助函数
class TestHelperFunctions:
    """测试辅助函数"""

    def test_extract_identifier_type_doi(self):
        """测试 DOI 类型识别"""
        from article_mcp.services.merged_results import extract_identifier_type
        test_cases = [
            "10.1234/test.doi",
            "doi:10.1234/test.doi",
            "https://doi.org/10.1234/test.doi",
        ]
        for case in test_cases:
            result = extract_identifier_type(case)
            assert result == "doi", f"Expected 'doi' for {case}, got {result}"

    def test_extract_identifier_type_pmid(self):
        """测试 PMID 类型识别"""
        from article_mcp.services.merged_results import extract_identifier_type
        test_cases = ["12345678", "pmid:12345678", "PMID:12345678"]
        for case in test_cases:
            result = extract_identifier_type(case)
            assert result == "pmid", f"Expected 'pmid' for {case}, got {result}"

    def test_extract_identifier_type_pmcid(self):
        """测试 PMCID 类型识别"""
        from article_mcp.services.merged_results import extract_identifier_type
        test_cases = ["PMC123456", "pmcid:PMC123456", "PMCID:PMC123456"]
        for case in test_cases:
            result = extract_identifier_type(case)
            assert result == "pmcid", f"Expected 'pmcid' for {case}, got {result}"

    def test_extract_identifier_type_arxiv(self):
        """测试 arXiv 类型识别"""
        from article_mcp.services.merged_results import extract_identifier_type
        test_cases = ["arXiv:2301.00001", "ARXIV:2301.00001"]
        for case in test_cases:
            result = extract_identifier_type(case)
            assert result == "arxiv_id", f"Expected 'arxiv_id' for {case}, got {result}"
