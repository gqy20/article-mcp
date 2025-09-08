#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文献详情工具模块
包含获取文献详情相关的工具函数
"""

from typing import Optional, Dict, Any
import logging
import os

# 在注册时会注入这些依赖
article_detail_tools_deps = {
    'europe_pmc_service': None,
    'logger': None
}


def register_article_detail_tools(mcp, europe_pmc_service, logger):
    """注册文献详情工具函数"""
    # 注入依赖
    article_detail_tools_deps['europe_pmc_service'] = europe_pmc_service
    article_detail_tools_deps['logger'] = logger

    @mcp.tool()
    def get_article_details(identifier: str, id_type: str = "pmid", mode: str = "sync", include_fulltext: bool = False) -> Dict[str, Any]:
        """获取特定文献的详细信息（高性能优化版本）
        
        功能说明：
        - 根据文献标识符获取文献的完整详细信息
        - 支持多种标识符类型（PMID、DOI、PMCID）
        - 支持同步和异步两种模式
        - 集成缓存机制，重复查询响应更快
        - 自动重试和错误恢复
        - 可选获取全文内容（当文献有PMC ID时）
        
        参数说明：
        - identifier: 必需，文献标识符（如："37769091"）
        - id_type: 可选，标识符类型，"pmid"（默认）、"doi" 或 "pmcid"
        - mode: 可选，获取模式，"sync"（同步，默认）或"async"（异步）
        - include_fulltext: 可选，是否包含全文内容，默认False
        
        返回值说明：
        - 包含与同步版本相同的字段
        - 额外提供：
          - processing_time: 处理耗时（秒）
          - cache_hit: 是否命中缓存
          - performance_info: 性能统计信息
          - retry_count: 重试次数
        - 如果include_fulltext=True且文献有PMC ID：
          - fulltext: 全文信息字典
            - html: 完整的HTML全文内容
            - available: 是否可获取全文
            - title: 文章标题
            - authors: 作者列表
            - abstract: 摘要
        
        使用场景：
        - 需要高性能的文献详情获取
        - 批量文献详情查询
        - 大规模数据处理
        - 需要获取文献全文内容
        
        性能特点：
        - 异步模式比同步模式快20-40%
        - 支持智能缓存
        - 自动重试机制
        - 并发控制
        """
        # 获取依赖
        europe_pmc_service = article_detail_tools_deps['europe_pmc_service']
        
        # 调用EuropePMC服务获取文献详情
        result = europe_pmc_service.fetch(identifier, id_type=id_type, mode=mode, include_fulltext=include_fulltext)
        
        return result

    return [get_article_details]