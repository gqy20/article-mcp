"""统一文献详情工具 - 核心工具2

设计原则：
1. 只使用 europe_pmc 单一数据源
2. 返回简单的 article 字典
3. 失败时返回 None
4. 有 PMCID 时自动获取全文
5. 支持按章节提取全文内容
6. 支持批量获取多篇文章
"""

import asyncio
import logging
import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_article_services = None
_logger = None


def register_article_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册文献详情工具"""
    global _article_services, _logger
    _article_services = services
    _logger = logger

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="""获取文献详情工具。通过DOI、PMID、PMCID获取文献的详细信息。

主要参数：
- identifier: 文献标识符（必填）：单个或列表[DOI、PMID、PMCID]
             单个字符串返回单个文献详情，列表返回批量结果
- id_type: 标识符类型（默认auto自动识别）：auto/doi/pmid/pmcid
- include_fulltext: 是否获取全文（默认true，有PMCID时）
- sections: 要提取的全文章节（可选）：["methods", "discussion", "results"等]
            None表示获取全部章节，空列表[]表示不获取全文

数据源：Europe PMC（单一数据源）
返回数据包含标题、作者、摘要、期刊、发表日期、DOI等完整信息
全文功能：如果文献有 PMCID，会自动获取全文（XML/Markdown/Text 格式）
章节提取：可通过 sections 参数只获取特定章节（如方法、讨论部分）
批量模式：传入多个标识符时，返回批量结果结构

批量返回结构：
{
    "total": 10,           # 总请求数
    "successful": 8,       # 成功获取数
    "failed": 2,           # 失败数
    "articles": [...],     # 成功的文章列表
    "fulltext_stats": {    # 全文统计（批量模式）
        "has_pmcid": 5,
        "fulltext_fetched": 3
    }
}

