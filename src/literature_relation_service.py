#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一的文献关联服务
整合参考文献、相似文献和引用文献的获取功能
"""

import asyncio
import aiohttp
import requests
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

# 导入现有的服务
from .europe_pmc import EuropePMCService
from .reference_service import UnifiedReferenceService
from .similar_articles import get_similar_articles_by_doi
from .pubmed_search import PubMedService


class LiteratureRelationService:
    """文献关联服务类"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.europe_pmc_service = EuropePMCService(self.logger)
        self.reference_service = UnifiedReferenceService(self.logger)
        self.pubmed_service = PubMedService(self.logger)
    
    def get_references(self, identifier: str, id_type: str = "doi") -> Dict[str, Any]:
        """获取参考文献列表
        
        Args:
            identifier: 文献标识符
            id_type: 标识符类型 (doi, pmid, pmcid)
            
        Returns:
            包含参考文献列表的字典
        """
        try:
            if id_type.lower() == "doi":
                return self.reference_service.get_references_batch_optimized(identifier)
            else:
                # 对于非DOI标识符，先获取DOI再获取参考文献
                article_details = self.europe_pmc_service.fetch(identifier, id_type=id_type, mode="sync")
                if article_details.get("article") and article_details["article"].get("doi"):
                    doi = article_details["article"]["doi"]
                    return self.reference_service.get_references_batch_optimized(doi)
                else:
                    return {
                        "references": [],
                        "message": "无法获取文献的DOI信息",
                        "error": "文献没有DOI信息，无法获取参考文献",
                        "total_count": 0
                    }
        except Exception as e:
            return {
                "references": [],
                "message": "获取参考文献失败",
                "error": str(e),
                "total_count": 0
            }
    
    def get_similar_articles(self, identifier: str, id_type: str = "doi", 
                           max_results: int = 20) -> Dict[str, Any]:
        """获取相似文献
        
        Args:
            identifier: 文献标识符
            id_type: 标识符类型 (doi, pmid, pmcid)
            max_results: 最大返回结果数
            
        Returns:
            包含相似文献列表的字典
        """
        try:
            # 如果不是DOI，先获取DOI
            doi = identifier
            if id_type.lower() != "doi":
                article_details = self.europe_pmc_service.fetch(identifier, id_type=id_type, mode="sync")
                if article_details.get("article") and article_details["article"].get("doi"):
                    doi = article_details["article"]["doi"]
                else:
                    return {
                        "original_article": None,
                        "similar_articles": [],
                        "total_similar_count": 0,
                        "retrieved_count": 0,
                        "error": "无法获取文献的DOI信息"
                    }
            
            # 调用现有的相似文献获取功能
            return get_similar_articles_by_doi(doi, max_results=max_results)
        except Exception as e:
            return {
                "original_article": None,
                "similar_articles": [],
                "total_similar_count": 0,
                "retrieved_count": 0,
                "error": str(e)
            }
    
    def get_citing_articles(self, identifier: str, id_type: str = "pmid", 
                          max_results: int = 20) -> Dict[str, Any]:
        """获取引用文献
        
        Args:
            identifier: 文献标识符
            id_type: 标识符类型 (doi, pmid, pmcid)
            max_results: 最大返回结果数
            
        Returns:
            包含引用文献列表的字典
        """
        try:
            # 如果不是PMID，先获取PMID
            pmid = identifier
            if id_type.lower() != "pmid":
                article_details = self.europe_pmc_service.fetch(identifier, id_type=id_type, mode="sync")
                if article_details.get("article") and article_details["article"].get("pmid"):
                    pmid = article_details["article"]["pmid"]
                else:
                    return {
                        "citing_articles": [],
                        "total_count": 0,
                        "error": "无法获取文献的PMID信息"
                    }
            
            # 调用现有的引用文献获取功能
            result = self.pubmed_service.get_citing_articles(pmid=pmid, max_results=max_results)
            
            # 如果PubMed没有结果，回退到Europe PMC
            if not result.get("citing_articles"):
                try:
                    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations.json"
                    resp = requests.get(url, timeout=20)
                    if resp.status_code == 200:
                        data = resp.json()
                        articles_json = data.get("resultList", {}).get("result", [])
                        citing_articles = []
                        for art in articles_json[:max_results]:
                            info = self.europe_pmc_service.process_europe_pmc_article(art)
                            if info:
                                citing_articles.append(info)
                        return {
                            "citing_articles": citing_articles,
                            "total_count": data.get("hitCount", len(citing_articles)),
                            "message": "来自 Europe PMC 的引用文献" if citing_articles else "未找到引用文献",
                            "error": None
                        }
                except Exception as e:
                    self.logger.warning(f"Europe PMC 获取引用失败: {e}")
            
            return result
        except Exception as e:
            return {
                "citing_articles": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def get_all_relations(self, identifier: str, id_type: str = "doi", 
                         max_results: int = 20) -> Dict[str, Any]:
        """获取所有类型的关联文献
        
        Args:
            identifier: 文献标识符
            id_type: 标识符类型 (doi, pmid, pmcid)
            max_results: 最大返回结果数
            
        Returns:
            包含所有关联文献的字典
        """
        return {
            "references": self.get_references(identifier, id_type),
            "similar_articles": self.get_similar_articles(identifier, id_type, max_results),
            "citing_articles": self.get_citing_articles(identifier, id_type, max_results)
        }


def create_literature_relation_service(logger: Optional[logging.Logger] = None) -> LiteratureRelationService:
    """创建文献关联服务实例"""
    return LiteratureRelationService(logger)