"""OpenAlex 指标补充服务

从 OpenAlex API 获取期刊指标，补充 EasyScholar 数据：
- h_index: h 指数
- citation_rate: 引用率 (2yr_mean_citedness)
- cited_by_count: 总引用数
- works_count: 总文章数

官方 API: https://openalex.org/
无需注册，无频率限制

缓存：与 EasyScholar 共享统一的缓存文件 .cache/journal_quality/journal_data.json
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path

import aiohttp

# 缓存配置 - 使用统一的期刊质量缓存文件
_CACHE_DIR = Path(os.getenv("JOURNAL_CACHE_DIR", ".cache/journal_quality"))
_CACHE_FILE = _CACHE_DIR / "journal_data.json"
_CACHE_TTL = int(os.getenv("JOURNAL_CACHE_TTL", "86400"))  # 24小时


class OpenAlexMetricsService:
    """OpenAlex 指标补充服务"""

    # API 端点
    API_URL = "https://api.openalex.org/sources"

    def __init__(self, logger: logging.Logger | None = None, timeout: int = 30):
        self.logger = logger or logging.getLogger(__name__)
        self._timeout_val = timeout
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10)

        # 确保缓存目录存在
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def _cache_file(self) -> Path:
        """获取缓存文件路径"""
        return _CACHE_FILE

    async def get_journal_metrics(
        self, journal_name: str, use_cache: bool = True
    ) -> dict[str, float] | None:
        """获取期刊的 OpenAlex 指标

        Args:
            journal_name: 期刊名称
            use_cache: 是否使用缓存

        Returns:
            包含 h_index, citation_rate 等指标的字典，如果未找到返回 None
        """
        try:
            # 尝试从缓存获取
            if use_cache:
                cached = await self._load_from_cache(journal_name)
                if cached:
                    self.logger.debug(f"OpenAlex 缓存命中: {journal_name}")
                    return cached

            # 从 API 获取
            metrics = await self._fetch_from_api(journal_name)

            # 保存到缓存
            if metrics and use_cache:
                await self._save_to_cache(journal_name, metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"获取 OpenAlex 指标失败 ({journal_name}): {e}")
            return None

    async def batch_get_journal_metrics(
        self, journal_names: list[str], use_cache: bool = True
    ) -> list[dict[str, float] | None]:
        """批量获取期刊指标

        Args:
            journal_names: 期刊名称列表
            use_cache: 是否使用缓存

        Returns:
            指标字典列表，未找到的期刊对应位置为 None
        """
        tasks = [self.get_journal_metrics(name, use_cache) for name in journal_names]
        return await asyncio.gather(*tasks)

    async def _fetch_from_api(self, journal_name: str) -> dict[str, float] | None:
        """从 OpenAlex API 获取期刊指标

        Args:
            journal_name: 期刊名称

        Returns:
            指标字典，如果未找到返回 None
        """
        try:
            import urllib.parse

            url = f"{self.API_URL}?search={urllib.parse.quote(journal_name)}"

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"OpenAlex API 返回状态 {response.status}")
                        return None

                    data = await response.json()

                    if not data.get("results"):
                        return None

                    # 提取第一个匹配的期刊
                    source = data["results"][0]

                    return self._parse_openalex_response(source)

        except asyncio.TimeoutError:
            self.logger.warning(f"OpenAlex API 超时: {journal_name}")
            return None
        except Exception as e:
            self.logger.error(f"OpenAlex API 请求失败: {e}")
            return None

    def _parse_openalex_response(self, source: dict) -> dict[str, float]:
        """解析 OpenAlex API 响应，提取指标

        Args:
            source: OpenAlex API 返回的 source 对象

        Returns:
            标准化的指标字典
        """
        summary_stats = source.get("summary_stats", {})

        return {
            "h_index": summary_stats.get("h_index"),
            "citation_rate": summary_stats.get("2yr_mean_citedness"),
            "cited_by_count": source.get("cited_by_count"),
            "works_count": source.get("works_count"),
            "i10_index": summary_stats.get("i10_index"),
        }

    async def _load_from_cache(self, journal_name: str) -> dict[str, float] | None:
        """从缓存加载期刊指标

        Args:
            journal_name: 期刊名称

        Returns:
            缓存的 OpenAlex 指标，如果不存在或已过期返回 None
        """
        if not self._cache_file.exists():
            return None

        try:
            with open(self._cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)

            cached = cache_data.get("journals", {}).get(journal_name)
            if cached:
                timestamp = cached.get("timestamp", 0)
                if time.time() - timestamp < _CACHE_TTL:
                    # 从 openalex_metrics 字段获取指标
                    openalex_metrics = cached.get("openalex_metrics")
                    if openalex_metrics:
                        self.logger.debug(f"OpenAlex 缓存命中: {journal_name}")
                        return openalex_metrics

        except Exception as e:
            self.logger.error(f"读取 OpenAlex 缓存失败: {e}")

        return None

    async def _save_to_cache(self, journal_name: str, metrics: dict[str, float]) -> None:
        """保存指标到缓存（与 EasyScholar 共享缓存文件）

        Args:
            journal_name: 期刊名称
            metrics: 要缓存的 OpenAlex 指标
        """
        try:
            # 读取现有缓存
            if self._cache_file.exists():
                with open(self._cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                cache_data = {"journals": {}, "version": "2.0", "created_at": time.time()}

            # 更新或创建期刊条目，添加 openalex_metrics 字段
            if journal_name in cache_data["journals"]:
                # 期刊已存在，只更新 openalex_metrics 和 timestamp
                cache_data["journals"][journal_name]["openalex_metrics"] = metrics
                cache_data["journals"][journal_name]["timestamp"] = time.time()
            else:
                # 期刊不存在，创建新条目（保留可能已存在的 data 字段）
                cache_data["journals"][journal_name] = {
                    "openalex_metrics": metrics,
                    "timestamp": time.time(),
                }
                # 注意：这里不会覆盖 data 字段，因为期刊是新创建的
                # 如果 EasyScholar 先保存了数据，它会在 else 分支中存在

            cache_data["last_updated"] = time.time()

            # 写入文件
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"OpenAlex 指标已缓存: {journal_name}")

        except Exception as e:
            self.logger.error(f"写入 OpenAlex 缓存失败: {e}")

    def merge_metrics(self, easyscholar_data: dict, openalex_metrics: dict[str, float]) -> dict:
        """合并 EasyScholar 和 OpenAlex 数据

        Args:
            easyscholar_data: EasyScholar 返回的数据
            openalex_metrics: OpenAlex 指标

        Returns:
            合并后的数据
        """
        result = easyscholar_data.copy()

        # 合并 quality_metrics
        if "quality_metrics" in result:
            result["quality_metrics"] = {
                **result["quality_metrics"],
                **openalex_metrics,
            }
        else:
            result["quality_metrics"] = openalex_metrics.copy()

        # 更新数据来源
        original_source = result.get("data_source", "easyscholar")
        result["data_source"] = f"{original_source}+openalex"

        return result

    async def enhance_quality_result(self, quality_result: dict, use_cache: bool = True) -> dict:
        """用 OpenAlex 数据增强质量评估结果

        Args:
            quality_result: EasyScholar 质量评估结果
            use_cache: 是否使用 OpenAlex 缓存

        Returns:
            增强后的结果（包含 OpenAlex 指标）
        """
        if not quality_result.get("success"):
            return quality_result

        journal_name = quality_result.get("journal_name")
        if not journal_name:
            return quality_result

        # 获取 OpenAlex 指标
        openalex_metrics = await self.get_journal_metrics(journal_name, use_cache)

        # 如果有 OpenAlex 数据，合并到结果中
        if openalex_metrics:
            return self.merge_metrics(quality_result, openalex_metrics)

        return quality_result


def create_openalex_metrics_service(
    logger: logging.Logger | None = None, timeout: int = 30
) -> OpenAlexMetricsService:
    """创建 OpenAlex 指标服务

    Args:
        logger: 日志记录器
        timeout: API 请求超时时间（秒）

    Returns:
        OpenAlexMetricsService 实例
    """
    return OpenAlexMetricsService(logger, timeout)
