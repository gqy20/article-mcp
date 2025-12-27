"""文献全文获取工具 - 核心工具2

简化设计原则：
1. 专门用于获取全文，只接受 PMCID 作为输入
2. 移除 id_type 参数（不再支持 DOI/PMID）
3. 移除 sections=[]（不获取全文）的选项
4. sections=None 表示获取全部章节（默认）
5. sections=["xxx"] 表示获取指定章节
6. 支持批量获取（最多20个 PMCID）

服务依赖：使用闭包捕获模式，无全局变量
"""

import asyncio
import time
from typing import Any

from fastmcp import FastMCP


def register_article_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册文献全文获取工具（使用闭包捕获服务依赖，无全局变量）"""
    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="""获取文献全文工具。

前置条件：需要 PMCID 标识符
- 如果您有 PMCID（如 PMC1234567），直接使用此工具
- 如果您只有关键词或标题，请先使用"文献搜索"工具查找并获取 PMCID

主要参数：
- pmcid: PMCID 标识符（必填）：单个或列表[PMC1234567, PMC2345678, ...]
         批量模式最多支持20个 PMCID
- sections: 全文章节控制（可选，默认None获取全部章节）
            None → 获取全部章节（全文）
            ["conclusion", "discussion"] → 只获取指定章节
- format: 全文格式（可选，默认"markdown"）
            "markdown" → Markdown格式（推荐，适合AI处理）
            "xml" → 原始XML格式
            "text" → 纯文本格式

数据源：Europe PMC + PMC 全文数据库
返回数据包含标题、作者、摘要、期刊、发表日期和全文内容

全文功能：
- 按需获取指定格式（默认Markdown）
- 支持按章节提取（如方法、讨论、结论等）
- 优化性能，只转换请求的格式

