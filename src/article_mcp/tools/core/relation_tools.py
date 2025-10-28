"""
文献关系分析工具 - 核心工具4（统一关系分析工具）
"""

import time
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_relation_services = None


def register_relation_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册文献关系分析工具"""
    global _relation_services
    _relation_services = services

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="文献关系分析工具。分析文献间的引用关系、相似性和合作网络。",
        annotations=ToolAnnotations(
            title="文献关系分析",
            readOnlyHint=True,
            openWorldHint=False
        ),
        tags={"relations", "network", "analysis", "citations"}
    )
    async def get_literature_relations(
        identifier: str | list[str] | None = None,
        identifiers: str | list[str] | None = None,
        id_type: str = "auto",
        relation_types: list[str] | None = None,
        max_results: int = 20,
        sources: list[str] | None = None,
        analysis_type: str = "basic",
        max_depth: int = 1,
    ) -> dict[str, Any]:
        """文献关系分析工具。分析文献间的引用关系、相似性和合作网络。

        Args:
            identifier: 文献标识符（单个）- 向后兼容参数
            identifiers: 文献标识符（单个或列表）- 主要参数
            id_type: 标识符类型 ["auto", "doi", "pmid", "pmcid"]
            relation_types: 关系类型 ["references", "similar", "citing"]
            max_results: 每种关系类型最大结果数
            sources: 数据源列表
            analysis_type: 分析类型 ["basic", "comprehensive", "network"]
            max_depth: 分析深度

        Returns:
            包含文献关系网络的字典，支持引用链和相似文献分析
        """
        try:
            # 参数优先级：identifier > identifiers
            if identifier is not None:
                final_identifiers = identifier
            elif identifiers is not None:
                final_identifiers = identifiers
            else:
                return {
                    "success": False,
                    "error": "必须提供 identifier 或 identifiers 参数",
                    "relations": {},
                }

            # 处理None值的参数
            if relation_types is None:
                relation_types = ["references", "similar", "citing"]
            if sources is None:
                sources = ["europe_pmc", "crossref", "openalex", "pubmed"]

            # 根据输入类型判断操作模式
            if isinstance(final_identifiers, str):
                # 单个文献的基本关系分析
                return _single_literature_relations(
                    final_identifiers, id_type, relation_types, max_results, sources, logger
                )
            elif isinstance(final_identifiers, list):
                if analysis_type == "basic":
                    # 多个文献的基本关系分析（批量处理）
                    return await _batch_literature_relations(
                        final_identifiers, id_type, relation_types, max_results, sources, logger
                    )
                else:
                    # 文献网络分析
                    return await _analyze_literature_network(
                        final_identifiers, analysis_type, max_depth, max_results, logger
                    )
            else:
                return {
                    "success": False,
                    "error": "identifier/identifiers参数必须是字符串或字符串列表",
                    "identifier": final_identifiers,
                    "relations": {},
                }

        except Exception as e:
            logger.error(f"文献关系分析异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "identifier": final_identifiers,
                "relations": {},
            }

    

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
                    similar = _get_similar_articles(
                        identifier, id_type, max_results, sources, logger
                    )
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
        statistics["relation_types_found"] = [
            rt for rt in relation_types if statistics.get(f"{rt}_count", 0) > 0
        ]

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
            _build_collaboration_network(identifiers, nodes, edges, node_map, max_results, logger)

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
            try:
                if source == "crossref" and "crossref" in _relation_services:
                    service = _relation_services["crossref"]
                    doi = _ensure_doi_identifier(identifier, id_type, logger)
                    if doi:
                        logger.info(f"使用CrossRef获取 {doi} 的参考文献")
                        result = service.get_references(doi, max_results)
                        if result.get("success", False):
                            crossref_refs = result.get("references", [])
                            references.extend(crossref_refs)
                            logger.info(f"CrossRef返回 {len(crossref_refs)} 篇参考文献")
                        else:
                            logger.warning(f"CrossRef获取参考文献失败: {result.get('error')}")
                    else:
                        logger.warning(f"无法转换标识符为DOI，跳过CrossRef查询")

                elif source == "europe_pmc" and "europe_pmc" in _relation_services:
                    # Europe PMC参考文献获取（第二阶段实现）
                    service = _relation_services["europe_pmc"]
                    # TODO: 实现Europe PMC参考文献API集成
                    logger.debug("Europe PMC参考文献功能待实现")

                elif source == "pubmed" and "pubmed" in _relation_services:
                    # PubMed参考文献获取逻辑
                    logger.debug("PubMed参考文献功能待实现")
                    # TODO: 实现PubMed参考文献API集成

            except Exception as e:
                logger.error(f"从 {source} 获取参考文献失败: {e}")

        # 去重和限制数量
        unique_references = _deduplicate_references(references, max_results)
        logger.info(f"参考文献去重后共 {len(unique_references)} 篇")

        return unique_references

    except Exception as e:
        if 'logger' in locals():
            logger.error(f"获取参考文献失败: {e}")
        else:
            print(f"获取参考文献失败: {e}")
        return []


def _get_similar_articles(
    identifier: str, id_type: str, max_results: int, sources: list[str], logger
) -> list[dict[str, Any]]:
    """获取相似文献"""
    try:
        # 确保有DOI标识符
        if id_type != "doi":
            doi = _convert_to_doi(identifier, id_type, logger)
            if not doi:
                logger.warning(f"无法将 {id_type}:{identifier} 转换为DOI，无法获取相似文献")
                return []
        else:
            doi = identifier

        logger.info(f"获取DOI {doi} 的相似文献")
        similar_articles = []

        for source in sources:
            try:
                if source == "pubmed" and "pubmed" in _relation_services:
                    # 使用现有的相似文献服务（基于PubMed E-utilities）
                    logger.info(f"使用PubMed服务获取 {doi} 的相似文献")
                    try:
                        from src.article_mcp.services.similar_articles import get_similar_articles_by_doi
                        result = get_similar_articles_by_doi(doi, max_results=max_results)

                        if result.get("similar_articles"):
                            pubmed_similar = result.get("similar_articles", [])
                            similar_articles.extend(pubmed_similar)
                            logger.info(f"PubMed返回 {len(pubmed_similar)} 篇相似文献")
                        else:
                            logger.warning(f"PubMed相似文献查询无结果")
                    except ImportError:
                        logger.error("无法导入similar_articles模块")
                    except Exception as e:
                        logger.warning(f"PubMed相似文献查询失败: {e}")

                elif source == "openalex" and "openalex" in _relation_services:
                    # OpenAlex相似文献查询（第二阶段实现）
                    service = _relation_services["openalex"]
                    logger.info(f"使用OpenAlex查询 {doi} 的相似文献")
                    # TODO: 实现OpenAlex相似文献API集成
                    logger.debug("OpenAlex相似文献功能待实现")

                elif source == "europe_pmc" and "europe_pmc" in _relation_services:
                    # Europe PMC相似文献查询（第二阶段实现）
                    service = _relation_services["europe_pmc"]
                    logger.info(f"使用Europe PMC查询 {doi} 的相似文献")
                    # TODO: 实现Europe PMC相似文献API集成
                    logger.debug("Europe PMC相似文献功能待实现")

            except Exception as e:
                logger.error(f"从 {source} 获取相似文献失败: {e}")

        # 去重和限制数量
        unique_similar = _deduplicate_references(similar_articles, max_results)
        logger.info(f"相似文献去重后共 {len(unique_similar)} 篇")

        return unique_similar

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
            try:
                if source == "openalex" and "openalex" in _relation_services:
                    service = _relation_services["openalex"]
                    doi = _ensure_doi_identifier(identifier, id_type, logger)
                    if doi:
                        logger.info(f"使用OpenAlex获取 {doi} 的引用文献")
                        result = service.get_citations(doi, max_results)
                        if result.get("success", False):
                            openalex_citations = result.get("citations", [])
                            citing_articles.extend(openalex_citations)
                            logger.info(f"OpenAlex返回 {len(openalex_citations)} 篇引用文献")
                        else:
                            logger.warning(f"OpenAlex获取引用文献失败: {result.get('error')}")
                    else:
                        logger.warning(f"无法转换标识符为DOI，跳过OpenAlex查询")

                elif source == "crossref" and "crossref" in _relation_services:
                    # Crossref也提供引用文献查询（作为备用）
                    service = _relation_services["crossref"]
                    doi = _ensure_doi_identifier(identifier, id_type, logger)
                    if doi:
                        logger.info(f"使用CrossRef查询 {doi} 的引用文献")
                        # TODO: 实现CrossRef引用文献API集成
                        logger.debug("CrossRef引用文献功能待实现")

                elif source == "europe_pmc" and "europe_pmc" in _relation_services:
                    # Europe PMC引用文献获取（第二阶段实现）
                    service = _relation_services["europe_pmc"]
                    # TODO: 实现Europe PMC引用文献API集成
                    logger.debug("Europe PMC引用文献功能待实现")

                elif source == "pubmed" and "pubmed" in _relation_services:
                    # PubMed引用文献获取逻辑
                    logger.debug("PubMed引用文献功能待实现")
                    # TODO: 实现PubMed引用文献API集成

            except Exception as e:
                logger.error(f"从 {source} 获取引用文献失败: {e}")

        # 限制数量（引用文献不需要去重，因为引用文献天然不会重复）
        final_citations = citing_articles[:max_results]
        logger.info(f"引用文献共 {len(final_citations)} 篇")

        return final_citations

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
                        "label": (
                            ref.get("title", ref_id)[:50] + "..."
                            if len(ref.get("title", ref_id)) > 50
                            else ref.get("title", ref_id)
                        ),
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
                        "label": (
                            cite.get("title", cite_id)[:50] + "..."
                            if len(cite.get("title", cite_id)) > 50
                            else cite.get("title", cite_id)
                        ),
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
            "network_density": (
                (2 * len(edges)) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
            ),
        }

        # 计算聚类大小分布
        cluster_sizes = {k: len(v) for k, v in clusters.items()}
        metrics["cluster_sizes"] = cluster_sizes
        metrics["largest_cluster_size"] = max(cluster_sizes.values()) if cluster_sizes else 0

        return metrics

    except Exception as e:
        logger.error(f"计算网络指标失败: {e}")
        return {}


# ======== 辅助函数 ========

def _ensure_doi_identifier(identifier: str, id_type: str, logger) -> str | None:
    """确保返回DOI标识符"""
    if id_type == "doi":
        return identifier
    elif id_type in ["pmid", "pmcid"]:
        return _convert_to_doi(identifier, id_type, logger)
    elif id_type == "arxiv_id":
        # arXiv ID暂时不转换为DOI
        logger.warning(f"arXiv ID {identifier} 暂时不支持转换为DOI")
        return None
    else:
        logger.warning(f"不支持的标识符类型: {id_type}")
        return None


def _convert_to_doi(identifier: str, id_type: str, logger) -> str | None:
    """标识符转换为DOI（基础版本）"""
    try:
        if id_type == "pmid":
            # 使用CrossRef API查询PMID对应的DOI
            return _pmid_to_doi(identifier, logger)
        elif id_type == "pmcid":
            # 使用Europe PMC API查询PMCID对应的DOI
            return _pmcid_to_doi(identifier, logger)
        else:
            logger.warning(f"不支持的转换类型: {id_type}")
            return None

    except Exception as e:
        logger.error(f"标识符转换失败: {e}")
        return None


def _pmid_to_doi(pmid: str, logger) -> str | None:
    """PMID转DOI（使用多种API策略）"""
    try:
        import requests
        import re

        # 确保PMID格式正确
        pmid = str(pmid).strip()
        if not pmid.isdigit():
            logger.warning(f"PMID格式不正确: {pmid}")
            return None

        # 策略1：使用Europe PMC API（最权威）
        doi = _pmid_to_doi_europe_pmc(pmid, logger)
        if doi:
            return doi

        # 策略2：使用CrossRef API（备选）
        doi = _pmid_to_doi_crossref(pmid, logger)
        if doi:
            return doi

        # 策略3：使用NCBI E-utilities（最后备选）
        doi = _pmid_to_doi_ncbi(pmid, logger)
        if doi:
            return doi

        logger.warning(f"所有API都无法找到PMID {pmid} 对应的DOI")
        return None

    except Exception as e:
        logger.error(f"PMID转DOI失败: {e}")
        return None


def _pmid_to_doi_europe_pmc(pmid: str, logger) -> str | None:
    """使用Europe PMC API进行PMID到DOI转换"""
    try:
        import requests
        import re

        # Europe PMC API: 通过PMID获取文章元数据
        url = f"https://www.ebi.ac.uk/europepmc/api/search"
        params = {
            "query": f"ext_id:{pmid}",
            "resulttype": "core",
            "format": "json",
            "size": 1
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("resultList", {}).get("result", [])

            if results:
                result = results[0]
                # 多种可能的DOI字段
                doi_fields = [
                    result.get("doi", ""),
                    result.get("pmcDoc", {}).get("doi", ""),
                    result.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("doi", "")
                ]

                for doi in doi_fields:
                    if doi and doi.startswith("10."):
                        logger.info(f"Europe PMC找到PMID {pmid} 对应的DOI: {doi}")
                        return doi

        return None

    except Exception as e:
        logger.warning(f"Europe PMC API转换PMID {pmid} 失败: {e}")
        return None


def _pmid_to_doi_crossref(pmid: str, logger) -> str | None:
    """使用CrossRef API进行PMID到DOI转换"""
    try:
        import requests

        # 方法1：查询PMID作为关键词
        url = "https://api.crossref.org/works"
        params = {
            "query.bibliographic": pmid,
            "select": "DOI,title,author,member",
            "rows": 10
        }

        headers = {
            "User-Agent": "Article-MCP/1.0 (mailto:user@example.com)"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("message", {}).get("items", [])

            # 查找最匹配的结果
            for item in items:
                doi = item.get("DOI")
                title = item.get("title", [])
                authors = item.get("author", [])

                if doi:
                    # 检查标题是否包含PMID相关信息（提高准确性）
                    if title and any(pmid in str(t) for t in title):
                        logger.info(f"CrossRef找到PMID {pmid} 对应的DOI: {doi}")
                        return doi

                    # 如果第一个结果有DOI且看起来合理，也使用
                    if items.index(item) == 0:
                        logger.info(f"CrossRef找到PMID {pmid} 对应的DOI: {doi}")
                        return doi

        return None

    except Exception as e:
        logger.warning(f"CrossRef API转换PMID {pmid} 失败: {e}")
        return None


def _pmid_to_doi_ncbi(pmid: str, logger) -> str | None:
    """使用NCBI E-utilities进行PMID到DOI转换"""
    try:
        import requests
        import re

        # NCBI E-utilities API
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "json"
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            article_data = result.get(str(pmid), {})

            if article_data:
                # 查找DOI信息
                doi = article_data.get("doi", "")
                if doi and doi.startswith("10."):
                    logger.info(f"NCBI找到PMID {pmid} 对应的DOI: {doi}")
                    return doi

        return None

    except Exception as e:
        logger.warning(f"NCBI API转换PMID {pmid} 失败: {e}")
        return None


def _pmcid_to_doi(pmcid: str, logger) -> str | None:
    """PMCID转DOI（使用多种API策略）"""
    try:
        import requests
        import re

        # 确保PMCID格式正确
        pmcid = str(pmcid).strip()
        if not pmcid.upper().startswith("PMC"):
            pmcid = f"PMC{pmcid}"

        # 策略1：使用Europe PMC RESTful API（JSON格式）
        doi = _pmcid_to_doi_europe_pmc_json(pmcid, logger)
        if doi:
            return doi

        # 策略2：使用Europe PMC metadata API（XML格式）
        doi = _pmcid_to_doi_europe_pmc_xml(pmcid, logger)
        if doi:
            return doi

        # 策略3：使用NCBI E-utilities反向查询
        doi = _pmcid_to_doi_ncbi(pmcid, logger)
        if doi:
            return doi

        logger.warning(f"所有API都无法找到PMCID {pmcid} 对应的DOI")
        return None

    except Exception as e:
        logger.error(f"PMCID转DOI失败: {e}")
        return None


def _pmcid_to_doi_europe_pmc_json(pmcid: str, logger) -> str | None:
    """使用Europe PMC JSON API进行PMCID到DOI转换"""
    try:
        import requests

        # Europe PMC搜索API：JSON格式
        url = "https://www.ebi.ac.uk/europepmc/api/search"
        params = {
            "query": f"pmcid:{pmcid}",
            "resulttype": "core",
            "format": "json",
            "size": 1
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("resultList", {}).get("result", [])

            if results:
                result = results[0]
                # 多种可能的DOI字段
                doi_fields = [
                    result.get("doi", ""),
                    result.get("pmcDoc", {}).get("doi", ""),
                    result.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("doi", "")
                ]

                for doi in doi_fields:
                    if doi and doi.startswith("10."):
                        logger.info(f"Europe PMC JSON找到PMCID {pmcid} 对应的DOI: {doi}")
                        return doi

        return None

    except Exception as e:
        logger.warning(f"Europe PMC JSON API转换PMCID {pmcid} 失败: {e}")
        return None


def _pmcid_to_doi_europe_pmc_xml(pmcid: str, logger) -> str | None:
    """使用Europe PMC XML API进行PMCID到DOI转换"""
    try:
        import requests
        import re

        # Europe PMC metadata API：XML格式
        url = f"https://www.ebi.ac.uk/europepmc/api/metadata/{pmcid}"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text

            # 更全面的DOI模式匹配
            doi_patterns = [
                r'<DOI>([^<]+)</DOI>',
                r'<article-id[^>]*pub-id-type="doi"[^>]*>([^<]+)</article-id>',
                r'10\.\d+/[^\s<">]+',
                r'doi:\s*(10\.\d+/[^\s<">]+)',
                r'https?://doi\.org/(10\.\d+/[^\s<">]+)'
            ]

            for pattern in doi_patterns:
                doi_match = re.search(pattern, content, re.IGNORECASE)
                if doi_match:
                    doi = doi_match.group(1).strip()
                    # 清理DOI格式
                    doi = re.sub(r'[^0-9a-zA-Z._/-]', '', doi)

                    if doi.startswith("10."):
                        logger.info(f"Europe PMC XML找到PMCID {pmcid} 对应的DOI: {doi}")
                        return doi

        return None

    except Exception as e:
        logger.warning(f"Europe PMC XML API转换PMCID {pmcid} 失败: {e}")
        return None


def _pmcid_to_doi_ncbi(pmcid: str, logger) -> str | None:
    """使用NCBI数据库进行PMCID到DOI转换"""
    try:
        import requests

        # 首先通过PMCID找到PMID，然后通过PMID找DOI
        url = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/.fcgi"
        params = {
            "id": pmcid,
            "format": "json",
            "format": "json"
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                records = data.get("records", [])

                if records:
                    record = records[0]
                    # 查找DOI信息
                    doi = record.get("doi", "")
                    if doi and doi.startswith("10."):
                        logger.info(f"NCBI OA找到PMCID {pmcid} 对应的DOI: {doi}")
                        return doi

                    # 如果没有直接DOI，尝试通过PMID转换
                    pmid = record.get("pmid", "")
                    if pmid:
                        doi = _pmid_to_doi(pmid, logger)
                        if doi:
                            logger.info(f"NCBI PMID转换找到PMCID {pmcid} 对应的DOI: {doi}")
                            return doi

            except ValueError:
                # JSON解析失败，跳过这个策略
                pass

        return None

    except Exception as e:
        logger.warning(f"NCBI API转换PMCID {pmcid} 失败: {e}")
        return None


def _deduplicate_references(references: list[dict[str, Any]], max_results: int) -> list[dict[str, Any]]:
    """参考文献去重和限制数量"""
    try:
        seen_dois = set()
        seen_titles = set()
        unique_references = []

        for ref in references:
            doi = ref.get("doi", "")
            title = ref.get("title", "")

            # 优先使用DOI去重
            if doi and doi not in seen_dois:
                seen_dois.add(doi)
                unique_references.append(ref)
            # 如果没有DOI，使用标题去重
            elif not doi and title and title not in seen_titles:
                seen_titles.add(title)
                unique_references.append(ref)
            # 既没有DOI也没有标题的文献也保留（但数量很少）
            elif not doi and not title:
                unique_references.append(ref)

        # 限制数量
        final_references = unique_references[:max_results]

        print(f"参考文献去重：{len(references)} -> {len(final_references)}")
        return final_references

    except Exception as e:
        print(f"参考文献去重失败: {e}")
        return references[:max_results]
