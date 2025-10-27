"""
结果合并工具 - 简单直接的合并函数
"""

from functools import lru_cache
from typing import Any


def merge_articles_by_doi(articles_by_source: dict[str, list[dict]]) -> list[dict]:
    """按DOI合并文章，保留所有来源信息"""
    doi_to_articles = {}

    # 收集所有文章，按DOI分组
    for source, articles in articles_by_source.items():
        for article in articles:
            doi = article.get("doi", "")
            if doi:
                if doi not in doi_to_articles:
                    doi_to_articles[doi] = []
                article["source_from"] = source
                doi_to_articles[doi].append(article)

    # 合并同一DOI的多源文章
    merged_articles = []
    for articles in doi_to_articles.values():
        merged = merge_same_doi_articles(articles)
        merged_articles.append(merged)

    # 添加无DOI的文章
    for source, articles in articles_by_source.items():
        for article in articles:
            if not article.get("doi") and article not in [
                a for merged in merged_articles for a in merged.get("sources", [])
            ]:
                article["sources"] = [source]
                merged_articles.append(article)

    return merged_articles


def merge_same_doi_articles(articles: list[dict]) -> dict:
    """合并同一DOI的多源文章"""
    if len(articles) == 1:
        article = articles[0]
        source_from = article.get("source_from", "unknown")
        return {
            **article,
            "sources": [source_from],
            "data_sources": {source_from: article},
        }

    # 选择最完整的数据作为基础
    base_article = articles[0]
    for article in articles[1:]:
        # 合并字段，优先选择非空值
        for key, value in article.items():
            if key not in base_article or not base_article[key]:
                base_article[key] = value

    return {
        **base_article,
        "sources": [a.get("source_from", "unknown") for a in articles],
        "data_sources": {a.get("source_from", "unknown"): a for a in articles},
    }


def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """简单去重，基于DOI和标题"""
    seen_dois = set()
    seen_titles = set()
    deduplicated = []

    for article in articles:
        doi = article.get("doi", "").lower()
        title = article.get("title", "").lower()

        # 检查DOI去重
        if doi and doi in seen_dois:
            continue

        # 检查标题去重（仅用于无DOI的文章）
        if not doi and title and title in seen_titles:
            continue

        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)

        deduplicated.append(article)

    return deduplicated


def simple_rank_articles(articles: list[dict], source_priority: list[str] = None) -> list[dict]:
    """简单的文章排序，基于数据源优先级"""
    if source_priority is None:
        source_priority = ["europe_pmc", "pubmed", "crossref", "openalex", "arxiv"]

    def get_priority_score(article):
        sources = article.get("sources", [article.get("source_from", "")])
        for i, priority_source in enumerate(source_priority):
            if priority_source in sources:
                return i
        return len(source_priority)  # 未知优先级排在最后

    return sorted(articles, key=get_priority_score)


def merge_reference_results(reference_results: dict[str, dict]) -> dict[str, Any]:
    """合并多个数据源的参考文献结果"""
    all_references = []
    sources_used = []
    total_count = 0

    for source, result in reference_results.items():
        if result.get("success", False):
            references = result.get("references", [])
            all_references.extend(references)
            sources_used.append(source)
            total_count += result.get("total_count", 0)

    # 去重并排序
    deduplicated_refs = deduplicate_references(all_references)

    return {
        "success": len(deduplicated_refs) > 0,
        "references": deduplicated_refs,
        "total_count": len(deduplicated_refs),
        "sources_used": sources_used,
        "raw_results": reference_results,
    }


def deduplicate_references(references: list[dict]) -> list[dict]:
    """参考文献去重，基于DOI和标题"""
    seen = set()
    deduplicated = []

    for ref in references:
        # 创建唯一标识
        doi = ref.get("doi", "").lower()
        title = ref.get("title", "").lower()

        # DOI优先作为唯一标识
        identifier = doi if doi else title

        if identifier and identifier not in seen:
            seen.add(identifier)
            deduplicated.append(ref)

    return deduplicated


def merge_citation_results(citation_results: dict[str, dict]) -> dict[str, Any]:
    """合并多个数据源的引用文献结果"""
    all_citations = []
    sources_used = []
    total_count = 0

    for source, result in citation_results.items():
        if result.get("success", False):
            citations = result.get("citations", [])
            all_citations.extend(citations)
            sources_used.append(source)
            total_count += result.get("total_count", 0)

    # 去重并排序
    deduplicated_citations = deduplicate_articles(all_citations)

    return {
        "success": len(deduplicated_citations) > 0,
        "citations": deduplicated_citations,
        "total_count": len(deduplicated_citations),
        "sources_used": sources_used,
        "raw_results": citation_results,
    }


@lru_cache(maxsize=5000)
def extract_identifier_type(identifier: str) -> str:
    """提取标识符类型"""
    identifier = identifier.strip()

    # DOI检测
    if identifier.startswith("10.") and "/" in identifier:
        return "doi"

    # PMID检测 (纯数字，通常7-8位)
    if identifier.isdigit() and 6 <= len(identifier) <= 8:
        return "pmid"

    # PMCID检测
    if identifier.startswith("PMC") and identifier[3:].isdigit():
        return "pmcid"

    # arXiv ID检测
    if identifier.startswith("arXiv:") or (
        "." in identifier
        and identifier.replace(".", "").replace("-", "").replace("_", "").isalnum()
    ):
        return "arxiv_id"

    # 默认尝试DOI
    return "doi"
