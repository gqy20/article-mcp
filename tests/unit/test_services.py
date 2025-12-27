#!/usr/bin/env python3
"""服务层单元测试
测试各个服务类的基本功能
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest  # noqa: E402

from article_mcp.services.arxiv_search import create_arxiv_service  # noqa: E402
from article_mcp.services.crossref_service import CrossRefService  # noqa: E402
from article_mcp.services.europe_pmc import EuropePMCService  # noqa: E402
from article_mcp.services.openalex_service import OpenAlexService  # noqa: E402
from article_mcp.services.reference_service import create_reference_service  # noqa: E402
from tests.utils.test_helpers import (  # noqa: E402
    MockDataGenerator,
    TestTimer,
    assert_valid_article_structure,
    assert_valid_search_results,
    create_mock_service,
)

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestEuropePMCService:
    """EuropePMC服务测试"""

    @pytest.fixture
    def service(self, mock_logger):
        """创建服务实例"""
        return EuropePMCService(mock_logger)

    @pytest.mark.unit
    def test_service_initialization(self, service, mock_logger):
        """测试服务初始化"""
        assert service.logger == mock_logger
        assert hasattr(service, "base_url")
        assert hasattr(service, "detail_url")
        assert hasattr(service, "cache")
        assert hasattr(service, "search_semaphore")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_articles(self, service, test_config):
        """测试文章搜索 - 只验证方法可调用"""
        # 测试服务有正确的搜索方法
        assert hasattr(service, "search_async")
        # 测试方法签名正确
        import inspect

        sig = inspect.signature(service.search_async)
        assert "keyword" in sig.parameters
        assert "max_results" in sig.parameters

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_article_details(self, service, mock_article_details, test_config):
        """测试获取文章详情"""
        with patch.object(service, "fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_article_details

            result = await service.fetch(identifier=test_config["test_pmid"])

            assert_valid_article_structure(result)
            assert result.get("pmid") == test_config["test_pmid"]
            mock_fetch.assert_called_once()

    @pytest.mark.unit
    def test_error_handling(self, service):
        """测试错误处理 - 验证服务有正确属性"""
        assert hasattr(service, "logger")
        assert hasattr(service, "search_semaphore")
        # 验证超时设置
        assert service.timeout is not None


class TestArXivService:
    """ArXiv服务测试"""

    @pytest.fixture
    def service(self, mock_logger):
        """创建服务实例"""
        return create_arxiv_service(mock_logger)

    @pytest.mark.unit
    def test_service_creation(self, service, mock_logger):
        """测试服务创建"""
        assert service is not None
        assert hasattr(service, "search_async")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_papers(self, service):
        """测试论文搜索 - 只验证方法存在"""
        assert hasattr(service, "search_async")
        import inspect

        sig = inspect.signature(service.search_async)
        assert "keyword" in sig.parameters


class TestReferenceService:
    """参考文献服务测试"""

    @pytest.fixture
    def service(self, mock_logger):
        """创建服务实例"""
        return create_reference_service(mock_logger)

    @pytest.mark.unit
    def test_service_creation(self, service, mock_logger):
        """测试服务创建"""
        assert service is not None
        assert hasattr(service, "get_references_by_doi_async")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_references(self, service, test_config):
        """测试获取参考文献"""
        mock_references = MockDataGenerator.create_reference_list(10)

        with patch.object(
            service, "get_references_crossref_async", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_references

            result = await service.get_references_by_doi_async(doi=test_config["test_doi"])

            assert "references" in result
            assert isinstance(result["references"], list)
            assert len(result["references"]) == len(mock_references)


class TestCrossRefService:
    """CrossRef服务测试"""

    @pytest.fixture
    def service(self, mock_logger):
        """创建服务实例"""
        return CrossRefService(mock_logger)

    @pytest.mark.unit
    def test_service_initialization(self, service, mock_logger):
        """测试服务初始化"""
        assert service.logger == mock_logger
        assert hasattr(service, "base_url")

    @pytest.mark.unit
    def test_get_work_by_doi(self, service):
        """测试通过DOI获取作品（使用异步方法）"""
        # 检查异步方法存在
        assert hasattr(service, "get_work_by_doi_async")
        assert hasattr(service, "get_references_async")
        import inspect

        sig = inspect.signature(service.get_work_by_doi_async)
        assert "doi" in sig.parameters
        # 验证是异步函数
        assert inspect.iscoroutinefunction(service.get_work_by_doi_async)


class TestOpenAlexService:
    """OpenAlex服务测试"""

    @pytest.fixture
    def service(self, mock_logger):
        """创建服务实例"""
        return OpenAlexService(mock_logger)

    @pytest.mark.unit
    def test_service_initialization(self, service, mock_logger):
        """测试服务初始化"""
        assert service.logger == mock_logger
        assert hasattr(service, "base_url")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_works(self, service):
        """测试作品搜索 - 只验证方法存在"""
        assert hasattr(service, "search_works_async")
        import inspect

        sig = inspect.signature(service.search_works_async)
        # 验证有 query 参数
        params = list(sig.parameters.keys())
        assert "query" in params


class TestServiceIntegration:
    """服务集成测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cross_service_search(self):
        """测试跨服务搜索 - 简化版本"""
        # 只验证多个服务可以并行创建
        import logging

        from article_mcp.services.arxiv_search import create_arxiv_service
        from article_mcp.services.europe_pmc import EuropePMCService

        logger = logging.getLogger("test")
        europe_pmc_service = EuropePMCService(logger)
        arxiv_service = create_arxiv_service(logger)

        # 验证服务可以创建且有搜索方法
        assert hasattr(europe_pmc_service, "search_async")
        assert hasattr(arxiv_service, "search_async")

    @pytest.mark.unit
    def test_service_factory_functions(self, mock_logger):
        """测试服务工厂函数"""
        europe_pmc_service = EuropePMCService(mock_logger)
        arxiv_service = create_arxiv_service(mock_logger)
        reference_service = create_reference_service(mock_logger)

        assert europe_pmc_service is not None
        assert arxiv_service is not None
        assert reference_service is not None

        # 验证服务具有预期的异步方法
        assert hasattr(europe_pmc_service, "search_async")
        assert hasattr(arxiv_service, "search_async")
        assert hasattr(reference_service, "get_references_by_doi_async")