批量返回结构：
{
    "total": 10,           # 总请求数
    "successful": 8,       # 成功获取数
    "failed": 2,           # 失败数
    "articles": [...],     # 成功的文章列表（含全文）
    "fulltext_stats": {    # 全文统计
        "has_pmcid": 8,    # 有 PMCID 数量
        "fulltext_fetched": 8  # 成功获取全文数量
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
        annotations=ToolAnnotations(title="文献全文", readOnlyHint=True, openWorldHint=False),
        tags={"literature", "fulltext", "pmc"},
    )
    async def get_article_details(
        pmcid: str | list[str],
        sections: str | list[str] | None = None,
        format: str = "markdown",
    ) -> dict[str, Any]:
        """获取文献全文工具。通过 PMCID 获取文献的全文内容。

        Args:
            pmcid: PMCID 标识符或 PMCID 列表（最多20个）
            sections: 全文章节控制，None=全部章节，"xxx"或["xxx"]=指定章节
            format: 全文格式，"markdown"|"xml"|"text"，默认"markdown"

        Returns:
            统一批量结果字典 {total, successful, failed, articles, fulltext_stats}

        """
        # 使用闭包捕获的 services 和 logger
        return await get_article_details_async(
            pmcid=pmcid,
            sections=sections,
            format=format,
            services=services,
            logger=logger,
        )


def _normalize_sections_param(sections: str | list[str] | None) -> list[str] | None:
    """规范化 sections 参数，自动转换字符串为数组。

    支持的格式：
    1. 数组: ["methods", "results"]
    2. 字符串: "methods" → ["methods"]
    3. None: None

    Args:
        sections: 原始 sections 参数

    Returns:
        规范化后的 sections（None 或字符串数组）
    """
    if sections is None:
        return None
    if isinstance(sections, str):
        return [sections]
    if isinstance(sections, list):
        # 验证所有元素都是字符串
        for item in sections:
            if not isinstance(item, str):
                raise ValueError(f"sections 数组元素必须是字符串，发现 {type(item)}")
        return sections
    # 其他类型，返回 None
    return None


def _normalize_pmcid_param(pmcid: str | list[str]) -> str | list[str]:
    """规范化 pmcid 参数，自动修复字符串化的数组。

    支持的格式：
    1. 正常的 JSON 数组: ["PMC123", "PMC456"]
    2. 字符串化的数组: '["PMC123", "PMC456"]' (自动解析)
    3. 单个字符串: "PMC123"

    Args:
        pmcid: 原始 pmcid 参数

    Returns:
        规范化后的 pmcid（字符串或字符串数组）

    Raises:
        ValueError: 如果字符串化的数组格式无效
    """
    import json

    # 如果是字符串，检查是否是字符串化的数组
    if isinstance(pmcid, str):
        # 检测字符串化的数组：以 [ 开头，以 ] 结尾
        if pmcid.startswith("[") and pmcid.endswith("]"):
            try:
                parsed = json.loads(pmcid)
                if isinstance(parsed, list):
                    # 验证解析后的数组元素都是字符串
                    for item in parsed:
                        if not isinstance(item, str):
                            raise ValueError(f"数组元素必须是字符串，发现 {type(item)}")
                    return parsed
                else:
                    # 解析结果不是数组，返回原字符串
                    return pmcid
            except json.JSONDecodeError as e:
                # JSON 解析失败，返回友好的错误
                raise ValueError(
                    f"pmcid 参数格式错误：检测到字符串化的数组，但 JSON 解析失败。"
                    f'请使用 JSON 数组格式：["PMC123", "PMC456"]。'
                    f"错误详情：{e}"
                )
        # 单个字符串，直接返回
        return pmcid

    # 如果已经是列表，验证元素类型
    if isinstance(pmcid, list):
        for item in pmcid:
            if not isinstance(item, str):
                raise ValueError(f"数组元素必须是字符串，发现 {type(item)}")
        return pmcid

    # 其他类型，直接返回
    return pmcid


async def get_article_details_async(
    pmcid: str | list[str],
    sections: str | list[str] | None = None,
    format: str = "markdown",
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """异步获取文献全文。

    Args:
        pmcid: PMCID 标识符或 PMCID 列表（最多20个）
        sections: 全文章节控制，None=全部章节，"xxx"或["xxx"]=指定章节
        format: 全文格式，"markdown"|"xml"|"text"，默认"markdown"
        services: 服务依赖注入字典（必需，闭包捕获模式）
        logger: 日志记录器（必需，闭包捕获模式）

    Returns:
        统一批量结果格式：
        {
            "total": 10,              # 总请求数
            "successful": 8,          # 成功获取数
            "failed": 2,              # 失败数
            "articles": [...],        # 成功的文章列表
            "fulltext_stats": {       # 全文统计
                "has_pmcid": 8,
                "fulltext_fetched": 8
            },
            "processing_time": 1.5    # 处理时间（秒）
        }

    """
    # 规范化 pmcid 参数（自动修复字符串化的数组）
    try:
        pmcid = _normalize_pmcid_param(pmcid)
    except ValueError as e:
        # 返回友好的错误信息
        total_estimate = (
            1 if isinstance(pmcid, str) else len(pmcid) if isinstance(pmcid, list) else 1
        )
        return {
            "total": total_estimate,
            "successful": 0,
            "failed": total_estimate,
            "articles": [],
            "fulltext_stats": None,
            "processing_time": 0,
            "error": str(e),
        }

    # 规范化 sections 参数（自动转换字符串为数组）
    try:
        sections = _normalize_sections_param(sections)
    except ValueError as e:
        # 返回友好的错误信息
        total_estimate = (
            1 if isinstance(pmcid, str) else len(pmcid) if isinstance(pmcid, list) else 1
        )
        return {
            "total": total_estimate,
            "successful": 0,
            "failed": total_estimate,
            "articles": [],
            "fulltext_stats": None,
            "processing_time": 0,
            "error": str(e),
        }

    # 验证 format 参数
    valid_formats = ["markdown", "xml", "text"]
    if format not in valid_formats:
        logger.error(f"无效的 format 参数: {format}，有效值为: {valid_formats}")
        return {
            "total": 1 if isinstance(pmcid, str) else len(pmcid) if pmcid else 0,
            "successful": 0,
            "failed": 1 if isinstance(pmcid, str) else len(pmcid) if pmcid else 0,
            "articles": [],
            "fulltext_stats": None,
            "processing_time": 0,
            "error": f"无效的 format 参数: {format}，有效值为: {', '.join(valid_formats)}",
        }

    # 统一转换为列表处理
    pmcids = [pmcid] if isinstance(pmcid, str) else pmcid

    # 空列表处理
    if not pmcids:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "articles": [],
            "fulltext_stats": None,
            "processing_time": 0,
        }

    # 验证 PMCID 数量上限
    if len(pmcids) > 20:
        logger.error(f"PMCID 数量超过限制：{len(pmcids)} > 20")
        return {
            "total": len(pmcids),
            "successful": 0,
            "failed": len(pmcids),
            "articles": [],
            "fulltext_stats": None,
            "processing_time": 0,
            "error": f"PMCID 数量超过限制，最多支持20个，当前传入{len(pmcids)}个",
        }

    return await _batch_get_article_details(
        pmcids=pmcids,
        sections=sections,
        format=format,
        services=services,
        logger=logger,
    )


async def _fetch_single_article(
    pmcid: str,
    sections: list[str] | None,
    format: str,
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any] | None:
    """获取单个文献全文（内部函数，不对外暴露）"""
    try:
        if not pmcid or not pmcid.strip():
            return None

        pmcid = pmcid.strip()

        # 验证必须是 PMCID 格式
        if not pmcid.startswith("PMC"):
            logger.warning(f"非 PMCID 格式: {pmcid}")
            return None

        # 获取服务
        europe_pmc_service = services.get("europe_pmc")
        pubmed_service = services.get("pubmed")

        if europe_pmc_service is None:
            logger.error("europe_pmc 服务未配置")
            return None

        if pubmed_service is None:
            logger.error("pubmed 服务未配置")
            return None

        # 获取文献详情（使用 pmcid 类型）
        result = europe_pmc_service.fetch(pmcid, id_type="pmcid")

        if not result or result.get("error") is not None or not result.get("article"):
            error_msg = result.get("error", "未知错误") if result else "服务未响应"
            logger.warning(f"未找到文献: {pmcid} - {error_msg}")
            return None

        article = result["article"]

        # 获取全文（这是全文获取工具，总是获取全文）
        try:
            fulltext = await pubmed_service.get_pmc_fulltext_html_async(pmcid, sections=sections)
            if fulltext.get("fulltext_available"):
                # 根据 format 参数只返回请求的格式
                format_key_map = {
                    "xml": "fulltext_xml",
                    "markdown": "fulltext_markdown",
                    "text": "fulltext_text",
                }
                content_key = format_key_map[format]

                article["fulltext"] = {
                    "format": format,
                    "content": fulltext.get(content_key),
                    "fulltext_available": True,
                }
                # 添加章节信息（如果有）
                if "sections_requested" in fulltext:
                    article["fulltext"]["sections_requested"] = fulltext.get("sections_requested")
                    article["fulltext"]["sections_found"] = fulltext.get("sections_found")
                    article["fulltext"]["sections_missing"] = fulltext.get("sections_missing")
        except Exception as e:
            logger.warning(f"获取全文失败: {e}")

        logger.info(f"成功获取文献全文: {pmcid}")
        return article

    except Exception as e:
        logger.error(f"获取文献全文异常: {e}")
        return None


async def _batch_get_article_details(
    pmcids: list[str],
    sections: list[str] | None = None,
    format: str = "markdown",
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """批量获取文献全文（内部函数）

    内部使用 Semaphore(5) 控制并发，确保每次最多5个请求同时执行。
    """
    start_time = time.time()

    # 控制并发数：内部固定为5
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_semaphore(pmcid: str) -> tuple[str, dict | None]:
        """带并发控制的获取"""
        async with semaphore:
            # 添加延迟避免过载
            await asyncio.sleep(0.3)
            result = await _fetch_single_article(
                pmcid=pmcid,
                sections=sections,
                format=format,
                services=services,
                logger=logger,
            )
            return pmcid, result

    # 并发获取所有文章
    tasks = [fetch_with_semaphore(pmcid) for pmcid in pmcids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    successful_articles = []
    failed_count = 0
    fulltext_fetched_count = 0

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"获取文献时发生异常: {result}")
            failed_count += 1
            continue

        pmcid, article = result
        if article:
            successful_articles.append(article)
            # 统计全文信息
            if article.get("fulltext") and article["fulltext"].get("fulltext_available"):
                fulltext_fetched_count += 1
        else:
            failed_count += 1

    processing_time = round(time.time() - start_time, 2)

    # 构建全文统计
    fulltext_stats = {
        "has_pmcid": len(successful_articles),
        "fulltext_fetched": fulltext_fetched_count,
        "no_fulltext": len(successful_articles) - fulltext_fetched_count,
    }

    return {
        "total": len(pmcids),
        "successful": len(successful_articles),
        "failed": failed_count,
        "articles": successful_articles,
        "fulltext_stats": fulltext_stats,
        "processing_time": processing_time,
    }
