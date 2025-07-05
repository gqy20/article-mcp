"""
精简版 Europe PMC 服务
保持核心功能，控制在500行以内
"""

import asyncio
import aiohttp
import requests
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Dict, Any
import logging


class EuropePMCService:
    """Europe PMC 服务类"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # API 配置
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        self.detail_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        self.rate_limit_delay = 1.0
        self.timeout = aiohttp.ClientTimeout(total=60)
        
        # 请求头
        self.headers = {
            'User-Agent': 'Europe-PMC-MCP-Server/1.0',
            'Accept': 'application/json'
        }
        
        # 并发控制
        self.search_semaphore = asyncio.Semaphore(3)
        
        # 缓存
        self.cache = {}
        self.cache_expiry = {}
    
    def _get_sync_session(self) -> requests.Session:
        """创建同步会话"""
        session = requests.Session()
        session.headers.update(self.headers)
        return session
    
    async def _get_cached_or_fetch(self, key: str, fetch_func, cache_duration_hours: int = 24):
        """获取缓存或执行获取函数"""
        now = datetime.now()
        if key in self.cache and key in self.cache_expiry:
            if now < self.cache_expiry[key]:
                return self.cache[key]
        
        result = await fetch_func()
        self.cache[key] = result
        self.cache_expiry[key] = now + timedelta(hours=cache_duration_hours)
        return result
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期格式: {date_str}")
    
    def process_europe_pmc_article(self, article_json: Dict) -> Optional[Dict]:
        """处理文献 JSON 信息"""
        try:
            # 基本信息
            title = article_json.get('title', '无标题').strip()
            author_string = article_json.get('authorString', '未知作者')
            authors = [author.strip() for author in author_string.split(',') if author.strip()]
            
            # 期刊信息
            journal_info = article_json.get('journalInfo', {})
            journal_title = journal_info.get('journal', {}).get('title', '未知期刊')
            
            # 发表日期
            pub_date_str = article_json.get('firstPublicationDate')
            if pub_date_str:
                publication_date = pub_date_str
            else:
                pub_year = str(journal_info.get('yearOfPublication', ''))
                publication_date = f"{pub_year}-01-01" if pub_year.isdigit() else "日期未知"
            
            # 摘要
            abstract = article_json.get('abstractText', '无摘要').strip()
            abstract = re.sub('<[^<]+?>', '', abstract)
            abstract = re.sub(r'\\s+', ' ', abstract).strip()
            
            return {
                "pmid": article_json.get('pmid', "N/A"),
                "title": title,
                "authors": authors,
                "journal_name": journal_title,
                "publication_date": publication_date,
                "abstract": abstract,
                "doi": article_json.get('doi'),
                "pmcid": article_json.get('pmcid')
            }
            
        except Exception as e:
            self.logger.error(f"处理文献 JSON 时发生错误: {str(e)}")
            return None
    
    def _build_query_params(self, keyword: str, start_date: str, end_date: str, max_results: int, email: str = None):
        """构建查询参数"""
        # 处理日期
        end_dt = self.parse_date(end_date) if end_date else datetime.now()
        start_dt = self.parse_date(start_date) if start_date else end_dt - relativedelta(years=3)
        
        if start_dt > end_dt:
            raise ValueError("起始日期不能晚于结束日期")
        
        # 构建查询
        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")
        date_filter = f'FIRST_PDATE:[{start_str} TO {end_str}]'
        full_query = f"({keyword}) AND ({date_filter})"
        
        params = {
            'query': full_query,
            'format': 'json',
            'pageSize': max_results,
            'resultType': 'core',
            'sort': 'FIRST_PDATE_D desc'
        }
        
        if email and self.validate_email(email):
            params['email'] = email
        
        return params
    
    def search_sync(
        self,
        keyword: str,
        email: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """同步搜索 Europe PMC 文献数据库"""
        self.logger.info(f"开始同步搜索: {keyword}")
        
        try:
            params = self._build_query_params(keyword, start_date, end_date, max_results, email)
            
            session = self._get_sync_session()
            response = session.get(self.base_url, params=params, timeout=45)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('resultList', {}).get('result', [])
            hit_count = data.get('hitCount', 0)
            
            if not results:
                return {"message": "未找到相关文献", "articles": [], "error": None}
            
            articles = []
            for article_json in results:
                article_info = self.process_europe_pmc_article(article_json)
                if article_info:
                    articles.append(article_info)
                if len(articles) >= max_results:
                    break
            
            return {
                "articles": articles,
                "error": None,
                "message": f"找到 {len(articles)} 篇相关文献 (共 {hit_count} 条)"
            }
            
        except ValueError as e:
            return {"error": f"参数错误: {str(e)}", "articles": [], "message": None}
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}", "articles": [], "message": None}
    
    async def search_async(
        self,
        keyword: str,
        email: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """异步搜索 Europe PMC 文献数据库"""
        async with self.search_semaphore:
            cache_key = f"search_{keyword}_{start_date}_{end_date}_{max_results}"
            
            async def fetch_from_api():
                self.logger.info(f"开始异步搜索: {keyword}")
                
                try:
                    params = self._build_query_params(keyword, start_date, end_date, max_results, email)
                    
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(self.base_url, params=params, headers=self.headers) as response:
                            if response.status != 200:
                                return {"error": f"API 请求失败: {response.status}", "articles": [], "message": None}
                            
                            data = await response.json()
                            results = data.get('resultList', {}).get('result', [])
                            hit_count = data.get('hitCount', 0)
                            
                            if not results:
                                return {"message": "未找到相关文献", "articles": [], "error": None}
                            
                            articles = []
                            for article_json in results:
                                article_info = self.process_europe_pmc_article(article_json)
                                if article_info:
                                    articles.append(article_info)
                                if len(articles) >= max_results:
                                    break
                            
                            await asyncio.sleep(self.rate_limit_delay)
                            
                            return {
                                "articles": articles,
                                "error": None,
                                "message": f"找到 {len(articles)} 篇相关文献 (共 {hit_count} 条)"
                            }
                            
                except ValueError as e:
                    return {"error": f"参数错误: {str(e)}", "articles": [], "message": None}
                except Exception as e:
                    return {"error": f"搜索失败: {str(e)}", "articles": [], "message": None}
            
            return await self._get_cached_or_fetch(cache_key, fetch_from_api)
    
    def get_article_details_sync(self, pmid: str) -> Dict[str, Any]:
        """同步获取文献详情"""
        self.logger.info(f"获取文献详情: PMID={pmid}")
        
        try:
            params = {'query': f'PMID:{pmid}', 'format': 'json', 'resultType': 'core'}
            session = self._get_sync_session()
            response = session.get(self.detail_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('resultList', {}).get('result', [])
            
            if not results:
                return {"error": f"未找到 PMID 为 {pmid} 的文献", "article": None}
            
            article_info = self.process_europe_pmc_article(results[0])
            return {"article": article_info, "error": None} if article_info else {"error": "处理文献信息失败", "article": None}
            
        except Exception as e:
            return {"error": f"获取文献详情失败: {str(e)}", "article": None}
    
    async def get_article_details_async(self, pmid: str) -> Dict[str, Any]:
        """异步获取文献详情"""
        async with self.search_semaphore:
            cache_key = f"article_{pmid}"
            
            async def fetch_from_api():
                self.logger.info(f"异步获取文献详情: PMID={pmid}")
                
                try:
                    params = {'query': f'PMID:{pmid}', 'format': 'json', 'resultType': 'core'}
                    
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(self.detail_url, params=params, headers=self.headers) as response:
                            if response.status != 200:
                                return {"error": f"API 请求失败: {response.status}", "article": None}
                            
                            data = await response.json()
                            results = data.get('resultList', {}).get('result', [])
                            
                            if not results:
                                return {"error": f"未找到 PMID 为 {pmid} 的文献", "article": None}
                            
                            article_info = self.process_europe_pmc_article(results[0])
                            await asyncio.sleep(self.rate_limit_delay)
                            
                            return {"article": article_info, "error": None} if article_info else {"error": "处理文献信息失败", "article": None}
                            
                except Exception as e:
                    return {"error": f"获取文献详情失败: {str(e)}", "article": None}
            
            return await self._get_cached_or_fetch(cache_key, fetch_from_api)
    
    # 批量查询功能
    async def search_batch_dois_async(
        self, 
        dois: List[str], 
        session: aiohttp.ClientSession
    ) -> List[Dict[str, Any]]:
        """批量查询多个 DOI - 10倍性能提升"""
        if not dois:
            return []
            
        try:
            # 构建批量查询 - 使用 OR 连接多个 DOI
            doi_queries = [f'DOI:"{doi}"' for doi in dois]
            query = " OR ".join(doi_queries)
            
            params = {
                'query': query,
                'format': 'json',
                'resultType': 'core',
                'pageSize': len(dois),
                'cursorMark': '*'
            }
            
            self.logger.info(f"批量查询 {len(dois)} 个 DOI")
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('resultList', {}).get('result', [])
                    self.logger.info(f"批量查询获得 {len(results)} 个结果")
                    return results
                else:
                    self.logger.error(f"批量查询失败: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"批量查询异常: {e}")
            return []
    
    # 统一接口
    def search(
        self,
        query: str,
        email: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10,
        mode: str = "sync"
    ) -> Dict[str, Any]:
        """统一搜索接口"""
        if mode == "async":
            return asyncio.run(self.search_async(query, email, start_date, end_date, max_results))
        else:
            return self.search_sync(query, email, start_date, end_date, max_results)

    def fetch(self, pmid: str, mode: str = "sync") -> Dict[str, Any]:
        """统一获取详情接口"""
        if mode == "async":
            return asyncio.run(self.get_article_details_async(pmid))
        else:
            return self.get_article_details_sync(pmid)


def create_europe_pmc_service(logger: Optional[logging.Logger] = None) -> EuropePMCService:
    """创建 Europe PMC 服务实例"""
    return EuropePMCService(logger) 