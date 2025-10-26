"""
Article MCP 服务层
包含所有外部API集成和业务逻辑服务
"""

# 导入核心服务
from .europe_pmc import EuropePMCService, create_europe_pmc_service
from .pubmed_search import create_pubmed_service
from .crossref_service import CrossRefService
from .openalex_service import OpenAlexService
from .reference_service import UnifiedReferenceService, create_reference_service
from .literature_relation_service import (
    LiteratureRelationService,
    create_literature_relation_service,
)
from .arxiv_search import create_arxiv_service, search_arxiv
from .similar_articles import get_similar_articles_by_doi

__all__ = [
    # 核心服务类
    "EuropePMCService",
    "CrossRefService",
    "OpenAlexService",
    "UnifiedReferenceService",
    "LiteratureRelationService",
    # 服务创建函数
    "create_europe_pmc_service",
    "create_pubmed_service",
    "create_reference_service",
    "create_literature_relation_service",
    "create_arxiv_service",
    # 工具函数
    "search_arxiv",
    "get_similar_articles_by_doi",
]
