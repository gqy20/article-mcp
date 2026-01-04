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

__version__ = "0.2.2"
__author__ = "gqy20"
__email__ = "qingyu_ge@foxmail.com"

# 导入CLI功能
from .cli import create_mcp_server

# 主要API导出
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    # CLI功能
    "create_mcp_server",
]
