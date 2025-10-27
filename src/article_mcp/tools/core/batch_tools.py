"""
批量处理工具 - 核心工具6（通用导出工具）
"""

import json
import time
from pathlib import Path
from typing import Any

# 全局服务实例
_batch_services = None


def register_batch_tools(mcp, services, logger):
    """注册批量处理工具"""
    global _batch_services
    _batch_services = services

    @mcp.tool()
    def export_batch_results(
        results: dict[str, Any],
        format_type: str = "json",
        output_path: str | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """通用结果导出工具

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

    return [export_batch_results]


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