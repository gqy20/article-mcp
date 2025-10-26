"""
统一的参考文献获取服务
整合同步和异步功能，减少代码重复
"""

import asyncio
import logging
import re
import time
from typing import Any

import aiohttp
import requests


class UnifiedReferenceService:
    """统一的参考文献获取服务类"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

        # 同步会话
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Europe-PMC-Reference-Tool/1.0"})

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
        self.cache = {}
        self.cache_expiry = {}

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

    # 同步方法
    def get_references_crossref_sync(self, doi: str) -> list[dict[str, Any]] | None:
        """同步获取 Crossref 参考文献"""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            self.logger.info(f"请求 Crossref: {url}")

            resp = self.session.get(url, timeout=20)
            if resp.status_code != 200:
                self.logger.warning(f"Crossref 失败，状态码: {resp.status_code}")
                return None

            message = resp.json().get("message", {})
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
                        "title": ref.get("article-title") or ref.get("title"),
                        "authors": authors,
                        "journal": ref.get("journal-title") or ref.get("journal"),
                        "year": ref.get("year"),
                        "doi": ref.get("DOI") or ref.get("doi"),
                        "source": "crossref",
                    }
                )

            self.logger.info(f"Crossref 获取到 {len(references)} 条参考文献")
            return references

        except Exception as e:
            self.logger.error(f"Crossref 异常: {e}")
            return None

    def search_europe_pmc_by_doi_sync(self, doi: str) -> dict[str, Any] | None:
        """同步搜索 Europe PMC"""
        try:
            query = f'DOI:"{doi}"'
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

            params = {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": 1,
                "cursorMark": "*",
            }

            self.logger.info(f"Europe PMC 搜索 DOI: {doi}")
            resp = self.session.get(url, params=params, timeout=15)

            if resp.status_code != 200:
                self.logger.warning(f"Europe PMC 搜索失败: {resp.status_code}")
                return None

            data = resp.json()
            results = data.get("resultList", {}).get("result", [])

            if not results:
                self.logger.info(f"Europe PMC 未找到: {doi}")
                return None

            return results[0]

        except Exception as e:
            self.logger.error(f"Europe PMC 搜索异常: {e}")
            return None

    def get_references_by_doi_sync(self, doi: str) -> dict[str, Any]:
        """同步获取参考文献"""
        start_time = time.time()

        try:
            self.logger.info(f"开始同步获取 DOI {doi} 的参考文献")

            # 1. 从 Crossref 获取参考文献列表
            references = self.get_references_crossref_sync(doi)

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

            # 2. 使用 Europe PMC 补全信息
            enriched_references = []
            for ref in references:
                doi_ref = ref.get("doi")
                if doi_ref and not (ref.get("abstract") or ref.get("pmid")):
                    self.logger.info(f"使用 Europe PMC 补全: {doi_ref}")

                    europe_pmc_info = self.search_europe_pmc_by_doi_sync(doi_ref)
                    if europe_pmc_info:
                        formatted_info = self._format_europe_pmc_metadata(europe_pmc_info)
                        for key, value in formatted_info.items():
                            if value and not ref.get(key):
                                ref[key] = value

                    time.sleep(0.2)  # 控制频率

                enriched_references.append(ref)

            # 3. 去重处理
            final_references = self.deduplicate_references(enriched_references)

            processing_time = time.time() - start_time

            return {
                "references": final_references,
                "message": f"成功获取 {len(final_references)} 条参考文献 (同步版本)",
                "error": None,
                "total_count": len(final_references),
                "enriched_count": len(
                    [r for r in final_references if r.get("source") == "europe_pmc"]
                ),
                "processing_time": round(processing_time, 2),
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"同步获取参考文献异常: {e}")
            return {
                "references": [],
                "message": "获取参考文献失败",
                "error": str(e),
                "total_count": 0,
                "processing_time": round(processing_time, 2),
            }

    # 异步方法（精简版）
    async def get_references_by_doi_async(self, doi: str) -> dict[str, Any]:
        """异步获取参考文献（使用同步版本的简化实现）"""
        # 为了保持500行限制，使用线程池运行同步版本
        import concurrent.futures

        def run_sync():
            return self.get_references_by_doi_sync(doi)

        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_sync)
                result["message"] = result.get("message", "").replace("同步版本", "异步版本")
                return result
        except Exception as e:
            self.logger.error(f"异步获取参考文献异常: {e}")
            return {
                "references": [],
                "message": "获取参考文献失败",
                "error": str(e),
                "total_count": 0,
            }

    # 新增批量查询方法
    def batch_search_europe_pmc_by_dois(self, dois: list[str]) -> dict[str, dict[str, Any]]:
        """批量搜索 Europe PMC - 使用 OR 操作符"""
        if not dois:
            return {}

        try:
            # 限制批量大小
            if len(dois) > self.max_batch_size:
                self.logger.warning(
                    f"DOI数量 {len(dois)} 超过最大批量大小 {self.max_batch_size}，将进行分批处理"
                )
                # 分批处理
                all_results = {}
                for i in range(0, len(dois), self.max_batch_size):
                    batch = dois[i : i + self.max_batch_size]
                    batch_results = self.batch_search_europe_pmc_by_dois(batch)
                    all_results.update(batch_results)
                return all_results

            # 构建 OR 操作符查询
            doi_queries = [f'DOI:"{doi}"' for doi in dois]
            query = " OR ".join(doi_queries)

            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            params = {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": len(dois) * 2,  # 确保能获取所有结果
                "cursorMark": "*",
            }

            self.logger.info(f"批量搜索 Europe PMC: {len(dois)} 个 DOI")

            resp = self.session.get(url, params=params, timeout=self.batch_timeout)

            if resp.status_code != 200:
                self.logger.warning(f"批量 Europe PMC 搜索失败: {resp.status_code}")
                return {}

            data = resp.json()
            results = data.get("resultList", {}).get("result", [])

            # 建立 DOI 到结果的映射
            doi_to_result = {}
            for result in results:
                result_doi = result.get("doi", "").lower()
                if result_doi:
                    # 查找匹配的原始DOI
                    for original_doi in dois:
                        if original_doi.lower() == result_doi:
                            doi_to_result[original_doi] = result
                            break

            self.logger.info(f"批量搜索找到 {len(doi_to_result)} 个匹配的DOI")
            return doi_to_result

        except Exception as e:
            self.logger.error(f"批量 Europe PMC 搜索异常: {e}")
            return {}

    def get_references_batch_optimized(self, doi: str) -> dict[str, Any]:
        """批量优化版本的参考文献获取"""
        start_time = time.time()

        try:
            self.logger.info(f"开始批量优化获取 DOI {doi} 的参考文献")

            # 1. 从 Crossref 获取参考文献列表
            references = self.get_references_crossref_sync(doi)

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

            # 2. 收集所有需要补全的DOI
            dois_to_enrich = []
            doi_to_ref_index = {}  # DOI到参考文献索引的映射

            for i, ref in enumerate(references):
                doi_ref = ref.get("doi")
                if doi_ref and not (ref.get("abstract") or ref.get("pmid")):
                    dois_to_enrich.append(doi_ref)
                    doi_to_ref_index[doi_ref] = i

            self.logger.info(f"需要补全信息的DOI数量: {len(dois_to_enrich)}")

            # 3. 使用批量查询补全信息
            enrichment_count = 0
            if dois_to_enrich:
                batch_results = self.batch_search_europe_pmc_by_dois(dois_to_enrich)

                for doi_ref, europe_pmc_info in batch_results.items():
                    if doi_ref in doi_to_ref_index:
                        ref_index = doi_to_ref_index[doi_ref]
                        formatted_info = self._format_europe_pmc_metadata(europe_pmc_info)

                        # 补全信息
                        for key, value in formatted_info.items():
                            if value and not references[ref_index].get(key):
                                references[ref_index][key] = value

                        enrichment_count += 1

            # 4. 去重处理
            final_references = self.deduplicate_references(references)

            processing_time = time.time() - start_time

            return {
                "references": final_references,
                "message": f"成功获取 {len(final_references)} 条参考文献 (批量优化版本 - {enrichment_count} 条已补全)",
                "error": None,
                "total_count": len(final_references),
                "enriched_count": enrichment_count,
                "batch_dois_processed": len(dois_to_enrich),
                "processing_time": round(processing_time, 2),
                "performance_note": f"批量处理 {len(dois_to_enrich)} 个DOI，预计比传统方法快 5-10 倍",
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"批量优化获取参考文献异常: {e}")
            return {
                "references": [],
                "message": "获取参考文献失败",
                "error": str(e),
                "total_count": 0,
                "processing_time": round(processing_time, 2),
            }


def create_unified_reference_service(
    logger: logging.Logger | None = None,
) -> UnifiedReferenceService:
    """创建统一参考文献服务实例"""
    return UnifiedReferenceService(logger)


# 兼容性函数
def create_reference_service(logger: logging.Logger | None = None) -> UnifiedReferenceService:
    """创建参考文献服务实例（兼容性函数）"""
    return create_unified_reference_service(logger)


def get_references_by_doi_sync(doi: str, logger: logging.Logger | None = None) -> dict[str, Any]:
    """同步调用参考文献获取（兼容性函数）"""
    service = create_unified_reference_service(logger)
    return asyncio.run(service.get_references_by_doi_async(doi))
