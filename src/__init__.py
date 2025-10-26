"""
Europe PMC 文献搜索和参考文献获取模块
"""

from .arxiv_search import search_arxiv
from .europe_pmc import EuropePMCService
from .reference_service import UnifiedReferenceService
from .similar_articles import get_similar_articles_by_doi

__all__ = [
    "UnifiedReferenceService",
    "EuropePMCService",
    "get_similar_articles_by_doi",
    "search_arxiv",
]
