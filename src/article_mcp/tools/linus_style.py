"""
Linus风格的超简化实现 - "Talk is cheap. Show me the code."
3个工具解决所有问题，没有过度抽象。
"""

import logging
from functools import lru_cache
from typing import Any

import requests


class SimpleLiteratureService:
    """简单的文献服务 - 不搞过度抽象"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 简单的缓存，不搞复杂的过期机制
        self._cache = {}

    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键 - 简单直接"""
        return f"{method}:{hash(str(sorted(kwargs.items())))}"

    def _cached_request(self, url: str, cache_key: str = None) -> dict:
        """带缓存的请求 - 不搞复杂的过期"""
        if cache_key and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if cache_key:
                self._cache[cache_key] = data
            return data
        except Exception as e:
            self.logger.error(f"请求失败 {url}: {e}")
            return {"error": str(e)}

    @lru_cache(maxsize=1000)
    def search(self, query: str, source: str = "all", max_results: int = 20) -> list[dict]:
        """
        统一搜索 - 不搞花哨的多源合并
        一个函数搞定所有搜索需求
        """
        if source == "all":
            # 简单轮询，不搞并发
            results = []
            for src in ["pubmed", "arxiv", "crossref"]:
                try:
                    src_results = self._search_single_source(query, src, max_results // 3)
                    results.extend(src_results)
                except:
                    continue  # 某个源失败不影响其他源
            return results[:max_results]
        else:
            return self._search_single_source(query, source, max_results)

    def _search_single_source(self, query: str, source: str, max_results: int) -> list[dict]:
        """搜索单个数据源 - 简单直接"""
        if source == "pubmed":
            return self._search_pubmed(query, max_results)
        elif source == "arxiv":
            return self._search_arxiv(query, max_results)
        elif source == "crossref":
            return self._search_crossref(query, max_results)
        else:
            return []

    def _search_pubmed(self, query: str, max_results: int) -> list[dict]:
        """PubMed搜索 - 不搞复杂的ESearch+EFetch"""
        # 简化实现：使用Europe PMC的PubMed接口
        url = "https://www.ebi.ac.uk/europepmc/api/search"
        params = {
            "query": query,
            "resulttype": "core",
            "format": "json",
            "size": max_results,
            "src": "med",
        }

        cache_key = self._get_cache_key("pubmed_search", query=query, max_results=max_results)
        data = self._cached_request(url, cache_key)

        if "error" in data:
            return []

        results = []
        for result in data.get("resultList", {}).get("result", []):
            results.append(
                {
                    "title": result.get("title", ""),
                    "authors": [
                        a.get("fullName", "")
                        for a in result.get("authorList", {}).get("author", [])
                    ],
                    "journal": result.get("journalInfo", {}).get("journal", {}).get("title", ""),
                    "year": result.get("journalInfo", {}).get("yearOfPublication", ""),
                    "doi": result.get("doi", ""),
                    "pmid": result.get("pmid", ""),
                    "abstract": result.get("abstractText", ""),
                    "source": "pubmed",
                }
            )
        return results

    def _search_arxiv(self, query: str, max_results: int) -> list[dict]:
        """arXiv搜索 - 直接调用API，不搞复杂封装"""
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        cache_key = self._get_cache_key("arxiv_search", query=query, max_results=max_results)

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()

            # 简单XML解析，不搞复杂的命名空间处理
            import xml.etree.ElementTree as ET

            root = ET.fromstring(resp.text)

            results = []
            for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry")[:max_results]:
                title = entry.find(".//{http://www.w3.org/2005/Atom}title")
                summary = entry.find(".//{http://www.w3.org/2005/Atom}summary")
                published = entry.find(".//{http://www.w3.org/2005/Atom}published")

                # 提取arXiv ID
                arxiv_id = ""
                id_elem = entry.find(".//{http://www.w3.org/2005/Atom}id")
                if id_elem is not None:
                    arxiv_id = id_elem.text.split("/")[-1]

                results.append(
                    {
                        "title": title.text if title is not None else "",
                        "abstract": summary.text if summary is not None else "",
                        "year": published.text[:4] if published is not None else "",
                        "arxiv_id": arxiv_id,
                        "source": "arxiv",
                    }
                )

            if cache_key:
                self._cache[cache_key] = {"results": results}
            return results

        except Exception as e:
            self.logger.error(f"arXiv搜索失败: {e}")
            return []

    def _search_crossref(self, query: str, max_results: int) -> list[dict]:
        """CrossRef搜索 - 简单直接"""
        url = "https://api.crossref.org/works"
        params = {"query": query, "rows": max_results, "sort": "relevance", "order": "desc"}

        cache_key = self._get_cache_key("crossref_search", query=query, max_results=max_results)
        data = self._cached_request(url, cache_key)

        if "error" in data:
            return []

        results = []
        for item in data.get("message", {}).get("items", []):
            results.append(
                {
                    "title": " ".join(item.get("title", [])),
                    "authors": [
                        f"{a.get('given', '')} {a.get('family', '')}"
                        for a in item.get("author", [])
                    ],
                    "year": item.get("published-print", {}).get("date-parts", [[""]])[0][0][:4],
                    "doi": item.get("DOI", ""),
                    "journal": item.get("container-title", [""])[0],
                    "source": "crossref",
                }
            )
        return results

    def get_details(self, identifier: str, id_type: str = "auto") -> dict | None:
        """
        获取详情 - 一个函数处理所有类型
        不搞复杂的类型推断，直接尝试
        """
        # 简单的标识符识别
        if identifier.startswith("10.") and "/" in identifier:
            return self._get_by_doi(identifier)
        elif identifier.isdigit():
            return self._get_by_pmid(identifier)
        elif identifier.startswith("arxiv:") or "." in identifier:
            arxiv_id = identifier.replace("arxiv:", "")
            return self._get_by_arxiv_id(arxiv_id)
        else:
            # 不确定类型，依次尝试
            for method in [self._get_by_doi, self._get_by_pmid, self._get_by_arxiv_id]:
                result = method(identifier)
                if result:
                    return result
            return None

    def _get_by_doi(self, doi: str) -> dict | None:
        """通过DOI获取 - 简单直接"""
        # 使用CrossRef
        url = f"https://api.crossref.org/works/{doi}"
        cache_key = f"doi:{doi}"
        data = self._cached_request(url, cache_key)

        if "error" in data:
            return None

        item = data.get("message", {})
        return {
            "title": " ".join(item.get("title", [])),
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}" for a in item.get("author", [])
            ],
            "year": item.get("published-print", {}).get("date-parts", [[""]])[0][0][:4],
            "doi": item.get("DOI", ""),
            "journal": item.get("container-title", [""])[0],
            "abstract": item.get("abstract", ""),
            "source": "crossref",
        }

    def _get_by_pmid(self, pmid: str) -> dict | None:
        """通过PMID获取 - 使用Europe PMC"""
        url = f"https://www.ebi.ac.uk/europepmc/api/article/PMID:{pmid}?format=json"
        cache_key = f"pmid:{pmid}"
        data = self._cached_request(url, cache_key)

        if "error" in data:
            return None

        result = data.get("result", {})
        return {
            "title": result.get("title", ""),
            "authors": [
                a.get("fullName", "") for a in result.get("authorList", {}).get("author", [])
            ],
            "year": result.get("journalInfo", {}).get("yearOfPublication", ""),
            "doi": result.get("doi", ""),
            "pmid": result.get("pmid", ""),
            "journal": result.get("journalInfo", {}).get("journal", {}).get("title", ""),
            "abstract": result.get("abstractText", ""),
            "source": "pubmed",
        }

    def _get_by_arxiv_id(self, arxiv_id: str) -> dict | None:
        """通过arXiv ID获取"""
        results = self._search_arxiv(f"id:{arxiv_id}", 1)
        return results[0] if results else None

    def get_references(self, identifier: str, id_type: str = "auto") -> list[dict]:
        """获取参考文献 - 简单实现"""
        details = self.get_details(identifier, id_type)
        if not details or details.get("source") != "pubmed":
            return []  # 目前只支持PubMed参考文献

        pmid = details.get("pmid")
        if not pmid:
            return []

        url = f"https://www.ebi.ac.uk/europepmc/api/article/PMID:{pmid}?format=json"
        cache_key = f"refs:{pmid}"
        data = self._cached_request(url, cache_key)

        if "error" in data:
            return []

        result = data.get("result", {})
        references = []

        # 处理参考文献列表
        ref_list = result.get("referenceList", [])
        for ref in ref_list[:50]:  # 限制数量，避免过大
            ref_info = {
                "title": ref.get("title", ""),
                "authors": [
                    a.get("fullName", "") for a in ref.get("authorList", {}).get("author", [])
                ],
                "year": ref.get("year", ""),
                "doi": ref.get("doi", ""),
                "pmid": ref.get("pmid", ""),
                "journal": ref.get("source", ""),
                "unstructured": ref.get("unstructured", ""),
            }
            references.append(ref_info)

        return references


