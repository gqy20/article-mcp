"""
CrossRef API服务 - 使用统一API调用
"""

import logging
from typing import Any

from .api_utils import get_api_client


class CrossRefService:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://api.crossref.org"
        self.api_client = get_api_client(logger)

    def search_works(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """搜索CrossRef学术文献"""
        try:
            url = f"{self.base_url}/works"
            params = {
                "query": query,
                "rows": max_results,
                "select": "title,author,DOI,created,member,short-container-title",
            }

            api_result = self.api_client.get(url, params=params)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            return {
                "success": True,
                "articles": self._format_articles(data.get("message", {}).get("items", [])),
                "total_count": data.get("message", {}).get("total-results", 0),
                "source": "crossref",
            }

        except Exception as e:
            self.logger.error(f"CrossRef搜索失败: {e}")
            return {
                "success": False,
                "articles": [],
                "total_count": 0,
                "source": "crossref",
                "error": str(e),
            }

    def get_work_by_doi(self, doi: str) -> dict[str, Any]:
        """通过DOI获取文献详情"""
        try:
            url = f"{self.base_url}/works/{doi}"
            api_result = self.api_client.get(url)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            article = data.get("message", {})

            return {
                "success": True,
                "article": self._format_single_article(article),
                "source": "crossref",
            }

        except Exception as e:
            self.logger.error(f"CrossRef获取详情失败: {e}")
            return {"success": False, "article": None, "source": "crossref", "error": str(e)}

    def get_references(self, doi: str, max_results: int = 20) -> dict[str, Any]:
        """获取参考文献列表"""
        try:
            url = f"{self.base_url}/works/{doi}/references"
            params = {"rows": max_results}
            api_result = self.api_client.get(url, params=params)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            references = data.get("message", {}).get("items", [])

            return {
                "success": True,
                "references": self._format_references(references),
                "total_count": len(references),
                "source": "crossref",
            }

        except Exception as e:
            self.logger.error(f"CrossRef获取参考文献失败: {e}")
            return {
                "success": False,
                "references": [],
                "total_count": 0,
                "source": "crossref",
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
        return {
            "title": self._extract_title(item.get("title") or []),
            "authors": self._extract_authors(item.get("author") or []),
            "doi": item.get("DOI"),
            "journal": (
                (item.get("short-container-title") or [""])[0]
                if item.get("short-container-title")
                else ""
            ),
            "publication_date": (item.get("created") or {}).get("date-time", ""),
            "source": "crossref",
            "raw_data": item,  # 保留原始数据用于调试
        }

    def _format_references(self, references: list[dict]) -> list[dict]:
        """格式化参考文献"""
        formatted_refs = []
        for ref in references:
            formatted_refs.append({
                "doi": ref.get("DOI"),
                "title": self._extract_title(ref.get("title") or []),
                "authors": self._extract_authors(ref.get("author") or []),
                "year": (ref.get("created") or {}).get("date-parts", [[None]])[0][0],
                "source": "crossref",
            })
        return formatted_refs

    def _extract_title(self, title_list: list) -> str:
        """提取标题"""
        return title_list[0] if title_list else ""

    def _extract_authors(self, author_list: list) -> list[str]:
        """提取作者"""
        authors = []
        for author in author_list:
            if not author:  # 跳过None值
                continue
            if "given" in author and "family" in author:
                authors.append(f"{author.get('given', '')} {author.get('family', '')}")
            elif "name" in author:
                authors.append(author["name"])
        return authors
