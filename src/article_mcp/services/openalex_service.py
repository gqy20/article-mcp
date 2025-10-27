"""
OpenAlex API服务 - 使用统一API调用
"""

import logging
from functools import lru_cache
from typing import Any

from .api_utils import get_api_client


class OpenAlexService:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://api.openalex.org"
        self.api_client = get_api_client(logger)

    def search_works(
        self, query: str, max_results: int = 10, filters: dict = None
    ) -> dict[str, Any]:
        """搜索OpenAlex学术文献"""
        try:
            url = f"{self.base_url}/works"
            params = {
                "search": query,
                "per-page": max_results,
                "select": "id,title,authorships,publication_year,primary_location,open_access",
            }

            if filters:
                params.update(filters)

            api_result = self.api_client.get(url, params=params)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            return {
                "success": True,
                "articles": self._format_articles(data.get("results", [])),
                "total_count": data.get("meta", {}).get("count", 0),
                "source": "openalex",
            }

        except Exception as e:
            self.logger.error(f"OpenAlex搜索失败: {e}")
            return {
                "success": False,
                "articles": [],
                "total_count": 0,
                "source": "openalex",
                "error": str(e),
            }

    def get_work_by_doi(self, doi: str) -> dict[str, Any]:
        """通过DOI获取文献详情"""
        try:
            url = f"{self.base_url}/works"
            params = {
                "filter": f"doi:{doi}",
                "select": "id,title,authorships,publication_year,primary_location,open_access",
            }

            api_result = self.api_client.get(url, params=params)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            results = data.get("results", [])

            if results:
                return {
                    "success": True,
                    "article": self._format_single_article(results[0]),
                    "source": "openalex",
                }
            else:
                return {
                    "success": False,
                    "article": None,
                    "source": "openalex",
                    "error": "未找到相关文献",
                }

        except Exception as e:
            self.logger.error(f"OpenAlex获取详情失败: {e}")
            return {"success": False, "article": None, "source": "openalex", "error": str(e)}

    def filter_open_access(self, works: list[dict]) -> list[dict]:
        """过滤开放获取文献"""
        open_access_works = []
        for work in works:
            if work.get("open_access", {}).get("is_oa", False):
                open_access_works.append(work)
        return open_access_works

    def get_citations(self, doi: str, max_results: int = 20) -> dict[str, Any]:
        """获取引用文献"""
        try:
            url = f"{self.base_url}/works"
            params = {
                "filter": f"cites:{doi}",
                "per-page": max_results,
                "select": "id,title,authorships,publication_year,primary_location",
            }

            api_result = self.api_client.get(url, params=params)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            citations = data.get("results", [])

            return {
                "success": True,
                "citations": self._format_articles(citations),
                "total_count": len(citations),
                "source": "openalex",
            }

        except Exception as e:
            self.logger.error(f"OpenAlex获取引用文献失败: {e}")
            return {
                "success": False,
                "citations": [],
                "total_count": 0,
                "source": "openalex",
                "error": str(e),
            }

    def _format_articles(self, items: list[dict]) -> list[dict]:
        """格式化文章列表"""
        articles = []
        for item in items:
            articles.append(self._format_single_article(item))
        return articles

    def _format_single_article(self, item: dict) -> dict:
        """格式化单篇文章"""
        # 提取作者信息
        authors = []
        authorships = item.get("authorships") or []
        for authorship in authorships:
            author = (authorship or {}).get("author") or {}
            if author.get("display_name"):
                authors.append(author["display_name"])

        # 提取期刊信息
        primary_location = item.get("primary_location", {})
        source = primary_location.get("source") or {}

        # 提取开放获取信息
        open_access = item.get("open_access") or {}

        return {
            "title": item.get("title", ""),
            "authors": authors,
            "doi": primary_location.get("doi"),
            "journal": source.get("display_name", ""),
            "publication_date": str(item.get("publication_year", "")),
            "open_access": {
                "is_oa": open_access.get("is_oa", False),
                "oa_url": open_access.get("oa_url", ""),
                "oa_status": open_access.get("oa_status", ""),
            },
            "source": "openalex",
            "raw_data": item,
        }
