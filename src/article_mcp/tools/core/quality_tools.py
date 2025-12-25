"""期刊质量评估工具 - 核心工具5（统一质量评估工具）"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_quality_services = None

# ========== 缓存配置 ==========
# 缓存目录
_CACHE_DIR = Path(os.getenv("JOURNAL_CACHE_DIR", ".cache/journal_quality"))
_CACHE_FILE = _CACHE_DIR / "journal_data.json"

# 缓存过期时间（秒），默认24小时
_CACHE_TTL = int(os.getenv("JOURNAL_CACHE_TTL", "86400"))

# 是否启用缓存
_CACHE_ENABLED = os.getenv("JOURNAL_CACHE_ENABLED", "true").lower() == "true"


def _parse_json_list_param(value: Any) -> Any:
    """解析可能是字符串形式的 JSON 数组参数

    某些 MCP 客户端会将列表参数序列化为字符串（如 '["a", "b"]'）。
    此函数检测并解析这种情况，如果是字符串则尝试解析为列表。

    Args:
        value: 参数值（可能是字符串、列表或其他类型）

    Returns:
        解析后的值：如果是有效的 JSON 数组字符串则返回列表，否则返回原值
    """
    if isinstance(value, str):
        # 尝试解析 JSON 数组字符串
        if value.startswith("[") and value.endswith("]"):
            try:
                import json

                return json.loads(value)
            except json.JSONDecodeError:
                pass
    return value


def register_quality_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册期刊质量评估工具"""
    global _quality_services
    _quality_services = services

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="期刊质量评估工具。评估期刊的学术质量和影响力指标。",
        annotations=ToolAnnotations(title="期刊质量评估", readOnlyHint=True, openWorldHint=False),
        tags={"quality", "journal", "metrics", "ranking"},
    )
    def get_journal_quality(
        journal_name: str | list[str],
        operation: str = "quality",
        evaluation_criteria: list[str] | None = None,
        include_metrics: list[str] | None = None,
        use_cache: bool = True,
        weight_config: dict[str, float] | None = None,
        ranking_type: str = "journal_impact",
        limit: int = 50,
    ) -> dict[str, Any]:
        """期刊质量评估工具。评估期刊的学术质量和影响力指标。

        Args:
            journal_name: 期刊名称（支持中英文）
            operation: 操作类型 ["quality", "ranking", "field_analysis"]
            evaluation_criteria: 评估标准 ["impact_factor", "quartile", "jci"]
            include_metrics: 包含的质量指标类型
            use_cache: 是否使用缓存数据

        Returns:
            包含期刊质量评估结果的字典，包括影响因子、分区等

        """
        try:
            # ========== 参数预处理：解析字符串形式的 JSON 数组 ==========
            # 某些 MCP 客户端会将列表参数序列化为字符串
            journal_name = _parse_json_list_param(journal_name)
            include_metrics = _parse_json_list_param(include_metrics)
            evaluation_criteria = _parse_json_list_param(evaluation_criteria)

            # 根据操作类型分发到具体处理函数
            if operation == "quality":
                if isinstance(journal_name, list):
                    # 批量期刊质量评估
                    return _batch_journal_quality(
                        journal_name, include_metrics or [], use_cache, logger
                    )
                else:
                    # 单个期刊质量评估
                    import asyncio
                    import threading

                    # 检查是否在事件循环中运行
                    try:
                        asyncio.get_running_loop()
                        # 在事件循环中，在新线程中运行
                        result_container = {"result": None}

                        def run_in_new_loop():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                result_container["result"] = new_loop.run_until_complete(
                                    _single_journal_quality(
                                        journal_name, include_metrics, use_cache, logger
                                    )
                                )
                            finally:
                                new_loop.close()

                        thread = threading.Thread(target=run_in_new_loop)
                        thread.start()
                        thread.join(timeout=60)

                        return result_container["result"]
                    except RuntimeError:
                        # 没有运行的事件循环，使用 asyncio.run
                        return asyncio.run(
                            _single_journal_quality(
                                journal_name, include_metrics, use_cache, logger
                            )
                        )

            elif operation == "evaluation":
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {operation}",
                    "journal_name": journal_name,
                    "quality_metrics": {},
                    "data_source": None,
                }

        except Exception as e:
            logger.error(f"期刊质量评估异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "journal_name": journal_name,
                "quality_metrics": {},
                "data_source": None,
            }


