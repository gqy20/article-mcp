"""EasyScholar 服务单元测试

测试 EasyScholar API 集成的期刊质量评估功能。
EasyScholar 是一个中国学术期刊评级服务。
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.services.easyscholar_service import (
    EasyScholarService,
    create_easyscholar_service,
)


@pytest.fixture
def logger():
    """创建测试用的 logger"""
    import logging

    return logging.getLogger(__name__)


@pytest.fixture
def mock_api_response():
    """模拟的 EasyScholar API 响应"""
    return {
        "success": True,
        "data": {
            "journal": "Nature",
            "impact_factor": 69.504,
            "quartile": "Q1",
            "jci": 25.8,
            "chinese_academy_sciences_zone": "中科院一区",
            "rank_in_category": 1,
            "total_journals_in_category": 200,
            "percentile": 99.5,
        },
    }


class TestEasyScholarService:
    """EasyScholar 服务测试类"""

    def test_init_with_api_key(self, logger):
        """测试使用 API 密钥初始化服务"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)
            assert service.base_url == "https://www.easyscholar.cc"
            assert service.api_key == "test_key_123"
            assert service._timeout_val == 30

    def test_init_without_api_key(self, logger):
        """测试没有 API 密钥时的初始化"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)
            assert service.api_key is None
            # 没有密钥时服务仍可初始化，但会返回模拟数据

    @pytest.mark.asyncio
    async def test_get_journal_quality_success_with_api_key(self, logger, mock_api_response):
        """测试使用 API 密钥成功获取期刊质量"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            # 模拟成功的 API 响应
            async def mock_request(journal_name):
                return {
                    "success": True,
                    "journal_name": journal_name,
                    "quality_metrics": {
                        "impact_factor": 69.504,
                        "quartile": "Q1",
                        "jci": 25.8,
                        "cas_zone": "中科院一区",
                    },
                    "ranking_info": {
                        "rank_in_category": 1,
                        "total_journals_in_category": 200,
                        "percentile": 99.5,
                    },
                    "data_source": "easyscholar_api",
                }

            with patch.object(service, "_make_request", side_effect=mock_request):
                result = await service.get_journal_quality("Nature")

                assert result["success"] is True
                assert result["quality_metrics"]["impact_factor"] == 69.504
                assert result["quality_metrics"]["quartile"] == "Q1"
                assert result["quality_metrics"]["jci"] == 25.8
                assert result["quality_metrics"]["cas_zone"] == "中科院一区"
                assert result["ranking_info"]["rank_in_category"] == 1
                assert result["data_source"] == "easyscholar_api"

    @pytest.mark.asyncio
    async def test_get_journal_quality_fallback_to_mock(self, logger):
        """测试没有 API 密钥时返回模拟数据"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)

            result = await service.get_journal_quality("Nature")

            # 没有密钥时返回模拟数据
            assert result["success"] is True
            assert "quality_metrics" in result
            assert "ranking_info" in result
            assert result["data_source"] == "mock_data"

    @pytest.mark.asyncio
    async def test_get_journal_quality_api_failure(self, logger):
        """测试 API 调用失败时的处理"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            # 模拟 API 失败（抛出异常）
            async def failing_request(journal_name):
                raise Exception("API request failed")

            with patch.object(service, "_make_request", side_effect=failing_request):
                result = await service.get_journal_quality("Nature")

                # API 失败时应该降级到模拟数据
                assert result["success"] is True
                assert result["data_source"] == "mock_data"

    @pytest.mark.asyncio
    async def test_get_journal_quality_api_timeout(self, logger):
        """测试 API 超时的处理"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            # 模拟超时
            async def timeout_request(*args, **kwargs):
                import asyncio

                await asyncio.sleep(35)  # 超过超时时间
                return {"success": False, "error": "Timeout"}

            with patch.object(service, "_make_request", side_effect=timeout_request):
                result = await service.get_journal_quality("Nature", timeout=10)

                # 超时时应该降级到模拟数据
                assert result["success"] is True
                assert result["data_source"] == "mock_data"

    @pytest.mark.asyncio
    async def test_get_journal_quality_empty_journal_name(self, logger):
        """测试空期刊名称的处理"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            result = await service.get_journal_quality("")

            # 空名称应该返回错误
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_batch_get_journal_quality(self, logger):
        """测试批量获取期刊质量"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            journals = ["Nature", "Science", "Cell"]

            # 模拟成功的 API 响应
            async def mock_request(journal_name):
                return {
                    "success": True,
                    "journal_name": journal_name,
                    "quality_metrics": {
                        "impact_factor": 10.0,
                        "quartile": "Q1",
                        "jci": 5.0,
                        "cas_zone": "中科院一区",
                    },
                    "ranking_info": {
                        "rank_in_category": 10,
                        "total_journals_in_category": 200,
                    },
                    "data_source": "easyscholar_api",
                }

            with patch.object(service, "get_journal_quality", side_effect=mock_request):
                results = await service.batch_get_journal_quality(journals)

                assert len(results) == 3
                assert all("quality_metrics" in r for r in results)

    def test_mock_quality_assessment_high_impact(self, logger):
        """测试高影响力期刊的模拟评估"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)
            result = service._get_mock_quality("Nature")

            assert result["quality_metrics"]["impact_factor"] >= 8.0
            assert result["quality_metrics"]["quartile"] == "Q1"
            assert result["quality_metrics"]["cas_zone"] == "中科院一区"

    def test_mock_quality_assessment_medium_impact(self, logger):
        """测试中等影响力期刊的模拟评估"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)
            result = service._get_mock_quality("Journal of Research")

            assert 3.0 <= result["quality_metrics"]["impact_factor"] < 8.0
            assert result["quality_metrics"]["quartile"] == "Q2"

    def test_mock_quality_assessment_low_impact(self, logger):
        """测试低影响力期刊的模拟评估"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)
            result = service._get_mock_quality("Unknown Quarterly")

            assert result["quality_metrics"]["impact_factor"] < 3.0
            assert result["quality_metrics"]["quartile"] in ["Q3", "Q4"]


class TestEasyScholarServiceFactory:
    """EasyScholar 服务工厂测试"""

    def test_create_easyscholar_service(self, logger):
        """测试创建 EasyScholar 服务"""
        service = create_easyscholar_service(logger)
        assert isinstance(service, EasyScholarService)
        assert hasattr(service, "get_journal_quality")
        assert hasattr(service, "batch_get_journal_quality")

    def test_create_easyscholar_service_with_env_key(self, logger):
        """测试使用环境变量创建服务"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "env_key_456"}):
            service = create_easyscholar_service(logger)
            assert service.api_key == "env_key_456"
