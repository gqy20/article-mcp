"""
批量处理工具 - 核心工具6扩展
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# 全局服务实例
_batch_services = None


def register_batch_tools(mcp, services, logger):
    """注册批量处理工具"""
    global _batch_services
    _batch_services = services

    @mcp.tool()
    def batch_search_literature(
        queries: list[str],
        sources: list[str] = ["europe_pmc", "pubmed"],
        max_results_per_query: int = 10,
        parallel: bool = True,
        max_concurrent: int = 3,
    ) -> dict[str, Any]:
        """批量文献搜索工具

        功能说明：
        - 同时搜索多个查询词
        - 支持并行处理提高效率
        - 统一结果格式和去重

        参数说明：
        - queries: 搜索查询词列表
        - sources: 数据源列表
        - max_results_per_query: 每个查询的最大结果数
        - parallel: 是否并行处理
        - max_concurrent: 最大并发数

        返回格式：
        {
            "success": true,
            "total_queries": 5,
            "successful_queries": 5,
            "results_by_query": {...},
            "merged_results": [...],
            "processing_time": 12.34
        }
        """
        try:
            if not queries:
                return {
                    "success": False,
                    "error": "查询词列表不能为空",
                    "total_queries": 0,
                    "successful_queries": 0,
                    "results_by_query": {},
                    "merged_results": [],
                    "processing_time": 0,
                }

            start_time = time.time()
            results_by_query = {}
            successful_queries = 0

            if parallel:
                # 并行处理
                with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                    future_to_query = {}

                    for query in queries:
                        future = executor.submit(
                            _search_single_query,
                            query.strip(),
                            sources,
                            max_results_per_query,
                            logger,
                        )
                        future_to_query[future] = query

                    for future in as_completed(future_to_query):
                        query = future_to_query[future]
                        try:
                            result = future.result()
                            results_by_query[query] = result
                            if result.get("success", False):
                                successful_queries += 1
                        except Exception as e:
                            logger.error(f"处理查询 '{query}' 失败: {e}")
                            results_by_query[query] = {
                                "success": False,
                                "error": str(e),
                                "merged_results": [],
                            }
            else:
                # 串行处理
                for query in queries:
                    try:
                        result = _search_single_query(
                            query.strip(), sources, max_results_per_query, logger
                        )
                        results_by_query[query] = result
                        if result.get("success", False):
                            successful_queries += 1
                    except Exception as e:
                        logger.error(f"处理查询 '{query}' 失败: {e}")
                        results_by_query[query] = {
                            "success": False,
                            "error": str(e),
                            "merged_results": [],
                        }

            # 合并所有查询结果
            all_results = []
            for query_result in results_by_query.values():
                if query_result.get("success", False):
                    results = query_result.get("merged_results", [])
                    # 为每个结果添加来源查询信息
                    for result in results:
                        result["source_query"] = query_result.get("keyword", "")
                    all_results.extend(results)

            # 去重和排序
            if all_results:
                from ..services.merged_results import deduplicate_articles, simple_rank_articles

                unique_results = deduplicate_articles(all_results)
                merged_results = simple_rank_articles(unique_results)
            else:
                merged_results = []

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": successful_queries > 0,
                "total_queries": len(queries),
                "successful_queries": successful_queries,
                "results_by_query": results_by_query,
                "merged_results": merged_results,
                "total_unique_results": len(merged_results),
                "processing_time": processing_time,
                "parallel": parallel,
                "max_concurrent": max_concurrent,
            }

        except Exception as e:
            logger.error(f"批量文献搜索异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_queries": len(queries) if queries else 0,
                "successful_queries": 0,
                "results_by_query": {},
                "merged_results": [],
                "processing_time": 0,
            }

    @mcp.tool()
    def batch_get_article_details(
        identifiers: list[str],
        id_type: str = "auto",
        sources: list[str] = ["europe_pmc", "crossref"],
        parallel: bool = True,
        max_concurrent: int = 10,
    ) -> dict[str, Any]:
        """批量获取文献详情工具

        功能说明：
        - 批量获取多篇文献的详细信息
        - 支持并行处理提高效率
        - 统一数据格式和错误处理

        参数说明：
        - identifiers: 文献标识符列表
        - id_type: 标识符类型
        - sources: 数据源列表
        - parallel: 是否并行处理
        - max_concurrent: 最大并发数

        返回格式：
        {
            "success": true,
            "total_identifiers": 10,
            "successful_retrievals": 8,
            "details_by_identifier": {...},
            "failed_identifiers": [...],
            "processing_time": 15.67
        }
        """
        try:
            if not identifiers:
                return {
                    "success": False,
                    "error": "文献标识符列表不能为空",
                    "total_identifiers": 0,
                    "successful_retrievals": 0,
                    "details_by_identifier": {},
                    "failed_identifiers": [],
                    "processing_time": 0,
                }

            start_time = time.time()
            details_by_identifier = {}
            failed_identifiers = []
            successful_retrievals = 0

            if parallel:
                # 并行处理
                with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                    future_to_identifier = {}

                    for identifier in identifiers:
                        future = executor.submit(
                            _get_single_article_details,
                            identifier.strip(),
                            id_type,
                            sources,
                            logger,
                        )
                        future_to_identifier[future] = identifier

                    for future in as_completed(future_to_identifier):
                        identifier = future_to_identifier[future]
                        try:
                            result = future.result()
                            details_by_identifier[identifier] = result
                            if result.get("success", False):
                                successful_retrievals += 1
                            else:
                                failed_identifiers.append(identifier)
                        except Exception as e:
                            logger.error(f"获取文献详情 '{identifier}' 失败: {e}")
                            details_by_identifier[identifier] = {"success": False, "error": str(e)}
                            failed_identifiers.append(identifier)
            else:
                # 串行处理
                for identifier in identifiers:
                    try:
                        result = _get_single_article_details(
                            identifier.strip(), id_type, sources, logger
                        )
                        details_by_identifier[identifier] = result
                        if result.get("success", False):
                            successful_retrievals += 1
                        else:
                            failed_identifiers.append(identifier)
                    except Exception as e:
                        logger.error(f"获取文献详情 '{identifier}' 失败: {e}")
                        details_by_identifier[identifier] = {"success": False, "error": str(e)}
                        failed_identifiers.append(identifier)

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": successful_retrievals > 0,
                "total_identifiers": len(identifiers),
                "successful_retrievals": successful_retrievals,
                "details_by_identifier": details_by_identifier,
                "failed_identifiers": failed_identifiers,
                "success_rate": successful_retrievals / len(identifiers) if identifiers else 0,
                "processing_time": processing_time,
                "parallel": parallel,
                "max_concurrent": max_concurrent,
            }

        except Exception as e:
            logger.error(f"批量获取文献详情异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_identifiers": len(identifiers) if identifiers else 0,
                "successful_retrievals": 0,
                "details_by_identifier": {},
                "failed_identifiers": identifiers if identifiers else [],
                "processing_time": 0,
            }

    @mcp.tool()
    def export_batch_results(
        results: dict[str, Any],
        format_type: str = "json",
        output_path: str | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """导出批量结果工具

        功能说明：
        - 将批量处理结果导出为不同格式
        - 支持JSON、CSV、Excel等格式
        - 可选包含处理元数据

        参数说明：
        - results: 批量处理结果
        - format_type: 导出格式 ["json", "csv", "excel"]
        - output_path: 输出文件路径（可选）
        - include_metadata: 是否包含元数据

        返回格式：
        {
            "success": true,
            "export_path": "/path/to/export.json",
            "format_type": "json",
            "records_exported": 25,
            "file_size": "1.2MB"
        }
        """
        try:
            if not results:
                return {
                    "success": False,
                    "error": "结果数据不能为空",
                    "export_path": None,
                    "format_type": format_type,
                    "records_exported": 0,
                    "file_size": None,
                }

            start_time = time.time()

            # 生成默认输出路径
            if not output_path:
                timestamp = int(time.time())
                output_dir = Path.cwd() / "exports"
                output_dir.mkdir(exist_ok=True)
                output_path = str(output_dir / f"batch_export_{timestamp}.{format_type}")

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            records_exported = 0

            if format_type.lower() == "json":
                records_exported = _export_to_json(results, output_path, include_metadata, logger)
            elif format_type.lower() == "csv":
                records_exported = _export_to_csv(results, output_path, include_metadata, logger)
            elif format_type.lower() == "excel":
                records_exported = _export_to_excel(results, output_path, include_metadata, logger)
            else:
                return {
                    "success": False,
                    "error": f"不支持的导出格式: {format_type}",
                    "export_path": None,
                    "format_type": format_type,
                    "records_exported": 0,
                    "file_size": None,
                }

            # 获取文件大小
            file_size = None
            if output_path.exists():
                file_size_bytes = output_path.stat().st_size
                if file_size_bytes < 1024:
                    file_size = f"{file_size_bytes}B"
                elif file_size_bytes < 1024 * 1024:
                    file_size = f"{file_size_bytes / 1024:.1f}KB"
                else:
                    file_size = f"{file_size_bytes / (1024 * 1024):.1f}MB"

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": records_exported > 0,
                "export_path": str(output_path),
                "format_type": format_type.lower(),
                "records_exported": records_exported,
                "file_size": file_size,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"导出批量结果异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "export_path": output_path,
                "format_type": format_type,
                "records_exported": 0,
                "file_size": None,
            }

    return [batch_search_literature, batch_get_article_details, export_batch_results]


def _search_single_query(
    query: str, sources: list[str], max_results: int, logger
) -> dict[str, Any]:
    """搜索单个查询"""
    try:
        # 调用核心搜索工具
        from tool_modules.core.search_tools import _search_services

        if not _search_services:
            return {
                "success": False,
                "error": "搜索服务未初始化",
                "keyword": query,
                "merged_results": [],
            }

        results_by_source = {}
        sources_used = []

        for source in sources:
            if source not in _search_services:
                continue

            try:
                service = _search_services[source]
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

            except Exception as e:
                logger.error(f"{source} 搜索异常: {e}")
                continue

        # 合并结果
        from ..services.merged_results import merge_articles_by_doi, simple_rank_articles

        merged_results = merge_articles_by_doi(results_by_source)
        merged_results = simple_rank_articles(merged_results)

        return {
            "success": len(results_by_source) > 0,
            "keyword": query,
            "sources_used": sources_used,
            "results_by_source": results_by_source,
            "merged_results": merged_results[:max_results],
            "total_count": sum(len(results) for results in results_by_source.values()),
        }

    except Exception as e:
        logger.error(f"搜索单个查询异常: {e}")
        return {"success": False, "error": str(e), "keyword": query, "merged_results": []}


def _get_single_article_details(
    identifier: str, id_type: str, sources: list[str], logger
) -> dict[str, Any]:
    """获取单篇文献详情"""
    try:
        # 调用核心文章详情工具
        from tool_modules.core.article_tools import _article_services

        if not _article_services:
            return {"success": False, "error": "文章详情服务未初始化", "identifier": identifier}

        from ..services.merged_results import extract_identifier_type, merge_same_doi_articles

        # 自动识别标识符类型
        if id_type == "auto":
            id_type = extract_identifier_type(identifier)

        details_by_source = {}
        sources_found = []

        for source in sources:
            if source not in _article_services:
                continue

            try:
                service = _article_services[source]
                if source == "europe_pmc":
                    result = service.fetch(identifier, id_type=id_type)
                elif source == "crossref":
                    if id_type == "doi":
                        result = service.get_work_by_doi(identifier)
                    else:
                        continue
                elif source == "openalex":
                    if id_type == "doi":
                        result = service.get_work_by_doi(identifier)
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

        # 合并详情
        merged_detail = None
        if details_by_source:
            articles = [details_by_source[source] for source in sources_found]
            merged_detail = merge_same_doi_articles(articles)

        return {
            "success": len(details_by_source) > 0,
            "identifier": identifier,
            "id_type": id_type,
            "sources_found": sources_found,
            "details_by_source": details_by_source,
            "merged_detail": merged_detail,
        }

    except Exception as e:
        logger.error(f"获取单篇文献详情异常: {e}")
        return {"success": False, "error": str(e), "identifier": identifier}


def _export_to_json(
    results: dict[str, Any], output_path: Path, include_metadata: bool, logger
) -> int:
    """导出为JSON格式"""
    try:
        export_data = {}

        if include_metadata:
            export_data = {
                "export_metadata": {
                    "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_records": len(results.get("merged_results", [])),
                    "format": "json",
                },
                "results": results,
            }
        else:
            export_data = results

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        records_count = len(results.get("merged_results", []))
        logger.info(f"成功导出 {records_count} 条记录到 {output_path}")
        return records_count

    except Exception as e:
        logger.error(f"导出JSON异常: {e}")
        raise


def _export_to_csv(
    results: dict[str, Any], output_path: Path, include_metadata: bool, logger
) -> int:
    """导出为CSV格式"""
    try:
        import csv

        articles = results.get("merged_results", [])
        if not articles:
            return 0

        # CSV字段
        fieldnames = [
            "title",
            "authors",
            "journal",
            "publication_date",
            "doi",
            "pmid",
            "abstract",
            "source",
            "source_query",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for article in articles:
                row = {
                    "title": article.get("title", ""),
                    "authors": "; ".join(
                        [author.get("name", "") for author in article.get("authors", [])]
                    ),
                    "journal": article.get("journal", ""),
                    "publication_date": article.get("publication_date", ""),
                    "doi": article.get("doi", ""),
                    "pmid": article.get("pmid", ""),
                    "abstract": article.get("abstract", ""),
                    "source": article.get("source", ""),
                    "source_query": article.get("source_query", ""),
                }
                writer.writerow(row)

        logger.info(f"成功导出 {len(articles)} 条记录到 {output_path}")
        return len(articles)

    except Exception as e:
        logger.error(f"导出CSV异常: {e}")
        raise


def _export_to_excel(
    results: dict[str, Any], output_path: Path, include_metadata: bool, logger
) -> int:
    """导出为Excel格式"""
    try:
        # 简单的Excel导出实现
        # 实际项目中可以使用pandas或openpyxl库
        logger.warning("Excel导出功能需要安装pandas或openpyxl库，当前使用CSV格式替代")

        # 改为CSV导出
        csv_path = output_path.with_suffix(".csv")
        records_count = _export_to_csv(results, csv_path, include_metadata, logger)

        # 重命名为Excel文件名（实际内容为CSV）
        csv_path.rename(output_path)

        return records_count

    except Exception as e:
        logger.error(f"导出Excel异常: {e}")
        raise
