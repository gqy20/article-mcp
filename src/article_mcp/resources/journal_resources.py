"""
期刊资源 - 提供期刊相关的动态资源
"""

import json
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


def register_journal_resources(mcp: FastMCP) -> None:
    """注册期刊资源"""

    @mcp.resource("journals://{journal_name}/quality")
    def get_journal_quality_resource(journal_name: str) -> dict[str, Any]:
        """获取期刊质量资源数据"""
        try:
            # 尝试从本地缓存获取
            cache_file = Path.home() / ".article_mcp_cache" / f"journal_{journal_name.replace(' ', '_').lower()}.json"

            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    return {
                        "journal_name": journal_name,
                        "quality_metrics": cached_data.get("quality_metrics", {}),
                        "ranking_info": cached_data.get("ranking_info", {}),
                        "data_source": "cache",
                        "last_updated": cached_data.get("timestamp"),
                        "resource_type": "journal_quality"
                    }

            # 如果没有缓存，返回基础信息
            return {
                "journal_name": journal_name,
                "quality_metrics": {},
                "ranking_info": {},
                "data_source": "none",
                "message": "No cached data available. Use get_journal_quality tool to fetch data.",
                "resource_type": "journal_quality"
            }

        except Exception as e:
            return {
                "journal_name": journal_name,
                "error": str(e),
                "resource_type": "journal_quality"
            }

    @mcp.resource("stats://cache")
    def get_cache_stats() -> dict[str, Any]:
        """获取缓存统计信息"""
        try:
            cache_dir = Path.home() / ".article_mcp_cache"

            if not cache_dir.exists():
                return {
                    "cache_enabled": True,
                    "cache_dir": str(cache_dir),
                    "total_files": 0,
                    "total_size_mb": 0,
                    "last_accessed": None
                }

            # 统计缓存文件
            total_files = 0
            total_size = 0
            newest_time = 0

            for cache_file in cache_dir.glob("*.json"):
                total_files += 1
                file_size = cache_file.stat().st_size
                total_size += file_size
                file_time = cache_file.stat().st_mtime
                newest_time = max(newest_time, file_time)

            return {
                "cache_enabled": True,
                "cache_dir": str(cache_dir),
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "last_accessed": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newest_time)) if newest_time > 0 else None,
                "resource_type": "cache_stats"
            }

        except Exception as e:
            return {
                "cache_enabled": False,
                "error": str(e),
                "resource_type": "cache_stats"
            }