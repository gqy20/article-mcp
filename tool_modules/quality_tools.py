#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
期刊质量工具模块
包含期刊质量评估相关的工具函数
"""

from typing import Optional, Dict, Any, List
import logging
import os

# 在注册时会注入这些依赖
quality_tools_deps = {
    'pubmed_service': None,
    'logger': None
}


def register_quality_tools(mcp, pubmed_service, logger):
    """注册期刊质量工具函数"""
    # 注入依赖
    quality_tools_deps['pubmed_service'] = pubmed_service
    quality_tools_deps['logger'] = logger

    @mcp.tool()
    def get_journal_quality(
        journal_name: str,
        secret_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取期刊质量评估信息（影响因子、分区等）
        
        功能说明：
        - 先从本地缓存（journal_info.json）查询期刊信息
        - 如果本地没有且提供了API密钥，则调用EasyScholar API获取
        - 返回期刊的影响因子、分区、JCI等质量指标
        
        参数说明：
        - journal_name: 必需，期刊名称
        - secret_key: 可选，EasyScholar API密钥（可从环境变量EASYSCHOLAR_SECRET_KEY获取）
        
        返回值说明：
        - journal_name: 期刊名称
        - source: 数据来源（local_cache 或 easyscholar_api）
        - quality_metrics: 质量指标字典
          - impact_factor: 影响因子
          - sci_quartile: SCI分区
          - sci_zone: SCI大区
          - jci: JCI指数
          - impact_factor_5year: 5年影响因子
        - error: 错误信息（如果有）
        
        使用场景：
        - 评估期刊质量
        - 选择投稿期刊
        - 文献质量评估
        """
        # 如果没有提供密钥，尝试从环境变量获取
        if not secret_key:
            secret_key = os.getenv('EASYSCHOLAR_SECRET_KEY')
        
        pubmed_service = quality_tools_deps['pubmed_service']
        return pubmed_service.get_journal_quality(journal_name, secret_key)

    @mcp.tool()
    def evaluate_articles_quality(
        articles: List[Dict[str, Any]],
        secret_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量评估文献的期刊质量
        
        功能说明：
        - 为文献列表中的每篇文献评估其期刊质量
        - 先从本地缓存查询，没有则调用EasyScholar API
        - 返回包含期刊质量信息的完整文献列表
        
        参数说明：
        - articles: 必需，文献列表（来自搜索结果）
        - secret_key: 可选，EasyScholar API密钥（可从环境变量EASYSCHOLAR_SECRET_KEY获取）
        
        返回值说明：
        - evaluated_articles: 包含期刊质量信息的文献列表
        - total_count: 评估的文献总数
        - message: 处理信息
        - error: 错误信息（如果有）
        
        使用场景：
        - 批量评估搜索结果的期刊质量
        - 文献质量筛选
        - 学术研究质量评估
        """
        try:
            # 如果没有提供密钥，尝试从环境变量获取
            if not secret_key:
                secret_key = os.getenv('EASYSCHOLAR_SECRET_KEY')
            
            if not articles:
                return {
                    "evaluated_articles": [],
                    "total_count": 0,
                    "message": "没有文献需要评估",
                    "error": None
                }
            
            pubmed_service = quality_tools_deps['pubmed_service']
            evaluated_articles = pubmed_service.evaluate_articles_quality(articles, secret_key)
            
            return {
                "evaluated_articles": evaluated_articles,
                "total_count": len(evaluated_articles),
                "message": f"成功评估 {len(evaluated_articles)} 篇文献的期刊质量",
                "error": None
            }
            
        except Exception as e:
            logger = quality_tools_deps['logger']
            logger.error(f"期刊质量评估失败: {e}")
            return {
                "evaluated_articles": [],
                "total_count": 0,
                "message": None,
                "error": f"期刊质量评估失败: {e}"
            }

    return [get_journal_quality, evaluate_articles_quality]