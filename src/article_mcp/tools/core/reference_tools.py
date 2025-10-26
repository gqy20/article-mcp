"""
统一参考文献工具 - 核心工具3
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

# 全局服务实例
_reference_services = None


def register_reference_tools(mcp, services, logger):
    """注册参考文献工具"""
    global _reference_services
    _reference_services = services

    @mcp.tool()
    def get_references(
        identifier: str,
        id_type: str = "doi",
        sources: list[str] = ["europe_pmc", "crossref"],
        max_results: int = 20,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """获取参考文献工具

        🎯 功能说明：
        - 获取指定文献的参考文献列表
        - 支持多种文献标识符类型
        - 提供完整的引用信息

        📋 使用示例：
        1. get_references("10.1038/s41586-021-03819-2")
        2. get_references("34567890", id_type="pmid", max_results=50)
        3. get_references("arXiv:2101.00001", sources=["arxiv"])

        🔧 参数说明：
        - identifier: 文献标识符 (支持DOI、PMID、PMCID)
        - id_type: 标识符类型 ["auto"(自动识别), "doi", "pmid", "pmcid"]
        - sources: 数据源列表 (目前主要支持 europe_pmc)
        - max_results: 最大返回参考文献数量 (建议20-100)
        - include_metadata: 是否包含详细元数据

        ✅ 推荐用法：
        - 获取引用关系：传入文献DOI，获取其参考文献
        - 大量参考文献：增加 max_results 参数
        - 特定数据源：指定 sources 参数

        📊 返回格式：
        {
            "success": true,
            "identifier": "查询的文献标识符",
            "id_type": "识别出的标识符类型",
            "sources_used": ["成功查询的数据源"],
            "references_by_source": {
                "数据源名称": [参考文献列表]
            },
            "merged_references": [去重合并后的参考文献],
            "total_count": 总参考文献数量,
            "processing_time": 处理耗时(秒)
        }
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
                }

            from src.merged_results import merge_reference_results

            start_time = time.time()
            reference_results = {}

            # 并行获取参考文献
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_source = {}

                for source in sources:
                    if source not in _reference_services:
                        continue

                    try:
                        service = _reference_services[source]
                        if source == "europe_pmc":
                            # Europe PMC需要从文献详情中获取参考文献
                            detail_result = service.fetch(identifier.strip(), id_type=id_type)
                            if detail_result.get("success", False):
                                article = detail_result.get("article", {})
                                references = article.get("references", [])
                                reference_results[source] = {
                                    "success": True,
                                    "references": references,
                                    "total_count": len(references),
                                    "source": source,
                                }
                        elif source == "crossref":
                            ref_result = service.get_references(identifier.strip(), max_results)
                            reference_results[source] = ref_result
                        elif source == "openalex":
                            # OpenAlex暂时没有直接的参考文献API
                            reference_results[source] = {
                                "success": False,
                                "references": [],
                                "total_count": 0,
                                "source": source,
                                "error": "OpenAlex暂不支持参考文献查询",
                            }

                    except Exception as e:
                        logger.error(f"{source} 获取参考文献异常: {e}")
                        reference_results[source] = {
                            "success": False,
                            "references": [],
                            "total_count": 0,
                            "source": source,
                            "error": str(e),
                        }

            # 合并参考文献
            merged_result = merge_reference_results(reference_results)
            processing_time = round(time.time() - start_time, 2)

            return {
                **merged_result,
                "identifier": identifier.strip(),
                "id_type": id_type,
                "processing_time": processing_time,
                "include_metadata": include_metadata,
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

    @mcp.tool()
    def batch_process_articles(
        identifiers: list[str],
        operations: list[str] = ["details", "quality"],
        parallel: bool = True,
        max_concurrent: int = 10,
    ) -> dict[str, Any]:
        """批量处理文献工具

        功能说明：
        - 批量处理多个文献标识符
        - 支持多种操作类型
        - 可选择并行或串行处理

        参数说明：
        - identifiers: 文献标识符列表
        - operations: 操作类型列表 ["details", "quality", "relations", "references"]
        - parallel: 是否并行处理
        - max_concurrent: 最大并发数

        返回格式：
        {
            "success": true,
            "processed_count": 5,
            "total_count": 5,
            "results": {...},
            "processing_time": 3.45
        }
        """
        try:
            if not identifiers:
                return {
                    "success": False,
                    "error": "文献标识符列表不能为空",
                    "processed_count": 0,
                    "total_count": 0,
                    "results": {},
                    "processing_time": 0,
                }

            from tool_modules.core.article_tools import _article_services
            from tool_modules.core.search_tools import _search_services

            start_time = time.time()
            results = {}

            if parallel:
                # 并行处理
                with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                    future_to_identifier = {}

                    for identifier in identifiers:
                        for operation in operations:
                            future = executor.submit(
                                _process_single_article,
                                identifier.strip(),
                                operation,
                                _search_services,
                                _article_services,
                                logger,
                            )
                            future_to_identifier[future] = (identifier, operation)

                    for future in as_completed(future_to_identifier):
                        identifier, operation = future_to_identifier[future]
                        try:
                            result = future.result()
                            if identifier not in results:
                                results[identifier] = {}
                            results[identifier][operation] = result
                        except Exception as e:
                            logger.error(f"处理 {identifier} 的 {operation} 操作失败: {e}")
                            if identifier not in results:
                                results[identifier] = {}
                            results[identifier][operation] = {"success": False, "error": str(e)}
            else:
                # 串行处理
                for identifier in identifiers:
                    identifier_results = {}
                    for operation in operations:
                        try:
                            result = _process_single_article(
                                identifier.strip(),
                                operation,
                                _search_services,
                                _article_services,
                                logger,
                            )
                            identifier_results[operation] = result
                        except Exception as e:
                            logger.error(f"处理 {identifier} 的 {operation} 操作失败: {e}")
                            identifier_results[operation] = {"success": False, "error": str(e)}
                    results[identifier] = identifier_results

            processing_time = round(time.time() - start_time, 2)
            processed_count = len(results)
            successful_count = sum(
                1 for r in results.values() if any(op.get("success", False) for op in r.values())
            )

            return {
                "success": successful_count > 0,
                "processed_count": processed_count,
                "total_count": len(identifiers),
                "successful_count": successful_count,
                "results": results,
                "processing_time": processing_time,
                "operations": operations,
                "parallel": parallel,
            }

        except Exception as e:
            from src.error_utils import format_error

            logger.error(f"批量处理文献异常: {e}")
            return format_error(
                "batch_process_articles",
                e,
                {
                    "processed_count": 0,
                    "total_count": len(identifiers) if identifiers else 0,
                    "successful_count": 0,
                    "results": {},
                    "processing_time": 0,
                },
            )

    return [get_references, batch_process_articles]


def _process_single_article(
    identifier: str, operation: str, search_services, article_services, logger
) -> dict[str, Any]:
    """处理单个文献的操作"""
    try:
        if operation == "details":
            # 使用article_services获取详情
            if article_services:
                sources = ["europe_pmc", "crossref", "openalex"]
                details_result = _get_article_details_internal(
                    identifier, "auto", sources, article_services, logger
                )
                return details_result
        elif operation == "quality":
            # 获取质量指标
            return {
                "success": True,
                "identifier": identifier,
                "operation": operation,
                "message": "质量评估功能待实现",
            }
        elif operation == "relations":
            # 获取文献关联信息
            return {
                "success": True,
                "identifier": identifier,
                "operation": operation,
                "message": "关系分析功能待实现",
            }
        elif operation == "references":
            # 获取参考文献
            # 这里不能直接调用get_references，因为它在工具注册后才定义
            # 返回一个简化的结果
            return {
                "success": True,
                "identifier": identifier,
                "operation": operation,
                "message": "参考文献获取功能已集成到get_references工具中",
                "references": [],
            }
        else:
            return {
                "success": False,
                "error": f"不支持的操作类型: {operation}",
                "identifier": identifier,
                "operation": operation,
            }

    except Exception as e:
        logger.error(f"处理文献 {identifier} 的 {operation} 操作异常: {e}")
        return {"success": False, "error": str(e), "identifier": identifier, "operation": operation}


def _get_article_details_internal(
    identifier: str, id_type: str, sources: list[str], article_services, logger
) -> dict[str, Any]:
    """内部文章详情获取函数"""
    if not article_services:
        return {"success": False, "error": "服务未初始化"}

    from src.merged_results import extract_identifier_type, merge_same_doi_articles

    details_by_source = {}
    sources_found = []

    # 自动识别标识符类型
    if id_type == "auto":
        id_type = extract_identifier_type(identifier.strip())

    for source in sources:
        if source not in article_services:
            continue

        try:
            service = article_services[source]
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
            else:
                continue

            if result.get("success", False) and result.get("article"):
                details_by_source[source] = result["article"]
                sources_found.append(source)

        except Exception as e:
            logger.error(f"{source} 获取详情异常: {e}")
            continue

    merged_detail = None
    if details_by_source:
        articles = [details_by_source[source] for source in sources_found]
        merged_detail = merge_same_doi_articles(articles)

    return {
        "success": len(details_by_source) > 0,
        "identifier": identifier.strip(),
        "id_type": id_type,
        "sources_found": sources_found,
        "details_by_source": details_by_source,
        "merged_detail": merged_detail,
    }
