"""
文献关系分析工具 - 核心工具4
"""

import logging
import time
from typing import Any

# 全局服务实例
_relation_services = None


def register_relation_tools(mcp, services, logger):
    """注册文献关系分析工具"""
    global _relation_services
    _relation_services = services

    @mcp.tool()
    def get_literature_relations(
        identifier: str,
        id_type: str = "auto",
        relation_types: list[str] = ["references", "similar", "citing"],
        max_results: int = 20,
        sources: list[str] = ["europe_pmc", "pubmed"],
    ) -> dict[str, Any]:
        """获取文献关联信息工具

        功能说明：
        - 获取指定文献的关联信息
        - 支持参考文献、相似文献、引用文献
        - 多数据源合并结果

        参数说明：
        - identifier: 文献标识符
        - id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
        - relation_types: 关系类型列表 ["references", "similar", "citing"]
        - max_results: 每种关系类型最大返回数
        - sources: 数据源列表

        返回格式：
        {
            "success": true,
            "identifier": "10.1234/example",
            "relations": {
                "references": [...],
                "similar": [...],
                "citing": [...]
            },
            "statistics": {...},
            "processing_time": 3.45
        }
        """
        try:
            if not identifier or not identifier.strip():
                return {
                    "success": False,
                    "error": "文献标识符不能为空",
                    "identifier": identifier,
                    "relations": {},
                    "statistics": {},
                    "processing_time": 0,
                }

            start_time = time.time()
            relations = {}
            statistics = {}

            # 自动识别标识符类型
            if id_type == "auto":
                from ..services.merged_results import extract_identifier_type

                id_type = extract_identifier_type(identifier.strip())

            # 处理每种关系类型
            for relation_type in relation_types:
                try:
                    if relation_type == "references":
                        result = _get_references(
                            identifier.strip(), id_type, max_results, sources, logger
                        )
                        relations["references"] = result.get("references", [])
                        statistics["references_count"] = len(relations["references"])

                    elif relation_type == "similar":
                        result = _get_similar_articles(
                            identifier.strip(), id_type, max_results, sources, logger
                        )
                        relations["similar"] = result.get("similar_articles", [])
                        statistics["similar_count"] = len(relations["similar"])

                    elif relation_type == "citing":
                        result = _get_citing_articles(
                            identifier.strip(), id_type, max_results, sources, logger
                        )
                        relations["citing"] = result.get("citing_articles", [])
                        statistics["citing_count"] = len(relations["citing"])

                    else:
                        logger.warning(f"不支持的关系类型: {relation_type}")

                except Exception as e:
                    logger.error(f"获取 {relation_type} 关系异常: {e}")
                    relations[relation_type] = []
                    statistics[f"{relation_type}_count"] = 0

            processing_time = round(time.time() - start_time, 2)

            # 计算总体统计
            total_relations = sum(statistics.values())
            found_relations = sum(1 for v in relations.values() if v)

            return {
                "success": found_relations > 0,
                "identifier": identifier.strip(),
                "id_type": id_type,
                "relations": relations,
                "statistics": {
                    **statistics,
                    "total_relations": total_relations,
                    "found_relation_types": found_relations,
                },
                "processing_time": processing_time,
                "relation_types_requested": relation_types,
                "sources_used": sources,
            }

        except Exception as e:
            logger.error(f"获取文献关系异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "identifier": identifier,
                "relations": {},
                "statistics": {},
                "processing_time": 0,
            }

    @mcp.tool()
    def analyze_literature_network(
        identifiers: list[str],
        analysis_type: str = "comprehensive",
        max_depth: int = 1,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """文献网络分析工具

        功能说明：
        - 分析多个文献之间的关联网络
        - 支持引用网络、合作网络分析
        - 可视化文献之间的关系

        参数说明：
        - identifiers: 文献标识符列表
        - analysis_type: 分析类型 ["comprehensive", "citation", "collaboration"]
        - max_depth: 分析深度（1表示直接关系，2表示间接关系）
        - max_results: 最大结果数

        返回格式：
        {
            "success": true,
            "network_data": {
                "nodes": [...],
                "edges": [...],
                "clusters": {...}
            },
            "analysis_metrics": {...},
            "processing_time": 8.76
        }
        """
        try:
            if not identifiers or len(identifiers) == 0:
                return {
                    "success": False,
                    "error": "文献标识符列表不能为空",
                    "network_data": {"nodes": [], "edges": [], "clusters": {}},
                    "analysis_metrics": {},
                    "processing_time": 0,
                }

            start_time = time.time()

            # 限制分析数量以避免性能问题
            if len(identifiers) > 10:
                identifiers = identifiers[:10]
                logger.warning("文献数量过多，限制为10篇进行分析")

            network_data = {"nodes": [], "edges": [], "clusters": {}}

            # 创建节点（文献）
            for i, identifier in enumerate(identifiers):
                node = {
                    "id": identifier.strip(),
                    "label": f"Paper {i+1}",
                    "type": "seed",
                    "metadata": {"identifier": identifier.strip()},
                }
                network_data["nodes"].append(node)

            # 分析关系并创建边
            edges = []
            if analysis_type in ["comprehensive", "citation"]:
                # 引用关系分析
                citation_edges = _analyze_citation_network(
                    identifiers, max_depth, max_results, logger
                )
                edges.extend(citation_edges)

            if analysis_type in ["comprehensive", "collaboration"]:
                # 合作关系分析
                collaboration_edges = _analyze_collaboration_network(
                    identifiers, max_results, logger
                )
                edges.extend(collaboration_edges)

            network_data["edges"] = edges

            # 简单聚类分析
            if edges:
                network_data["clusters"] = _detect_communities(network_data)

            processing_time = round(time.time() - start_time, 2)

            # 计算分析指标
            analysis_metrics = {
                "total_nodes": len(network_data["nodes"]),
                "total_edges": len(network_data["edges"]),
                "network_density": (
                    len(edges) / (len(identifiers) * (len(identifiers) - 1))
                    if len(identifiers) > 1
                    else 0
                ),
                "clusters_found": len(network_data["clusters"]),
                "analysis_depth": max_depth,
                "papers_analyzed": len(identifiers),
            }

            return {
                "success": True,
                "network_data": network_data,
                "analysis_metrics": analysis_metrics,
                "processing_time": processing_time,
                "analysis_type": analysis_type,
            }

        except Exception as e:
            logger.error(f"文献网络分析异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "network_data": {"nodes": [], "edges": [], "clusters": {}},
                "analysis_metrics": {},
                "processing_time": 0,
            }

    return [get_literature_relations, analyze_literature_network]


def _get_references(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> dict[str, Any]:
    """获取参考文献"""
    try:
        if not _relation_services:
            return {"references": []}

        # 使用Europe PMC获取参考文献
        if "europe_pmc" in _relation_services:
            service = _relation_services["europe_pmc"]
            result = service.fetch(identifier, id_type=id_type)

            if result.get("success", False):
                article = result.get("article", {})
                references = article.get("references", [])

                # 限制结果数量
                if len(references) > max_results:
                    references = references[:max_results]

                return {"references": references}

        return {"references": []}

    except Exception as e:
        logger.error(f"获取参考文献异常: {e}")
        return {"references": []}


def _get_similar_articles(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> dict[str, Any]:
    """获取相似文献 - 基于标题关键词相似度匹配"""
    try:
        if not _relation_services:
            return {"similar_articles": []}

        # 先获取目标文献详情
        target_article = _get_target_article_details(identifier, id_type, logger)
        if not target_article:
            return {"similar_articles": []}

        # 提取关键词
        keywords = _extract_keywords(target_article.get("title", ""))
        if not keywords:
            return {"similar_articles": []}

        # 使用关键词搜索相似文献
        similar_articles = []
        search_query = " ".join(keywords[:3])  # 使用前3个关键词

        if "europe_pmc" in _relation_services:
            service = _relation_services["europe_pmc"]
            result = service.search(search_query, max_results=max_results * 2)

            if result.get("success", False):
                articles = result.get("articles", [])
                # 排除目标文献本身
                similar_articles = [
                    article
                    for article in articles
                    if article.get("doi", "") != target_article.get("doi", "")
                    and article.get("pmid", "") != target_article.get("pmid", "")
                ][:max_results]

        return {"similar_articles": similar_articles}

    except Exception as e:
        logger.error(f"获取相似文献异常: {e}")
        return {"similar_articles": []}


def _get_target_article_details(identifier: str, id_type: str, logger) -> dict | None:
    """获取目标文献详情"""
    try:
        if "europe_pmc" in _relation_services:
            service = _relation_services["europe_pmc"]
            result = service.fetch(identifier, id_type=id_type)

            if result.get("success", False):
                return result.get("article")
        return None
    except Exception as e:
        logger.error(f"获取目标文献详情异常: {e}")
        return None


def _extract_keywords(title: str) -> list[str]:
    """从标题中提取关键词 - 简单的关键词提取"""
    import re

    # 移除常见的停用词
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "study",
        "studies",
        "analysis",
        "research",
        "investigation",
        "investigations",
        "paper",
        "papers",
        "article",
        "articles",
    }

    # 提取单词（包含连字符的词）
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]*\b", title.lower())

    # 过滤停用词和短词
    keywords = [word.strip("-") for word in words if len(word) > 2 and word not in stop_words]

    return keywords


def _get_citing_articles(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> dict[str, Any]:
    """获取引用文献 - 使用CrossRef citation API"""
    try:
        if not _relation_services:
            return {"citing_articles": []}

        # 先获取目标文献的DOI
        target_doi = _get_doi_from_identifier(identifier, id_type, logger)
        if not target_doi:
            return {"citing_articles": []}

        # 使用CrossRef citation API获取引用文献
        citing_articles = _fetch_citing_articles_from_crossref(target_doi, max_results, logger)

        return {"citing_articles": citing_articles}

    except Exception as e:
        logger.error(f"获取引用文献异常: {e}")
        return {"citing_articles": []}


def _get_doi_from_identifier(identifier: str, id_type: str, logger) -> str | None:
    """从标识符获取DOI"""
    try:
        # 如果已经是DOI格式，直接返回
        if id_type == "doi" or (identifier.startswith("10.") and "/" in identifier):
            return identifier

        # 通过其他标识符获取DOI
        if "europe_pmc" in _relation_services:
            service = _relation_services["europe_pmc"]
            result = service.fetch(identifier, id_type=id_type)

            if result.get("success", False):
                article = result.get("article", {})
                doi = article.get("doi", "")
                if doi:
                    return doi

        return None
    except Exception as e:
        logger.error(f"获取DOI异常: {e}")
        return None


def _fetch_citing_articles_from_crossref(doi: str, max_results: int, logger) -> list[dict]:
    """从CrossRef获取引用文献"""
    try:
        import requests

        # CrossRef citation API
        url = f"https://api.crossref.org/works/{doi}/references"
        headers = {"User-Agent": "Article-MCP/2.0", "Accept": "application/json"}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        citing_articles = []

        # 处理引用文献
        references = data.get("message", {}).get("reference", [])
        for ref in references[:max_results]:
            if ref.get("doi"):
                # 获取引用文献的详细信息
                citing_article = _get_article_by_doi(ref["doi"], logger)
                if citing_article:
                    citing_articles.append(citing_article)

        return citing_articles

    except Exception as e:
        logger.error(f"从CrossRef获取引用文献异常: {e}")
        return []


def _get_article_by_doi(doi: str, logger) -> dict | None:
    """通过DOI获取文章详情"""
    try:
        import requests

        url = f"https://api.crossref.org/works/{doi}"
        headers = {"User-Agent": "Article-MCP/2.0", "Accept": "application/json"}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        item = data.get("message", {})

        return {
            "title": " ".join(item.get("title", [])),
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", [])
            ],
            "year": item.get("published-print", {}).get("date-parts", [[""]])[0][0][:4],
            "doi": item.get("DOI", ""),
            "journal": item.get("container-title", [""])[0],
            "source": "crossref",
        }

    except Exception as e:
        logger.debug(f"获取DOI {doi} 详情失败: {e}")
        return None


def _analyze_citation_network(
    identifiers: list[str], max_depth: int, max_results: int, logger
) -> list[dict]:
    """分析引用网络"""
    edges = []

    try:
        # 对于每对文献，检查引用关系
        for i, source_id in enumerate(identifiers):
            source_refs = _get_references(source_id, "auto", max_results, ["europe_pmc"], logger)
            references = source_refs.get("references", [])

            # 提取参考文献的标识符
            ref_identifiers = []
            for ref in references:
                if ref.get("doi"):
                    ref_identifiers.append(ref["doi"])
                elif ref.get("pmid"):
                    ref_identifiers.append(f"PMID:{ref['pmid']}")

            # 检查目标文献是否在参考文献中
            for j, target_id in enumerate(identifiers):
                if i != j:  # 不和自己比较
                    if target_id in ref_identifiers or any(
                        target_id in ref.get("title", "") for ref in references
                    ):
                        edge = {
                            "source": source_id,
                            "target": target_id,
                            "type": "citation",
                            "weight": 1,
                            "metadata": {"citation_type": "direct"},
                        }
                        edges.append(edge)

        return edges

    except Exception as e:
        logger.error(f"分析引用网络异常: {e}")
        return []


def _analyze_collaboration_network(identifiers: list[str], max_results: int, logger) -> list[dict]:
    """分析合作网络"""
    edges = []

    try:
        # 获取每篇文献的作者信息
        authors_by_paper = {}

        for identifier in identifiers:
            if _relation_services and "europe_pmc" in _relation_services:
                service = _relation_services["europe_pmc"]
                result = service.fetch(identifier, id_type="auto")

                if result.get("success", False):
                    article = result.get("article", {})
                    authors = article.get("authors", [])
                    author_names = [
                        author.get("name", "") for author in authors if author.get("name")
                    ]
                    authors_by_paper[identifier] = author_names

        # 分析作者合作关系
        for i, paper1 in enumerate(identifiers):
            for j, paper2 in enumerate(identifiers):
                if i < j:  # 避免重复比较
                    authors1 = authors_by_paper.get(paper1, [])
                    authors2 = authors_by_paper.get(paper2, [])

                    # 计算共同作者数量
                    common_authors = set(authors1) & set(authors2)

                    if common_authors:
                        collaboration_strength = len(common_authors)
                        edge = {
                            "source": paper1,
                            "target": paper2,
                            "type": "collaboration",
                            "weight": collaboration_strength,
                            "metadata": {
                                "common_authors": list(common_authors),
                                "collaboration_strength": collaboration_strength,
                            },
                        }
                        edges.append(edge)

        return edges

    except Exception as e:
        logger.error(f"分析合作网络异常: {e}")
        return []


def _detect_communities(network_data: dict) -> dict:
    """简单的社区检测算法"""
    try:
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        if not nodes or not edges:
            return {}

        # 构建邻接表
        adjacency = {node["id"]: set() for node in nodes}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adjacency and target in adjacency:
                adjacency[source].add(target)
                adjacency[target].add(source)

        # 简单的连通组件检测
        visited = set()
        communities = {}
        community_id = 0

        for node_id in adjacency:
            if node_id not in visited:
                # BFS遍历连通组件
                queue = [node_id]
                community_nodes = []

                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        community_nodes.append(current)
                        queue.extend(adjacency[current] - visited)

                if len(community_nodes) > 1:
                    communities[f"community_{community_id}"] = community_nodes
                    community_id += 1

        return communities

    except Exception as e:
        logging.error(f"社区检测异常: {e}")
        return {}
