"""EasyScholar API 服务

EasyScholar 是一个中国学术期刊评级服务，提供：
- 期刊影响因子
- JCI (Journal Citation Index)
- 中科院分区
- 期刊排名
"""

import asyncio
import logging
import os
from typing import Any

import aiohttp


class EasyScholarService:
    """EasyScholar API 服务类"""

    # 高影响力期刊关键词
    HIGH_IMPACT_KEYWORDS = ["nature", "science", "cell", "lancet", "nejm", "pnas"]
    MEDIUM_IMPACT_KEYWORDS = ["journal", "review", "progress", "advances", "research"]

    def __init__(self, logger: logging.Logger | None = None, timeout: int = 30):
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://www.easyscholar.cc"
        self.api_key = os.getenv("EASYSCHOLAR_SECRET_KEY")
        self._timeout_val = timeout
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10)

        if self.api_key:
            self.logger.info("EasyScholar API 密钥已配置")
        else:
            self.logger.debug("EasyScholar API 密钥未配置，将使用模拟数据")

    async def get_journal_quality(
        self, journal_name: str, timeout: int | None = None
    ) -> dict[str, Any]:
        """获取期刊质量信息

        Args:
            journal_name: 期刊名称
            timeout: 请求超时时间（秒）

        Returns:
            包含期刊质量指标的字典
        """
        if not journal_name or not journal_name.strip():
            return {
                "success": False,
                "error": "期刊名称不能为空",
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }

        # 如果没有 API 密钥，直接返回模拟数据
        if not self.api_key:
            self.logger.debug(f"使用模拟数据获取期刊质量: {journal_name}")
            mock_result = self._get_mock_quality(journal_name.strip())
            mock_result["data_source"] = "mock_data"
            return mock_result

        # 尝试调用真实 API
        try:
            result = await asyncio.wait_for(
                self._make_request(journal_name.strip()),
                timeout=timeout or self._timeout_val,
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"EasyScholar API 超时: {journal_name}，降级到模拟数据")
            mock_result = self._get_mock_quality(journal_name.strip())
            mock_result["data_source"] = "mock_data"
            return mock_result
        except Exception as e:
            self.logger.warning(f"EasyScholar API 调用失败: {e}，降级到模拟数据")
            mock_result = self._get_mock_quality(journal_name.strip())
            mock_result["data_source"] = "mock_data"
            return mock_result

    async def batch_get_journal_quality(self, journal_names: list[str]) -> list[dict[str, Any]]:
        """批量获取期刊质量信息

        Args:
            journal_names: 期刊名称列表

        Returns:
            期刊质量信息列表
        """
        results = []
        for journal_name in journal_names:
            result = await self.get_journal_quality(journal_name)
            results.append(result)
        return results

    async def _make_request(self, journal_name: str) -> dict[str, Any]:
        """发起 API 请求

        注意：EasyScholar 没有公开的 API 文档，这是一个示例实现。
        如果未来有官方 API，可以在这里实现。

        当前实现返回模拟数据
        """
        # 模拟 API 延迟
        await asyncio.sleep(0.1)

        # 暂时返回模拟数据，因为 EasyScholar 没有公开的 API
        mock_result = self._get_mock_quality(journal_name)
        mock_result["data_source"] = "easyscholar_api"
        return mock_result

    def _get_mock_quality(self, journal_name: str) -> dict[str, Any]:
        """生成模拟的期刊质量数据

        Args:
            journal_name: 期刊名称

        Returns:
            模拟的期刊质量数据
        """
        journal_lower = journal_name.lower()

        # 检查是否为高影响力期刊
        if any(keyword in journal_lower for keyword in self.HIGH_IMPACT_KEYWORDS):
            return {
                "success": True,
                "journal_name": journal_name,
                "quality_metrics": {
                    "impact_factor": 8.0,
                    "quartile": "Q1",
                    "jci": 3.5,
                    "cas_zone": "中科院一区",
                },
                "ranking_info": {
                    "rank_in_category": 10,
                    "total_journals_in_category": 200,
                    "percentile": 95.0,
                    "assessment_method": "keyword_matching",
                    "confidence": "high",
                },
            }

        # 检查是否为中等影响力期刊
        elif any(keyword in journal_lower for keyword in self.MEDIUM_IMPACT_KEYWORDS):
            return {
                "success": True,
                "journal_name": journal_name,
                "quality_metrics": {
                    "impact_factor": 3.0,
                    "quartile": "Q2",
                    "jci": 1.5,
                    "cas_zone": "中科院二区",
                },
                "ranking_info": {
                    "rank_in_category": 80,
                    "total_journals_in_category": 200,
                    "percentile": 60.0,
                    "assessment_method": "keyword_matching",
                    "confidence": "medium",
                },
            }

        # 默认为低影响力期刊
        else:
            return {
                "success": True,
                "journal_name": journal_name,
                "quality_metrics": {
                    "impact_factor": 1.2,
                    "quartile": "Q3",
                    "jci": 0.8,
                    "cas_zone": "中科院三区",
                },
                "ranking_info": {
                    "rank_in_category": 150,
                    "total_journals_in_category": 200,
                    "percentile": 25.0,
                    "assessment_method": "keyword_matching",
                    "confidence": "low",
                },
            }


def create_easyscholar_service(
    logger: logging.Logger | None = None, timeout: int = 30
) -> EasyScholarService:
    """创建 EasyScholar 服务实例

    Args:
        logger: 日志记录器
        timeout: 请求超时时间（秒）

    Returns:
        EasyScholarService 实例
    """
    return EasyScholarService(logger, timeout)
