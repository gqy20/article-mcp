"""统一文献详情工具 - 核心工具2

设计原则：
1. 只使用 europe_pmc 单一数据源
2. 返回简单的 article 字典
3. 失败时返回 None
4. 有 PMCID 时自动获取全文
"""

import logging
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
- identifier: 文献标识符（必填）：DOI、PMID、PMCID
- id_type: 标识符类型（默认auto自动识别）：auto/doi/pmid/pmcid

数据源：Europe PMC（单一数据源）
返回数据包含标题、作者、摘要、期刊、发表日期、DOI等完整信息
注意：如果文献有 PMCID，会自动获取全文（XML/Markdown/Text 格式）""",
        annotations=ToolAnnotations(title="文献详情", readOnlyHint=True, openWorldHint=False),
        tags={"literature", "details", "metadata"},
    )
    async def get_article_details(
        identifier: str,
        id_type: str = "auto",
    ) -> dict[str, Any]:
        """获取文献详情工具。通过DOI、PMID、PMCID获取文献的详细信息。

        Args:
            identifier: 文献标识符 (DOI, PMID, PMCID)
            id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]

        Returns:
            文献详细信息字典
            如果有 PMCID，会自动附加 fulltext 字段
            如果获取失败则返回 None

        """
        return await get_article_details_async(
            identifier=identifier,
            id_type=id_type,
        )


async def get_article_details_async(
    identifier: str,
    id_type: str = "auto",
) -> dict[str, Any] | None:
    """异步获取文献详情。

    Args:
        identifier: 文献标识符 (DOI, PMID, PMCID)
        id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]

    Returns:
        文献详细信息字典，有 PMCID 时附加 fulltext
        如果获取失败则返回 None

    """
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

        # 核心任务：有 PMCID 时获取全文
        pmcid = article.get("pmcid")
        if pubmed_service and pmcid:
            try:
                fulltext = pubmed_service.get_pmc_fulltext_html(pmcid)
                if fulltext.get("fulltext_available"):
                    article["fulltext"] = {
                        "pmc_id": fulltext.get("pmc_id"),
                        "fulltext_xml": fulltext.get("fulltext_xml"),
                        "fulltext_markdown": fulltext.get("fulltext_markdown"),
                        "fulltext_text": fulltext.get("fulltext_text"),
                        "fulltext_available": True,
                    }
            except Exception as e:
                logger.warning(f"获取全文失败: {e}")

        logger.info(f"成功获取文献详情: {identifier}")
        return article

    except Exception as e:
        logger.error(f"获取文献详情异常: {e}")
        return None
