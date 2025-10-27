"""
统一搜索工具 - 核心工具1
"""

import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_search_services = None


def register_search_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册搜索工具"""
    global _search_services
    _search_services = services

    @mcp.tool()
    def search_literature(
        keyword: str,
        sources: list[str] | None = None,
        max_results: int = 10,
        search_type: str = "comprehensive",
    ) -> dict[str, Any]:
        """多源文献搜索工具

        搜索多个学术数据库的文献，支持关键词检索和结果合并。

        Args:
            keyword: 搜索关键词
            sources: 数据源列表，可选 ["europe_pmc", "pubmed", "arxiv", "crossref", "openalex"]
            max_results: 最大结果数 (建议10-50)
            search_type: 搜索策略 ["comprehensive", "recent", "high_quality"]

        Returns:
            包含搜索结果的字典，包括成功状态、文章列表和统计信息
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

            from ..services.merged_results import merge_articles_by_doi
            from ..services.merged_results import simple_rank_articles

            start_time = time.time()
            results_by_source = {}
            sources_used = []

            # 处理None值的sources参数
            if sources is None:
                sources = ["europe_pmc", "pubmed"]

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
