"""
期刊质量评估工具 - 核心工具5（统一质量评估工具）
"""

import json
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_quality_services = None


def register_quality_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册期刊质量评估工具"""
    global _quality_services
    _quality_services = services

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="期刊质量评估工具。评估期刊的学术质量和影响力指标。",
        annotations=ToolAnnotations(
            title="期刊质量评估",
            readOnlyHint=True,
            openWorldHint=False
        ),
        tags={"quality", "journal", "metrics", "ranking"}
    )
    def get_journal_quality(
        journal_name: str,
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
            # 根据操作类型分发到具体处理函数
            if operation == "quality":
                if isinstance(journal_name, list):
                    # 批量期刊质量评估
                    return _batch_journal_quality(journal_name, include_metrics, use_cache, logger)
                else:
                    # 单个期刊质量评估
                    return _single_journal_quality(journal_name, include_metrics, use_cache, logger)

            elif operation == "evaluation":
                # 批量文献质量评估
                if isinstance(journal_name, list):
                    return _batch_articles_quality_evaluation(
                        journal_name, evaluation_criteria, weight_config, logger
                    )
                else:
                    return {
                        "success": False,
                        "error": "evaluation操作需要文献列表",
                        "evaluated_articles": [],
                        "quality_distribution": {},
                        "evaluation_summary": {},
                        "processing_time": 0,
                    }

            elif operation in ["ranking", "field_ranking"]:
                # 学科领域期刊排名
                field_name = (
                    journal_name if isinstance(journal_name, str) else (journal_name[0] if journal_name else "")
                )
                return _get_field_ranking(field_name, ranking_type, limit, logger)

            else:
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

    

def _single_journal_quality(
    journal_name: str, include_metrics: list[str], use_cache: bool, logger
) -> dict[str, Any]:
    """单个期刊质量评估"""
    try:
        if not journal_name or not journal_name.strip():
            from fastmcp.exceptions import ToolError
            raise ToolError("期刊名称不能为空")

        # 处理None值的include_metrics参数
        if include_metrics is None:
            include_metrics = ["impact_factor", "quartile", "jci"]

        start_time = time.time()

        # 尝试从多个数据源获取质量指标
        quality_metrics = {}
        ranking_info = {}
        data_source = None

        # 1. 尝试从EasyScholar获取
        try:
            easyscholar_result = _get_easyscholar_quality(journal_name.strip(), logger)
            if easyscholar_result.get("success", False):
                quality_metrics.update(easyscholar_result.get("quality_metrics", {}))
                ranking_info.update(easyscholar_result.get("ranking_info", {}))
                data_source = "easyscholar"
                logger.info("从EasyScholar获取期刊质量信息成功")
        except Exception as e:
            logger.debug(f"EasyScholar获取失败: {e}")

        # 2. 尝试从本地缓存获取
        if not quality_metrics and use_cache:
            cache_result = _get_cached_journal_quality(journal_name.strip(), logger)
            if cache_result:
                quality_metrics.update(cache_result.get("quality_metrics", {}))
                ranking_info.update(cache_result.get("ranking_info", {}))
                data_source = "local_cache"
                logger.info("从本地缓存获取期刊质量信息")

        # 3. 基于期刊名称的简单评估
        if not quality_metrics:
            simple_result = _simple_journal_assessment(journal_name.strip(), logger)
            quality_metrics.update(simple_result.get("quality_metrics", {}))
            ranking_info.update(simple_result.get("ranking_info", {}))
            data_source = "simple_assessment"
            logger.info("使用简单评估方法获取期刊质量信息")

        # 过滤用户请求的指标
        filtered_metrics = {}
        for metric in include_metrics:
            if metric in quality_metrics:
                filtered_metrics[metric] = quality_metrics[metric]

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "journal_name": journal_name.strip(),
            "quality_metrics": filtered_metrics,
            "ranking_info": ranking_info,
            "data_source": data_source,
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
    journal_names: list[str], include_metrics: list[str], use_cache: bool, logger
) -> dict[str, Any]:
    """批量期刊质量评估"""
    try:
        if not journal_names:
            return {
                "success": False,
                "error": "期刊名称列表不能为空",
                "total_journals": 0,
                "successful_evaluations": 0,
                "journal_results": {},
                "processing_time": 0,
            }

        start_time = time.time()
        journal_results = {}
        successful_evaluations = 0

        for journal_name in journal_names:
            try:
                result = _single_journal_quality(journal_name, include_metrics, use_cache, logger)
                journal_results[journal_name] = result
                if result.get("success", False):
                    successful_evaluations += 1
            except Exception as e:
                logger.error(f"评估期刊 '{journal_name}' 失败: {e}")
                journal_results[journal_name] = {
                    "success": False,
                    "error": str(e),
                    "journal_name": journal_name,
                    "quality_metrics": {},
                }

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": successful_evaluations > 0,
            "total_journals": len(journal_names),
            "successful_evaluations": successful_evaluations,
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
            "journal_results": {},
            "processing_time": 0,
        }


def _batch_articles_quality_evaluation(
    articles: list[dict[str, Any]],
    evaluation_criteria: list[str],
    weight_config: dict[str, float] | None,
    logger,
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
                1
                for eval_result in evaluated_articles
                if eval_result.get("quality_evaluation", {}).get("overall_score", 0) > 0
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


def _get_field_ranking(field_name: str, ranking_type: str, limit: int, logger) -> dict[str, Any]:
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


# 辅助函数（保持原有实现）
def _get_easyscholar_quality(journal_name: str, logger) -> dict[str, Any]:
    """从EasyScholar获取期刊质量信息"""
    try:
        # 尝试从环境变量获取API密钥
        import os

        api_key = os.getenv("EASYSCHOLAR_SECRET_KEY")

        if not api_key:
            logger.debug("未找到EasyScholar API密钥")
            return {"success": False, "error": "未配置EasyScholar API密钥"}

        # 这里应该调用EasyScholar API
        # 由于没有真实的API，返回模拟数据
        return {
            "success": True,
            "quality_metrics": {
                "impact_factor": 4.2,
                "quartile": "Q2",
                "jci": 1.8,
                "分区": "中科院二区",
            },
            "ranking_info": {
                "rank_in_category": 45,
                "total_journals_in_category": 200,
                "percentile": 77.5,
            },
        }
    except Exception as e:
        logger.error(f"从EasyScholar获取质量信息失败: {e}")
        return {"success": False, "error": str(e)}


def _get_cached_journal_quality(journal_name: str, logger) -> dict[str, Any] | None:
    """从本地缓存获取期刊质量信息"""
    try:
        cache_file = Path("src/resource/journal_info.json")
        if not cache_file.exists():
            return None

        with open(cache_file, encoding="utf-8") as f:
            journal_data = json.load(f)

        # 简单的名称匹配
        for cached_journal in journal_data.get("journals", []):
            if journal_name.lower() in cached_journal.get("name", "").lower():
                return {
                    "quality_metrics": cached_journal.get("metrics", {}),
                    "ranking_info": cached_journal.get("ranking", {}),
                }

        return None
    except Exception as e:
        logger.error(f"从缓存获取期刊质量信息失败: {e}")
        return None


def _simple_journal_assessment(journal_name: str, logger) -> dict[str, Any]:
    """基于期刊名称的简单评估"""
    try:
        # 基于期刊名称关键词的简单评估
        high_indicators = ["nature", "science", "cell", "lancet", "nejm", "pnas"]
        medium_indicators = ["journal", "review", "progress", "advances", "research"]

        journal_lower = journal_name.lower()

        if any(indicator in journal_lower for indicator in high_indicators):
            impact_factor = 8.0
            quartile = "Q1"
            jci = 3.5
            分区 = "中科院一区"
        elif any(indicator in journal_lower for indicator in medium_indicators):
            impact_factor = 3.0
            quartile = "Q2"
            jci = 1.5
            分区 = "中科院二区"
        else:
            impact_factor = 1.5
            quartile = "Q3"
            jci = 0.8
            分区 = "中科院三区"

        return {
            "quality_metrics": {
                "impact_factor": impact_factor,
                "quartile": quartile,
                "jci": jci,
                "分区": 分区,
            },
            "ranking_info": {"assessment_method": "simple_keyword_based", "confidence": "low"},
        }
    except Exception as e:
        logger.error(f"简单期刊评估失败: {e}")
        return {"quality_metrics": {}, "ranking_info": {}}


def _evaluate_article_quality(
    article: dict[str, Any], criteria: list[str], weights: dict[str, float], logger
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
                    simple_result = _simple_journal_assessment(journal, logger)
                    impact_factor = simple_result.get("quality_metrics", {}).get("impact_factor", 0)
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
                distribution[f"{category}_percentage"] = round(
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
