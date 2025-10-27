"""
精简版 Europe PMC 服务
保持核心功能，控制在500行以内
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from datetime import timedelta
from typing import Any

import aiohttp
import requests
from dateutil.relativedelta import relativedelta


class EuropePMCService:
    """Europe PMC 服务类"""

    def __init__(self, logger: logging.Logger | None = None, pubmed_service=None):
        self.logger = logger or logging.getLogger(__name__)
        self.pubmed_service = pubmed_service  # 注入PubMed服务用于PMC全文获取

        # API 配置
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        self.detail_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        self.rate_limit_delay = 1.0
        self.timeout = aiohttp.ClientTimeout(total=60)

        # 请求头
        self.headers = {"User-Agent": "Europe-PMC-MCP-Server/1.0", "Accept": "application/json"}

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

    def _get_cached_or_fetch_sync(self, key: str, fetch_func, cache_duration_hours: int = 24):
        """获取缓存或执行获取函数（同步版本），返回结果和缓存命中信息"""
        now = datetime.now()
        cache_hit = False
        if key in self.cache and key in self.cache_expiry:
            if now < self.cache_expiry[key]:
                cache_hit = True
                result = self.cache[key]
            else:
                # 缓存过期，需要重新获取
                result = fetch_func()
                self.cache[key] = result
                self.cache_expiry[key] = now + timedelta(hours=cache_duration_hours)
        else:
            # 没有缓存，需要获取
            result = fetch_func()
            self.cache[key] = result
            self.cache_expiry[key] = now + timedelta(hours=cache_duration_hours)

        # 添加缓存命中信息到结果中
        if isinstance(result, dict):
            result["cache_hit"] = cache_hit

        return result

    async def _get_cached_or_fetch(self, key: str, fetch_func, cache_duration_hours: int = 24):
        """获取缓存或执行获取函数，返回结果和缓存命中信息"""
        now = datetime.now()
        cache_hit = False
        if key in self.cache and key in self.cache_expiry:
            if now < self.cache_expiry[key]:
                cache_hit = True
                result = self.cache[key]
            else:
                # 缓存过期，需要重新获取
                result = await fetch_func()
                self.cache[key] = result
                self.cache_expiry[key] = now + timedelta(hours=cache_duration_hours)
        else:
            # 没有缓存，需要获取
            result = await fetch_func()
            self.cache[key] = result
            self.cache_expiry[key] = now + timedelta(hours=cache_duration_hours)

        # 添加缓存命中信息到结果中
        if isinstance(result, dict):
            result["cache_hit"] = cache_hit

        return result

    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
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

    def process_europe_pmc_article(self, article_json: dict) -> dict | None:
        """处理文献 JSON 信息"""
        try:
            # 基本信息
            title = article_json.get("title", "无标题").strip()
            author_string = article_json.get("authorString", "未知作者")
            authors = [author.strip() for author in author_string.split(",") if author.strip()]

            # 期刊信息
            journal_info = article_json.get("journalInfo", {})
            journal_title = journal_info.get("journal", {}).get("title", "未知期刊")

            # 发表日期
            pub_date_str = article_json.get("firstPublicationDate")
            if pub_date_str:
                publication_date = pub_date_str
            else:
                pub_year = str(journal_info.get("yearOfPublication", ""))
                publication_date = f"{pub_year}-01-01" if pub_year.isdigit() else "日期未知"

            # 摘要
            abstract = article_json.get("abstractText", "无摘要").strip()
            abstract = re.sub("<[^<]+?>", "", abstract)
            abstract = re.sub(r"\\s+", " ", abstract).strip()

            return {
                "pmid": article_json.get("pmid", "N/A"),
                "title": title,
                "authors": authors,
                "journal_name": journal_title,
                "publication_date": publication_date,
                "abstract": abstract,
                "doi": article_json.get("doi"),
                "pmcid": article_json.get("pmcid"),
            }

        except Exception as e:
            self.logger.error(f"处理文献 JSON 时发生错误: {str(e)}")
            return None

    def _build_query_params(
        self, keyword: str, start_date: str, end_date: str, max_results: int, email: str = None
    ):
        """构建查询参数"""
        # 处理日期
        end_dt = self.parse_date(end_date) if end_date else datetime.now()
        start_dt = self.parse_date(start_date) if start_date else end_dt - relativedelta(years=3)

        if start_dt > end_dt:
            raise ValueError("起始日期不能晚于结束日期")

        # 构建查询
        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")
        date_filter = f"FIRST_PDATE:[{start_str} TO {end_str}]"
        full_query = f"({keyword}) AND ({date_filter})"

        params = {
            "query": full_query,
            "format": "json",
            "pageSize": max_results,
            "resultType": "core",
            "sort": "FIRST_PDATE_D desc",
        }

        if email and self.validate_email(email):
            params["email"] = email

        return params

    def search_sync(
        self,
        keyword: str,
        email: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """同步搜索 Europe PMC 文献数据库"""
        self.logger.info(f"开始同步搜索: {keyword}")

        try:
            params = self._build_query_params(keyword, start_date, end_date, max_results, email)

            session = self._get_sync_session()
            response = session.get(self.base_url, params=params, timeout=45)
            response.raise_for_status()

            data = response.json()
            results = data.get("resultList", {}).get("result", [])
            hit_count = data.get("hitCount", 0)

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
                "message": f"找到 {len(articles)} 篇相关文献 (共 {hit_count} 条)",
            }

        except ValueError as e:
            return {"error": f"参数错误: {str(e)}", "articles": [], "message": None}
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}", "articles": [], "message": None}

    async def search_async(
        self,
        keyword: str,
        email: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """异步搜索 Europe PMC 文献数据库"""
        async with self.search_semaphore:
            cache_key = f"search_{keyword}_{start_date}_{end_date}_{max_results}"

            async def fetch_from_api():
                self.logger.info(f"开始异步搜索: {keyword}")

                try:
                    params = self._build_query_params(
                        keyword, start_date, end_date, max_results, email
                    )

                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(
                            self.base_url, params=params, headers=self.headers
                        ) as response:
                            if response.status != 200:
                                return {
                                    "error": f"API 请求失败: {response.status}",
                                    "articles": [],
                                    "message": None,
                                }

                            data = await response.json()
                            results = data.get("resultList", {}).get("result", [])
                            hit_count = data.get("hitCount", 0)

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
                                "message": f"找到 {len(articles)} 篇相关文献 (共 {hit_count} 条)",
                            }

                except ValueError as e:
                    return {"error": f"参数错误: {str(e)}", "articles": [], "message": None}
                except Exception as e:
                    return {"error": f"搜索失败: {str(e)}", "articles": [], "message": None}

            return await self._get_cached_or_fetch(cache_key, fetch_from_api)

    def get_article_details_sync(
        self, identifier: str, id_type: str = "pmid", include_fulltext: bool = False
    ) -> dict[str, Any]:
        """同步获取文献详情"""
        self.logger.info(f"获取文献详情: {id_type}={identifier}")

        def fetch_from_api():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 根据标识符类型构建查询
                    if id_type.lower() == "pmid":
                        query = f"EXT_ID:{identifier}"
                    elif id_type.lower() == "pmcid":
                        # 对于PMCID，使用特殊的查询语法
                        if identifier.startswith("PMC"):
                            query = f"PMCID:{identifier}"
                        else:
                            query = f"PMCID:PMC{identifier}"
                    else:
                        query = f"{id_type.upper()}:{identifier}"

                    params = {"query": query, "format": "json", "resultType": "core"}
                    session = self._get_sync_session()
                    response = session.get(self.detail_url, params=params, timeout=30)

                    # 检查HTTP状态码
                    if response.status_code == 429:  # 速率限制
                        self.logger.warning(
                            f"遇到速率限制，等待后重试 ({attempt + 1}/{max_retries})"
                        )
                        time.sleep(2**attempt)  # 指数退避
                        continue
                    elif response.status_code == 503:  # 服务不可用
                        self.logger.warning(
                            f"服务暂时不可用，等待后重试 ({attempt + 1}/{max_retries})"
                        )
                        time.sleep(2**attempt)  # 指数退避
                        continue
                    elif response.status_code != 200:
                        return {
                            "error": f"API 请求失败: HTTP {response.status_code}",
                            "article": None,
                        }

                    response.raise_for_status()

                    data = response.json()
                    results = data.get("resultList", {}).get("result", [])

                    if not results:
                        return {
                            "error": f"未找到 {id_type.upper()} 为 {identifier} 的文献",
                            "article": None,
                        }

                    article_info = self.process_europe_pmc_article(results[0])

                    # 如果需要全文且结果中有PMC ID，则获取全文
                    if (
                        include_fulltext
                        and article_info
                        and article_info.get("pmcid")
                        and self.pubmed_service
                    ):
                        try:
                            pmc_id = article_info["pmcid"]
                            self.logger.info(f"获取PMC全文: {pmc_id}")
                            fulltext_result = self.pubmed_service.get_pmc_fulltext_html(pmc_id)
                            if not fulltext_result.get("error"):
                                article_info["fulltext"] = {
                                    "html": fulltext_result.get("fulltext_html"),
                                    "available": fulltext_result.get("fulltext_available", False),
                                    "title": fulltext_result.get("title"),
                                    "authors": fulltext_result.get("authors"),
                                    "abstract": fulltext_result.get("abstract"),
                                }
                            else:
                                self.logger.warning(
                                    f"获取PMC全文失败: {fulltext_result.get('error')}"
                                )
                        except Exception as e:
                            self.logger.error(f"获取PMC全文时发生错误: {str(e)}")

                    return (
                        {"article": article_info, "error": None}
                        if article_info
                        else {"error": "处理文献信息失败", "article": None}
                    )

                except requests.exceptions.Timeout:
                    self.logger.warning(f"请求超时，重试 ({attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # 指数退避
                        continue
                    else:
                        return {
                            "error": f"获取文献详情超时: {id_type}={identifier}",
                            "article": None,
                        }
                except requests.exceptions.ConnectionError:
                    self.logger.warning(f"连接错误，重试 ({attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # 指数退避
                        continue
                    else:
                        return {"error": f"连接到API失败: {id_type}={identifier}", "article": None}
                except Exception as e:
                    self.logger.error(f"获取文献详情时发生未预期错误: {str(e)}")
                    return {"error": f"获取文献详情失败: {str(e)}", "article": None}

            return {"error": f"经过 {max_retries} 次重试后仍失败", "article": None}

        cache_key = f"article_{id_type}_{identifier}"
        return self._get_cached_or_fetch_sync(cache_key, fetch_from_api)

    async def get_article_details_async(
        self, identifier: str, id_type: str = "pmid", include_fulltext: bool = False
    ) -> dict[str, Any]:
        """异步获取文献详情"""
        async with self.search_semaphore:
            cache_key = f"article_{id_type}_{identifier}"

            async def fetch_from_api():
                self.logger.info(f"异步获取文献详情: {id_type}={identifier}")

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # 根据标识符类型构建查询
                        if id_type.lower() == "pmid":
                            query = f"EXT_ID:{identifier}"
                        elif id_type.lower() == "pmcid":
                            # 对于PMCID，使用特殊的查询语法
                            if identifier.startswith("PMC"):
                                query = f"PMCID:{identifier}"
                            else:
                                query = f"PMCID:PMC{identifier}"
                        else:
                            query = f"{id_type.upper()}:{identifier}"

                        params = {"query": query, "format": "json", "resultType": "core"}

                        async with aiohttp.ClientSession(timeout=self.timeout) as session:
                            async with session.get(
                                self.detail_url, params=params, headers=self.headers
                            ) as response:
                                # 检查HTTP状态码
                                if response.status == 429:  # 速率限制
                                    self.logger.warning(
                                        f"遇到速率限制，等待后重试 ({attempt + 1}/{max_retries})"
                                    )
                                    await asyncio.sleep(2**attempt)  # 指数退避
                                    continue
                                elif response.status == 503:  # 服务不可用
                                    self.logger.warning(
                                        f"服务暂时不可用，等待后重试 ({attempt + 1}/{max_retries})"
                                    )
                                    await asyncio.sleep(2**attempt)  # 指数退避
                                    continue
                                elif response.status != 200:
                                    return {
                                        "error": f"API 请求失败: HTTP {response.status}",
                                        "article": None,
                                    }

                                data = await response.json()
                                results = data.get("resultList", {}).get("result", [])

                                if not results:
                                    return {
                                        "error": f"未找到 {id_type.upper()} 为 {identifier} 的文献",
                                        "article": None,
                                    }

                                article_info = self.process_europe_pmc_article(results[0])

                                # 如果需要全文且结果中有PMC ID，则获取全文
                                if (
                                    include_fulltext
                                    and article_info
                                    and article_info.get("pmc_id")
                                    and self.pubmed_service
                                ):
                                    try:
                                        pmc_id = article_info["pmc_id"]
                                        self.logger.info(f"异步获取PMC全文: {pmc_id}")
                                        fulltext_result = self.pubmed_service.get_pmc_fulltext_html(
                                            pmc_id
                                        )
                                        if not fulltext_result.get("error"):
                                            article_info["fulltext"] = {
                                                "html": fulltext_result.get("fulltext_html"),
                                                "available": fulltext_result.get(
                                                    "fulltext_available", False
                                                ),
                                                "title": fulltext_result.get("title"),
                                                "authors": fulltext_result.get("authors"),
                                                "abstract": fulltext_result.get("abstract"),
                                            }
                                        else:
                                            self.logger.warning(
                                                f"获取PMC全文失败: {fulltext_result.get('error')}"
                                            )
                                    except Exception as e:
                                        self.logger.error(f"获取PMC全文时发生错误: {str(e)}")

                                await asyncio.sleep(self.rate_limit_delay)

                                return (
                                    {"article": article_info, "error": None}
                                    if article_info
                                    else {"error": "处理文献信息失败", "article": None}
                                )

                    except asyncio.TimeoutError:
                        self.logger.warning(f"异步请求超时，重试 ({attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2**attempt)  # 指数退避
                            continue
                        else:
                            return {
                                "error": f"异步获取文献详情超时: {id_type}={identifier}",
                                "article": None,
                            }
                    except Exception as e:
                        self.logger.error(f"异步获取文献详情时发生未预期错误: {str(e)}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2**attempt)  # 指数退避
                            continue
                        else:
                            return {"error": f"异步获取文献详情失败: {str(e)}", "article": None}

                return {"error": f"经过 {max_retries} 次重试后仍失败", "article": None}

            return await self._get_cached_or_fetch(cache_key, fetch_from_api)

    # 批量查询功能
    async def search_batch_dois_async(
        self, dois: list[str], session: aiohttp.ClientSession
    ) -> list[dict[str, Any]]:
        """批量查询多个 DOI - 10倍性能提升"""
        if not dois:
            return []

        try:
            # 构建批量查询 - 使用 OR 连接多个 DOI
            doi_queries = [f'DOI:"{doi}"' for doi in dois]
            query = " OR ".join(doi_queries)

            params = {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": len(dois),
                "cursorMark": "*",
            }

            self.logger.info(f"批量查询 {len(dois)} 个 DOI")

            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("resultList", {}).get("result", [])
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
        email: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
        mode: str = "sync",
    ) -> dict[str, Any]:
        """统一搜索接口"""
        if mode == "async":
            return asyncio.run(self.search_async(query, email, start_date, end_date, max_results))
        else:
            return self.search_sync(query, email, start_date, end_date, max_results)

    def fetch(
        self,
        identifier: str,
        id_type: str = "pmid",
        mode: str = "sync",
        include_fulltext: bool = False,
    ) -> dict[str, Any]:
        """统一获取详情接口"""
        import time

        start_time = time.time()

        if mode == "async":
            result = asyncio.run(
                self.get_article_details_async(identifier, id_type, include_fulltext)
            )
        else:
            result = self.get_article_details_sync(identifier, id_type, include_fulltext)

        # 添加性能统计信息
        processing_time = time.time() - start_time
        if isinstance(result, dict):
            result["processing_time"] = round(processing_time, 3)

        return result


def create_europe_pmc_service(
    logger: logging.Logger | None = None, pubmed_service=None
) -> EuropePMCService:
    """创建 Europe PMC 服务实例"""
    return EuropePMCService(logger, pubmed_service)
