"""Article MCP 服务层
包含所有外部API集成和业务逻辑服务
"""

from .arxiv_search import create_arxiv_service, search_arxiv
from .crossref_service import CrossRefService

# 导入核心服务
from .easyscholar_service import EasyScholarService, create_easyscholar_service
from .europe_pmc import EuropePMCService, create_europe_pmc_service
from .openalex_metrics_service import (
    OpenAlexMetricsService,
    create_openalex_metrics_service,
)
from .openalex_service import OpenAlexService
from .pubmed_search import create_pubmed_service
from .reference_service import (
    UnifiedReferenceService,
    create_unified_reference_service,
)
from .similar_articles import get_similar_articles_by_doi

__all__ = [
    # 核心服务类
    "EuropePMCService",
    "CrossRefService",
    "OpenAlexService",
    "OpenAlexMetricsService",
    "UnifiedReferenceService",
    "EasyScholarService",
    # 服务创建函数
    "create_europe_pmc_service",
    "create_pubmed_service",
    "create_unified_reference_service",
    "create_arxiv_service",
    "create_easyscholar_service",
    "create_openalex_metrics_service",
    # 工具函数
    "search_arxiv",
    "get_similar_articles_by_doi",
]
