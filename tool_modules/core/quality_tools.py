"""
期刊质量评估工具 - 核心工具5
"""
from typing import Dict, Any, List, Optional
import logging
import time
import json
from pathlib import Path

# 全局服务实例
_quality_services = None

def register_quality_tools(mcp, services, logger):
    """注册期刊质量评估工具"""
    global _quality_services
    _quality_services = services

    @mcp.tool()
    def get_journal_quality(
        journal_name: str,
        include_metrics: List[str] = ["impact_factor", "quartile", "jci"],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取期刊质量指标工具

        功能说明：
        - 获取期刊的质量指标和排名信息
        - 支持多种评估指标
        - 集成EasyScholar等质量评估服务

        参数说明：
        - journal_name: 期刊名称
        - include_metrics: 包含的指标类型
        - use_cache: 是否使用缓存

        返回格式：
        {
            "success": true,
            "journal_name": "Nature",
            "quality_metrics": {
                "impact_factor": 69.504,
                "quartile": "Q1",
                "jci": 25.8,
                "分区": "中科院一区"
            },
            "ranking_info": {...},
            "data_source": "easyscholar"
        }
        """
        try:
            if not journal_name or not journal_name.strip():
                return {
                    "success": False,
                    "error": "期刊名称不能为空",
                    "journal_name": journal_name,
                    "quality_metrics": {},
                    "ranking_info": {},
                    "data_source": None
                }

            start_time = time.time()

            # 尝试从多个数据源获取质量指标
            quality_metrics = {}
            ranking_info = {}
            data_source = None

            # 1. 尝试从EasyScholar获取
            try:
                easyscholar_result = _get_easyscholar_quality(
                    journal_name.strip(), logger
                )
                if easyscholar_result.get("success", False):
                    quality_metrics.update(easyscholar_result.get("quality_metrics", {}))
                    ranking_info.update(easyscholar_result.get("ranking_info", {}))
                    data_source = "easyscholar"
                    logger.info(f"从EasyScholar获取期刊质量信息成功")
            except Exception as e:
                logger.debug(f"EasyScholar获取失败: {e}")

            # 2. 尝试从本地缓存获取
            if not quality_metrics and use_cache:
                cache_result = _get_cached_journal_quality(journal_name.strip(), logger)
                if cache_result:
                    quality_metrics.update(cache_result.get("quality_metrics", {}))
                    ranking_info.update(cache_result.get("ranking_info", {}))
                    data_source = "local_cache"
                    logger.info(f"从本地缓存获取期刊质量信息")

            # 3. 基于期刊名称的简单评估
            if not quality_metrics:
                simple_result = _simple_journal_assessment(journal_name.strip(), logger)
                quality_metrics.update(simple_result.get("quality_metrics", {}))
                ranking_info.update(simple_result.get("ranking_info", {}))
                data_source = "simple_assessment"
                logger.info(f"使用简单评估方法获取期刊质量信息")

            # 过滤用户请求的指标
            filtered_metrics = {}
            for metric in include_metrics:
                if metric in quality_metrics:
                    filtered_metrics[metric] = quality_metrics[metric]

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": len(quality_metrics) > 0,
                "journal_name": journal_name.strip(),
                "quality_metrics": filtered_metrics,
                "all_metrics": quality_metrics,
                "ranking_info": ranking_info,
                "data_source": data_source,
                "processing_time": processing_time,
                "available_metrics": list(quality_metrics.keys())
            }

        except Exception as e:
            logger.error(f"获取期刊质量异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": None,
                "processing_time": 0
            }

    @mcp.tool()
    def evaluate_articles_quality(
        articles: List[Dict[str, Any]],
        evaluation_criteria: List[str] = ["journal_quality", "citation_count", "open_access"],
        weight_config: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """批量评估文献质量工具

        功能说明：
        - 批量评估多篇文献的质量
        - 支持多种评估标准和权重配置
        - 生成质量评分和排名

        参数说明：
        - articles: 文献列表，每篇文献包含标题、期刊、作者等信息
        - evaluation_criteria: 评估标准列表
        - weight_config: 各标准的权重配置

        返回格式：
        {
            "success": true,
            "evaluated_articles": [...],
            "quality_distribution": {...},
            "ranking": [...],
            "evaluation_summary": {...}
        }
        """
        try:
            if not articles:
                return {
                    "success": False,
                    "error": "文献列表不能为空",
                    "evaluated_articles": [],
                    "quality_distribution": {},
                    "ranking": [],
                    "evaluation_summary": {}
                }

            start_time = time.time()

            # 默认权重配置
            default_weights = {
                "journal_quality": 0.4,
                "citation_count": 0.3,
                "open_access": 0.1,
                "author_reputation": 0.1,
                "publication_recency": 0.1
            }

            weights = weight_config or default_weights

            evaluated_articles = []
            quality_scores = []

            for article in articles:
                try:
                    # 评估单篇文献
                    article_evaluation = _evaluate_single_article(
                        article, evaluation_criteria, weights, logger
                    )

                    evaluated_articles.append({
                        **article,
                        "quality_evaluation": article_evaluation
                    })

                    quality_scores.append(article_evaluation.get("overall_score", 0))

                except Exception as e:
                    logger.error(f"评估文献异常: {e}")
                    evaluated_articles.append({
                        **article,
                        "quality_evaluation": {
                            "overall_score": 0,
                            "error": str(e),
                            "evaluated_criteria": []
                        }
                    })

            # 计算质量分布
            quality_distribution = _calculate_quality_distribution(quality_scores)

            # 生成排名
            ranking = sorted(
                [(i, score) for i, score in enumerate(quality_scores)],
                key=lambda x: x[1],
                reverse=True
            )

            # 统计信息
            evaluation_summary = {
                "total_articles": len(articles),
                "successful_evaluations": sum(1 for eval_result in evaluated_articles
                                            if eval_result.get("quality_evaluation", {}).get("overall_score", 0) > 0),
                "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "highest_score": max(quality_scores) if quality_scores else 0,
                "lowest_score": min(quality_scores) if quality_scores else 0,
                "evaluation_criteria_used": evaluation_criteria,
                "weights_applied": weights
            }

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": True,
                "evaluated_articles": evaluated_articles,
                "quality_distribution": quality_distribution,
                "ranking": [{"article_index": idx, "rank": i+1, "score": score}
                           for i, (idx, score) in enumerate(ranking)],
                "evaluation_summary": evaluation_summary,
                "processing_time": processing_time
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
                "processing_time": 0
            }

    @mcp.tool()
    def get_field_ranking(
        field_name: str,
        ranking_type: str = "journal_impact",
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取学科领域期刊排名工具

        功能说明：
        - 获取特定学科领域的期刊排名
        - 支持多种排名类型
        - 提供学科领域内的相对位置

        参数说明：
        - field_name: 学科领域名称
        - ranking_type: 排名类型 ["journal_impact", "jci", "citation_score"]
        - limit: 返回结果数量限制

        返回格式：
        {
            "success": true,
            "field_name": "Biology",
            "ranking_type": "journal_impact",
            "top_journals": [...],
            "field_statistics": {...}
        }
        """
        try:
            if not field_name or not field_name.strip():
                return {
                    "success": False,
                    "error": "学科领域名称不能为空",
                    "field_name": field_name,
                    "ranking_type": ranking_type,
                    "top_journals": [],
                    "field_statistics": {}
                }

            start_time = time.time()

            # 预定义的学科领域期刊排名（示例数据）
            field_rankings = _get_predefined_field_rankings()

            field_key = field_name.strip().lower()
            ranking_data = field_rankings.get(field_key, {})

            if not ranking_data:
                # 如果没有预定义数据，返回通用排名
                ranking_data = field_rankings.get("general", {})

            top_journals = ranking_data.get(ranking_type, [])[:limit]

            field_statistics = ranking_data.get("statistics", {
                "total_journals": len(top_journals),
                "average_impact_factor": sum(j.get("impact_factor", 0) for j in top_journals) / len(top_journals) if top_journals else 0,
                "highest_impact": top_journals[0].get("impact_factor", 0) if top_journals else 0,
                "lowest_impact": top_journals[-1].get("impact_factor", 0) if top_journals else 0
            })

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": True,
                "field_name": field_name.strip(),
                "ranking_type": ranking_type,
                "top_journals": top_journals,
                "field_statistics": field_statistics,
                "data_source": "predefined",
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"获取学科领域排名异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "field_name": field_name,
                "ranking_type": ranking_type,
                "top_journals": [],
                "field_statistics": {},
                "processing_time": 0
            }

    return [get_journal_quality, evaluate_articles_quality, get_field_ranking]


