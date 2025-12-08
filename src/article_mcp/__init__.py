"""
Article MCP - 文献搜索服务器
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

# 设置编码环境，确保emoji字符正确处理
os.environ['PYTHONIOENCODING'] = 'utf-8'

__version__ = "0.1.9"
__author__ = "gqy20"
__email__ = "qingyu_ge@foxmail.com"

# 导入核心服务（使用新的包结构）
try:
    from .services.arxiv_search import search_arxiv
    from .services.europe_pmc import EuropePMCService
    from .services.reference_service import UnifiedReferenceService
    from .services.similar_articles import get_similar_articles_by_doi
except ImportError:
    # 如果相对导入失败，尝试回退导入
    try:
        from src.arxiv_search import search_arxiv
        from src.europe_pmc import EuropePMCService
        from src.reference_service import UnifiedReferenceService
        from src.similar_articles import get_similar_articles_by_doi
    except ImportError:
        # 如果都失败，提供一个占位符
        EuropePMCService = None
        UnifiedReferenceService = None
        search_arxiv = None
        get_similar_articles_by_doi = None

# 导入CLI功能
from .cli import create_mcp_server
from .cli import main as cli_main

# 主要API导出
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    # 服务类 (如果可用)
    "EuropePMCService",
    "UnifiedReferenceService",
    "search_arxiv",
    "get_similar_articles_by_doi",
    # CLI功能
    "create_mcp_server",
    "cli_main",
]


# 便捷入口函数
def main():
    """CLI入口点 - 启动Article MCP服务器"""
    cli_main()


def get_version():
    """获取版本信息"""
    return __version__


def get_server_info():
    """获取服务器信息"""
    return {
        "name": "Article MCP Server",
        "version": __version__,
        "author": __author__,
        "description": "基于 FastMCP 框架的学术文献搜索工具",
        "supported_databases": ["Europe PMC", "arXiv", "PubMed", "CrossRef", "OpenAlex"],
    }


# 模块级别的便捷函数
def quick_search(keyword, max_results=10):
    """快速搜索接口 (需要MCP环境)"""
    print("快速搜索功能需要在MCP客户端环境中使用")
    print(f"搜索关键词: {keyword}")
    print(f"最大结果数: {max_results}")
    print("请使用 'article-mcp server' 启动MCP服务器")


def quick_article_details(identifier, id_type="auto"):
    """快速获取文献详情接口 (需要MCP环境)"""
    print("文献详情获取功能需要在MCP客户端环境中使用")
    print(f"标识符: {identifier}")
    print(f"标识类型: {id_type}")
    print("请使用 'article-mcp server' 启动MCP服务器")
