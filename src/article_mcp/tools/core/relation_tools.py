"""
文献关系分析工具 - 核心工具4（统一关系分析工具）
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
        identifiers: str | list[str],
        id_type: str = "auto",
        relation_types: list[str] = ["references", "similar", "citing"],
        max_results: int = 20,
        sources: list[str] = ["europe_pmc", "pubmed"],
        analysis_type: str = "basic",
        max_depth: int = 1,
    ) -> dict[str, Any]:
        """统一文献关系分析工具

        功能说明：
        - 支持单个或多个文献的关系分析
        - 支持参考文献、相似文献、引用文献查询
        - 支持文献网络分析和可视化

        参数说明：
        - identifiers: 文献标识符（字符串或字符串列表）
        - id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
        - relation_types: 关系类型列表 ["references", "similar", "citing"]
        - max_results: 每种关系类型最大返回数
        - sources: 数据源列表
        - analysis_type: 分析类型 ["basic", "comprehensive", "citation", "collaboration"]
        - max_depth: 分析深度（用于网络分析）

        返回格式：
        basic操作: {"success": true, "identifier": "...", "relations": {...}}
        comprehensive操作: {"success": true, "network_data": {...}, "analysis_metrics": {...}}
        """
        try:
            # 根据输入类型判断操作模式
            if isinstance(identifiers, str):
                # 单个文献的基本关系分析
                return _single_literature_relations(
                    identifiers, id_type, relation_types, max_results, sources, logger
                )
            elif isinstance(identifiers, list):
                if analysis_type == "basic":
                    # 多个文献的基本关系分析（批量处理）
                    return _batch_literature_relations(
                        identifiers, id_type, relation_types, max_results, sources, logger
                    )
                else:
                    # 文献网络分析
                    return _analyze_literature_network(
                        identifiers, analysis_type, max_depth, max_results, logger
                    )
            else:
                return {
                    "success": False,
                    "error": "identifiers参数必须是字符串或字符串列表",
                    "identifier": identifiers,
                    "relations": {},
                }

        except Exception as e:
            logger.error(f"文献关系分析异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "identifier": identifiers,
                "relations": {},
            }

    return [get_literature_relations]


def _single_literature_relations(
    identifier: str,
    id_type: str,
    relation_types: list[str],
    max_results: int,
    sources: list[str],
    logger,
) -> dict[str, Any]:
    """单个文献的关系分析"""
    try:
        if not identifier or not identifier.strip():
            return {
                "success": False,
                "error": "文献标识符不能为空",
                "identifier": identifier,
                "relations": {},
                "statistics": {},
            }

        start_time = time.time()
        relations = {}
        statistics = {}

        # 自动识别标识符类型
        if id_type == "auto":
            id_type = _extract_identifier_type(identifier.strip())

        # 获取各种类型的关系
        for relation_type in relation_types:
            try:
                if relation_type == "references":
                    references = _get_references(identifier, id_type, max_results, sources, logger)
                    relations["references"] = references
                    statistics["references_count"] = len(references)

                elif relation_type == "similar":
                    similar = _get_similar_articles(identifier, id_type, max_results, sources, logger)
                    relations["similar"] = similar
                    statistics["similar_count"] = len(similar)

                elif relation_type == "citing":
                    citing = _get_citing_articles(identifier, id_type, max_results, sources, logger)
                    relations["citing"] = citing
                    statistics["citing_count"] = len(citing)

            except Exception as e:
                logger.error(f"获取 {relation_type} 关系失败: {e}")
                relations[relation_type] = []
                statistics[f"{relation_type}_count"] = 0

        # 计算总体统计
        total_relations = sum(statistics.values())
        statistics["total_relations"] = total_relations
        statistics["relation_types_found"] = [rt for rt in relation_types if statistics.get(f"{rt}_count", 0) > 0]

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "identifier": identifier.strip(),
            "id_type": id_type,
            "relations": relations,
            "statistics": statistics,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"单个文献关系分析异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "identifier": identifier,
            "relations": {},
            "statistics": {},
        }


def _batch_literature_relations(
    identifiers: list[str],
    id_type: str,
    relation_types: list[str],
    max_results: int,
    sources: list[str],
    logger,
) -> dict[str, Any]:
    """批量文献关系分析"""
    try:
        if not identifiers:
            return {
                "success": False,
                "error": "文献标识符列表不能为空",
                "total_identifiers": 0,
                "successful_analyses": 0,
                "batch_results": {},
                "processing_time": 0,
            }

        start_time = time.time()
        batch_results = {}
        successful_analyses = 0

        for identifier in identifiers:
            try:
                result = _single_literature_relations(
                    identifier, id_type, relation_types, max_results, sources, logger
                )
                batch_results[identifier] = result
                if result.get("success", False):
                    successful_analyses += 1
            except Exception as e:
                logger.error(f"分析文献 '{identifier}' 失败: {e}")
                batch_results[identifier] = {
                    "success": False,
                    "error": str(e),
                    "identifier": identifier,
                    "relations": {},
                }

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": successful_analyses > 0,
            "total_identifiers": len(identifiers),
            "successful_analyses": successful_analyses,
            "success_rate": successful_analyses / len(identifiers) if identifiers else 0,
            "batch_results": batch_results,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"批量文献关系分析异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_identifiers": len(identifiers) if identifiers else 0,
            "successful_analyses": 0,
            "batch_results": {},
            "processing_time": 0,
        }


def _analyze_literature_network(
    identifiers: list[str],
    analysis_type: str,
    max_depth: int,
    max_results: int,
    logger,
) -> dict[str, Any]:
    """文献网络分析"""
    try:
        if not identifiers:
            return {
                "success": False,
                "error": "文献标识符列表不能为空",
                "network_data": {"nodes": [], "edges": [], "clusters": {}},
                "analysis_metrics": {},
                "processing_time": 0,
            }

        start_time = time.time()

        # 构建网络节点
        nodes = []
        edges = []
        node_map = {}  # 标识符到节点索引的映射

        # 添加初始节点
        for i, identifier in enumerate(identifiers):
            node = {
                "id": identifier,
                "label": identifier,
                "type": "seed",
                "x": 100 * (i % 3),
                "y": 100 * (i // 3),
            }
            nodes.append(node)
            node_map[identifier] = i

        # 根据分析类型构建网络
        if analysis_type in ["comprehensive", "citation"]:
            # 引用网络分析
            _build_citation_network(
                identifiers, nodes, edges, node_map, max_depth, max_results, logger
            )

        if analysis_type in ["comprehensive", "collaboration"]:
            # 合作网络分析（基于作者信息）
            _build_collaboration_network(
                identifiers, nodes, edges, node_map, max_results, logger
            )

        # 网络聚类分析
        clusters = _detect_network_clusters(nodes, edges, logger)

        # 计算网络指标
        analysis_metrics = _calculate_network_metrics(nodes, edges, clusters, logger)

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "network_data": {
                "nodes": nodes,
                "edges": edges,
                "clusters": clusters,
                "analysis_type": analysis_type,
                "max_depth": max_depth,
            },
            "analysis_metrics": analysis_metrics,
            "processing_time": processing_time,
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


# 辅助函数
def _extract_identifier_type(identifier: str) -> str:
    """提取标识符类型"""
    identifier = identifier.strip().upper()

    if identifier.startswith("DOI:") or "//" in identifier or identifier.startswith("10."):
        return "doi"
    elif identifier.startswith("PMCID:") or identifier.startswith("PMC"):
        return "pmcid"
    elif identifier.isdigit() or identifier.startswith("PMID:"):
        return "pmid"
    elif identifier.startswith("ARXIV:"):
        return "arxiv_id"
    else:
        return "doi"  # 默认当作DOI处理


def _get_references(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> list[dict[str, Any]]:
    """获取参考文献"""
    try:
        references = []

        for source in sources:
            if source == "europe_pmc" and "europe_pmc" in _relation_services:
                service = _relation_services["europe_pmc"]
                result = service.get_references(identifier, id_type, max_results)
                if result.get("success", False):
                    references.extend(result.get("references", []))

            elif source == "pubmed" and "pubmed" in _relation_services:
                # PubMed参考文献获取逻辑
                pass  # 实际实现中会调用PubMed服务

        # 去重和限制数量
        seen_dois = set()
        unique_references = []
        for ref in references:
            doi = ref.get("doi", "")
            if doi and doi not in seen_dois:
                seen_dois.add(doi)
                unique_references.append(ref)
            elif not doi:
                unique_references.append(ref)

        return unique_references[:max_results]

    except Exception as e:
        logger.error(f"获取参考文献失败: {e}")
        return []


def _get_similar_articles(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> list[dict[str, Any]]:
    """获取相似文献"""
    try:
        similar_articles = []

        for source in sources:
            if source == "europe_pmc" and "europe_pmc" in _relation_services:
                service = _relation_services["europe_pmc"]
                # 实际实现中会调用相似文献API
                pass

            elif source == "pubmed" and "pubmed" in _relation_services:
                service = _relation_services["pubmed"]
                result = service.get_similar_articles(identifier, max_results)
                if result.get("success", False):
                    similar_articles.extend(result.get("similar_articles", []))

        return similar_articles[:max_results]

    except Exception as e:
        logger.error(f"获取相似文献失败: {e}")
        return []


def _get_citing_articles(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> list[dict[str, Any]]:
    """获取引用文献"""
    try:
        citing_articles = []

        for source in sources:
            if source == "europe_pmc" and "europe_pmc" in _relation_services:
                service = _relation_services["europe_pmc"]
                result = service.get_citing_articles(identifier, max_results)
                if result.get("success", False):
                    citing_articles.extend(result.get("citing_articles", []))

            elif source == "pubmed" and "pubmed" in _relation_services:
                service = _relation_services["pubmed"]
                result = service.get_citing_articles(identifier, max_results)
                if result.get("success", False):
                    citing_articles.extend(result.get("citing_articles", []))

        return citing_articles[:max_results]

    except Exception as e:
        logger.error(f"获取引用文献失败: {e}")
        return []


def _build_citation_network(
    identifiers: list[str],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    node_map: dict[str, int],
    max_depth: int,
    max_results: int,
    logger,
) -> None:
    """构建引用网络"""
    try:
        if max_depth < 1:
            return

        for identifier in identifiers:
            # 获取参考文献
            references = _get_references(identifier, "auto", max_results, ["europe_pmc"], logger)

            for ref in references:
                ref_id = ref.get("doi", "") or ref.get("pmid", "") or ref.get("title", "")
                if ref_id and ref_id not in node_map:
                    # 添加新节点
                    node_index = len(nodes)
                    node = {
                        "id": ref_id,
                        "label": ref.get("title", ref_id)[:50] + "..." if len(ref.get("title", ref_id)) > 50 else ref.get("title", ref_id),
                        "type": "reference",
                        "x": nodes[node_map[identifier]]["x"] + (len(edges) % 5 - 2) * 50,
                        "y": nodes[node_map[identifier]]["y"] + 100,
                    }
                    nodes.append(node)
                    node_map[ref_id] = node_index

                # 添加边
                edge = {
                    "source": node_map[identifier],
                    "target": node_map[ref_id],
                    "type": "references",
                    "weight": 1,
                }
                edges.append(edge)

            # 获取引用文献
            citing = _get_citing_articles(identifier, "auto", max_results, ["europe_pmc"], logger)

            for cite in citing:
                cite_id = cite.get("doi", "") or cite.get("pmid", "") or cite.get("title", "")
                if cite_id and cite_id not in node_map:
                    # 添加新节点
                    node_index = len(nodes)
                    node = {
                        "id": cite_id,
                        "label": cite.get("title", cite_id)[:50] + "..." if len(cite.get("title", cite_id)) > 50 else cite.get("title", cite_id),
                        "type": "citing",
                        "x": nodes[node_map[identifier]]["x"] + (len(edges) % 5 - 2) * 50,
                        "y": nodes[node_map[identifier]]["y"] - 100,
                    }
                    nodes.append(node)
                    node_map[cite_id] = node_index

                # 添加边
                edge = {
                    "source": node_map[cite_id],
                    "target": node_map[identifier],
                    "type": "citing",
                    "weight": 1,
                }
                edges.append(edge)

    except Exception as e:
        logger.error(f"构建引用网络失败: {e}")


def _build_collaboration_network(
    identifiers: list[str],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    node_map: dict[str, int],
    max_results: int,
    logger,
) -> None:
    """构建合作网络"""
    try:
        # 这里应该基于作者信息构建合作网络
        # 由于没有真实的作者数据，这里只做示意性实现
        pass

    except Exception as e:
        logger.error(f"构建合作网络失败: {e}")


def _detect_network_clusters(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]], logger
) -> dict[str, Any]:
    """检测网络聚类"""
    try:
        clusters = {
            "seed_papers": [i for i, node in enumerate(nodes) if node.get("type") == "seed"],
            "references": [i for i, node in enumerate(nodes) if node.get("type") == "reference"],
            "citing": [i for i, node in enumerate(nodes) if node.get("type") == "citing"],
        }

        return clusters

    except Exception as e:
        logger.error(f"检测网络聚类失败: {e}")
        return {}


def _calculate_network_metrics(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    clusters: dict[str, Any],
    logger,
) -> dict[str, Any]:
    """计算网络指标"""
    try:
        metrics = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "average_degree": (2 * len(edges)) / len(nodes) if nodes else 0,
            "cluster_count": len([k for k, v in clusters.items() if v]),
            "network_density": (2 * len(edges)) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0,
        }

        # 计算聚类大小分布
        cluster_sizes = {k: len(v) for k, v in clusters.items()}
        metrics["cluster_sizes"] = cluster_sizes
        metrics["largest_cluster_size"] = max(cluster_sizes.values()) if cluster_sizes else 0

        return metrics

    except Exception as e:
        logger.error(f"计算网络指标失败: {e}")
        return {}