async def _single_journal_quality(
    journal_name: str, include_metrics: list[str] | None, use_cache: bool, logger: Any
) -> dict[str, Any]:
    """单个期刊质量评估（带文件缓存支持）"""
    try:
        if not journal_name or not journal_name.strip():
            from fastmcp.exceptions import ToolError

            raise ToolError("期刊名称不能为空")

        # 处理None值的include_metrics参数
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
            easyscholar_service = _get_easyscholar_service(logger)
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

        # 过滤用户请求的指标
        quality_metrics = result.get("quality_metrics", {})
        filtered_metrics = {}
        for metric in include_metrics:
            if metric in quality_metrics:
                filtered_metrics[metric] = quality_metrics[metric]
            # 添加别名映射
            elif metric == "cas_zone" and "cas_zone" in quality_metrics:
                filtered_metrics[metric] = quality_metrics[metric]
            elif metric == "chinese_academy_sciences_zone" and "cas_zone" in quality_metrics:
                filtered_metrics[metric] = quality_metrics["cas_zone"]

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "journal_name": normalized_name,
            "quality_metrics": filtered_metrics,
            "ranking_info": result.get("ranking_info", {}),
            "data_source": data_source,
            "cache_hit": cache_hit,
            "processing_time": processing_time,
        }

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


def _batch_journal_quality(
    journal_names: list[str], include_metrics: list[str], use_cache: bool, logger: Any
) -> dict[str, Any]:
    """批量期刊质量评估（带文件缓存支持）"""
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

        # 使用异步批量评估
        async def batch_eval() -> None:
            nonlocal successful_evaluations, cache_hits

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
            easyscholar_service = _get_easyscholar_service(logger)
            fetched_results = await easyscholar_service.batch_get_journal_quality(journals_to_fetch)

            # 合并结果
            all_results = {}
            all_results.update(cached_journals)
            for i, result in enumerate(fetched_results):
                all_results[journals_to_fetch[i]] = (result, False)

            # 处理每个期刊的结果
            for journal_name, (result, is_cached) in all_results.items():
                # 过滤请求的指标
                if result.get("success", False):
                    quality_metrics = result.get("quality_metrics", {})
                    filtered_metrics = {}
                    for metric in include_metrics:
                        if metric in quality_metrics:
                            filtered_metrics[metric] = quality_metrics[metric]

                    journal_results[journal_name] = {
                        "success": True,
                        "journal_name": journal_name,
                        "quality_metrics": filtered_metrics,
                        "ranking_info": result.get("ranking_info", {}),
                        "data_source": "cache"
                        if is_cached
                        else result.get("data_source", "easyscholar"),
                        "cache_hit": is_cached,
                    }
                    successful_evaluations += 1

                    # 保存到缓存（仅限新获取的数据）
                    if use_cache and _CACHE_ENABLED and not is_cached:
                        await asyncio.to_thread(_save_to_file_cache, journal_name, result, logger)
                else:
                    journal_results[journal_name] = result

        # 运行异步批量评估
        try:
            # 尝试获取正在运行的事件循环
            asyncio.get_running_loop()
            # 如果能获取到，说明已经在事件循环中
            # 在新线程中运行以避免嵌套事件循环问题
            import threading

            result_container = {"done": False, "result": None}

            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(batch_eval())
                    result_container["done"] = True
                finally:
                    new_loop.close()

            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join(timeout=60)
        except RuntimeError:
            # 没有正在运行的事件循环，使用 asyncio.run
            asyncio.run(batch_eval())

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


