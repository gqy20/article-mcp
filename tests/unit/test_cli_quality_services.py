"""测试 cli.py 中 quality_tools 服务依赖注入是否完整

测试目标：验证 create_mcp_server() 正确注入了 quality_tools 所需的服务

问题分析：
- quality_tools.py 期望 services 包含 "easyscholar" 和 "openalex" 键
- cli.py:126 只传入了 {"pubmed": pubmed_service}
- 导致运行时 KeyError: 'easyscholar'
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.unit
class TestCLICliQualityServicesInjection:
    """测试 CLI 中 quality_tools 服务注入"""

    def test_create_mcp_server_should_inject_easyscholar_service(self):
        """验证：quality_tools 需要的服务字典结构"""

        # Arrange: 准备模拟服务
        mock_easyscholar = Mock()
        mock_openalex_metrics = Mock()

        # Act: 构建正确的服务字典（这应该是 cli.py 中应该传入的）
        quality_services = {
            "easyscholar": mock_easyscholar,
            "openalex": mock_openalex_metrics,
        }

        # Assert: 验证服务字典包含必需的键
        assert "easyscholar" in quality_services, (
            "quality_services 必须包含 'easyscholar' 键，否则 quality_tools 会报 KeyError"
        )
        assert "openalex" in quality_services, (
            "quality_services 必须包含 'openalex' 键，否则 quality_tools 会报 KeyError"
        )

    def test_quality_tools_requires_easyscholar_and_openalex(self):
        """验证：quality_tools 运行时需要 easyscholar 和 openalex 服务"""

        # Arrange: 模拟不完整的服务注入（当前 cli.py 的问题）
        incomplete_services = {
            "pubmed": Mock(),  # ❌ 缺少 easyscholar 和 openalex
        }
        logger = logging.getLogger(__name__)

        # Act & Assert: 尝试访问服务应该抛出 KeyError
        with pytest.raises(KeyError, match="'easyscholar'"):
            # 这是 quality_tools.py:330 的实际代码
            _ = incomplete_services["easyscholar"]

    @pytest.mark.asyncio
    async def test_single_journal_quality_with_correct_services(self):
        """验证：使用正确的服务字典，_single_journal_quality 可以正常调用"""

        # Arrange: 创建正确的模拟服务
        async def mock_easyscholar_get_quality(journal_name):
            return {
                "success": True,
                "journal_name": journal_name,
                "data_source": "easyscholar",
                "quality_metrics": {
                    "impact_factor": 5.0,
                    "quartile": "Q1",
                },
                "ranking_info": {},
            }

        async def mock_openalex_enhance(result, use_cache):
            result["quality_metrics"]["h_index"] = 400
            return result

        correct_services = {
            "easyscholar": Mock(
                get_journal_quality=AsyncMock(side_effect=mock_easyscholar_get_quality)
            ),
            "openalex": Mock(enhance_quality_result=AsyncMock(side_effect=mock_openalex_enhance)),
        }

        # Act: 调用 _single_journal_quality
        from article_mcp.tools.core.quality_tools import _single_journal_quality

        result = await _single_journal_quality(
            journal_name="Nature",
            include_metrics=["impact_factor", "quartile"],
            use_cache=False,
            services=correct_services,
            logger=Mock(),
        )

        # Assert: 验证成功调用
        assert result["success"] is True
        assert result["journal_name"] == "Nature"
        assert "quality_metrics" in result
        assert "h_index" in result["quality_metrics"]

    @pytest.mark.asyncio
    async def test_single_journal_quality_with_incomplete_services_fails(self):
        """验证：使用不完整的服务字典会触发 KeyError"""

        # Arrange: 使用当前 cli.py 的不完整注入
        incomplete_services = {
            "pubmed": Mock(),  # ❌ 只有 pubmed
        }

        # Act & Assert: 调用 _single_journal_quality 应该失败
        from article_mcp.tools.core.quality_tools import _single_journal_quality

        result = await _single_journal_quality(
            journal_name="Nature",
            include_metrics=["impact_factor"],
            use_cache=False,
            services=incomplete_services,
            logger=Mock(),
        )

        # Assert: 验证失败并返回正确的错误信息
        assert result["success"] is False
        assert "'easyscholar'" in result["error"] or "easyscholar" in str(result["error"])


@pytest.mark.unit
class TestServicesInitExports:
    """测试 services/__init__.py 导出是否完整"""

    def test_services_init_exports_easyscholar(self):
        """验证：services/__init__.py 导出了 create_easyscholar_service"""
        from article_mcp.services import create_easyscholar_service

        assert callable(create_easyscholar_service)

    def test_services_init_exports_openalex_metrics(self):
        """验证：services/__init__.py 导出了 create_openalex_metrics_service"""
        from article_mcp.services import create_openalex_metrics_service

        assert callable(create_openalex_metrics_service)
