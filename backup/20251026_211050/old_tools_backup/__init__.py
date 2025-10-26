"""
Article MCP 工具层
包含所有MCP工具的实现和注册逻辑
"""

# 导入核心工具模块
from .core.search_tools import register_search_tools
from .core.article_tools import register_article_tools
from .core.reference_tools import register_reference_tools
from .core.relation_tools import register_relation_tools
from .core.quality_tools import register_quality_tools
from .core.batch_tools import register_batch_tools

# 导入传统工具模块（兼容性）
from .search_tools import *
from .article_detail_tools import *
from .reference_tools import *
from .relation_tools import *
from .quality_tools import *

__all__ = [
    # 核心工具注册函数
    "register_search_tools",
    "register_article_tools",
    "register_reference_tools",
    "register_relation_tools",
    "register_quality_tools",
    "register_batch_tools",

    # 传统工具函数（兼容性）
    "search_europe_pmc",
    "get_article_details",
    "get_references_by_doi",
    "batch_enrich_references_by_dois",
    "get_similar_articles",
    "search_arxiv_papers",
    "get_citing_articles",
    "get_literature_relations",
    "get_journal_quality",
    "evaluate_articles_quality",
]