"""
批量处理工具 - 核心工具6（通用导出工具）
"""

import json
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_batch_services = None


def register_batch_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册批量处理工具"""
    global _batch_services
    _batch_services = services

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="通用结果导出工具。导出批量处理结果为JSON或CSV格式文件。",
        annotations=ToolAnnotations(
            title="批量结果导出",
            readOnlyHint=False,
            openWorldHint=True
        ),
        tags={"export", "batch", "json", "csv"}
    )
    def export_batch_results(
        results: dict[str, Any],
        format_type: str = "json",
        output_path: str | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """批量结果导出工具。导出批量处理结果为JSON或CSV格式文件。

        Args:
            results: 批量处理结果
            format_type: 导出格式 ["json", "csv"]
            output_path: 输出文件路径(可选)
            include_metadata: 是否包含元数据

        Returns:
            包含导出结果的字典，包括文件路径、记录数量和文件大小
        """
        try:
            # 检查输入数据的有效性
            if not results or not isinstance(results, dict):
                return {
                    "success": False,
                    "error": "结果数据必须是非空的字典格式",
                    "export_path": None,
                    "format_type": format_type,
                    "records_exported": 0,
                    "file_size": None,
                }

            # 检查是否有可导出的数据
            records_count = 0
            if "merged_results" in results and isinstance(results["merged_results"], list):
                records_count = len(results["merged_results"])
            elif "batch_results" in results and isinstance(results["batch_results"], dict):
                records_count = len(results["batch_results"])
            elif "results" in results and isinstance(results["results"], list):
                records_count = len(results["results"])
            else:
                # 如果没有标准的记录字段，尝试计算数据量
                records_count = 1  # 至少导出元数据

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
                # Excel格式已移除，自动降级为CSV格式
                logger.warning("Excel格式已移除，使用CSV格式替代")
                output_path = output_path.with_suffix(".csv")
                records_exported = _export_to_csv(results, output_path, include_metadata, logger)
            else:
                return {
                    "success": False,
                    "error": f"不支持的导出格式: {format_type}，支持的格式: json, csv",
                    "export_path": None,
                    "format_type": format_type,
                    "records_exported": 0,
                    "file_size": None,
                }

            # 如果导出成功但records_exported为0，使用预计算的记录数
            if records_exported == 0 and records_count > 0:
                records_exported = records_count

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

    

def _export_to_json(
    results: dict[str, Any], output_path: Path, include_metadata: bool, logger
) -> int:
    """导出为JSON格式"""
    try:
        export_data = {}

        # 计算实际记录数
        records_count = 0
        if "merged_results" in results and isinstance(results["merged_results"], list):
            records_count = len(results["merged_results"])
        elif "batch_results" in results and isinstance(results["batch_results"], dict):
            records_count = len(results["batch_results"])
        elif "results" in results and isinstance(results["results"], list):
            records_count = len(results["results"])
        else:
            records_count = 1  # 至少导出了数据结构本身

        if include_metadata:
            export_data = {
                "export_metadata": {
                    "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_records": records_count,
                    "format": "json",
                },
                "results": results,
            }
        else:
            export_data = results

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

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

        # 尝试从不同的字段获取文章数据
        articles = []
        if "merged_results" in results and isinstance(results["merged_results"], list):
            articles = results["merged_results"]
        elif "batch_results" in results and isinstance(results["batch_results"], dict):
            # 从batch_results中提取文章数据
            for key, value in results["batch_results"].items():
                if isinstance(value, dict) and "success" in value and value.get("success"):
                    if "article" in value:
                        articles.append(value["article"])
                    elif "details" in value:
                        articles.append(value["details"])
        elif "results" in results and isinstance(results["results"], list):
            articles = results["results"]

        if not articles:
            # 如果没有找到文章数据，尝试将整个results作为单行数据导出
            articles = [results]

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


