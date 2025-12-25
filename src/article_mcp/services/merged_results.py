"""结果合并工具 - 简单直接的合并函数"""

from functools import lru_cache
from typing import Any


def merge_articles_by_doi(articles_by_source: dict[str, list[dict]]) -> list[dict]:
    """按DOI合并文章，保留所有来源信息"""
    doi_to_articles: dict[str, list[dict]] = {}

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
    base_article = articles[0].copy()
    for article in articles[1:]:
        # 合并字段，优先选择非空值
        for key, value in article.items():
            if key not in base_article or not base_article[key]:
                base_article[key] = value

    # 从 data_sources 中提升字段到顶层
    sources_list = [a.get("source_from", "unknown") for a in articles]
    data_sources_dict = {}

    for a in articles:
        source = a.get("source_from", "unknown")
        # 如果 data_sources 已经有这个源的数据，需要合并
        if source in data_sources_dict:
            existing = data_sources_dict[source]
            # 合并新字段到现有数据（排除某些特殊字段）
            for key, value in a.items():
                if key not in ("data_sources", "source_from"):
                    if key not in existing or not existing[key]:
                        existing[key] = value
        else:
            # 复制文章数据，但排除某些特殊字段
            article_copy = {k: v for k, v in a.items() if k not in ("data_sources",)}
            data_sources_dict[source] = article_copy

    # 提升所有 data_sources 中的字段到顶层（如果顶层没有）
    for source_data in data_sources_dict.values():
        for key, value in source_data.items():
            if key not in ("data_sources", "source_from"):
                if key not in base_article or not base_article[key]:
                    base_article[key] = value

    # 处理每个文章原有的 data_sources 字段（递归提升）
    for a in articles:
        nested_data_sources = a.get("data_sources", {})
        if nested_data_sources:
            for _nested_source, nested_data in nested_data_sources.items():
                # 提升嵌套数据中的字段到顶层
                for key, value in nested_data.items():
                    if key not in ("data_sources", "source_from"):
                        if key not in base_article or not base_article[key]:
                            base_article[key] = value

    return {
        **base_article,
        "sources": sources_list,
        "data_sources": data_sources_dict,
    }


def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """简单去重，基于DOI和标题"""
    seen_dois = set()
    seen_titles = set()
    deduplicated = []

    for article in articles:
        doi = article.get("doi") or ""  # 处理 None 值
        title = article.get("title") or ""  # 处理 None 值

        doi = doi.lower() if doi else ""
        title = title.lower() if title else ""

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


def simple_rank_articles(
    articles: list[dict], source_priority: list[str] | None = None
) -> list[dict]:
    """简单的文章排序，基于数据源优先级"""
    if source_priority is None:
        source_priority = [
            "nature",
            "science",
            "cell",
            "europe_pmc",
            "pubmed",
            "crossref",
            "openalex",
            "arxiv",
        ]
    else:
        # 使用传入的优先级
        pass

    def get_priority_score(article: dict) -> int:
        # 优先使用 sources 字段
        sources = article.get("sources", [])
        if not sources:
            # 兼容旧格式：使用 source 或 source_from 字段
            source = article.get("source") or article.get("source_from", "")
            sources = [source] if source else []

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
        "merged_references": deduplicated_refs,  # 保持向后兼容
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
        "merged_citations": deduplicated_citations,  # 保持向后兼容
        "citations": deduplicated_citations,
        "total_count": len(deduplicated_citations),
        "sources_used": sources_used,
        "raw_results": citation_results,
    }


@lru_cache(maxsize=5000)
def extract_identifier_type(identifier: str) -> str:
    """提取标识符类型，支持带前缀的格式"""
    original = identifier
    identifier = identifier.strip().upper()

    # DOI检测 (支持 DOI: 前缀、URL 格式、或直接以 10. 开头)
    if (
        identifier.startswith("DOI:")
        or "//" in identifier
        or (original.startswith("10.") and "/" in original)
    ):
        return "doi"

    # PMCID检测 (支持 PMCID: 或 PMC 前缀)
    if identifier.startswith("PMCID:") or identifier.startswith("PMC"):
        return "pmcid"

    # PMID检测 (支持 PMID: 前缀，或纯数字7-8位)
    if identifier.startswith("PMID:") or (original.isdigit() and 6 <= len(original) <= 8):
        return "pmid"

    # arXiv ID检测 (支持 ARXIV: 前缀、arXiv: 前缀，或 YYMM.NNNNN 格式)
    if (
        identifier.startswith("ARXIV:")
        or original.startswith("arXiv:")
        or (
            identifier.replace(".", "").replace("V", "").isdigit()
            and len(identifier.replace(".", "").replace("V", "")) >= 8
        )
    ):
        return "arxiv_id"

    # 默认返回 unknown
    return "unknown"
