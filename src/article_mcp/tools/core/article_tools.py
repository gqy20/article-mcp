"""
统一文献详情工具 - 核心工具2
"""

import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_article_services = None


def register_article_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册文献详情工具"""
    global _article_services
    _article_services = services

    @mcp.tool()
    def get_article_details(
        identifier: str,
        id_type: str = "auto",
        sources: list[str] = ["europe_pmc", "crossref"],
        include_quality_metrics: bool = False,
    ) -> dict[str, Any]:
        """获取文献详情工具

        🎯 功能说明：
        - 获取单篇文献的完整详细信息
        - 自动识别标识符类型
        - 合并多源数据，信息更完整

        📋 使用示例：
        1. get_article_details("10.1038/s41586-021-03819-2")
        2. get_article_details("34567890", id_type="pmid")
        3. get_article_details("arXiv:2101.00001", sources=["arxiv"])
        4. get_article_details("10.1234/example", include_quality_metrics=True)

        🔧 参数说明：
        - identifier: 文献标识符 (支持DOI、PMID、PMCID、arXiv ID)
        - id_type: 标识符类型，可选 ["auto"(自动识别), "doi", "pmid", "pmcid", "arxiv_id"]
        - sources: 数据源列表，推荐 ["europe_pmc", "crossref", "openalex", "arxiv"]
        - include_quality_metrics: 是否包含期刊质量指标 (需要EasyScholar密钥)

        ✅ 推荐用法：
        - 已知DOI：直接传入，使用默认参数
        - 已知PMID：指定 id_type="pmid"
        - 需要质量评估：设置 include_quality_metrics=True
        - 查询arXiv论文：指定 arxiv 数据源

        📊 返回格式：
        {
            "success": true,
            "identifier": "传入的标识符",
            "id_type": "识别出的标识符类型",
            "sources_found": ["成功获取的数据源"],
            "details_by_source": {
                "数据源名称": {原始数据}
            },
            "merged_detail": {合并后的完整数据},
            "quality_metrics": {期刊质量指标(如果请求)},
            "processing_time": 处理耗时(秒)
        }
        """
        try:
            if not identifier or not identifier.strip():
                return {"success": False, "error": "文献标识符不能为空", "identifier": identifier}

            from ..services.merged_results import extract_identifier_type, merge_same_doi_articles

            start_time = time.time()
            details_by_source = {}
            sources_found = []

            # 自动识别标识符类型
            if id_type == "auto":
                id_type = extract_identifier_type(identifier.strip())

            # 从每个数据源获取详情
            for source in sources:
                if source not in _article_services:
                    continue

                try:
                    service = _article_services[source]
                    if source == "europe_pmc":
                        result = service.fetch(identifier.strip(), id_type=id_type)
                    elif source == "crossref":
                        if id_type == "doi":
                            result = service.get_work_by_doi(identifier.strip())
                        else:
                            continue
                    elif source == "openalex":
                        if id_type == "doi":
                            result = service.get_work_by_doi(identifier.strip())
                        else:
                            continue
                    elif source == "arxiv":
                        if id_type == "arxiv_id":
                            result = service.fetch(identifier.strip(), id_type=id_type)
                        else:
                            continue
                    else:
                        continue

                    if result.get("success", False) and result.get("article"):
                        details_by_source[source] = result["article"]
                        sources_found.append(source)
                        logger.info(f"{source} 获取详情成功")
                    else:
                        logger.debug(f"{source} 未找到文献详情")

                except Exception as e:
                    logger.error(f"{source} 获取详情异常: {e}")
                    continue

            # 合并详情
            merged_detail = None
            if details_by_source:
                articles = [details_by_source[source] for source in sources_found]
                merged_detail = merge_same_doi_articles(articles)

            # 获取质量指标
            quality_metrics = None
            if include_quality_metrics and merged_detail:
                journal_name = merged_detail.get("journal", "")
                if journal_name:
                    try:
                        from ..services.mcp_config import get_easyscholar_key

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
                "identifier": identifier.strip(),
                "id_type": id_type,
                "sources_found": sources_found,
                "details_by_source": details_by_source,
                "merged_detail": merged_detail,
                "quality_metrics": quality_metrics,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"获取文献详情异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "identifier": identifier,
                "sources_found": [],
                "details_by_source": {},
                "merged_detail": None,
                "quality_metrics": None,
                "processing_time": 0,
            }

    return [get_article_details]
