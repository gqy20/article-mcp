"""
统一参考文献工具 - 核心工具3
"""

import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_reference_services = None


def register_reference_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册参考文献工具"""
    global _reference_services
    _reference_services = services

    @mcp.tool()
    def get_references(
        identifier: str,
        id_type: str = "doi",
        sources: list[str] | None = None,
        max_results: int = 20,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """获取参考文献工具

        通过文献标识符获取其引用的参考文献列表。

        Args:
            identifier: 文献标识符 (DOI, PMID, PMCID, arXiv ID)
            id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
            sources: 数据源列表，支持多源查询
            max_results: 最大参考文献数量 (建议20-100)
            include_metadata: 是否包含详细元数据

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

            # 从多个数据源获取参考文献
            for source in sources:
                try:
                    if source == "europe_pmc" and "europe_pmc" in _reference_services:
                        service = _reference_services["europe_pmc"]
                        result = service.get_references(identifier, id_type, max_results)
                        if result.get("success", False):
                            references = result.get("references", [])
                            references_by_source[source] = references
                            sources_used.append(source)
                            logger.info(f"从Europe PMC获取到 {len(references)} 条参考文献")

                    elif source == "crossref" and "crossref" in _reference_services:
                        # Crossref参考文献获取逻辑
                        service = _reference_services["crossref"]
                        result = service.get_work_references(identifier, max_results)
                        if result.get("success", False):
                            references = result.get("references", [])
                            references_by_source[source] = references
                            sources_used.append(source)
                            logger.info(f"从Crossref获取到 {len(references)} 条参考文献")

                    elif source == "pubmed" and "pubmed" in _reference_services:
                        # PubMed参考文献获取逻辑
                        service = _reference_services["pubmed"]
                        result = service.get_pubmed_references(identifier, max_results)
                        if result.get("success", False):
                            references = result.get("references", [])
                            references_by_source[source] = references
                            sources_used.append(source)
                            logger.info(f"从PubMed获取到 {len(references)} 条参考文献")

                except Exception as e:
                    logger.error(f"从 {source} 获取参考文献失败: {e}")
                    continue

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
            return {
                "success": False,
                "error": str(e),
                "identifier": identifier,
                "sources_used": [],
                "references_by_source": {},
                "merged_references": [],
                "total_count": 0,
                "processing_time": 0,
            }

    return [get_references]


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
    references_by_source: dict[str, list[dict[str, Any]]], include_metadata: bool, logger
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
        logger.error(f"合并和去重参考文献失败: {e}")
        return []