# 全局服务实例 - 简单直接
_simple_service = None


def get_simple_service():
    """获取简单服务实例"""
    global _simple_service
    if _simple_service is None:
        _simple_service = SimpleLiteratureService()
    return _simple_service


def register_linus_tools(mcp):
    """注册Linus风格的工具 - 3个工具解决所有问题"""
    service = get_simple_service()

    @mcp.tool()
    def search(query: str, source: str = "all", max_results: int = 20) -> dict[str, Any]:
        """
        搜索文献 - 一个工具搞定所有搜索
        """
        try:
            results = service.search(query, source, max_results)
            return {
                "success": True,
                "query": query,
                "source": source,
                "results": results,
                "total": len(results),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "total": 0}

    @mcp.tool()
    def get(identifier: str, id_type: str = "auto") -> dict[str, Any]:
        """
        获取文献详情 - 一个工具搞定所有获取
        """
        try:
            details = service.get_details(identifier, id_type)
            if details:
                return {"success": True, "identifier": identifier, "details": details}
            else:
                return {"success": False, "error": f"未找到文献: {identifier}", "details": None}
        except Exception as e:
            return {"success": False, "error": str(e), "details": None}

    @mcp.tool()
    def references(identifier: str, id_type: str = "auto") -> dict[str, Any]:
        """
        获取参考文献 - 一个工具搞定参考文献
        """
        try:
            refs = service.get_references(identifier, id_type)
            return {
                "success": True,
                "identifier": identifier,
                "references": refs,
                "total": len(refs),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "references": [], "total": 0}

    return [search, get, references]
