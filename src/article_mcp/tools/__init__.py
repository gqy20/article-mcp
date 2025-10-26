"""
Article MCP 工具层
包含所有MCP工具的实现和注册逻辑
"""

from .core.article_tools import register_article_tools
from .core.batch_tools import register_batch_tools
from .core.quality_tools import register_quality_tools
from .core.reference_tools import register_reference_tools
from .core.relation_tools import register_relation_tools

# 导入核心工具模块
from .core.search_tools import register_search_tools

__all__ = [
    # 核心工具注册函数
    "register_search_tools",
    "register_article_tools",
    "register_reference_tools",
    "register_relation_tools",
    "register_quality_tools",
    "register_batch_tools",
]
