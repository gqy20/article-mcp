"""EasyScholar 服务单元测试

测试 EasyScholar API 集成的期刊质量评估功能。
EasyScholar 是一个中国学术期刊评级服务。

简化后的测试：
- 移除了模拟数据降级机制相关测试
- 专注于 API 密钥验证和错误处理
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
        "code": 200,
        "msg": "success",
        "data": {
            "officialRank": {
                "all": {
                    "sciif": "69.504",  # SCI影响因子
                    "sci": "1区",  # SCI分区
                    "jci": "25.8",  # JCI指数
                    "sciUp": "1区",  # 中科院升级版分区
                    "sciBase": "1区",  # 中科院基础版分区
                    "sciUpSmall": "生物学1区",  # 小类分区
                    "sciUpTop": "TOP",  # TOP期刊
                }
            }
        },
    }


class TestEasyScholarService:
    """EasyScholar 服务测试类"""

    def test_init_with_api_key(self, logger):
        """测试使用 API 密钥初始化服务"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)
            assert service.api_key == "test_key_123"
            assert service._timeout_val == 30

    def test_init_without_api_key(self, logger):
        """测试没有 API 密钥时的初始化"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)
            assert service.api_key is None

    @pytest.mark.asyncio
    async def test_get_journal_quality_success_with_api_key(self, logger, mock_api_response):
        """测试使用 API 密钥成功获取期刊质量"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            # 直接模拟 _parse_api_response 的结果
            expected_result = {
                "success": True,
                "journal_name": "Nature",
                "quality_metrics": {
                    "impact_factor": 69.504,
                    "quartile": "1区",
                    "jci": "25.8",
                    "cas_zone": "中科院一区",
                },
                "ranking_info": {
                    "rank_in_category": 1,
                    "total_journals_in_category": 200,
                    "percentile": 99.5,
                },
                "data_source": "easyscholar_api",
            }

            async def mock_make_request(journal_name):
                return expected_result

            with patch.object(service, "_make_request", side_effect=mock_make_request):
                result = await service.get_journal_quality("Nature")

                assert result["success"] is True
                assert result["quality_metrics"]["impact_factor"] == 69.504
                assert result["quality_metrics"]["quartile"] == "1区"
                assert result["quality_metrics"]["jci"] == "25.8"
                assert result["data_source"] == "easyscholar_api"

    @pytest.mark.asyncio
    async def test_get_journal_quality_without_api_key(self, logger):
        """测试没有 API 密钥时返回错误提示"""
        with patch.dict("os.environ", {}, clear=True):
            service = EasyScholarService(logger)

            result = await service.get_journal_quality("Nature")

            # 没有密钥时应该返回配置提示错误
            assert result["success"] is False
            assert "EASYSCHOLAR_SECRET_KEY" in result["error"]
            assert result["data_source"] is None

    @pytest.mark.asyncio
    async def test_get_journal_quality_empty_journal_name(self, logger):
        """测试空期刊名称的处理"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            result = await service.get_journal_quality("")

            # 空名称应该返回错误
            assert result["success"] is False
            assert "期刊名称不能为空" in result["error"]

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

                # 超时时应该返回错误
                assert result["success"] is False
                assert "超时" in result["error"]

    @pytest.mark.asyncio
    async def test_get_journal_quality_journal_not_found(self, logger):
        """测试期刊未找到的处理"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            # 模拟 API 返回空结果（quality_metrics 为空）
            async def mock_request(journal_name):
                return {
                    "success": True,
                    "journal_name": journal_name,
                    "quality_metrics": {},  # 空指标
                    "ranking_info": {},
                    "data_source": "easyscholar_api",
                }

            # 当 quality_metrics 为空时，_parse_api_response 会返回失败结果
            async def mock_make_request(journal_name):
                # 直接返回失败结果（模拟 _parse_api_response 的行为）
                return {
                    "success": False,
                    "error": f"未找到期刊 '{journal_name}' 的质量信息",
                    "journal_name": journal_name,
                    "quality_metrics": {},
                    "ranking_info": {},
                    "data_source": None,
                }

            with patch.object(service, "_make_request", side_effect=mock_make_request):
                result = await service.get_journal_quality("Unknown Journal")

                assert result["success"] is False
                assert "未找到" in result["error"]

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
                        "quartile": "1区",
                        "jci": "5.0",
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
                assert all(r["success"] for r in results)
                assert all("quality_metrics" in r for r in results)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, logger):
        """测试速率限制（每秒最多2次请求）"""
        with patch.dict("os.environ", {"EASYSCHOLAR_SECRET_KEY": "test_key_123"}):
            service = EasyScholarService(logger)

            # 模拟快速多次请求
            call_times = []

            async def track_request(journal_name):
                import time

                call_times.append(time.time())
                return {
                    "success": True,
                    "journal_name": journal_name,
                    "quality_metrics": {"impact_factor": 10.0},
                    "data_source": "easyscholar_api",
                }

            with patch.object(service, "_make_request", side_effect=track_request):
                # 批量请求应该遵守速率限制
                journals = ["Nature", "Science", "Cell"]
                await service.batch_get_journal_quality(journals)

                # 验证请求之间有间隔
                assert len(call_times) == 3
                for i in range(1, len(call_times)):
                    # 每次请求应该至少间隔 0.5 秒
                    assert call_times[i] - call_times[i - 1] >= 0.5


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

    def test_create_easyscholar_service_custom_timeout(self, logger):
        """测试自定义超时时间"""
        service = create_easyscholar_service(logger, timeout=60)
        assert service._timeout_val == 60
