"""Article MCP - 文献搜索服务器
基于 FastMCP 框架的学术文献搜索工具

这个包提供了统一的API来搜索和获取学术文献信息，支持多个数据源：
- Europe PMC: 生物医学文献数据库
- arXiv: 预印本文献库
- PubMed: 生物医学文献库
- CrossRef: DOI解析服务
- OpenAlex: 开放学术数据库

主要功能:
- 多源文献搜索
- 文献详情获取
- 参考文献管理
- 期刊质量评估
- 文献关系分析
"""

import os
from typing import Any

# 设置编码环境，确保emoji字符正确处理
os.environ["PYTHONIOENCODING"] = "utf-8"

__version__ = "0.1.9"
__author__ = "gqy20"
__email__ = "qingyu_ge@foxmail.com"

# 导入CLI功能
from .cli import create_mcp_server
from .cli import main as cli_main

# 主要API导出
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    # CLI功能
    "create_mcp_server",
    "cli_main",
    "main",
    "get_version",
    "get_server_info",
]


# 便捷入口函数
def main() -> None:
    """CLI入口点 - 启动Article MCP服务器"""
    cli_main()


def get_version() -> str:
    """获取版本信息"""
    return __version__


def get_server_info() -> dict[str, Any]:
    """获取服务器信息"""
    return {
        "name": "Article MCP Server",
        "version": __version__,
        "author": __author__,
        "description": "基于 FastMCP 框架的学术文献搜索工具",
        "supported_databases": ["Europe PMC", "arXiv", "PubMed", "CrossRef", "OpenAlex"],
    }
