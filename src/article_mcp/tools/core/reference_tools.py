"""统一参考文献工具 - 核心工具3

服务依赖：使用闭包捕获模式，无全局变量
"""

import asyncio
import time
from typing import Any

from fastmcp import FastMCP


def register_reference_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册参考文献工具（使用闭包捕获服务依赖，无全局变量）"""
    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="""获取参考文献工具。通过文献标识符获取其引用的参考文献列表，支持智能去重。

主要参数：
- identifier: 文献标识符（必填）：DOI、PMID、PMCID
- id_type: 标识符类型（默认doi）：auto/doi/pmid/pmcid
- sources: 数据源列表（默认["europe_pmc", "crossref"]）
- max_results: 最大参考文献数量（默认20，建议20-100）
- include_metadata: 是否包含详细元数据（默认true）

支持的数据源：Europe PMC、CrossRef、PubMed
去重规则：优先按DOI去重，其次按标题去重；按数据源优先级排序""",
        annotations=ToolAnnotations(title="参考文献", readOnlyHint=True, openWorldHint=False),
        tags={"references", "citations", "bibliography"},
    )
    async def get_references(
        identifier: str,
        id_type: str = "doi",
        sources: list[str] | None = None,
        max_results: int = 20,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """获取参考文献工具。通过文献标识符获取其引用的参考文献列表。

        Args:
            identifier: 文献标识符 (DOI, PMID, PMCID, arXiv ID)
            id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
            sources: 数据源列表，支持多源查询
            max_results: 最大参考文献数量 (建议20-100)
            include_metadata: 是否包含详细元数据

        Returns:
            包含参考文献列表的字典，包括引用信息和统计

        """
        # 使用闭包捕获的 services 和 logger
        return await get_references_async(
            identifier=identifier,
            id_type=id_type,
            sources=sources,
            max_results=max_results,
            include_metadata=include_metadata,
            services=services,
            logger=logger,
        )


def _extract_identifier_type(identifier: str) -> str:
    """提取标识符类型"""
    identifier = identifier.strip().upper()

    if identifier.startswith("DOI:") or "//" in identifier or identifier.startswith("10."):
        return "doi"
    elif identifier.startswith("PMCID:") or identifier.startswith("PMC"):
        return "pmcid"
    elif identifier.isdigit() or identifier.startswith("PMID:"):
        return "pmid"
    elif identifier.startswith("ARXIV:"):
        return "arxiv_id"
    else:
        return "doi"  # 默认当作DOI处理


def _merge_and_deduplicate_references(
    references_by_source: dict[str, list[dict[str, Any]]], include_metadata: bool, logger: Any
) -> list[dict[str, Any]]:
    """合并和去重参考文献"""
    try:
        all_references = []
        seen_dois = set()
        seen_titles = set()

        for source, references in references_by_source.items():
            for ref in references:
                # 创建标准化的参考文献记录
                std_ref = {
                    "title": ref.get("title", ""),
                    "authors": ref.get("authors", []),
                    "journal": ref.get("journal", ""),
                    "publication_date": ref.get("publication_date", ""),
                    "doi": ref.get("doi", ""),
                    "pmid": ref.get("pmid", ""),
                    "pmcid": ref.get("pmcid", ""),
                    "source": source,
                }

                # 去重逻辑
                doi = std_ref["doi"]
                title = std_ref["title"]
                is_duplicate = False

                if doi and doi in seen_dois:
                    is_duplicate = True
                elif title and title.lower() in seen_titles:
                    is_duplicate = True

                if not is_duplicate:
                    if doi:
                        seen_dois.add(doi)
                    if title:
                        seen_titles.add(title.lower())

                    # 添加元数据
                    if include_metadata:
                        std_ref.update(
                            {
                                "abstract": ref.get("abstract", ""),
                                "volume": ref.get("volume", ""),
                                "issue": ref.get("issue", ""),
                                "pages": ref.get("pages", ""),
                                "issn": ref.get("issn", ""),
                                "publisher": ref.get("publisher", ""),
                            }
                        )

                    all_references.append(std_ref)

        # 按相关性排序（这里简单按来源排序）
        source_priority = {"europe_pmc": 1, "pubmed": 2, "crossref": 3}
        all_references.sort(key=lambda x: source_priority.get(x.get("source", ""), 4))

        return all_references

    except Exception as e:
        if logger:
            logger.error(f"合并和去重参考文献失败: {e}")
        return []


async def get_references_async(
    identifier: str,
    id_type: str = "doi",
    sources: list[str] | None = None,
    max_results: int = 20,
    include_metadata: bool = True,
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """异步获取参考文献工具。通过文献标识符获取其引用的参考文献列表。

    Args:
        identifier: 文献标识符 (DOI, PMID, PMCID, arXiv ID)
        id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
        sources: 数据源列表，支持多源查询
        max_results: 最大参考文献数量 (建议20-100)
        include_metadata: 是否包含详细元数据
        services: 服务依赖注入字典（必需，闭包捕获模式）
        logger: 日志记录器（必需，闭包捕获模式）

    Returns:
        包含参考文献列表的字典，包括引用信息和统计

    """
    try:
        if not identifier or not identifier.strip():
            return {
                "success": False,
                "error": "文献标识符不能为空",
                "identifier": identifier,
                "sources_used": [],
                "references_by_source": {},
                "merged_references": [],
                "total_count": 0,
                "processing_time": 0,
            }

        # 处理None值的sources参数
        if sources is None:
            sources = ["europe_pmc", "crossref"]

        start_time = time.time()
        identifier = identifier.strip()

        # 自动识别标识符类型
        if id_type == "auto":
            id_type = _extract_identifier_type(identifier)

        references_by_source = {}
        sources_used = []

        # 并行从多个数据源获取参考文献
        async def fetch_from_source(source: str) -> tuple[str, list[dict] | None]:
            """从单个数据源异步获取参考文献"""
            try:
                if source == "europe_pmc" and "reference" in services:
                    service = services["reference"]
                    if id_type == "doi":
                        result = await service.get_references_by_doi_async(identifier)
                        references = result.get("references", [])
                        if references:
                            return source, references
                    return source, None

                elif source == "crossref" and "reference" in services:
                    service = services["reference"]
                    if id_type == "doi":
                        references = await service.get_references_crossref_async(identifier)
                        if references:
                            return source, references
                    return source, None

                elif source == "pubmed" and "reference" in services:
                    service = services["reference"]
                    if id_type == "doi":
                        result = await service.get_references_by_doi_async(identifier)
                        references = result.get("references", [])
                        if references:
                            return source, references
                    return source, None

                return source, None

            except Exception as e:
                logger.error(f"从 {source} 获取参考文献失败: {e}")
                return source, None

        # 并行执行所有数据源的查询
        fetch_tasks = [fetch_from_source(source) for source in sources]
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # 处理结果
        for result in fetch_results:
            if isinstance(result, Exception):
                logger.error(f"获取参考文献时发生异常: {result}")
                continue

            source, references = result  # type: ignore[misc]
            if references:
                references_by_source[source] = references
                sources_used.append(source)
                logger.info(f"从 {source} 获取到 {len(references)} 条参考文献")

        # 合并和去重参考文献
        merged_references = _merge_and_deduplicate_references(
            references_by_source, include_metadata, logger
        )

        # 限制返回数量
        if len(merged_references) > max_results:
            merged_references = merged_references[:max_results]

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": len(merged_references) > 0,
            "identifier": identifier,
            "id_type": id_type,
            "sources_used": sources_used,
            "references_by_source": references_by_source,
            "merged_references": merged_references,
            "total_count": len(merged_references),
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"获取参考文献异常: {e}")
        # 抛出MCP标准错误
        from mcp import McpError
        from mcp.types import ErrorData

        raise McpError(
            ErrorData(code=-32603, message=f"获取参考文献失败: {type(e).__name__}: {str(e)}")
        )
