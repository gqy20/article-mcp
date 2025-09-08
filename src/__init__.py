"""
Europe PMC 文献搜索和参考文献获取模块
"""

from .reference_service import UnifiedReferenceService
from .europe_pmc import EuropePMCService
from .similar_articles import get_similar_articles_by_doi
from .arxiv_search import search_arxiv

__all__ = [
    "UnifiedReferenceService",
    "EuropePMCService",
    "get_similar_articles_by_doi",
    "search_arxiv"
] 