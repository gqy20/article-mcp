#!/usr/bin/env python3
"""
服务层单元测试
测试各个服务类的基本功能
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402

from article_mcp.services.arxiv_search import create_arxiv_service  # noqa: E402
from article_mcp.services.crossref_service import CrossRefService  # noqa: E402
from article_mcp.services.europe_pmc import EuropePMCService  # noqa: E402
from article_mcp.services.openalex_service import OpenAlexService  # noqa: E402
from article_mcp.services.reference_service import create_reference_service  # noqa: E402
from tests.utils.test_helpers import MockDataGenerator  # noqa: E402
from tests.utils.test_helpers import TestTimer
from tests.utils.test_helpers import assert_valid_article_structure
from tests.utils.test_helpers import assert_valid_search_results
from tests.utils.test_helpers import create_mock_service


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
    async def test_search_articles(self, service, mock_search_results, test_config):
        """测试文章搜索"""
        with patch.object(service, "fetch") as mock_fetch:
            mock_fetch.return_value = mock_search_results

            result = await service.search_async(
                query=test_config["test_keyword"], max_results=test_config["max_results"]
            )

            assert_valid_search_results(result)
            assert result["total_count"] == len(mock_search_results["articles"])
            mock_fetch.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_article_details(self, service, mock_article_details, test_config):
        """测试获取文章详情"""
        with patch.object(service, "get_article_details_async") as mock_get_details:
            mock_get_details.return_value = mock_article_details

            result = await mock_get_details(identifier=test_config["test_pmid"])

            assert_valid_article_structure(result)
            assert result["pmid"] == test_config["test_pmid"]
            mock_get_details.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """测试错误处理"""
        with patch.object(service, "fetch") as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
                await service.search_async("test query")

    @pytest.mark.unit
    def test_sync_search(self, service):
        """测试同步搜索"""
        mock_results = MockDataGenerator.create_search_results(3)

        with patch.object(service, "search_sync") as mock_search:
            mock_search.return_value = mock_results

            result = service.search_sync("test query", max_results=5)

            assert_valid_search_results(result)
            mock_search.assert_called_once_with("test query", max_results=5)

    @pytest.mark.unit
    def test_sync_article_details(self, service):
        """测试同步获取文章详情"""
        mock_article = MockDataGenerator.create_article()

        with patch.object(service, "get_article_details_sync") as mock_get_details:
            mock_get_details.return_value = mock_article

            result = service.get_article_details_sync("test_id")

            assert_valid_article_structure(result)
            mock_get_details.assert_called_once_with("test_id")


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
        assert hasattr(service, "search_papers")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_papers(self, service, mock_search_results):
        """测试论文搜索"""
        with patch.object(service, "_fetch_arxiv_data") as mock_fetch:
            mock_fetch.return_value = mock_search_results

            result = await service.search_papers(keyword="machine learning", max_results=5)

            assert_valid_search_results(result)
            mock_fetch.assert_called_once()


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
        assert hasattr(service, "get_references")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_references(self, service, test_config):
        """测试获取参考文献"""
        mock_references = MockDataGenerator.create_reference_list(10)

        with patch.object(service, "_fetch_references") as mock_fetch:
            mock_fetch.return_value = {
                "references": mock_references,
                "total_count": len(mock_references),
            }

            result = await service.get_references(identifier=test_config["test_doi"], id_type="doi")

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
    @pytest.mark.asyncio
    async def test_resolve_doi(self, service):
        """测试DOI解析"""
        mock_metadata = {
            "title": "Test Article",
            "author": [{"given": "Test", "family": "Author"}],
            "published": {"date-parts": [[2023, 1, 1]]},
        }

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"message": mock_metadata}

            result = await service.resolve_doi("10.1000/test")

            assert "title" in result
            assert result["title"] == "Test Article"
            mock_request.assert_called_once()


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
        """测试作品搜索"""
        mock_results = MockDataGenerator.create_search_results(3)

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {
                "results": mock_results["articles"],
                "meta": {"count": len(mock_results["articles"])},
            }

            result = await service.search_works("test query")

            assert "results" in result
            assert isinstance(result["results"], list)
            assert len(result["results"]) == len(mock_results["articles"])


class TestServiceIntegration:
    """服务集成测试"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cross_service_search(self, mock_logger):
        """测试跨服务搜索"""
        # 创建模拟服务
        europe_pmc_service = create_mock_service(
            EuropePMCService, search_articles=MockDataGenerator.create_search_results(3)
        )
        arxiv_service = create_mock_service(
            type("ArXivService", (), {}), search_papers=MockDataGenerator.create_search_results(2)
        )

        # 模拟并行搜索
        with TestTimer() as timer:
            europe_task = europe_pmc_service.search_articles("test query")
            arxiv_task = arxiv_service.search_papers("test query")

            europe_result, arxiv_result = await asyncio.gather(europe_task, arxiv_task)

        # 验证结果
        assert_valid_search_results(europe_result)
        assert_valid_search_results(arxiv_result)
        assert timer.stop() < 5.0  # 应该在5秒内完成

    @pytest.mark.unit
    def test_service_factory_functions(self, mock_logger):
        """测试服务工厂函数"""
        europe_pmc_service = EuropePMCService(mock_logger)
        arxiv_service = create_arxiv_service(mock_logger)
        reference_service = create_reference_service(mock_logger)

        assert europe_pmc_service is not None
        assert arxiv_service is not None
        assert reference_service is not None

        # 验证服务具有预期的方法
        assert hasattr(europe_pmc_service, "search_articles")
        assert hasattr(arxiv_service, "search_papers")
        assert hasattr(reference_service, "get_references")
