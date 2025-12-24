"""
统一文献详情工具 - 核心工具2
"""

import asyncio
import logging
import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_article_services = None
_logger = None  # 全局 logger


def register_article_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册文献详情工具"""
    global _article_services, _logger
    _article_services = services
    _logger = logger

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="获取文献详情工具。通过DOI、PMID等标识符获取文献的详细信息。",
        annotations=ToolAnnotations(
            title="文献详情",
            readOnlyHint=True,
            openWorldHint=False
        ),
        tags={"literature", "details", "metadata"}
    )
    async def get_article_details(
        identifier: str,
        id_type: str = "auto",
        sources: list[str] | None = None,
        include_quality_metrics: bool = False,
    ) -> dict[str, Any]:
        """获取文献详情工具。通过DOI、PMID等标识符获取文献的详细信息。

        Args:
            identifier: 文献标识符 (DOI, PMID, PMCID, arXiv ID)
            id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid", "arxiv_id"]
            sources: 数据源列表，优先级顺序查询
            include_quality_metrics: 是否包含期刊质量指标

        Returns:
            包含文献详细信息的字典，包括标题、作者、摘要、期刊等
        """
        return await get_article_details_async(
            identifier=identifier,
            id_type=id_type,
            sources=sources,
            include_quality_metrics=include_quality_metrics,
        )


async def get_article_details_async(
    identifier: str,
    id_type: str = "auto",
    sources: list[str] | None = None,
    include_quality_metrics: bool = False,
) -> dict[str, Any]:
    """异步获取文献详情。通过DOI、PMID等标识符获取文献的详细信息。

    Args:
        identifier: 文献标识符 (DOI, PMID, PMCID, arXiv ID)
        id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid", "arxiv_id"]
        sources: 数据源列表，支持并行查询
        include_quality_metrics: 是否包含期刊质量指标

    Returns:
        包含文献详细信息的字典，包括标题、作者、摘要、期刊等
    """
    # 使用全局 logger 或创建默认 logger
    logger = _logger or logging.getLogger(__name__)

    try:
        if not identifier or not identifier.strip():
            return {
                "success": False,
                "error": "文献标识符不能为空",
                "identifier": identifier,
                "id_type": id_type,
                "sources_found": [],
                "details_by_source": {},
                "merged_detail": None,
                "total_count": 0,
                "processing_time": 0,
            }

        from article_mcp.services.merged_results import extract_identifier_type
        from article_mcp.services.merged_results import merge_same_doi_articles

        start_time = time.time()
        details_by_source = {}
        sources_found = []

        # 处理None值的sources参数
        if sources is None:
            sources = ["europe_pmc", "crossref"]

        # 自动识别标识符类型
        if id_type == "auto":
            id_type = extract_identifier_type(identifier.strip())

        identifier = identifier.strip()

        # 并行从多个数据源获取详情
        async def fetch_from_source(source: str) -> tuple[str, dict | None]:
            """从单个数据源异步获取文献详情"""
            try:
                if source not in _article_services:
                    return source, None

                service = _article_services[source]

                if source == "europe_pmc":
                    # Europe PMC - 使用 fetch 方法
                    result = service.fetch(identifier, id_type=id_type)
                    article = result.get("article") if result else None
                    if article:
                        return source, article
                elif source == "crossref":
                    if id_type == "doi":
                        result = service.get_work_by_doi(identifier)
                        article = result.get("article") if result else None
                        if article:
                            return source, article
                elif source == "openalex":
                    if id_type == "doi":
                        result = service.get_work_by_doi(identifier)
                        article = result.get("article") if result else None
                        if article:
                            return source, article
                elif source == "arxiv":
                    if id_type == "arxiv_id":
                        result = service.fetch(identifier, id_type=id_type)
                        article = result.get("article") if result else None
                        if article:
                            return source, article

                return source, None

            except Exception as e:
                logger.error(f"{source} 获取详情异常: {e}")
                return source, None

        # 并行执行所有数据源的查询
        fetch_tasks = [fetch_from_source(source) for source in sources]
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # 处理结果
        for result in fetch_results:
            if isinstance(result, Exception):
                logger.error(f"获取文献详情时发生异常: {result}")
                continue

            source, article = result
            if article:
                details_by_source[source] = article
                sources_found.append(source)
                logger.info(f"{source} 获取详情成功")

        # 合并详情
        merged_detail = None
        if details_by_source:
            articles = [details_by_source[source] for source in sources_found]
            merged_detail = merge_same_doi_articles(articles)

        # 获取质量指标（保持同步，因为这不是性能瓶颈）
        quality_metrics = None
        if include_quality_metrics and merged_detail:
            journal_name = merged_detail.get("journal", "")
            if journal_name:
                try:
                    from article_mcp.services.mcp_config import get_easyscholar_key

                    secret_key = get_easyscholar_key(None, logger)
                    pubmed_service = _article_services.get("pubmed")
                    if pubmed_service:
                        quality_metrics = pubmed_service.get_journal_quality(
                            journal_name, secret_key
                        )
                except Exception as e:
                    logger.warning(f"获取期刊质量指标失败: {e}")

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": len(details_by_source) > 0,
            "identifier": identifier,
            "id_type": id_type,
            "sources_found": sources_found,
            "details_by_source": details_by_source,
            "merged_detail": merged_detail,
            "quality_metrics": quality_metrics,
            "total_count": len(details_by_source),
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"获取文献详情异常: {e}")
        # 抛出MCP标准错误
        from mcp import McpError
        from mcp.types import ErrorData
        raise McpError(ErrorData(
            code=-32603,
            message=f"获取文献详情失败: {type(e).__name__}: {str(e)}"
        ))
