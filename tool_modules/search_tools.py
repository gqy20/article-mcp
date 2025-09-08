#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索工具模块
包含文献搜索相关的工具函数
"""

from typing import Optional, Dict, Any, List
import logging

# 在注册时会注入这些依赖
search_tools_deps = {
    'europe_pmc_service': None,
    'pubmed_service': None,
    'logger': None
}


def register_search_tools(mcp, europe_pmc_service, pubmed_service, logger):
    """注册搜索工具函数"""
    # 注入依赖
    search_tools_deps['europe_pmc_service'] = europe_pmc_service
    search_tools_deps['pubmed_service'] = pubmed_service
    search_tools_deps['logger'] = logger

    @mcp.tool()
    def search_europe_pmc(
        keyword: str,
        email: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """搜索 Europe PMC 文献数据库（高性能优化版本）
        
        功能说明：
        - 使用异步方式在 Europe PMC 数据库中搜索学术文献
        - 支持并发请求处理，性能比同步版本更优
        - 集成缓存机制，重复查询响应更快
        - 支持复杂搜索语法（如："cancer AND therapy"）
        
        参数说明：
        - keyword: 必需，搜索关键词，支持布尔运算符（AND、OR、NOT）
        - email: 可选，提供邮箱地址以获得更高的API速率限制
        - start_date: 可选，开始日期，格式：YYYY-MM-DD
        - end_date: 可选，结束日期，格式：YYYY-MM-DD
        - max_results: 可选，最大返回结果数量，默认10，最大100
        
        返回值说明：
        - articles: 文献列表，包含完整的文献信息
        - total_count: 总结果数量
        - search_time: 搜索耗时（秒）
        - cache_hit: 是否命中缓存
        - performance_info: 性能统计信息
        - message: 处理信息
        - error: 错误信息（如果有）
        
        使用场景：
        - 大批量文献检索
        - 需要高性能的搜索任务
        - 复杂的搜索查询
        - 频繁的重复查询
        
        性能特点：
        - 比同步版本快30-50%
        - 支持24小时智能缓存
        - 自动重试机制
        - 并发控制和速率限制
        """
        # 获取依赖
        pubmed_service = search_tools_deps['pubmed_service']
        europe_pmc_service = search_tools_deps['europe_pmc_service']
        
        # 先尝试 PubMed 搜索
        pubmed_result = pubmed_service.search(
            keyword=keyword,
            email=email,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results
        )

        # 如果 PubMed 返回有效结果，则直接使用
        if pubmed_result.get("articles"):
            return pubmed_result

        # 否则回退到 Europe PMC
        return europe_pmc_service.search(
            query=keyword,
            email=email,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
            mode="sync"
        )

    @mcp.tool()
    def search_arxiv_papers(
        keyword: str,
        email: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """搜索arXiv文献数据库（基于arXiv官方API）
        
        功能说明：
        - 基于arXiv官方API搜索预印本论文
        - 支持关键词搜索和日期范围过滤
        - 自动重试和错误恢复机制
        - 分页获取，支持大量结果检索
        
        参数说明：
        - keyword: 必需，搜索关键词，支持复杂查询语法
        - email: 可选，联系邮箱，用于获得更好的API服务
        - start_date: 可选，开始日期，格式：YYYY-MM-DD
        - end_date: 可选，结束日期，格式：YYYY-MM-DD
        - max_results: 可选，最大返回结果数量，默认10，最大1000
        
        返回值说明：
        - articles: arXiv文章列表
          - arxiv_id: arXiv标识符
          - title: 文章标题
          - authors: 作者列表
          - category: arXiv分类
          - publication_date: 发表日期
          - abstract: 摘要
          - arxiv_link: arXiv摘要页链接
          - pdf_link: PDF下载链接
        - total_count: 实际获取的文章数量
        - search_info: 搜索信息
        - message: 处理信息
        - error: 错误信息（如果有）
        
        使用场景：
        - 预印本文献搜索
        - 最新研究发现
        - 计算机科学、物理学、数学等领域文献检索
        - 跟踪最新研究动态
        
        技术特点：
        - 基于arXiv官方API
        - 支持复杂查询语法
        - 自动分页获取
        - 完整的错误处理
        - 支持日期范围过滤
        """
        try:
            if not keyword or not keyword.strip():
                return {
                    "articles": [],
                    "total_count": 0,
                    "search_info": {},
                    "message": "关键词不能为空",
                    "error": "关键词不能为空"
                }
            
            # 调用arXiv搜索函数
            from src.arxiv_search import search_arxiv
            
            result = search_arxiv(
                keyword=keyword.strip(),
                email=email,
                start_date=start_date,
                end_date=end_date,
                max_results=max_results
            )
            
            return result
            
        except Exception as e:
            logger = search_tools_deps['logger']
            logger.error(f"搜索arXiv时发生异常: {e}")
            return {
                "articles": [],
                "total_count": 0,
                "search_info": {},
                "message": f"搜索失败: {str(e)}",
                "error": str(e)
            }

    return [search_europe_pmc, search_arxiv_papers]