def _get_easyscholar_quality(journal_name: str, logger) -> Dict[str, Any]:
    """从EasyScholar获取期刊质量信息"""
    try:
        from src.mcp_config import get_easyscholar_key

        # 尝试获取EasyScholar密钥
        secret_key = get_easyscholar_key(None, logger)
        if not secret_key:
            logger.debug("未找到EasyScholar密钥")
            return {"success": False, "error": "未配置EasyScholar密钥"}

        # 使用Pubmed服务获取期刊质量
        if _quality_services and "pubmed" in _quality_services:
            service = _quality_services["pubmed"]
            result = service.get_journal_quality(journal_name, secret_key)
            return result

        return {"success": False, "error": "Pubmed服务未初始化"}

    except Exception as e:
        logger.error(f"从EasyScholar获取质量信息异常: {e}")
        return {"success": False, "error": str(e)}


def _get_cached_journal_quality(journal_name: str, logger) -> Optional[Dict[str, Any]]:
    """从本地缓存获取期刊质量信息"""
    try:
        cache_file = Path(__file__).parent.parent.parent / "data" / "journal_quality_cache.json"

        if not cache_file.exists():
            return None

        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        return cache_data.get(journal_name.lower())

    except Exception as e:
        logger.debug(f"读取缓存失败: {e}")
        return None


