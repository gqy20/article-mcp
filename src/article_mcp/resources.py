"""
MCP服务器资源模块
提供配置资源和期刊信息资源
"""

import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_config_resources(mcp: FastMCP) -> None:
    """注册配置相关资源"""

    @mcp.resource("config://server-info")
    def get_server_info() -> str:
        """获取服务器基本信息"""
        try:
            from article_mcp import __version__, __author__, get_server_info

            info = get_server_info()
            info.update({
                "current_version": __version__,
                "author": __author__,
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
                "supported_databases": ["Europe PMC", "arXiv", "PubMed", "CrossRef", "OpenAlex"],
                "available_tools": [
                    "search_literature",
                    "get_article_details",
                    "get_references",
                    "get_literature_relations",
                    "get_journal_quality",
                    "export_batch_results"
                ]
            })

            return json.dumps(info, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取服务器信息失败: {e}")
            return json.dumps({
                "error": "无法获取服务器信息",
                "message": str(e)
            }, ensure_ascii=False, indent=2)

    @mcp.resource("config://tool-list")
    def get_tool_list() -> str:
        """获取可用工具列表"""
        try:
            tools = []
            for tool_name, tool_info in mcp.tools.items():
                tools.append({
                    "name": tool_name,
                    "description": tool_info.description,
                    "tags": getattr(tool_info, 'tags', [])
                })

            return json.dumps({
                "total_tools": len(tools),
                "tools": tools
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            return json.dumps({
                "error": "无法获取工具列表",
                "message": str(e)
            }, ensure_ascii=False, indent=2)

    @mcp.resource("config://api-status")
    def get_api_status() -> str:
        """获取各API服务状态"""
        try:
            status = {}

            # 检查各API服务状态
            apis = [
                ("Europe PMC", "https://www.ebi.ac.uk/europepmc/api"),
                ("arXiv", "http://export.arxiv.org/api/query"),
                ("CrossRef", "https://api.crossref.org/works"),
                ("OpenAlex", "https://api.openalex.org"),
                ("PubMed", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
            ]

            import requests
            for name, url in apis:
                try:
                    response = requests.get(url, timeout=5)
                    status[name] = {
                        "status": "online" if response.status_code == 200 else "error",
                        "response_code": response.status_code,
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                    }
                except requests.RequestException as e:
                    status[name] = {
                        "status": "offline",
                        "error": str(e)
                    }

            return json.dumps({
                "check_time": json.dumps({"timestamp": __import__('time').time()}, default=str),
                "services": status
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取API状态失败: {e}")
            return json.dumps({
                "error": "无法检查API状态",
                "message": str(e)
            }, ensure_ascii=False, indent=2)


def register_journal_resources(mcp: FastMCP) -> None:
    """注册期刊信息相关资源"""

    @mcp.resource("journal://quality-metrics")
    def get_journal_quality_metrics() -> str:
        """获取期刊质量指标定义"""
        try:
            metrics = {
                "impact_factor": {
                    "name": "影响因子",
                    "description": "期刊前两年论文在当前年被引用的平均次数",
                    "range": "通常 0.1 - 100+",
                    "interpretation": {
                        "high": ">10",
                        "medium": "3-10",
                        "low": "<3"
                    }
                },
                "quartile": {
                    "name": "JCR分区",
                    "description": "基于影响因子的学科排名分区",
                    "range": "Q1, Q2, Q3, Q4",
                    "interpretation": {
                        "Q1": "前25%（顶级期刊）",
                        "Q2": "25%-50%（优秀期刊）",
                        "Q3": "50%-75%（良好期刊）",
                        "Q4": "后25%（一般期刊）"
                    }
                },
                "jci": {
                    "name": "期刊引文指标",
                    "description": "标准化后的引文影响力，考虑学科差异",
                    "range": "通常 0.5 - 5.0",
                    "interpretation": {
                        "high": ">2.0",
                        "medium": "1.0-2.0",
                        "low": "<1.0"
                    }
                },
                "cinese_quartile": {
                    "name": "中科院分区",
                    "description": "中国科学院期刊分区表",
                    "range": "一区, 二区, 三区, 四区",
                    "interpretation": {
                        "一区": "顶级期刊（前5%）",
                        "二区": "优秀期刊（6%-20%）",
                        "三区": "良好期刊（21%-50%）",
                        "四区": "一般期刊（后50%）"
                    }
                }
            }

            return json.dumps(metrics, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取期刊质量指标定义失败: {e}")
            return json.dumps({
                "error": "无法获取期刊质量指标定义",
                "message": str(e)
            }, ensure_ascii=False, indent=2)

    @mcp.resource("journal://top-journals")
    def get_top_journals() -> str:
        """获取顶级期刊列表"""
        try:
            # 预定义的顶级期刊列表
            top_journals = {
                "综合类": [
                    {"name": "Nature", "impact_factor": 69.504, "quartile": "Q1", "country": "UK"},
                    {"name": "Science", "impact_factor": 63.714, "quartile": "Q1", "country": "USA"},
                    {"name": "Cell", "impact_factor": 66.850, "quartile": "Q1", "country": "USA"},
                    {"name": "PNAS", "impact_factor": 12.779, "quartile": "Q1", "country": "USA"}
                ],
                "医学类": [
                    {"name": "The Lancet", "impact_factor": 202.731, "quartile": "Q1", "country": "UK"},
                    {"name": "New England Journal of Medicine", "impact_factor": 158.432, "quartile": "Q1", "country": "USA"},
                    {"name": "Nature Medicine", "impact_factor": 82.889, "quartile": "Q1", "country": "USA"},
                    {"name": "JAMA", "impact_factor": 120.754, "quartile": "Q1", "country": "USA"}
                ],
                "计算机类": [
                    {"name": "Nature Machine Intelligence", "impact_factor": 25.898, "quartile": "Q1", "country": "UK"},
                    {"name": "IEEE Transactions on Pattern Analysis", "impact_factor": 24.314, "quartile": "Q1", "country": "USA"},
                    {"name": "Journal of Machine Learning Research", "impact_factor": 6.775, "quartile": "Q1", "country": "USA"}
                ]
            }

            return json.dumps(top_journals, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取顶级期刊列表失败: {e}")
            return json.dumps({
                "error": "无法获取顶级期刊列表",
                "message": str(e)
            }, ensure_ascii=False, indent=2)

    @mcp.resource("journal://field-rankings")
    def get_field_rankings() -> str:
        """获取学科领域排名"""
        try:
            # 预定义的学科领域排名
            field_rankings = [
                {
                    "field": "生物学",
                    "top_journals": [
                        {"rank": 1, "name": "Nature", "impact_factor": 69.504},
                        {"rank": 2, "name": "Science", "impact_factor": 63.714},
                        {"rank": 3, "name": "Cell", "impact_factor": 66.850}
                    ],
                    "total_journals": 500,
                    "description": "生物学领域顶级期刊"
                },
                {
                    "field": "医学",
                    "top_journals": [
                        {"rank": 1, "name": "The Lancet", "impact_factor": 202.731},
                        {"rank": 2, "name": "New England Journal of Medicine", "impact_factor": 158.432},
                        {"rank": 3, "name": "Nature Medicine", "impact_factor": 82.889}
                    ],
                    "total_journals": 800,
                    "description": "医学领域顶级期刊"
                },
                {
                    "field": "计算机科学",
                    "top_journals": [
                        {"rank": 1, "name": "Nature Machine Intelligence", "impact_factor": 25.898},
                        {"rank": 2, "name": "IEEE Transactions on Pattern Analysis", "impact_factor": 24.314},
                        {"rank": 3, "name": "Journal of Machine Learning Research", "impact_factor": 6.775}
                    ],
                    "total_journals": 300,
                    "description": "计算机科学领域顶级期刊"
                }
            ]

            return json.dumps(field_rankings, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取学科领域排名失败: {e}")
            return json.dumps({
                "error": "无法获取学科领域排名",
                "message": str(e)
            }, ensure_ascii=False, indent=2)

    @mcp.resource("journal://cached-journals")
    def get_cached_journals() -> str:
        """获取缓存的期刊信息"""
        try:
            cache_file = Path("src/resource/journal_info.json")

            if not cache_file.exists():
                return json.dumps({
                    "message": "暂无缓存的期刊信息",
                    "cache_file": str(cache_file),
                    "exists": False
                }, ensure_ascii=False, indent=2)

            with open(cache_file, encoding="utf-8") as f:
                journal_data = json.load(f)

            # 统计缓存信息
            journals = journal_data.get("journals", [])
            total_journals = len(journals)

            # 按影响因子分类统计
            high_impact = len([j for j in journals if j.get("metrics", {}).get("impact_factor", 0) > 10])
            medium_impact = len([j for j in journals if 3 <= j.get("metrics", {}).get("impact_factor", 0) <= 10])
            low_impact = len([j for j in journals if j.get("metrics", {}).get("impact_factor", 0) < 3])

            cache_info = {
                "cache_file": str(cache_file),
                "exists": True,
                "total_journals": total_journals,
                "impact_distribution": {
                    "high_impact": high_impact,
                    "medium_impact": medium_impact,
                    "low_impact": low_impact
                },
                "last_updated": cache_file.stat().st_mtime,
                "journals": journals[:10]  # 只返回前10个期刊作为示例
            }

            return json.dumps(cache_info, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取缓存期刊信息失败: {e}")
            return json.dumps({
                "error": "无法获取缓存期刊信息",
                "message": str(e)
            }, ensure_ascii=False, indent=2)


# 便捷函数用于注册所有资源
def register_all_resources(mcp: FastMCP) -> None:
    """注册所有资源"""
    register_config_resources(mcp)
    register_journal_resources(mcp)
    logger.info("所有MCP资源注册完成")


# 资源列表工具函数
def get_available_resources() -> list[str]:
    """获取可用资源列表"""
    return [
        "config://server-info",
        "config://tool-list",
        "config://api-status",
        "journal://quality-metrics",
        "journal://top-journals",
        "journal://field-rankings",
        "journal://cached-journals"
    ]


def get_resource_description(resource_uri: str) -> str:
    """获取资源描述"""
    descriptions = {
        "config://server-info": "服务器基本信息和配置",
        "config://tool-list": "可用工具列表和描述",
        "config://api-status": "各API服务状态检查",
        "journal://quality-metrics": "期刊质量指标定义和解释",
        "journal://top-journals": "各学科顶级期刊列表",
        "journal://field-rankings": "学科领域期刊排名信息",
        "journal://cached-journals": "本地缓存的期刊信息"
    }
    return descriptions.get(resource_uri, "未知资源")