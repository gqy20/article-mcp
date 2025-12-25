"""OpenAlex 指标补充服务单元测试

TDD 测试：
- OpenAlex 指标获取功能
- 文件缓存机制
- 与 EasyScholar 数据合并
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.services.openalex_metrics_service import (
    OpenAlexMetricsService,
    create_openalex_metrics_service,
)


@pytest.fixture
def logger():
    """创建测试用的 logger"""
    import logging

    return logging.getLogger(__name__)


@pytest.fixture
def mock_openalex_api_response():
    """模拟的 OpenAlex API 响应"""
    return {
        "meta": {"count": 1},
        "results": [
            {
                "id": "https://openalex.org/S137773608",
                "display_name": "Nature",
                "summary_stats": {
                    "h_index": 1812,
                    "i10_index": 118873,
                    "2yr_mean_citedness": 21.897004189392142,
                },
                "cited_by_count": 26225053,
                "works_count": 446231,
            }
        ],
    }


class TestOpenAlexMetricsService:
    """OpenAlex 指标服务测试类"""

    def test_init_service(self, logger):
        """测试服务初始化"""
        service = OpenAlexMetricsService(logger)
        assert service.API_URL == "https://api.openalex.org/sources"
        assert service._timeout_val == 30

    @pytest.mark.asyncio
    async def test_get_journal_metrics_success(self, logger, mock_openalex_api_response):
        """测试成功获取期刊指标"""
        service = OpenAlexMetricsService(logger)

        expected_metrics = {
            "h_index": 1812,
            "citation_rate": 21.897004189392142,  # 2yr_mean_citedness (完整精度)
            "cited_by_count": 26225053,
            "works_count": 446231,
            "i10_index": 118873,
        }

        with patch.object(service, "_fetch_from_api", return_value=expected_metrics):
            metrics = await service.get_journal_metrics("Nature")

            assert metrics["h_index"] == 1812
            assert metrics["citation_rate"] == 21.897004189392142
            assert metrics["cited_by_count"] == 26225053
            assert metrics["works_count"] == 446231

    @pytest.mark.asyncio
    async def test_get_journal_metrics_not_found(self, logger):
        """测试期刊未找到的情况"""
        service = OpenAlexMetricsService(logger)

        with patch.object(service, "_fetch_from_api", return_value=None):
            metrics = await service.get_journal_metrics("Unknown Journal")

            assert metrics is None

    @pytest.mark.asyncio
    async def test_get_journal_metrics_with_cache(self, logger):
        """测试从缓存获取指标"""
        service = OpenAlexMetricsService(logger)

        # 清空缓存文件
        if service._cache_file.exists():
            service._cache_file.unlink()

        # 第一次调用应该从 API 获取
        with patch.object(service, "_fetch_from_api", return_value={"h_index": 100}) as mock_api:
            metrics1 = await service.get_journal_metrics("Nature", use_cache=True)
            assert metrics1["h_index"] == 100
            mock_api.assert_called_once()

        # 第二次调用应该从缓存获取
        with patch.object(service, "_fetch_from_api", return_value={"h_index": 200}) as mock_api:
            metrics2 = await service.get_journal_metrics("Nature", use_cache=True)
            # 缓存命中，不应调用 API，返回第一次的值
            mock_api.assert_not_called()
            assert metrics2["h_index"] == 100  # 从缓存读取，不是 mock 的 200

    @pytest.mark.asyncio
    async def test_batch_get_journal_metrics(self, logger, mock_openalex_api_response):
        """测试批量获取期刊指标"""
        service = OpenAlexMetricsService(logger)

        expected_metrics = {
            "h_index": 1812,
            "citation_rate": 21.897004189392142,
            "cited_by_count": 26225053,
            "works_count": 446231,
        }

        async def mock_get(journal, use_cache=True):
            return expected_metrics

        with patch.object(service, "get_journal_metrics", side_effect=mock_get):
            results = await service.batch_get_journal_metrics(["Nature", "Science"])

            assert len(results) == 2
            assert all(r["h_index"] == 1812 for r in results)

    @pytest.mark.asyncio
    async def test_merge_metrics_with_easyscholar(self, logger):
        """测试与 EasyScholar 数据合并"""
        service = OpenAlexMetricsService(logger)

        easyscholar_data = {
            "quality_metrics": {
                "impact_factor": 69.504,
                "quartile": "1区",
                "jci": "25.8",
            }
        }

        openalex_metrics = {
            "h_index": 1812,
            "citation_rate": 21.897004189392142,
            "cited_by_count": 26225053,
            "works_count": 446231,
        }

        merged = service.merge_metrics(easyscholar_data, openalex_metrics)

        assert merged["quality_metrics"]["impact_factor"] == 69.504
        assert merged["quality_metrics"]["h_index"] == 1812
        assert merged["quality_metrics"]["citation_rate"] == 21.897004189392142
        assert merged["quality_metrics"]["cited_by_count"] == 26225053


class TestOpenAlexCache:
    """OpenAlex 缓存功能测试"""

    def test_cache_file_path(self, logger):
        """测试缓存文件路径（与 EasyScholar 共享）"""
        service = OpenAlexMetricsService(logger)
        # 现在使用与 EasyScholar 相同的缓存文件
        assert service._cache_file.name.endswith("journal_data.json")
        assert "journal_quality" in str(service._cache_file)

    @pytest.mark.asyncio
    async def test_save_to_cache(self, logger):
        """测试保存到缓存"""
        service = OpenAlexMetricsService(logger)

        metrics = {"h_index": 1812, "citation_rate": 21.897}

        # 删除旧缓存
        if service._cache_file.exists():
            service._cache_file.unlink()

        await service._save_to_cache("Nature", metrics)

        # 验证缓存文件存在
        assert service._cache_file.exists()

    @pytest.mark.asyncio
    async def test_load_from_cache_hit(self, logger):
        """测试从缓存加载（命中）"""
        service = OpenAlexMetricsService(logger)

        metrics = {"h_index": 1812, "citation_rate": 21.897}
        await service._save_to_cache("Nature", metrics)

        loaded = await service._load_from_cache("Nature")

        assert loaded["h_index"] == 1812
        assert loaded["citation_rate"] == 21.897

    @pytest.mark.asyncio
    async def test_load_from_cache_miss(self, logger):
        """测试从缓存加载（未命中）"""
        service = OpenAlexMetricsService(logger)

        # 清空缓存
        if service._cache_file.exists():
            service._cache_file.unlink()

        loaded = await service._load_from_cache("Unknown")

        assert loaded is None

    @pytest.mark.asyncio
    async def test_cache_expiry(self, logger):
        """测试缓存过期"""
        service = OpenAlexMetricsService(logger)

        # 保存一个旧的缓存（设置旧时间戳）
        import time

        metrics = {"h_index": 1812}
        await service._save_to_cache("Nature", metrics)

        # 修改缓存文件，设置过期时间戳
        import json

        with open(service._cache_file, encoding="utf-8") as f:
            cache_data = json.load(f)

        cache_data["journals"]["Nature"]["timestamp"] = time.time() - 90000  # 25小时前

        with open(service._cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # 缓存应该过期
        loaded = await service._load_from_cache("Nature")

        assert loaded is None


class TestOpenAlexMetricsServiceFactory:
    """OpenAlex 指标服务工厂测试"""

    def test_create_openalex_metrics_service(self, logger):
        """测试创建 OpenAlex 指标服务"""
        service = create_openalex_metrics_service(logger)
        assert isinstance(service, OpenAlexMetricsService)
        assert hasattr(service, "get_journal_metrics")
        assert hasattr(service, "batch_get_journal_metrics")

    def test_create_service_custom_timeout(self, logger):
        """测试自定义超时时间"""
        service = create_openalex_metrics_service(logger, timeout=60)
        assert service._timeout_val == 60


class TestIntegrationWithQualityTools:
    """与 quality_tools 集成测试"""

    @pytest.mark.asyncio
    async def test_enhance_quality_result_with_openalex(self, logger):
        """测试用 OpenAlex 数据增强质量评估结果"""
        service = OpenAlexMetricsService(logger)

        quality_result = {
            "success": True,
            "journal_name": "Nature",
            "quality_metrics": {"impact_factor": 69.504, "quartile": "1区"},
            "ranking_info": {},
            "data_source": "easyscholar_api",
        }

        openalex_metrics = {
            "h_index": 1812,
            "citation_rate": 21.897004189392142,
            "cited_by_count": 26225053,
            "works_count": 446231,
        }

        with patch.object(service, "get_journal_metrics", return_value=openalex_metrics):
            enhanced = await service.enhance_quality_result(quality_result)

            assert enhanced["quality_metrics"]["impact_factor"] == 69.504
            assert enhanced["quality_metrics"]["h_index"] == 1812
            assert enhanced["quality_metrics"]["citation_rate"] == 21.897004189392142
            assert "openalex" in enhanced["data_source"]

    @pytest.mark.asyncio
    async def test_enhance_quality_result_no_openalex_data(self, logger):
        """测试 OpenAlex 无数据时不影响原结果"""
        service = OpenAlexMetricsService(logger)

        quality_result = {
            "success": True,
            "journal_name": "Unknown Journal",
            "quality_metrics": {"impact_factor": 1.0},
            "ranking_info": {},
            "data_source": "easyscholar_api",
        }

        with patch.object(service, "get_journal_metrics", return_value=None):
            enhanced = await service.enhance_quality_result(quality_result)

            # 原数据应该保持不变
            assert enhanced["quality_metrics"]["impact_factor"] == 1.0
            assert "h_index" not in enhanced["quality_metrics"]