def _batch_articles_quality_evaluation(
    articles: list[dict[str, Any]],
    evaluation_criteria: list[str],
    weight_config: dict[str, float] | None,
    logger: Any,
) -> dict[str, Any]:
    """批量文献质量评估"""
    try:
        if not articles:
            return {
                "success": False,
                "error": "文献列表不能为空",
                "evaluated_articles": [],
                "quality_distribution": {},
                "ranking": [],
                "evaluation_summary": {},
                "processing_time": 0,
            }

        start_time = time.time()

        # 设置默认权重
        if weight_config is None:
            weights = {
                "journal_quality": 0.5,
                "citation_count": 0.3,
                "open_access": 0.2,
            }
        else:
            weights = weight_config

        evaluated_articles = []
        quality_scores = []

        for i, article in enumerate(articles):
            try:
                quality_evaluation = _evaluate_article_quality(
                    article, evaluation_criteria, weights, logger
                )
                quality_score = quality_evaluation.get("overall_score", 0)

                evaluated_articles.append(
                    {
                        "index": i,
                        "article": article,
                        "quality_evaluation": quality_evaluation,
                    }
                )
                quality_scores.append(quality_score)

            except Exception as e:
                logger.error(f"评估第 {i + 1} 篇文献失败: {e}")
                evaluated_articles.append(
                    {
                        "index": i,
                        "article": article,
                        "quality_evaluation": {
                            "overall_score": 0,
                            "evaluated_criteria": [],
                        },
                    }
                )

        # 计算质量分布
        quality_distribution = _calculate_quality_distribution(quality_scores)

        # 生成排名
        ranking = sorted(
            [(i, score) for i, score in enumerate(quality_scores)],
            key=lambda x: x[1],
            reverse=True,
        )

        # 统计信息
        evaluation_summary = {
            "total_articles": len(articles),
            "successful_evaluations": sum(
                1  # type: ignore[misc]
                for eval_result in evaluated_articles
                if isinstance(eval_result, dict)
                and eval_result.get("quality_evaluation", {}).get("overall_score", 0) > 0  # type: ignore[attr-defined]
            ),
            "average_quality_score": (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0
            ),
            "highest_score": max(quality_scores) if quality_scores else 0,
            "lowest_score": min(quality_scores) if quality_scores else 0,
            "evaluation_criteria_used": evaluation_criteria,
            "weights_applied": weights,
        }

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "evaluated_articles": evaluated_articles,
            "quality_distribution": quality_distribution,
            "ranking": [
                {"article_index": idx, "rank": i + 1, "score": score}
                for i, (idx, score) in enumerate(ranking)
            ],
            "evaluation_summary": evaluation_summary,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"批量评估文献质量异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "evaluated_articles": [],
            "quality_distribution": {},
            "ranking": [],
            "evaluation_summary": {},
            "processing_time": 0,
        }


def _get_field_ranking(
    field_name: str, ranking_type: str, limit: int, logger: Any
) -> dict[str, Any]:
    """获取学科领域期刊排名"""
    try:
        if not field_name or not field_name.strip():
            return {
                "success": False,
                "error": "学科领域名称不能为空",
                "field_name": field_name,
                "ranking_type": ranking_type,
                "top_journals": [],
                "field_statistics": {},
            }

        start_time = time.time()

        # 预定义的学科领域期刊排名（示例数据）
        field_rankings = _get_predefined_field_rankings()

        # 查找匹配的领域排名
        field_data = None
        for field in field_rankings:
            if (
                field_name.lower() in field["name"].lower()
                or field["name"].lower() in field_name.lower()
            ):
                field_data = field
                break

        if not field_data:
            return {
                "success": False,
                "error": f"未找到学科领域 '{field_name}' 的排名数据",
                "field_name": field_name,
                "ranking_type": ranking_type,
                "top_journals": [],
                "field_statistics": {},
            }

        # 根据排名类型排序
        journals = field_data.get("journals", [])
        if ranking_type == "journal_impact":
            journals.sort(key=lambda x: x.get("impact_factor", 0), reverse=True)
        elif ranking_type == "jci":
            journals.sort(key=lambda x: x.get("jci", 0), reverse=True)
        elif ranking_type == "citation_score":
            journals.sort(key=lambda x: x.get("citation_score", 0), reverse=True)

        # 限制返回数量
        top_journals = journals[:limit]

        # 计算统计信息
        field_statistics = {
            "total_journals": len(journals),
            "ranking_type": ranking_type,
            "average_impact_factor": (
                sum(j.get("impact_factor", 0) for j in journals) / len(journals) if journals else 0
            ),
            "highest_impact_factor": (
                max(j.get("impact_factor", 0) for j in journals) if journals else 0
            ),
            "lowest_impact_factor": (
                min(j.get("impact_factor", 0) for j in journals) if journals else 0
            ),
        }

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "field_name": field_name.strip(),
            "ranking_type": ranking_type,
            "top_journals": top_journals,
            "field_statistics": field_statistics,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"获取学科领域期刊排名异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "field_name": field_name,
            "ranking_type": ranking_type,
            "top_journals": [],
            "field_statistics": {},
        }