支持的章节名称：
- methods（方法）: methods, methodology, materials and methods
- introduction（引言）: introduction, intro, background
- results（结果）: results, findings
- discussion（讨论）: discussion
- conclusion（结论）: conclusion, conclusions
- abstract（摘要）: abstract, summary
- references（参考文献）: references, bibliography""",
        annotations=ToolAnnotations(title="文献详情", readOnlyHint=True, openWorldHint=False),
        tags={"literature", "details", "metadata"},
    )
    async def get_article_details(
        identifier: str | list[str],
        id_type: str = "auto",
        include_fulltext: bool = True,
        sections: list[str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """获取文献详情工具。通过DOI、PMID、PMCID获取文献的详细信息。

        Args:
            identifier: 文献标识符 (DOI, PMID, PMCID) 或标识符列表
            id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
            include_fulltext: 是否获取全文（有PMCID时）
            sections: 要提取的全文章节列表，None表示全部，[]表示不获取全文

        Returns:
            单个标识符：返回文献详细信息字典或None
            多个标识符：返回批量结果字典 {total, successful, failed, articles, fulltext_stats}

        """
        return await get_article_details_async(
            identifier=identifier,
            id_type=id_type,
            include_fulltext=include_fulltext,
            sections=sections,
        )


async def get_article_details_async(
    identifier: str | list[str],
    id_type: str = "auto",
    include_fulltext: bool = True,
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """异步获取文献详情。

    Args:
        identifier: 文献标识符 (DOI, PMID, PMCID) 或标识符列表
        id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
        include_fulltext: 是否获取全文（有PMCID时）
        sections: 要提取的全文章节列表，None表示全部，[]表示不获取全文

    Returns:
        统一批量结果格式：
        {
            "total": 10,              # 总请求数
            "successful": 8,          # 成功获取数
            "failed": 2,              # 失败数
            "articles": [...],        # 成功的文章列表
            "fulltext_stats": {       # 全文统计（仅当 include_fulltext=True）
                "has_pmcid": 5,
                "fulltext_fetched": 3,
                "no_pmcid": 3
            },
            "processing_time": 1.5    # 处理时间（秒）
        }

    """
    # 统一转换为列表处理
    identifiers = [identifier] if isinstance(identifier, str) else identifier

    # 空列表处理
    if not identifiers:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "articles": [],
            "fulltext_stats": None,
            "processing_time": 0,
        }

    return await _batch_get_article_details(
        identifiers=identifiers,
        id_type=id_type,
        include_fulltext=include_fulltext,
        sections=sections,
    )


async def _fetch_single_article(
    identifier: str,
    id_type: str,
    include_fulltext: bool,
    sections: list[str] | None,
) -> dict[str, Any] | None:
    """获取单个文献详情（内部函数，不对外暴露）"""

    logger = _logger or logging.getLogger(__name__)

    try:
        if not identifier or not identifier.strip():
            return None

        from article_mcp.services.merged_results import extract_identifier_type

        if id_type == "auto":
            id_type = extract_identifier_type(identifier.strip())
        identifier = identifier.strip()

        # 获取服务
        europe_pmc_service = _article_services.get("europe_pmc")  # type: ignore[union-attr]
        pubmed_service = _article_services.get("pubmed")  # type: ignore[union-attr]

        if europe_pmc_service is None:
            logger.error("europe_pmc 服务未配置")
            return None

        # 获取文献详情
        result = europe_pmc_service.fetch(identifier, id_type=id_type)

        if not result or result.get("error") is not None or not result.get("article"):
            error_msg = result.get("error", "未知错误") if result else "服务未响应"
            logger.warning(f"未找到文献: {identifier} - {error_msg}")
            return None

        article = result["article"]

        # 获取全文（如果启用）
        if include_fulltext:
            pmcid = article.get("pmcid")
            if pubmed_service and pmcid:
                try:
                    # 如果 sections 是空列表，跳过全文获取
                    if sections == []:
                        logger.info("sections 为空列表，跳过全文获取")
                    else:
                        fulltext = pubmed_service.get_pmc_fulltext_html(pmcid, sections=sections)
                        if fulltext.get("fulltext_available"):
                            article["fulltext"] = {
                                "pmc_id": fulltext.get("pmc_id"),
                                "fulltext_xml": fulltext.get("fulltext_xml"),
                                "fulltext_markdown": fulltext.get("fulltext_markdown"),
                                "fulltext_text": fulltext.get("fulltext_text"),
                                "fulltext_available": True,
                            }
                            # 添加章节信息（如果有）
                            if "sections_requested" in fulltext:
                                article["fulltext"]["sections_requested"] = fulltext.get(
                                    "sections_requested"
                                )
                                article["fulltext"]["sections_found"] = fulltext.get(
                                    "sections_found"
                                )
                                article["fulltext"]["sections_missing"] = fulltext.get(
                                    "sections_missing"
                                )
                except Exception as e:
                    logger.warning(f"获取全文失败: {e}")

        logger.info(f"成功获取文献详情: {identifier}")
        return article

    except Exception as e:
        logger.error(f"获取文献详情异常: {e}")
        return None


async def _batch_get_article_details(
    identifiers: list[str],
    id_type: str = "auto",
    include_fulltext: bool = True,
    sections: list[str] | None = None,
    max_concurrent: int = 5,
) -> dict[str, Any]:
    """批量获取文献详情（内部函数）"""

    logger = _logger or logging.getLogger(__name__)
    start_time = time.time()

    # 控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(identifier: str) -> tuple[str, dict | None]:
        """带并发控制的获取"""
        async with semaphore:
            # 添加延迟避免过载
            await asyncio.sleep(0.3)
            result = await _fetch_single_article(
                identifier=identifier,
                id_type=id_type,
                include_fulltext=include_fulltext,
                sections=sections,
            )
            return identifier, result

    # 并发获取所有文章
    tasks = [fetch_with_semaphore(ident) for ident in identifiers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    successful_articles = []
    failed_count = 0
    has_pmcid_count = 0
    fulltext_fetched_count = 0

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"获取文献时发生异常: {result}")
            failed_count += 1
            continue

        identifier, article = result
        if article:
            successful_articles.append(article)
            # 统计全文信息
            if include_fulltext:
                pmcid = article.get("pmcid")
                if pmcid:
                    has_pmcid_count += 1
                    if article.get("fulltext") and article["fulltext"].get("fulltext_available"):
                        fulltext_fetched_count += 1
        else:
            failed_count += 1

    processing_time = round(time.time() - start_time, 2)

    # 构建全文统计
    fulltext_stats = None
    if include_fulltext:
        fulltext_stats = {
            "has_pmcid": has_pmcid_count,
            "fulltext_fetched": fulltext_fetched_count,
            "no_pmcid": len(successful_articles) - has_pmcid_count,
        }

    return {
        "total": len(identifiers),
        "successful": len(successful_articles),
        "failed": failed_count,
        "articles": successful_articles,
        "fulltext_stats": fulltext_stats,
        "processing_time": processing_time,
    }
