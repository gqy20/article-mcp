"""统一的参考文献获取服务 - 纯异步实现

重构目标：
- 移除同步的 requests.Session
- 所有方法改为纯异步
- 只使用 AsyncAPIClient
"""

import asyncio
import logging
import re
import time
from typing import Any

import aiohttp


class UnifiedReferenceService:
    """统一的参考文献获取服务类"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

        # 异步配置
        self.crossref_delay = 0.02  # 50 requests/second
        self.europe_pmc_delay = 1.0  # 保守的1秒间隔

        self.timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_read=30)
        self.headers = {
            "User-Agent": "Europe-PMC-Reference-Tool/1.0 (https://github.com/mcp)",
            "mailto": "researcher@example.com",
        }

        # 并发控制
        self.crossref_semaphore = asyncio.Semaphore(10)
        self.europe_pmc_semaphore = asyncio.Semaphore(3)

        # 缓存
        self.cache: dict[str, Any] = {}
        self.cache_expiry: dict[str, Any] = {}

        # 批量查询配置
        self.max_batch_size = 20  # 最大批量大小
        self.batch_timeout = 30  # 批量查询超时时间

    # 通用辅助方法
    def _format_europe_pmc_metadata(self, article_info: dict[str, Any]) -> dict[str, Any]:
        """格式化 Europe PMC 元数据"""
        formatted = {
            "title": article_info.get("title"),
            "authors": self._extract_authors(article_info.get("authorList", {})),
            "journal": article_info.get("journalTitle"),
            "year": article_info.get("pubYear"),
            "doi": article_info.get("doi"),
            "pmid": article_info.get("pmid"),
            "pmcid": article_info.get("pmcid"),
            "abstract": article_info.get("abstractText"),
            "source": "europe_pmc",
        }
        return formatted

    def _extract_authors(self, author_list: dict[str, Any]) -> list[str] | None:
        """提取作者列表"""
        try:
            authors = author_list.get("author", [])
            if not authors:
                return None

            author_names = []
            for author in authors:
                if isinstance(author, dict):
                    first_name = author.get("firstName", "")
                    last_name = author.get("lastName", "")
                    if first_name and last_name:
                        author_names.append(f"{first_name} {last_name}")
                    elif last_name:
                        author_names.append(last_name)
                elif isinstance(author, str):
                    author_names.append(author)

            return author_names if author_names else None

        except Exception as e:
            self.logger.error(f"提取作者信息异常: {e}")
            return None

    def deduplicate_references(self, references: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重参考文献"""
        unique_refs = {}
        no_doi_refs = []

        for ref in references:
            doi = ref.get("doi")
            if not doi:
                no_doi_refs.append(ref)
                continue

            if doi not in unique_refs:
                unique_refs[doi] = ref
            else:
                current_score = self._calculate_completeness_score(ref)
                existing_score = self._calculate_completeness_score(unique_refs[doi])

                if current_score > existing_score:
                    unique_refs[doi] = ref

        result = list(unique_refs.values()) + no_doi_refs
        self.logger.info(f"去重后保留 {len(result)} 条参考文献")
        return result

    def _calculate_completeness_score(self, ref: dict[str, Any]) -> int:
        """计算参考文献信息完整度得分"""
        score = 0
        important_fields = ["title", "authors", "journal", "year", "abstract", "pmid"]

        for field in important_fields:
            if ref.get(field):
                score += 1

        return score

    # 异步方法
    async def get_references_crossref_async(self, doi: str) -> list[dict[str, Any]] | None:
        """异步获取 Crossref 参考文献"""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            self.logger.info(f"异步请求 Crossref: {url}")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status != 200:
                        self.logger.warning(f"Crossref 失败，状态码: {resp.status}")
                        return None

                    data = await resp.json()
                    message = data.get("message", {})
                    refs_raw = message.get("reference", [])

                    if not refs_raw:
                        self.logger.info("Crossref 未返回参考文献")
                        return []

                    references = []
                    for ref in refs_raw:
                        author_raw = ref.get("author")
                        authors = None
                        if author_raw:
                            authors = [a.strip() for a in re.split("[;,]", author_raw) if a.strip()]

                        references.append(
                            {
                                "title": ref.get("article-title") or ref.get("unstructured"),
                                "authors": authors,
                                "journal": ref.get("journal-title") or ref.get("journal"),
                                "year": ref.get("year"),
                                "doi": ref.get("DOI") or ref.get("doi"),
                                "source": "crossref",
                            }
                        )

                    self.logger.info(f"Crossref 异步获取到 {len(references)} 条参考文献")
                    return references

        except Exception as e:
            self.logger.error(f"Crossref 异步异常: {e}")
            return None

    async def get_references_by_doi_async(self, doi: str) -> dict[str, Any]:
        """异步获取参考文献"""
        start_time = time.time()

        try:
            self.logger.info(f"开始异步获取 DOI {doi} 的参考文献")

            # 1. 从 Crossref 获取参考文献列表
            references = await self.get_references_crossref_async(doi)

            if references is None:
                return {
                    "references": [],
                    "message": "Crossref 查询失败",
                    "error": "未能从 Crossref 获取参考文献列表",
                    "total_count": 0,
                    "processing_time": time.time() - start_time,
                }

            if not references:
                return {
                    "references": [],
                    "message": "未找到参考文献",
                    "error": None,
                    "total_count": 0,
                    "processing_time": time.time() - start_time,
                }

            # 2. 使用 Europe PMC 补全信息（异步批量）
            enriched_references = []
            dois_to_enrich = []

            for ref in references:
                doi_ref = ref.get("doi")
                if doi_ref and not (ref.get("abstract") or ref.get("pmid")):
                    dois_to_enrich.append(doi_ref)
                else:
                    enriched_references.append(ref)

            # 异步批量补全信息
            if dois_to_enrich:
                batch_results = await self.batch_search_europe_pmc_by_dois_async(dois_to_enrich)

                for ref in references:
                    doi_ref = ref.get("doi")
                    if doi_ref in batch_results:
                        europe_pmc_info = batch_results[doi_ref]
                        formatted_info = self._format_europe_pmc_metadata(europe_pmc_info)
                        for key, value in formatted_info.items():
                            if value and not ref.get(key):
                                ref[key] = value

                    enriched_references.append(ref)

            # 3. 去重处理
            final_references = self.deduplicate_references(enriched_references)

            processing_time = time.time() - start_time

            return {
                "references": final_references,
                "message": f"成功获取 {len(final_references)} 条参考文献 (异步版本)",
                "error": None,
                "total_count": len(final_references),
                "enriched_count": len([r for r in final_references if r.get("abstract")]),
                "processing_time": round(processing_time, 2),
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"异步获取参考文献异常: {e}")
            return {
                "references": [],
                "message": "获取参考文献失败",
                "error": str(e),
                "total_count": 0,
                "processing_time": round(processing_time, 2),
            }

    async def batch_search_europe_pmc_by_dois_async(
        self, dois: list[str]
    ) -> dict[str, dict[str, Any]]:
        """异步批量搜索 Europe PMC"""
        if not dois:
            return {}

        try:
            # 限制批量大小
            if len(dois) > self.max_batch_size:
                self.logger.warning(
                    f"DOI数量 {len(dois)} 超过最大批量大小 {self.max_batch_size}，将进行分批处理"
                )
                all_results = {}
                for i in range(0, len(dois), self.max_batch_size):
                    batch = dois[i : i + self.max_batch_size]
                    batch_results = await self.batch_search_europe_pmc_by_dois_async(batch)
                    all_results.update(batch_results)
                    # 添加延迟避免速率限制
                    if i + self.max_batch_size < len(dois):
                        await asyncio.sleep(self.europe_pmc_delay)
                return all_results

            # 构建 OR 操作符查询
            doi_queries = [f'DOI:"{doi}"' for doi in dois]
            query = " OR ".join(doi_queries)

            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            params = {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": len(dois) * 2,
                "cursorMark": "*",
            }

            self.logger.info(f"异步批量搜索 Europe PMC: {len(dois)} 个 DOI")

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params, headers=self.headers) as resp:
                    if resp.status != 200:
                        self.logger.warning(f"批量 Europe PMC 搜索失败: {resp.status}")
                        return {}

                    data = await resp.json()
                    results = data.get("resultList", {}).get("result", [])

                    # 建立 DOI 到结果的映射
                    doi_to_result = {}
                    for result in results:
                        result_doi = result.get("doi", "").lower()
                        if result_doi:
                            for original_doi in dois:
                                if original_doi.lower() == result_doi:
                                    doi_to_result[original_doi] = result
                                    break

                    self.logger.info(f"批量搜索找到 {len(doi_to_result)} 个匹配的DOI")
                    return doi_to_result

        except Exception as e:
            self.logger.error(f"异步批量 Europe PMC 搜索异常: {e}")
            return {}


def create_unified_reference_service(
    logger: logging.Logger | None = None,
) -> UnifiedReferenceService:
    """创建统一参考文献服务实例"""
    return UnifiedReferenceService(logger)


# 兼容性函数
def create_reference_service(logger: logging.Logger | None = None) -> UnifiedReferenceService:
    """创建参考文献服务实例（兼容性函数）"""
    return create_unified_reference_service(logger)