# 辅助函数
def _get_easyscholar_service(logger: Any) -> Any:
    """获取 EasyScholar 服务实例"""
    from article_mcp.services.easyscholar_service import create_easyscholar_service

    return create_easyscholar_service(logger)


# ========== 缓存辅助函数 ==========


def _get_from_file_cache(journal_name: str, logger: Any) -> dict[str, Any] | None:
    """从文件缓存获取期刊质量信息

    Args:
        journal_name: 期刊名称
        logger: 日志记录器

    Returns:
        缓存的数据，如果不存在或已过期返回 None
    """
    if not _CACHE_FILE.exists():
        return None

    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            cache_data = json.load(f)

        # 检查是否过期
        cached = cache_data.get("journals", {}).get(journal_name)
        if cached:
            timestamp = cached.get("timestamp", 0)
            if time.time() - timestamp < _CACHE_TTL:
                logger.debug(f"文件缓存命中: {journal_name}")
                data = cached.get("data")
                if isinstance(data, dict):
                    return data
                return None

        return None
    except Exception as e:
        logger.error(f"读取文件缓存失败: {e}")
        return None


def _save_to_file_cache(journal_name: str, data: dict[str, Any], logger: Any) -> None:
    """保存到文件缓存

    Args:
        journal_name: 期刊名称
        data: 要缓存的数据
        logger: 日志记录器
    """
    try:
        # 确保缓存目录存在
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # 读取现有缓存
        if _CACHE_FILE.exists():
            with open(_CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)
        else:
            cache_data = {"journals": {}, "version": "1.0", "created_at": time.time()}

        # 更新缓存
        cache_data["journals"][journal_name] = {
            "data": data,
            "timestamp": time.time(),
        }
        cache_data["last_updated"] = time.time()

        # 写入文件
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"已保存到文件缓存: {journal_name}")
    except Exception as e:
        logger.error(f"写入文件缓存失败: {e}")


def _evaluate_article_quality(
    article: dict[str, Any], criteria: list[str], weights: dict[str, float], logger: Any
) -> dict[str, Any]:
    """评估单篇文献的质量"""
    try:
        scores = {}
        total_score = 0

        for criterion in criteria:
            if criterion == "journal_quality":
                # 基于期刊名称评估质量
                journal = article.get("journal", "")
                if journal:
                    import asyncio

                    service = _get_easyscholar_service(logger)
                    quality_result = asyncio.run(service.get_journal_quality(journal))
                    impact_factor = quality_result.get("quality_metrics", {}).get(
                        "impact_factor", 0
                    )
                    # 归一化影响因子到0-100分
                    score = min(impact_factor * 10, 100)
                    scores[criterion] = score
                else:
                    scores[criterion] = 0

            elif criterion == "citation_count":
                # 基于引用数量评估（这里使用模拟值）
                scores[criterion] = 50  # 模拟分数

            elif criterion == "open_access":
                # 检查是否为开放获取
                scores[criterion] = 80 if article.get("open_access", False) else 30

            else:
                scores[criterion] = 0

        # 计算加权总分
        for criterion, score in scores.items():
            weight = weights.get(criterion, 0)
            total_score += score * weight

        return {
            "overall_score": round(total_score, 2),
            "individual_scores": scores,
            "weights_applied": weights,
            "evaluated_criteria": criteria,
        }

    except Exception as e:
        logger.error(f"评估文献质量失败: {e}")
        return {
            "overall_score": 0,
            "individual_scores": {},
            "weights_applied": {},
            "evaluated_criteria": [],
        }


