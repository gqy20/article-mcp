"""
统一搜索工具 - 核心工具1
"""

import asyncio
import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_search_services = None


def register_search_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册搜索工具"""
    global _search_services
    _search_services = services

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="多源文献搜索工具。搜索学术数据库文献，支持关键词检索和结果合并。",
        annotations=ToolAnnotations(
            title="文献搜索",
            readOnlyHint=True,
            openWorldHint=False
        ),
        tags={"search", "literature", "academic"}
    )
    def search_literature(
        keyword: str,
        sources: list[str] | None = None,
        max_results: int = 10,
        search_type: str = "comprehensive",
    ) -> dict[str, Any]:
        """多源文献搜索工具。搜索学术数据库文献，支持关键词检索和结果合并。

        Args:
            keyword: 搜索关键词
            sources: 数据源列表
            max_results: 最大结果数
            search_type: 搜索策略

        Returns:
            搜索结果字典，包含文章列表和统计信息
        """
        try:
            if not keyword or not keyword.strip():
                from fastmcp.exceptions import ToolError
                raise ToolError("搜索关键词不能为空")

            from article_mcp.services.merged_results import merge_articles_by_doi
            from article_mcp.services.merged_results import simple_rank_articles

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

                    # 判断搜索成功：没有错误且有文章结果
                    error = result.get("error")
                    articles = result.get("articles", [])
                    if not error and articles:
                        results_by_source[source] = articles
                        sources_used.append(source)
                        logger.info(
                            f"{source} 搜索成功，找到 {len(articles)} 篇文章"
                        )
                    else:
                        logger.warning(f"{source} 搜索失败: {error or '无搜索结果'}")

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
            # 抛出MCP标准错误
            from mcp import McpError
            from mcp.types import ErrorData
            raise McpError(ErrorData(
                code=-32603,
                message=f"搜索失败: {type(e).__name__}: {str(e)}"
            ))


async def search_literature_async(
    keyword: str,
    sources: list[str] | None = None,
    max_results: int = 10,
    search_type: str = "comprehensive",
    use_cache: bool = True,
    cache: Any = None,
    services: dict[str, Any] | None = None,
    logger: Any = None,
) -> dict[str, Any]:
    """异步多源文献搜索工具。并行搜索多个学术数据库，显著提升搜索速度。

    与同步版本的区别：
    - 使用 asyncio.gather() 并行搜索多个数据源
    - 调用各服务的 search_async() 或 search_works_async() 方法
    - 搜索时间大幅减少（接近最慢单个数据源的耗时，而非累加）

    Args:
        keyword: 搜索关键词
        sources: 数据源列表 (默认: ["europe_pmc", "pubmed"])
        max_results: 每个数据源的最大结果数
        search_type: 搜索策略 (fast, comprehensive, precise, preprint)
        use_cache: 是否使用缓存
        cache: 缓存实例（可选）
        services: 服务实例字典（用于测试，默认使用全局 _search_services）
        logger: 日志记录器（用于测试）

    Returns:
        搜索结果字典，包含文章列表和统计信息
    """
    try:
        if not keyword or not keyword.strip():
            from fastmcp.exceptions import ToolError
            raise ToolError("搜索关键词不能为空")

        # 使用提供的服务或全局服务
        search_services = services if services is not None else _search_services
        if logger is None:
            import logging
            logger = logging.getLogger(__name__)

        from article_mcp.services.merged_results import merge_articles_by_doi
        from article_mcp.services.merged_results import simple_rank_articles

        start_time = time.time()
        results_by_source = {}
        sources_used = []

        # 处理None值的sources参数 - 根据搜索策略选择默认数据源
        if sources is None:
            if search_type == "fast":
                sources = ["europe_pmc", "pubmed"]
            elif search_type == "preprint":
                sources = ["arxiv", "europe_pmc"]
            elif search_type == "precise":
                sources = ["pubmed", "crossref"]
            else:  # comprehensive
                sources = ["europe_pmc", "pubmed", "arxiv"]

        # 定义每个数据源的异步搜索函数
        async def search_source(source: str) -> tuple[str, dict | None]:
            """搜索单个数据源，返回 (source_name, articles)"""
            if source not in search_services:
                logger.warning(f"未知数据源: {source}")
                return (source, None)

            try:
                service = search_services[source]
                query = keyword

                # 调用对应的异步搜索方法
                if source == "europe_pmc":
                    result = await service.search_async(query, max_results=max_results)
                elif source == "pubmed":
                    result = await service.search_async(query, max_results=max_results)
                elif source == "arxiv":
                    result = await service.search_async(query, max_results=max_results)
                elif source == "crossref":
                    result = await service.search_works_async(query, max_results=max_results)
                elif source == "openalex":
                    result = await service.search_works_async(query, max_results=max_results)
                else:
                    return (source, None)

                # 判断搜索成功：没有错误且有文章结果
                error = result.get("error") if result else None
                articles = result.get("articles", []) if result else []
                if not error and articles:
                    logger.info(f"{source} 异步搜索成功，找到 {len(articles)} 篇文章")
                    return (source, articles)
                else:
                    logger.warning(f"{source} 搜索失败: {error or '无搜索结果'}")
                    return (source, None)

            except Exception as e:
                logger.error(f"{source} 搜索异常: {e}")
                return (source, None)

        # 并行搜索所有数据源
        search_tasks = [search_source(source) for source in sources]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 处理搜索结果
        for result in search_results:
            if isinstance(result, Exception):
                logger.error(f"搜索任务异常: {result}")
                continue

            source, articles = result
            if articles is not None:
                results_by_source[source] = articles
                sources_used.append(source)

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
            "cached": False,  # TODO: 实现缓存支持
        }

    except Exception as e:
        if logger:
            logger.error(f"异步搜索过程中发生异常: {e}")
        # 抛出MCP标准错误
        from mcp import McpError
        from mcp.types import ErrorData
        raise McpError(ErrorData(
            code=-32603,
            message=f"异步搜索失败: {type(e).__name__}: {str(e)}"
        ))