def _simple_journal_assessment(journal_name: str, logger) -> Dict[str, Any]:
    """基于期刊名称的简单质量评估"""
    try:
        # 基于期刊名称模式的简单评估
        journal_lower = journal_name.lower()

        # 高质量期刊关键词
        high_quality_indicators = [
            "nature", "science", "cell", " lancet", "nejm", "pnas",
            "nature communications", "nature genetics", "nature medicine",
            "science advances", "science translational medicine"
        ]

        # 中等质量期刊关键词
        medium_quality_indicators = [
            "journal", "review", "research", "studies", "international",
            "applied", "clinical", "experimental", "molecular", "biochemical"
        ]

        quality_metrics = {}
        ranking_info = {}

        if any(indicator in journal_lower for indicator in high_quality_indicators):
            quality_metrics = {
                "impact_factor_estimate": 10.0,
                "quartile_estimate": "Q1",
                "quality_tier": "High"
            }
            ranking_info = {
                "estimated_rank": "Top 5%",
                "confidence": "Medium"
            }
        elif any(indicator in journal_lower for indicator in medium_quality_indicators):
            quality_metrics = {
                "impact_factor_estimate": 3.0,
                "quartile_estimate": "Q2",
                "quality_tier": "Medium"
            }
            ranking_info = {
                "estimated_rank": "Top 25%",
                "confidence": "Low"
            }
        else:
            quality_metrics = {
                "impact_factor_estimate": 1.0,
                "quartile_estimate": "Q3-Q4",
                "quality_tier": "Unknown"
            }
            ranking_info = {
                "estimated_rank": "Unknown",
                "confidence": "Very Low"
            }

        return {
            "quality_metrics": quality_metrics,
            "ranking_info": ranking_info
        }

    except Exception as e:
        logger.error(f"简单评估异常: {e}")
        return {"quality_metrics": {}, "ranking_info": {}}


def _evaluate_single_article(
    article: Dict[str, Any],
    criteria: List[str],
    weights: Dict[str, float],
    logger
) -> Dict[str, Any]:
    """评估单篇文献质量"""
    try:
        evaluation = {
            "overall_score": 0,
            "criteria_scores": {},
            "evaluated_criteria": []
        }

        total_score = 0
        total_weight = 0

        for criterion in criteria:
            if criterion not in weights:
                continue

            try:
                score = _evaluate_criterion(article, criterion, logger)
                weight = weights[criterion]

                evaluation["criteria_scores"][criterion] = {
                    "score": score,
                    "weight": weight,
                    "weighted_score": score * weight
                }

                total_score += score * weight
                total_weight += weight
                evaluation["evaluated_criteria"].append(criterion)

            except Exception as e:
                logger.error(f"评估标准 {criterion} 异常: {e}")
                continue

        if total_weight > 0:
            evaluation["overall_score"] = total_score / total_weight

        return evaluation

    except Exception as e:
        logger.error(f"评估单篇文献异常: {e}")
        return {"overall_score": 0, "criteria_scores": {}, "evaluated_criteria": []}


