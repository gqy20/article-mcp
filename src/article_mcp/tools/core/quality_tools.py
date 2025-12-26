"""期刊质量评估工具 - 核心工具5

简化版本：
- 只保留期刊质量查询功能（单个/批量）
- 移除了 evaluation、field_analysis、ranking 模式
- 移除了模拟数据和降级机制
- 服务依赖：使用闭包捕获模式，无全局变量
- 缓存并发安全：使用文件锁保护缓存读写操作
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from filelock import FileLock, Timeout

# ========== 缓存配置 ==========
# 缓存目录
_CACHE_DIR = Path(os.getenv("JOURNAL_CACHE_DIR", ".cache/journal_quality"))
_CACHE_FILE = _CACHE_DIR / "journal_data.json"

# 缓存过期时间（秒），默认24小时
_CACHE_TTL = int(os.getenv("JOURNAL_CACHE_TTL", "86400"))

# 是否启用缓存
_CACHE_ENABLED = os.getenv("JOURNAL_CACHE_ENABLED", "true").lower() == "true"

# ========== EasyScholar API + OpenAlex 支持的指标 ==========
# 定义实际提供的指标，用于用户提示和验证

# EasyScholar API 提供的指标
_EASYSCHOLAR_METRICS = {
    "impact_factor": "影响因子（Impact Factor）",
    "quartile": "SCI分区（Q1-Q4）",
    "jci": "JCI指数",
    "cas_zone": "中科院分区（完整）",
    "cas_zone_base": "中科院基础版分区",
    "cas_zone_small": "中科院小类分区",
    "cas_zone_top": "TOP期刊标识",
}

# OpenAlex API 提供的指标
_OPENALEX_METRICS = {
    "h_index": "h指数（来自 OpenAlex）",
    "citation_rate": "引用率（2年平均，来自 OpenAlex）",
    "cited_by_count": "总引用数（来自 OpenAlex）",
    "works_count": "总文章数（来自 OpenAlex）",
    "i10_index": "i10指数（来自 OpenAlex）",
}

# 合并的可用指标
_AVAILABLE_METRICS = {**_EASYSCHOLAR_METRICS, **_OPENALEX_METRICS}

# 预留但当前不可用的指标（为未来扩展预留）
_RESERVED_METRICS = {
    "acceptance_rate": "录用率（暂无免费 API）",
    "eigenfactor": "特征因子（需付费数据源）",
    "sjr": "SJR排名（需 Scopus 数据源）",
    "snip": "SNIP指标（需 Scopus 数据源）",
    "issn": "ISSN号（计划中）",
    "publisher": "出版社（计划中）",
    "country": "出版国家（计划中）",
    "is_oa": "开放获取标识（计划中）",
    "risk_level": "风险等级（计划中）",
    "etc_fat_score": "ETC FAT分数（计划中）",
    "category_rank": "分类排名（计划中）",
    "percentile": "百分位（已在 ranking_info 中提供）",
}


def _parse_json_param(value: Any) -> Any:
    """解析可能是字符串形式的 JSON 参数

    某些 MCP 客户端会将列表/字典参数序列化为字符串：
    - 列表: '["a", "b"]' -> ["a", "b"]
    - 字典: '{"key": "value"}' -> {"key": "value"}

    此函数检测并解析这种情况。

    Args:
        value: 参数值（可能是字符串、列表、字典或其他类型）

    Returns:
        解析后的值：如果是有效的 JSON 字符串则返回解析后的对象，否则返回原值
    """
    if isinstance(value, str):
        # 尝试解析 JSON 字符串
        if value.startswith("[") or value.startswith("{"):
            try:
                import json

                return json.loads(value)
            except json.JSONDecodeError:
                pass
    return value


async def get_journal_quality_async(
    journal_name: str | list[str],
    include_metrics: list[str] | None = None,
    use_cache: bool = True,
    sort_by: str | None = None,
    sort_order: str = "desc",
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """期刊质量评估工具（纯异步版本）

    这是 get_journal_quality 的纯异步版本，不使用 threading 混合模式。
    可用于在异步上下文中直接调用。

    Args:
        journal_name: 期刊名称（单个期刊或期刊列表）
        include_metrics: 返回的质量指标类型
        use_cache: 是否使用缓存数据
        sort_by: 排序字段（仅批量查询有效）
        sort_order: 排序顺序（仅批量查询有效）
        services: 服务依赖注入字典（必需，闭包模式）
        logger: 日志记录器（必需）

    Returns:
        包含期刊质量评估结果的字典
    """
    try:
        # 参数预处理
        journal_name = _parse_json_param(journal_name)
        include_metrics = _parse_json_param(include_metrics)

        if include_metrics is None:
            include_metrics = ["impact_factor", "quartile", "jci"]

        # 判断是单个期刊还是批量期刊
        if isinstance(journal_name, list):
            # 批量期刊质量评估
            if not journal_name:
                return {
                    "success": False,
                    "error": "期刊名称列表不能为空",
                    "total_journals": 0,
                    "successful_evaluations": 0,
                    "journal_results": {},
                    "processing_time": 0,
                }
            result = await _batch_journal_quality(
                journal_name,
                include_metrics,
                use_cache,
                services=services,
                logger=logger,
            )
            # 应用排序（仅批量查询）
            return _apply_sorting(result, sort_by, sort_order)
        else:
            # 单个期刊质量评估 - 直接调用异步函数
            return await _single_journal_quality(
                journal_name,
                include_metrics,
                use_cache,
                services=services,
                logger=logger,
            )

    except Exception as e:
        logger.error(f"期刊质量评估异常（异步版本）: {e}")
        return {
            "success": False,
            "error": str(e),
            "journal_name": journal_name if isinstance(journal_name, str) else "multiple",
            "quality_metrics": {},
            "data_source": None,
        }


def register_quality_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册期刊质量评估工具（使用闭包捕获服务依赖，无全局变量）"""
    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="""期刊质量评估工具。评估期刊的学术质量和影响力指标，集成 EasyScholar + OpenAlex 双数据源。

支持的指标：
EasyScholar 提供：impact_factor（影响因子）、quartile（SCI分区 Q1-Q4）、jci（JCI指数）、cas_zone（中科院分区）、cas_zone_top（TOP期刊标识）
OpenAlex 提供：h_index（h指数）、citation_rate（2年引用率）、cited_by_count（总引用数）、works_count（总文章数）、i10_index（i10指数）

主要参数：
- journal_name: 期刊名称（单个或列表）
- include_metrics: 返回的指标列表（默认["impact_factor", "quartile", "jci"]）
- use_cache: 是否使用24小时缓存（默认true）
- sort_by: 排序字段，仅批量查询有效（默认null）：impact_factor/quartile/jci
- sort_order: 排序顺序，仅批量查询有效（默认desc）：desc降序/asc升序

使用示例：单个期刊查询、批量期刊查询、批量查询并排序、指定返回指标""",
        annotations=ToolAnnotations(title="期刊质量评估", readOnlyHint=True, openWorldHint=False),
        tags={"quality", "journal", "metrics"},
    )
    async def get_journal_quality(
        journal_name: str | list[str],
        include_metrics: str | list[str] | None = None,
        use_cache: bool = True,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """期刊质量评估工具（纯异步版本）。评估期刊的学术质量和影响力指标。

        Args:
            journal_name: 期刊名称（单个期刊或期刊列表）
            include_metrics: 返回的质量指标类型（如 ["impact_factor", "quartile", "jci"]）
            use_cache: 是否使用缓存数据
            sort_by: 排序字段（仅批量查询有效）：impact_factor, quartile, jci
            sort_order: 排序顺序（仅批量查询有效）：desc 降序，asc 升序

        Returns:
            包含期刊质量评估结果的字典，包括影响因子、分区等

        Examples:
            # 单个期刊查询
            await get_journal_quality("Nature")

            # 批量期刊查询
            await get_journal_quality(["Nature", "Science", "Cell"])

            # 批量查询并按影响因子降序排序
            await get_journal_quality(["Nature", "Science"], sort_by="impact_factor", sort_order="desc")

            # 指定返回指标
            await get_journal_quality("Nature", include_metrics=["impact_factor", "cas_zone"])
        """
        try:
            # ========== 参数预处理：解析字符串形式的 JSON 参数 ==========
            # 某些 MCP 客户端会将列表/字典参数序列化为字符串
            journal_name = _parse_json_param(journal_name)
            include_metrics = _parse_json_param(include_metrics)

            # 处理 None 值的 include_metrics 参数
            if include_metrics is None:
                include_metrics = ["impact_factor", "quartile", "jci"]

            # 判断是单个期刊还是批量期刊
            if isinstance(journal_name, list):
                # 批量期刊质量评估
                if not journal_name:
                    return {
                        "success": False,
                        "error": "期刊名称列表不能为空",
                        "total_journals": 0,
                        "successful_evaluations": 0,
                        "journal_results": {},
                        "processing_time": 0,
                    }
                result = await _batch_journal_quality(
                    journal_name,
                    include_metrics,
                    use_cache,
                    services=services,  # 使用闭包捕获的 services
                    logger=logger,
                )
                # 应用排序（仅批量查询）
                return _apply_sorting(result, sort_by, sort_order)
            else:
                # 单个期刊质量评估 - 纯异步调用
                return await _single_journal_quality(
                    journal_name,
                    include_metrics,
                    use_cache,
                    services=services,  # 使用闭包捕获的 services
                    logger=logger,
                )

        except Exception as e:
            logger.error(f"期刊质量评估异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "journal_name": journal_name if isinstance(journal_name, str) else "multiple",
                "quality_metrics": {},
                "data_source": None,
            }


async def _single_journal_quality(
    journal_name: str,
    include_metrics: list[str] | None,
    use_cache: bool,
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """单个期刊质量评估（带文件缓存支持）

    Args:
        journal_name: 期刊名称
        include_metrics: 返回的指标列表
        use_cache: 是否使用缓存
        services: 服务依赖注入字典（必需，闭包捕获模式）
        logger: 日志记录器（必需，闭包捕获模式）
    """
    try:
        if not journal_name or not journal_name.strip():
            from fastmcp.exceptions import ToolError

            raise ToolError("期刊名称不能为空")

        # 处理 None 值的 include_metrics 参数
        if include_metrics is None:
            include_metrics = ["impact_factor", "quartile", "jci"]

        start_time = time.time()
        normalized_name = journal_name.strip()
        result = None
        data_source = None
        cache_hit = False

        # ========== 缓存查询 ==========
        if use_cache and _CACHE_ENABLED:
            # 从文件缓存查询
            cached_result = await asyncio.to_thread(_get_from_file_cache, normalized_name, logger)
            if cached_result:
                logger.debug(f"缓存命中: {normalized_name}")
                result = cached_result
                data_source = "cache"
                cache_hit = True

        # API 调用（缓存未命中或禁用）
        if result is None:
            easyscholar_service = services["easyscholar"]
            result = await easyscholar_service.get_journal_quality(normalized_name)
            data_source = result.get("data_source", "easyscholar")

            # 保存到缓存
            if use_cache and _CACHE_ENABLED and result.get("success", False):
                await asyncio.to_thread(_save_to_file_cache, normalized_name, result, logger)

        if not result.get("success", False):
            return {
                "success": False,
                "error": result.get("error", "获取期刊质量失败"),
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
            }

        # 过滤用户请求的指标，并跟踪不可用指标
        quality_metrics = result.get("quality_metrics", {})
        filtered_metrics = {}
        unavailable_metrics = []

        for metric in include_metrics:
            if metric in quality_metrics:
                filtered_metrics[metric] = quality_metrics[metric]
            # 添加别名映射
            elif metric == "cas_zone" and "cas_zone" in quality_metrics:
                filtered_metrics[metric] = quality_metrics[metric]
            elif metric == "chinese_academy_sciences_zone" and "cas_zone" in quality_metrics:
                filtered_metrics[metric] = quality_metrics["cas_zone"]
            else:
                # 记录不可用的指标
                if metric not in unavailable_metrics:
                    unavailable_metrics.append(metric)

        processing_time = round(time.time() - start_time, 2)

        response = {
            "success": True,
            "journal_name": normalized_name,
            "quality_metrics": filtered_metrics,
            "ranking_info": result.get("ranking_info", {}),
            "data_source": data_source,
            "cache_hit": cache_hit,
            "processing_time": processing_time,
        }

        # 添加指标可用性信息
        if unavailable_metrics:
            response["metrics_info"] = {
                "unavailable_metrics": unavailable_metrics,
                "available_metrics": list(_AVAILABLE_METRICS.keys()),
                "note": "某些请求的指标在当前数据源中不可用",
            }

        # 集成 OpenAlex 指标补充（在当前异步上下文中运行）
        try:
            openalex_service = services["openalex"]
            response = await openalex_service.enhance_quality_result(response, use_cache)
        except Exception as e:
            # OpenAlex 补充失败不影响主流程
            logger.debug(f"OpenAlex 指标补充失败（非致命）: {e}")

        return response

    except Exception as e:
        logger.error(f"单个期刊质量评估异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "journal_name": journal_name,
            "quality_metrics": {},
            "ranking_info": {},
            "data_source": None,
        }


async def _batch_journal_quality(
    journal_names: list[str],
    include_metrics: list[str],
    use_cache: bool,
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """批量期刊质量评估（纯异步版本，带文件缓存支持）"""
    try:
        if not journal_names:
            return {
                "success": False,
                "error": "期刊名称列表不能为空",
                "total_journals": 0,
                "successful_evaluations": 0,
                "journal_results": {},
                "cache_hits": 0,
                "processing_time": 0,
            }

        start_time = time.time()
        journal_results = {}
        successful_evaluations = 0
        cache_hits = 0

        # 先从缓存查找
        cached_journals = {}
        journals_to_fetch = []

        if use_cache and _CACHE_ENABLED:
            for journal_name in journal_names:
                cached_result = await asyncio.to_thread(
                    _get_from_file_cache, journal_name.strip(), logger
                )
                if cached_result:
                    cached_journals[journal_name] = (cached_result, True)
                    cache_hits += 1
                else:
                    journals_to_fetch.append(journal_name)
        else:
            journals_to_fetch = journal_names.copy()

        # 获取未缓存的数据
        easyscholar_service = services["easyscholar"]
        fetched_results = await easyscholar_service.batch_get_journal_quality(journals_to_fetch)

        # 合并结果
        all_results = {}
        all_results.update(cached_journals)
        for i, result in enumerate(fetched_results):
            all_results[journals_to_fetch[i]] = (result, False)

        # 处理每个期刊的结果
        for journal_name, (result, is_cached) in all_results.items():
            # 过滤请求的指标，并跟踪不可用指标
            if result.get("success", False):
                quality_metrics = result.get("quality_metrics", {})
                filtered_metrics = {}
                unavailable_metrics = []

                for metric in include_metrics:
                    if metric in quality_metrics:
                        filtered_metrics[metric] = quality_metrics[metric]
                    else:
                        # 记录不可用的指标
                        if metric not in unavailable_metrics:
                            unavailable_metrics.append(metric)

                journal_entry = {
                    "success": True,
                    "journal_name": journal_name,
                    "quality_metrics": filtered_metrics,
                    "ranking_info": result.get("ranking_info", {}),
                    "data_source": "cache"
                    if is_cached
                    else result.get("data_source", "easyscholar"),
                    "cache_hit": is_cached,
                }

                # 为每个期刊添加指标可用性信息
                if unavailable_metrics:
                    journal_entry["metrics_info"] = {
                        "unavailable_metrics": unavailable_metrics,
                        "available_metrics": list(_AVAILABLE_METRICS.keys()),
                    }

                # 集成 OpenAlex 指标补充
                try:
                    openalex_service = services["openalex"]
                    journal_entry = await openalex_service.enhance_quality_result(
                        journal_entry, use_cache
                    )
                except Exception as e:
                    # OpenAlex 补充失败不影响主流程
                    logger.debug(f"OpenAlex 指标补充失败（非致命）: {e}")

                journal_results[journal_name] = journal_entry
                successful_evaluations += 1

                # 保存到缓存（仅限新获取的数据）
                if use_cache and _CACHE_ENABLED and not is_cached:
                    await asyncio.to_thread(_save_to_file_cache, journal_name, result, logger)
            else:
                journal_results[journal_name] = result

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": successful_evaluations > 0,
            "total_journals": len(journal_names),
            "successful_evaluations": successful_evaluations,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / len(journal_names) if journal_names else 0,
            "success_rate": successful_evaluations / len(journal_names) if journal_names else 0,
            "journal_results": journal_results,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"批量期刊质量评估异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_journals": len(journal_names) if journal_names else 0,
            "successful_evaluations": 0,
            "cache_hits": 0,
            "journal_results": {},
            "processing_time": 0,
        }


# 辅助函数
def _get_easyscholar_service(logger: Any) -> Any:
    """获取 EasyScholar 服务实例"""
    from article_mcp.services.easyscholar_service import create_easyscholar_service

    return create_easyscholar_service(logger)


def _get_openalex_service(logger: Any) -> Any:
    """获取 OpenAlex 指标补充服务实例"""
    from article_mcp.services.openalex_metrics_service import create_openalex_metrics_service

    return create_openalex_metrics_service(logger)


# ========== 缓存辅助函数 ==========


def _get_from_file_cache(journal_name: str, logger: Any) -> dict[str, Any] | None:
    """从文件缓存获取期刊质量信息（合并 EasyScholar 和 OpenAlex 数据）

    使用文件锁确保并发读安全性。

    Args:
        journal_name: 期刊名称
        logger: 日志记录器

    Returns:
        合并后的缓存数据，如果不存在或已过期返回 None
    """
    if not _CACHE_FILE.exists():
        return None

    try:
        # 使用文件锁保护读取操作（超时5秒）
        lock_file = _CACHE_FILE.with_suffix(".lock")
        with FileLock(lock_file, timeout=5):
            with open(_CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)

        # 检查是否过期
        cached = cache_data.get("journals", {}).get(journal_name)
        if cached:
            timestamp = cached.get("timestamp", 0)
            if time.time() - timestamp < _CACHE_TTL:
                logger.debug(f"文件缓存命中: {journal_name}")

                # 获取 EasyScholar 数据
                data = cached.get("data")
                if not isinstance(data, dict):
                    return None

                # 获取 OpenAlex 指标（如果存在）
                openalex_metrics = cached.get("openalex_metrics")
                if isinstance(openalex_metrics, dict):
                    # 合并 OpenAlex 指标到 quality_metrics
                    if "quality_metrics" in data:
                        data["quality_metrics"] = {
                            **data["quality_metrics"],
                            **openalex_metrics,
                        }
                    else:
                        data["quality_metrics"] = openalex_metrics.copy()

                    # 更新数据来源标记
                    original_source = data.get("data_source", "easyscholar")
                    data["data_source"] = f"{original_source}+openalex_cache"

                return data

        return None
    except Timeout:
        logger.warning(f"获取缓存文件锁超时: {journal_name}")
        return None
    except Exception as e:
        logger.error(f"读取文件缓存失败: {e}")
        return None


def _save_to_file_cache(journal_name: str, data: dict[str, Any], logger: Any) -> None:
    """保存到文件缓存（与 OpenAlex 共享缓存文件）

    使用文件锁确保并发写安全性，防止数据丢失或损坏。

    Args:
        journal_name: 期刊名称
        data: 要缓存的数据
        logger: 日志记录器
    """
    try:
        # 确保缓存目录存在
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # 使用文件锁保护写操作（超时5秒）
        lock_file = _CACHE_FILE.with_suffix(".lock")
        with FileLock(lock_file, timeout=5):
            # 读取现有缓存
            if _CACHE_FILE.exists():
                with open(_CACHE_FILE, encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                cache_data = {"journals": {}, "version": "2.0", "created_at": time.time()}

            # 更新缓存（保留可能已存在的 openalex_metrics）
            if journal_name in cache_data["journals"]:
                # 期刊已存在，保留 openalex_metrics，更新 data 和 timestamp
                cache_data["journals"][journal_name]["data"] = data
                cache_data["journals"][journal_name]["timestamp"] = time.time()
            else:
                # 期刊不存在，创建新条目
                cache_data["journals"][journal_name] = {
                    "data": data,
                    "timestamp": time.time(),
                }

            cache_data["last_updated"] = time.time()

            # 写入文件
            with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"已保存到文件缓存: {journal_name}")
    except Timeout:
        logger.error(f"获取缓存文件锁超时（写入失败）: {journal_name}")
    except Exception as e:
        logger.error(f"写入文件缓存失败: {e}")


# ========== 排序辅助函数 ==========


def _get_quartile_order(quartile: str) -> int:
    """获取分区的排序值

    分区排序优先级：Q1 > Q2 > Q3 > Q4
    支持英文格式（Q1-Q4）和中文格式（1区-4区）

    Args:
        quartile: 分区字符串（如 "Q1", "1区", "Q2", "2区" 等）

    Returns:
        排序值，值越大排序越靠前
    """
    quartile_map = {
        # 英文格式
        "Q1": 4,
        "Q2": 3,
        "Q3": 2,
        "Q4": 1,
        # 中文格式
        "1区": 4,
        "2区": 3,
        "3区": 2,
        "4区": 1,
    }
    return quartile_map.get(quartile, 0)  # 无效分区返回 0，排在最后


def _get_sort_key(journal_data: dict, sort_by: str) -> tuple:
    """获取期刊数据的排序键

    Args:
        journal_data: 期刊数据字典
        sort_by: 排序字段（impact_factor, quartile, jci）

    Returns:
        排序键值元组，用于比较排序：(primary_key, secondary_key, ...)
        主键相同的情况下使用次键，确保排序稳定
    """
    quality_metrics = journal_data.get("quality_metrics", {})
    journal_name = journal_data.get("journal_name", "")

    if sort_by == "impact_factor":
        value = quality_metrics.get("impact_factor")
        if value is None:
            return (0, 0, journal_name)  # 缺失值排最后：(has_value, value, name)
        return (1, float(value), journal_name)

    if sort_by == "quartile":
        quartile = quality_metrics.get("quartile", "")
        order = _get_quartile_order(quartile)
        return (order, quartile, journal_name)  # 同分区时按名称排序

    if sort_by == "jci":
        value = quality_metrics.get("jci")
        if value is None:
            return (0, 0, journal_name)  # 缺失值排最后
        return (1, float(value), journal_name)

    # 未知字段
    return (0, "", journal_name)


def _apply_sorting(
    result: dict[str, Any], sort_by: str | None = None, sort_order: str = "desc"
) -> dict[str, Any]:
    """对批量期刊查询结果应用排序

    Args:
        result: 批量期刊查询结果
        sort_by: 排序字段（impact_factor, quartile, jci），None 表示不排序
        sort_order: 排序顺序（"desc" 降序，"asc" 升序）

    Returns:
        统一返回列表格式，包含 journals 和 sort_info
        - sort_by 为 None 时，journals 按原始顺序排列，sort_info 为 None
        - sort_by 有值时，journals 按指定字段排序
    """
    # 提取期刊结果
    journal_results = result.get("journal_results", {})
    if not journal_results:
        return result

    # 提取成功的期刊结果
    successful_journals = [data for data in journal_results.values() if data.get("success", False)]

    if not successful_journals:
        return result

    # 排序逻辑（仅当指定了有效排序字段时）
    valid_fields = {"impact_factor", "quartile", "jci"}
    if sort_by in valid_fields:
        reverse = sort_order.lower() == "desc"
        successful_journals = sorted(
            successful_journals,
            key=lambda j: _get_sort_key(j, sort_by),
            reverse=reverse,
        )

    # 统一返回列表格式
    sorted_result = {
        "success": result.get("success", True),
        "total_journals": result.get("total_journals", len(successful_journals)),
        "successful_evaluations": len(successful_journals),
        "cache_hits": result.get("cache_hits", 0),
        "cache_hit_rate": result.get("cache_hit_rate", 0),
        "success_rate": result.get("success_rate", 1.0),
        "journals": successful_journals,  # 统一列表格式
        "sort_info": {"field": sort_by, "order": sort_order} if sort_by in valid_fields else None,
        "processing_time": result.get("processing_time", 0),
    }

    return sorted_result
