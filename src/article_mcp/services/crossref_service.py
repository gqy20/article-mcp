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
            import urllib.parse

            # 对DOI进行URL编码处理，保留斜杠
            encoded_doi = urllib.parse.quote(doi, safe='/')
            url = f"{self.base_url}/works/{encoded_doi}"
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
            import urllib.parse

            # CrossRef API: 参考文献数据包含在主查询结果中
            # 对DOI进行URL编码处理，保留斜杠
            encoded_doi = urllib.parse.quote(doi, safe='/')
            url = f"{self.base_url}/works/{encoded_doi}"
            # 简化API调用，不使用select参数避免400错误
            api_result = self.api_client.get(url)

            if not api_result.get("success", False):
                raise Exception(api_result.get("error", "API调用失败"))

            data = api_result.get("data", {})
            work_data = data.get("message", {})
            references = work_data.get("reference", [])

            return {
                "success": True,
                "references": self._format_references(references[:max_results]),
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
            if not ref:  # 跳过空引用
                continue

            # 处理CrossRef参考文献格式
            formatted_ref = {
                "doi": ref.get("DOI"),
                "title": ref.get("unstructured", ""),  # 非结构化文本通常是标题
                "authors": self._extract_ref_authors(ref),
                "year": self._extract_ref_year(ref),
                "journal": ref.get("journal-title", ""),
                "volume": ref.get("volume"),
                "issue": ref.get("issue"),
                "page": ref.get("first-page"),
                "source": "crossref",
            }

            # 如果没有结构化文本但有其他信息，尝试构建标题
            if not formatted_ref["title"] and ref.get("article-title"):
                formatted_ref["title"] = ref.get("article-title", "")

            formatted_refs.append(formatted_ref)
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

    def _extract_ref_authors(self, ref: dict) -> list[str]:
        """提取参考文献的作者"""
        authors = []
        if "author" in ref:
            author_list = ref["author"]
            if isinstance(author_list, list):
                for author in author_list:
                    if isinstance(author, dict):
                        if "given" in author and "family" in author:
                            authors.append(f"{author.get('given', '')} {author.get('family', '')}")
                        elif "family" in author:
                            authors.append(author.get('family', ''))
                        elif "name" in author:
                            authors.append(author["name"])
        return authors

    def _extract_ref_year(self, ref: dict) -> str:
        """提取参考文献的年份"""
        # 尝试从不同字段提取年份
        year = ""

        # 方法1: 直接的year字段
        if "year" in ref:
            year = str(ref["year"])

        # 方法2: 从created date-parts提取
        elif "created" in ref and "date-parts" in ref["created"]:
            date_parts = ref["created"]["date-parts"]
            if date_parts and len(date_parts) > 0:
                year = str(date_parts[0][0])

        # 方法3: 从published date-parts提取
        elif "published" in ref and "date-parts" in ref["published"]:
            date_parts = ref["published"]["date-parts"]
            if date_parts and len(date_parts) > 0:
                year = str(date_parts[0][0])

        # 方法4: 从published-print date-parts提取
        elif "published-print" in ref and "date-parts" in ref["published-print"]:
            date_parts = ref["published-print"]["date-parts"]
            if date_parts and len(date_parts) > 0:
                year = str(date_parts[0][0])

        return year
