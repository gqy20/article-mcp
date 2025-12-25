"""核心工具模块 - 5个核心工具"""

from .article_tools import register_article_tools
from .quality_tools import register_quality_tools
from .reference_tools import register_reference_tools
from .relation_tools import register_relation_tools
from .search_tools import register_search_tools

# 导出所有注册函数
__all__ = [
    "register_article_tools",
    "register_quality_tools",
    "register_reference_tools",
    "register_relation_tools",
    "register_search_tools",
]