def _calculate_quality_distribution(scores: list[float]) -> dict[str, Any]:
    """计算质量分布"""
    try:
        if not scores:
            return {}

        distribution = {
            "excellent": sum(1 for score in scores if score >= 80),
            "good": sum(1 for score in scores if 60 <= score < 80),
            "average": sum(1 for score in scores if 40 <= score < 60),
            "poor": sum(1 for score in scores if score < 40),
        }

        distribution["total"] = len(scores)

        # 计算百分比
        for category in ["excellent", "good", "average", "poor"]:
            if distribution["total"] > 0:
                distribution[f"{category}_percentage"] = round(  # type: ignore[assignment]
                    (distribution[category] / distribution["total"]) * 100, 2
                )
            else:
                distribution[f"{category}_percentage"] = 0

        return distribution

    except Exception:
        # 由于这是内部函数，我们不使用logger，而是静默处理异常
        return {}


def _get_predefined_field_rankings() -> list[dict[str, Any]]:
    """获取预定义的学科领域排名数据"""
    return [
        {
            "name": "Biology",
            "journals": [
                {"name": "Nature", "impact_factor": 69.504, "jci": 25.8, "citation_score": 89.2},
                {"name": "Science", "impact_factor": 63.714, "jci": 24.1, "citation_score": 87.5},
                {"name": "Cell", "impact_factor": 66.850, "jci": 23.9, "citation_score": 85.3},
                {"name": "PNAS", "impact_factor": 12.779, "jci": 8.5, "citation_score": 65.2},
                {
                    "name": "Nature Communications",
                    "impact_factor": 17.694,
                    "jci": 12.3,
                    "citation_score": 72.8,
                },
            ],
        },
        {
            "name": "Medicine",
            "journals": [
                {
                    "name": "The Lancet",
                    "impact_factor": 202.731,
                    "jci": 45.2,
                    "citation_score": 95.8,
                },
                {
                    "name": "New England Journal of Medicine",
                    "impact_factor": 158.432,
                    "jci": 42.1,
                    "citation_score": 94.2,
                },
                {
                    "name": "Nature Medicine",
                    "impact_factor": 82.889,
                    "jci": 28.5,
                    "citation_score": 88.9,
                },
                {"name": "BMJ", "impact_factor": 105.726, "jci": 32.4, "citation_score": 91.3},
                {"name": "JAMA", "impact_factor": 120.754, "jci": 35.8, "citation_score": 92.7},
            ],
        },
        {
            "name": "Computer Science",
            "journals": [
                {
                    "name": "Nature Machine Intelligence",
                    "impact_factor": 25.898,
                    "jci": 15.2,
                    "citation_score": 78.5,
                },
                {
                    "name": "IEEE Transactions on Pattern Analysis",
                    "impact_factor": 24.314,
                    "jci": 14.8,
                    "citation_score": 76.2,
                },
                {
                    "name": "Journal of Machine Learning Research",
                    "impact_factor": 6.775,
                    "jci": 8.9,
                    "citation_score": 68.4,
                },
                {
                    "name": "Nature Communications",
                    "impact_factor": 17.694,
                    "jci": 12.3,
                    "citation_score": 72.8,
                },
                {
                    "name": "Advanced Neural Networks",
                    "impact_factor": 12.345,
                    "jci": 9.8,
                    "citation_score": 69.7,
                },
            ],
        },
    ]
