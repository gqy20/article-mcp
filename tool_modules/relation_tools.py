#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文献关联工具模块
包含获取文献关联信息相关的工具函数
"""

from typing import Optional, Dict, Any
import logging
import time

# 在注册时会注入这些依赖
relation_tools_deps = {
    'literature_relation_service': None,
    'logger': None
}


def register_relation_tools(mcp, literature_relation_service, logger):
    """注册文献关联工具函数"""
    # 注入依赖
    relation_tools_deps['literature_relation_service'] = literature_relation_service
    relation_tools_deps['logger'] = logger

    @mcp.tool()
    def get_similar_articles(
        identifier: str,
        id_type: str = "doi",
        email: Optional[str] = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """根据文献标识符获取相似文章（基于PubMed相关文章算法）
        
        功能说明：
        - 基于PubMed的相关文章算法查找与给定文献相似的文献
        - 使用NCBI eLink服务查找相关文章
        - 自动过滤最近5年内的文献
        - 批量获取相关文章的详细信息
        - 支持多种文献标识符类型（DOI、PMID、PMCID）
        
        参数说明：
        - identifier: 必需，文献标识符（如："10.1126/science.adf6218"）
        - id_type: 可选，标识符类型，"doi"（默认）、"pmid" 或 "pmcid"
        - email: 可选，联系邮箱，用于获得更高的API访问限制
        - max_results: 可选，返回的最大相似文章数量，默认20篇
        
        返回值说明：
        - original_article: 原始文章信息
          - title: 文章标题
          - authors: 作者列表
          - journal: 期刊名称
          - publication_date: 发表日期
          - pmid: PubMed ID
          - pmcid: PMC ID（如果有）
          - abstract: 摘要
        - similar_articles: 相似文章列表（格式同原始文章）
        - total_similar_count: 总相似文章数量
        - retrieved_count: 实际获取的文章数量
        - message: 处理信息
        - error: 错误信息（如果有）
        
        使用场景：
        - 文献综述研究
        - 寻找相关研究
        - 学术调研
        - 相关工作分析
        
        技术特点：
        - 基于PubMed官方相关文章算法
        - 自动日期过滤（最近5年）
        - 批量获取详细信息
        - 完整的错误处理
        - 支持多种标识符类型
        """
        try:
            if not identifier or not identifier.strip():
                return {
                    "original_article": None,
                    "similar_articles": [],
                    "total_similar_count": 0,
                    "retrieved_count": 0,
                    "error": "文献标识符不能为空"
                }
            
            # 使用统一文献关联服务
            literature_relation_service = relation_tools_deps['literature_relation_service']
            result = literature_relation_service.get_similar_articles(
                identifier.strip(), 
                id_type=id_type.lower(), 
                max_results=max_results
            )
            
            return result
            
        except Exception as e:
            logger = relation_tools_deps['logger']
            logger.error(f"获取相似文章过程中发生异常: {e}")
            return {
                "original_article": None,
                "similar_articles": [],
                "total_similar_count": 0,
                "retrieved_count": 0,
                "error": str(e)
            }

    @mcp.tool()
    def get_citing_articles(
        identifier: str,
        id_type: str = "pmid",
        max_results: int = 20,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取引用该文献的文献信息
        
        功能说明：
        - 获取引用指定文献的其他文献信息
        - 支持多种文献标识符类型（DOI、PMID、PMCID）
        - 先通过 PubMed `elink`+`efetch` 获取引用 PMID 列表及详情
        - 如 PubMed 未返回结果，则回退到 Europe PMC `/citations` 接口
        - 返回统一结构：citing_articles、total_count、message、error
        """
        try:
            if not identifier or not identifier.strip():
                return {
                    "citing_articles": [],
                    "total_count": 0,
                    "error": "文献标识符不能为空"
                }
            
            # 使用统一文献关联服务
            literature_relation_service = relation_tools_deps['literature_relation_service']
            result = literature_relation_service.get_citing_articles(
                identifier.strip(),
                id_type=id_type.lower(),
                max_results=max_results
            )
            
            return result
            
        except Exception as e:
            logger = relation_tools_deps['logger']
            logger.error(f"获取引用文献过程中发生异常: {e}")
            return {
                "citing_articles": [],
                "total_count": 0,
                "error": str(e)
            }

    @mcp.tool()
    def get_literature_relations(
        identifier: str,
        id_type: str = "doi",
        max_results: int = 20
    ) -> Dict[str, Any]:
        """获取文献的所有关联信息（参考文献、相似文献、引用文献）
        
        功能说明：
        - 一次性获取文献的所有关联信息
        - 包括参考文献、相似文献和引用文献
        - 支持多种文献标识符类型（DOI、PMID、PMCID）
        - 统一的错误处理和返回格式
        
        参数说明：
        - identifier: 必需，文献标识符
        - id_type: 可选，标识符类型，"doi"（默认）、"pmid" 或 "pmcid"
        - max_results: 可选，每种关联文献的最大返回数量，默认20篇
        
        返回值说明：
        - references: 参考文献信息
        - similar_articles: 相似文献信息
        - citing_articles: 引用文献信息
        - processing_time: 总处理耗时（秒）
        - error: 错误信息（如果有）
        
        使用场景：
        - 全面的文献分析
        - 学术研究综述
        - 文献数据库构建
        - 知识图谱构建
        
        技术特点：
        - 一站式获取所有关联信息
        - 支持多种标识符类型
        - 统一的错误处理机制
        - 详细的性能统计
        """
        start_time = time.time()
        
        try:
            if not identifier or not identifier.strip():
                return {
                    "references": {},
                    "similar_articles": {},
                    "citing_articles": {},
                    "error": "文献标识符不能为空"
                }
            
            # 使用统一文献关联服务获取所有关联信息
            literature_relation_service = relation_tools_deps['literature_relation_service']
            result = literature_relation_service.get_all_relations(
                identifier.strip(),
                id_type=id_type.lower(),
                max_results=max_results
            )
            
            # 添加处理时间
            result["processing_time"] = round(time.time() - start_time, 2)
            
            return result
            
        except Exception as e:
            logger = relation_tools_deps['logger']
            logger.error(f"获取文献关联信息过程中发生异常: {e}")
            return {
                "references": {},
                "similar_articles": {},
                "citing_articles": {},
                "error": str(e),
                "processing_time": round(time.time() - start_time, 2)
            }

    return [get_similar_articles, get_citing_articles, get_literature_relations]