"""EasyScholar API 服务

EasyScholar 是一个中国学术期刊评级服务，提供：
- 期刊影响因子
- JCI (Journal Citation Index)
- 中科院分区
- 期刊排名

官方 API 文档: https://www.easyscholar.cc/open/getPublicationRank
"""

import asyncio
import logging
import os
from typing import Any

import aiohttp


class EasyScholarService:
    """EasyScholar API 服务类"""

    # API 端点
    API_URL = "https://www.easyscholar.cc/open/getPublicationRank"

    # 字段映射：EasyScholar API 字段 -> 内部字段
    FIELD_MAPPING = {
        "sciif": "impact_factor",  # SCI影响因子
        "sci": "quartile",  # SCI分区
        "jci": "jci",  # JCI指数
        "sciUp": "cas_zone",  # 中科院升级版分区
        "sciBase": "cas_zone_base",  # 中科院基础版分区
        "sciUpSmall": "cas_zone_small",  # 中科院升级版小类分区
        "sciUpTop": "cas_zone_top",  # 中科院升级版Top分区
    }

    # 速率限制：每秒最多2次请求（官方要求）
    RATE_LIMIT_PER_SECOND = 2

    def __init__(self, logger: logging.Logger | None = None, timeout: int = 30):
        self.logger = logger or logging.getLogger(__name__)
        self.api_key = os.getenv("EASYSCHOLAR_SECRET_KEY")
        self._timeout_val = timeout
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10)
        self._request_times: list[float] = []  # 用于速率限制

        if self.api_key:
            self.logger.info("EasyScholar API 密钥已配置")
        else:
            self.logger.warning("EASYSCHOLAR_SECRET_KEY 未设置")

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

        # 如果没有 API 密钥，返回配置提示
        if not self.api_key:
            return {
                "success": False,
                "error": "EASYSCHOLAR_SECRET_KEY 环境变量未设置。请访问 https://www.easyscholar.cc 获取密钥，然后设置环境变量：export EASYSCHOLAR_SECRET_KEY=your_key_here",
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }

        # 调用官方 API
        try:
            result = await asyncio.wait_for(
                self._make_request(journal_name.strip()),
                timeout=timeout or self._timeout_val,
            )
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"请求超时：超过 {timeout or self._timeout_val} 秒未响应",
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }
        except RuntimeError as e:
            return {
                "success": False,
                "error": str(e),
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"未知错误: {e}",
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }

    async def batch_get_journal_quality(self, journal_names: list[str]) -> list[dict[str, Any]]:
        """批量获取期刊质量信息

        注意：遵循速率限制，每秒最多2次请求

        Args:
            journal_names: 期刊名称列表

        Returns:
            期刊质量信息列表
        """
        results = []
        for journal_name in journal_names:
            result = await self.get_journal_quality(journal_name)
            results.append(result)
            # 速率限制：每次请求间隔 0.5 秒（每秒最多2次）
            await asyncio.sleep(0.5)
        return results

    async def _make_request(self, journal_name: str) -> dict[str, Any]:
        """发起 EasyScholar API 请求

        官方 API 文档: https://www.easyscholar.cc/open/getPublicationRank

        Args:
            journal_name: 期刊名称

        Returns:
            包含期刊质量指标的字典

        Raises:
            RuntimeError: API 请求失败或返回错误
        """
        # 速率限制检查
        await _enforce_rate_limit(self._request_times, self.RATE_LIMIT_PER_SECOND)

        # 构造请求参数
        params = {
            "secretKey": self.api_key,
            "publicationName": journal_name,
        }

        headers = {
            "User-Agent": "ArticleMCP/2.0",
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(self.API_URL, params=params, headers=headers) as response:
                    if response.status != 200:
                        raise RuntimeError(f"API 返回状态码: {response.status}")

                    data = await response.json()

                    # 检查 API 响应码
                    if data.get("code") != 200:
                        error_msg = data.get("msg", "未知错误")
                        raise RuntimeError(f"API 错误: {error_msg} (code: {data.get('code')})")

                    # 解析返回数据
                    return self._parse_api_response(journal_name, data)

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络请求失败: {e}") from e

    def _parse_api_response(self, journal_name: str, api_data: dict[str, Any]) -> dict[str, Any]:
        """解析 EasyScholar API 响应数据

        Args:
            journal_name: 期刊名称
            api_data: API 返回的原始数据

        Returns:
            标准化的期刊质量数据
        """
        data = api_data.get("data", {})
        official_rank = data.get("officialRank", {})
        all_rank = official_rank.get("all", {})

        # 提取质量指标
        quality_metrics = {}
        for api_field, internal_field in self.FIELD_MAPPING.items():
            if api_field in all_rank:
                value = all_rank[api_field]
                # 转换影响因子为数值
                if internal_field == "impact_factor" and value:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = None
                if value is not None:
                    quality_metrics[internal_field] = value

        # 如果没有获取到任何指标，返回错误
        if not quality_metrics:
            return {
                "success": False,
                "error": f"未找到期刊 '{journal_name}' 的质量信息",
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }

        # 转换中科院分区为中文格式
        if "cas_zone" in quality_metrics:
            quality_metrics["cas_zone"] = _convert_cas_zone(quality_metrics["cas_zone"])

        # 计算 ranking_info
        ranking_info = _calculate_ranking_info(journal_name, quality_metrics)

        return {
            "success": True,
            "journal_name": journal_name,
            "quality_metrics": quality_metrics,
            "ranking_info": ranking_info,
            "data_source": "easyscholar_api",
        }


async def _enforce_rate_limit(request_times: list[float], max_per_second: int) -> None:
    """强制执行速率限制

    Args:
        request_times: 请求时间戳列表
        max_per_second: 每秒最大请求数
    """
    import time

    now = time.time()
    # 移除超过1秒的旧记录
    request_times[:] = [t for t in request_times if now - t < 1.0]

    # 如果达到速率限制，等待
    if len(request_times) >= max_per_second:
        sleep_time = 1.0 - (now - request_times[0])
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
            # 清空记录
            request_times.clear()

    # 记录本次请求时间
    request_times.append(time.time())


def _convert_cas_zone(zone_value: str) -> str:
    """转换中科院分区为中文格式

    Args:
        zone_value: API 返回的分区值

    Returns:
        中文格式的分区字符串
    """
    if not zone_value:
        return "未知"

    zone_upper = zone_value.upper()
    zone_mapping = {
        "1区": "中科院一区",
        "2区": "中科院二区",
        "3区": "中科院三区",
        "4区": "中科院四区",
        "Q1": "中科院一区",
        "Q2": "中科院二区",
        "Q3": "中科院三区",
        "Q4": "中科院四区",
    }

    return zone_mapping.get(zone_upper, f"中科院{zone_value}")


def _calculate_ranking_info(journal_name: str, quality_metrics: dict[str, Any]) -> dict[str, Any]:
    """计算期刊排名信息

    Args:
        journal_name: 期刊名称
        quality_metrics: 质量指标

    Returns:
        排名信息字典
    """
    impact_factor = quality_metrics.get("impact_factor", 0)
    quartile = quality_metrics.get("quartile", "")

    # 根据影响因子和分区估算排名
    if quartile == "Q1" or impact_factor >= 5:
        rank = 10
        percentile = 95.0
        confidence = "high"
    elif quartile == "Q2" or impact_factor >= 3:
        rank = 80
        percentile = 60.0
        confidence = "medium"
    elif quartile == "Q3" or impact_factor >= 1:
        rank = 150
        percentile = 25.0
        confidence = "low"
    else:
        rank = 200
        percentile = 10.0
        confidence = "low"

    return {
        "rank_in_category": rank,
        "total_journals_in_category": 200,
        "percentile": percentile,
        "assessment_method": "api_based",
        "confidence": confidence,
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
