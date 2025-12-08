"""
配置资源 - 提供系统配置和状态信息
"""

import time
from typing import Any

from fastmcp import FastMCP


def register_config_resources(mcp: FastMCP) -> None:
    """注册配置资源"""

    @mcp.resource("config://version")
    def get_version() -> str:
        """获取服务器版本信息"""
        return "2.0.0"

    @mcp.resource("config://status")
    def get_system_status() -> dict[str, Any]:
        """获取系统状态"""
        return {
            "status": "running",
            "server": "Article MCP Server",
            "version": "0.1.9",
            "timestamp": time.time(),
            "uptime": "N/A",  # 可以后续实现
            "supported_data_sources": [
                "europe_pmc",
                "pubmed",
                "arxiv",
                "crossref",
                "openalex"
            ]
        }

    @mcp.resource("config://tools")
    def get_available_tools() -> list[dict[str, str]]:
        """获取可用工具列表"""
        return [
            {
                "name": "search_literature",
                "description": "多源文献搜索工具",
                "category": "search"
            },
            {
                "name": "get_article_details",
                "description": "获取文献详情",
                "category": "details"
            },
            {
                "name": "get_references",
                "description": "获取参考文献",
                "category": "references"
            },
            {
                "name": "get_literature_relations",
                "description": "文献关系分析",
                "category": "analysis"
            },
            {
                "name": "get_journal_quality",
                "description": "期刊质量评估",
                "category": "quality"
            },
            {
                "name": "export_batch_results",
                "description": "批量结果导出",
                "category": "export"
            }
        ]