def _evaluate_criterion(article: Dict[str, Any], criterion: str, logger) -> float:
    """评估单个标准"""
    try:
        if criterion == "journal_quality":
            journal = article.get("journal", "")
            if not journal:
                return 0.5  # 默认分数

            # 基于期刊名称的简单评分
            journal_lower = journal.lower()
            if "nature" in journal_lower or "science" in journal_lower or "cell" in journal_lower:
                return 1.0
            elif "journal" in journal_lower and "international" in journal_lower:
                return 0.7
            else:
                return 0.5

        elif criterion == "citation_count":
            # 基于引用数的评分（如果有的话）
            citations = article.get("citation_count", 0)
            if citations >= 100:
                return 1.0
            elif citations >= 50:
                return 0.8
            elif citations >= 10:
                return 0.6
            else:
                return 0.3

        elif criterion == "open_access":
            # 开放获取评分
            open_access = article.get("open_access", {})
            if isinstance(open_access, dict):
                is_oa = open_access.get("is_oa", False)
            else:
                is_oa = bool(open_access)

            return 1.0 if is_oa else 0.3

        elif criterion == "author_reputation":
            # 作者声誉评分（基于作者数量等简单指标）
            authors = article.get("authors", [])
            author_count = len(authors)

            if author_count <= 5:
                return 0.8  # 适中的作者数量可能表明较好的合作
            elif author_count <= 10:
                return 0.6
            else:
                return 0.4

        elif criterion == "publication_recency":
            # 发表新近度评分
            pub_date = article.get("publication_date", "")
            if pub_date:
                # 简单的年份评分逻辑
                try:
                    year = int(pub_date.split("-")[0])
                    current_year = 2024  # 假设当前年份
                    years_diff = current_year - year

                    if years_diff <= 1:
                        return 1.0
                    elif years_diff <= 3:
                        return 0.8
                    elif years_diff <= 5:
                        return 0.6
                    elif years_diff <= 10:
                        return 0.4
                    else:
                        return 0.2
                except:
                    return 0.5
            else:
                return 0.5

        else:
            return 0.5  # 默认分数

    except Exception as e:
        logger.error(f"评估标准 {criterion} 异常: {e}")
        return 0.0


def _calculate_quality_distribution(scores: List[float]) -> Dict[str, Any]:
    """计算质量分布统计"""
    try:
        if not scores:
            return {}

        scores.sort()
        n = len(scores)

        distribution = {
            "count": n,
            "mean": sum(scores) / n,
            "median": scores[n // 2] if n % 2 == 1 else (scores[n // 2 - 1] + scores[n // 2]) / 2,
            "min": scores[0],
            "max": scores[-1],
            "quartiles": {
                "q1": scores[n // 4],
                "q2": scores[n // 2],
                "q3": scores[3 * n // 4]
            }
        }

        # 质量等级分布
        grade_distribution = {
            "excellent": sum(1 for s in scores if s >= 0.8),
            "good": sum(1 for s in scores if 0.6 <= s < 0.8),
            "average": sum(1 for s in scores if 0.4 <= s < 0.6),
            "poor": sum(1 for s in scores if s < 0.4)
        }

        distribution["grade_distribution"] = grade_distribution

        return distribution

    except Exception as e:
        logger.error(f"计算质量分布异常: {e}")
        return {}


def _get_predefined_field_rankings() -> Dict[str, Any]:
    """获取预定义的学科领域排名数据"""
    return {
        "biology": {
            "journal_impact": [
                {"name": "Nature", "impact_factor": 69.504, "rank": 1},
                {"name": "Science", "impact_factor": 63.714, "rank": 2},
                {"name": "Cell", "impact_factor": 66.850, "rank": 3},
                {"name": "Nature Medicine", "impact_factor": 82.9, "rank": 4},
                {"name": "Nature Genetics", "impact_factor": 38.33, "rank": 5}
            ],
            "statistics": {
                "total_journals": 100,
                "average_impact_factor": 4.2
            }
        },
        "medicine": {
            "journal_impact": [
                {"name": "The Lancet", "impact_factor": 202.731, "rank": 1},
                {"name": "New England Journal of Medicine", "impact_factor": 158.5, "rank": 2},
                {"name": "Nature Medicine", "impact_factor": 82.9, "rank": 3},
                {"name": "BMJ", "impact_factor": 105.7, "rank": 4},
                {"name": "JAMA", "impact_factor": 120.7, "rank": 5}
            ],
            "statistics": {
                "total_journals": 150,
                "average_impact_factor": 6.8
            }
        },
        "general": {
            "journal_impact": [
                {"name": "Nature", "impact_factor": 69.504, "rank": 1},
                {"name": "Science", "impact_factor": 63.714, "rank": 2},
                {"name": "Cell", "impact_factor": 66.850, "rank": 3}
            ],
            "statistics": {
                "total_journals": 50,
                "average_impact_factor": 3.5
            }
        }
    }