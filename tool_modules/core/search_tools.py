"""
统一搜索工具 - 核心工具1
"""

import time
from typing import Any

# 全局服务实例
_search_services = None


def register_search_tools(mcp, services, logger):
    """注册搜索工具"""
    global _search_services
    _search_services = services

    @mcp.tool()
    def search_literature(
        keyword: str,
        sources: list[str] = ["europe_pmc", "pubmed"],
        max_results: int = 10,
        search_type: str = "comprehensive",
    ) -> dict[str, Any]:
        """多源文献搜索工具

        🎯 功能说明：
        - 从5个主要学术数据库搜索文献
        - 自动去重和智能排序
        - 透明显示每个数据源的搜索结果

        📋 使用示例：
        1. search_literature("CRISPR gene editing")
        2. search_literature("machine learning", sources=["pubmed", "arxiv"], max_results=20)
        3. search_literature("COVID-19 vaccine", search_type="recent")

        🚀 高级检索示例：
        1. search_literature("cancer[Title] AND immunotherapy[Abstract]")
        2. search_literature("author:smith AND journal:nature AND 2023:2024")
        3. search_literature('"machine learning"[Title/Abstract] NOT review[Publication Type]')
        4. search_literature("CRISPR[Title] AND (gene editing OR genome editing) AND 2020[Publication Date]")

        🔧 参数说明：
        - keyword: 搜索关键词，支持各API原生高级检索语法
        - sources: 数据源列表，可选 ["europe_pmc", "pubmed", "arxiv", "crossref", "openalex"]
        - max_results: 每个数据源最大返回结果数 (建议10-50)
        - search_type: 搜索策略 ["comprehensive"(默认), "recent", "high_quality"]

        🔍 支持的高级检索语法：
        • Europe PMC: title:cancer, abstract:immunotherapy, author:smith
        • PubMed: cancer[Title], immunotherapy[Abstract], smith[Author]
        • 布尔运算：AND, OR, NOT (所有API支持)
        • 时间范围：2020:2024[Publication Date] (PubMed), 2020-2024 (Europe PMC)
        • 精确匹配："machine learning" (所有API支持)
        • 括号分组：(gene editing OR genome editing) AND CRISPR (所有API支持)

        ✅ 推荐用法：
        - 新手：使用默认参数，搜索关键词即可
        - 专业人士：直接使用API原生语法进行精确检索
        - 大规模搜索：使用批量工具 batch_search_literature

        📊 返回格式：
        {
            "success": true,
            "keyword": "搜索的关键词",
            "sources_used": ["实际搜索的数据源"],
            "results_by_source": {
                "数据源名称": [搜索结果列表]
            },
            "merged_results": [去重后的结果列表],
            "total_count": 总结果数量,
            "search_time": 搜索耗时(秒)
        }
        """
        try:
            if not keyword or not keyword.strip():
                return {
                    "success": False,
                    "error": "搜索关键词不能为空",
                    "keyword": keyword,
                    "sources_used": [],
                    "results_by_source": {},
                    "merged_results": [],
                    "total_count": 0,
                }

            from src.merged_results import merge_articles_by_doi, simple_rank_articles

            start_time = time.time()
            results_by_source = {}
            sources_used = []

            # 搜索每个指定的数据源
            for source in sources:
                if source not in _search_services:
                    logger.warning(f"未知数据源: {source}")
                    continue

                try:
                    service = _search_services[source]

                    # 直接使用原始查询 - 各API原生支持高级语法
                    query = keyword

                    if source == "europe_pmc":
                        result = service.search(query, max_results=max_results)
                    elif source == "pubmed":
                        result = service.search(query, max_results=max_results)
                    elif source == "arxiv":
                        result = service.search(query, max_results=max_results)
                    elif source == "crossref":
                        result = service.search_works(query, max_results=max_results)
                    elif source == "openalex":
                        result = service.search_works(query, max_results=max_results)
                    else:
                        continue

                    if result.get("success", False):
                        results_by_source[source] = result.get("articles", [])
                        sources_used.append(source)
                        logger.info(
                            f"{source} 搜索成功，找到 {len(results_by_source[source])} 篇文章"
                        )
                    else:
                        logger.warning(f"{source} 搜索失败: {result.get('error', '未知错误')}")

                except Exception as e:
                    logger.error(f"{source} 搜索异常: {e}")
                    continue

            # 合并结果
            merged_results = merge_articles_by_doi(results_by_source)
            merged_results = simple_rank_articles(merged_results)

            search_time = round(time.time() - start_time, 2)

            return {
                "success": True,
                "keyword": keyword.strip(),
                "sources_used": sources_used,
                "results_by_source": results_by_source,
                "merged_results": merged_results[: max_results * len(sources)],
                "total_count": sum(len(results) for results in results_by_source.values()),
                "search_time": search_time,
                "search_type": search_type,
            }

        except Exception as e:
            logger.error(f"搜索过程中发生异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "keyword": keyword,
                "sources_used": [],
                "results_by_source": {},
                "merged_results": [],
                "total_count": 0,
                "search_time": 0,
            }

    return [search_literature]
