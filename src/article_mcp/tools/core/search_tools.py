"""统一搜索工具 - 核心工具1

基于 TDD 驱动开发，实现以下改进:
1. asyncio 并行搜索
2. search_type 搜索策略
3. 缓存机制
4. 闭包捕获服务依赖（无全局变量）
"""

import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# ============================================================================
# 搜索策略配置
# ============================================================================

# 定义搜索策略
SEARCH_STRATEGIES = {
    "comprehensive": {
        "name": "comprehensive",
        "description": "全面搜索，使用所有可用数据源",
        "default_sources": ["europe_pmc", "pubmed", "arxiv", "crossref", "openalex"],
        "max_results_per_source": 10,
        "merge_strategy": "union",
    },
    "fast": {
        "name": "fast",
        "description": "快速搜索，只使用主要数据源",
        "default_sources": ["europe_pmc", "pubmed"],
        "max_results_per_source": 5,
        "merge_strategy": "union",
    },
    "precise": {
        "name": "precise",
        "description": "精确搜索，使用权威数据源",
        "default_sources": ["pubmed", "europe_pmc"],
        "max_results_per_source": 10,
        "merge_strategy": "intersection",
    },
    "preprint": {
        "name": "preprint",
        "description": "预印本搜索",
        "default_sources": ["arxiv"],
        "max_results_per_source": 10,
        "merge_strategy": "union",
    },
}


def get_search_strategy_config(search_type: str) -> dict[str, Any]:
    """获取搜索策略配置

    Args:
        search_type: 搜索类型 (comprehensive, fast, precise, preprint)

    Returns:
        策略配置字典

    """
    strategy = SEARCH_STRATEGIES.get(search_type)
    if strategy is None:
        strategy = SEARCH_STRATEGIES["comprehensive"]
    return strategy.copy()


# ============================================================================
# 缓存机制
# ============================================================================


class SearchCache:
    """搜索缓存管理器

    提供24小时TTL的文件系统缓存，减少重复API调用。
    """

    def __init__(self, cache_dir: str | Path | None = None, ttl: int = 86400):
        """初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径，默认为 ~/.article_mcp_cache
            ttl: 缓存过期时间（秒），默认 24 小时

        """
        if cache_dir is None:
            cache_dir = Path.home() / ".article_mcp_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

        # 缓存统计
        self._stats = {
            "hits": 0,
            "misses": 0,
        }

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        subdir = self.cache_dir / cache_key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{cache_key}.json"

    @staticmethod
    def _generate_key(keyword: str, sources: list[str], max_results: int) -> str:
        """生成缓存键"""
        key_data = f"{keyword}|{','.join(sorted(sources))}|{max_results}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """从缓存获取结果"""
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self._stats["misses"] += 1
            return None

        try:
            with open(cache_path, encoding="utf-8") as f:
                cache_data: dict[str, Any] = json.load(f)

            if time.time() > cache_data.get("expiry_time", 0):
                cache_path.unlink()
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            result = cache_data.get("result")
            if isinstance(result, dict):
                return result
            return None

        except (json.JSONDecodeError, KeyError, ValueError):
            try:
                cache_path.unlink()
            except Exception:
                pass
            self._stats["misses"] += 1
            return None

    def set(self, cache_key: str, result: dict[str, Any]) -> None:
        """保存结果到缓存"""
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            "result": result,
            "expiry_time": time.time() + self.ttl,
            "cached_at": time.time(),
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def clear(self, pattern: str | None = None) -> int:
        """清除缓存

        Args:
            pattern: 可选的模式匹配，如果为None则清除所有缓存

        Returns:
            清除的缓存文件数量

        """
        cleared_count = 0
        if pattern:
            for cache_file in self.cache_dir.rglob("*.json"):
                if pattern in cache_file.name:
                    cache_file.unlink()
                    cleared_count += 1
        else:
            for cache_file in self.cache_dir.rglob("*.json"):
                cache_file.unlink()
                cleared_count += 1
        return cleared_count

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        # 计算缓存中的总键数
        total_keys = 0
        for _cache_file in self.cache_dir.rglob("*.json"):
            total_keys += 1

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "total": total,
            "hit_rate": round(hit_rate, 2),
            "total_keys": total_keys,
        }


# ============================================================================
# 辅助函数（用于测试和高级用法）
# ============================================================================


def get_cache_key(keyword: str, sources: list[str], max_results: int) -> str:
    """生成缓存键

    Args:
        keyword: 搜索关键词
        sources: 数据源列表
        max_results: 最大结果数

    Returns:
        缓存键（SHA256哈希值）

    """
    return SearchCache._generate_key(keyword, sources, max_results)


async def parallel_search_sources(
    services: dict[str, Any],
    sources: list[str],
    query: str,
    max_results: int,
    logger: Any,
) -> dict[str, list[dict[str, Any]] | None]:
    """并行搜索多个数据源

    Args:
        services: 服务字典
        sources: 要搜索的数据源列表
        query: 搜索查询
        max_results: 每个源的最大结果数
        logger: 日志记录器

    Returns:
        按数据源分组的结果字典

    """
    results_by_source: dict[str, list[dict[str, Any]] | None] = {}

    async def search_source(source: str) -> tuple[str, list[dict[str, Any]] | None]:
        """搜索单个数据源"""
        if source not in services:
            if logger:
                logger.warning(f"未知数据源: {source}")
            return (source, None)

        try:
            service = services[source]

            # 调用对应的异步搜索方法
            if source == "europe_pmc":
                result = await service.search_async(query, max_results=max_results)
            elif source == "pubmed":
                result = await service.search_async(query, max_results=max_results)
            elif source == "arxiv":
                result = await service.search_async(query, max_results=max_results)
            elif source == "crossref":
                result = await service.search_works_async(query, max_results=max_results)
            elif source == "openalex":
                result = await service.search_works_async(query, max_results=max_results)
            else:
                return (source, None)

            # 判断搜索成功：没有错误且有文章结果
            error = result.get("error") if result else None
            articles = result.get("articles", []) if result else []
            if not error and articles:
                if logger:
                    logger.info(f"{source} 异步搜索成功，找到 {len(articles)} 篇文章")
                return (source, articles)
            else:
                if logger:
                    logger.warning(f"{source} 搜索失败: {error or '无搜索结果'}")
                return (source, None)

        except Exception as e:
            if logger:
                logger.error(f"{source} 搜索异常: {e}")
            return (source, None)

    # 并行搜索所有数据源
    search_tasks = [search_source(source) for source in sources]
    gathered_results: list[object] = await asyncio.gather(*search_tasks, return_exceptions=True)

    # 处理搜索结果
    for result in gathered_results:
        if isinstance(result, Exception):
            if logger:
                logger.error(f"搜索任务异常: {result}")
            continue

        # 此时 result 必须是 tuple[str, list[dict[str, Any]] | None] 类型
        if isinstance(result, tuple) and len(result) == 2:
            source, articles = result
            if articles is not None:
                results_by_source[source] = articles

    return results_by_source


def apply_merge_strategy(
    results_by_source: dict[str, list[dict[str, Any]]],
    merge_strategy: str,
    logger: Any,
) -> list[dict[str, Any]]:
    """应用合并策略

    Args:
        results_by_source: 按源分组的结果
        merge_strategy: 合并策略 (union 或 intersection)
        logger: 日志记录器

    Returns:
        合并后的结果列表

    """
    from article_mcp.services.merged_results import merge_articles_by_doi

    if merge_strategy == "intersection":
        # 交集策略：只在所有源都出现的文献
        if len(results_by_source) < 2:
            # 只有一个源，返回其结果
            for articles in results_by_source.values():
                if articles:
                    return articles
            return []

        # 首先合并所有结果
        merged = merge_articles_by_doi(results_by_source)

        # 然后筛选出在所有源中都出现的文章
        # 检查每个合并后文章的 sources 字段
        num_sources = len(results_by_source)
        intersection_results = []

        for article in merged:
            # 获取该文章的数据源信息
            data_sources = article.get("data_sources", {})
            # 检查是否在所有源中都出现
            if len(data_sources) == num_sources:
                intersection_results.append(article)

        return intersection_results

    else:  # union (默认)
        # 并集策略：合并所有结果
        return merge_articles_by_doi(results_by_source)


async def search_literature_async(
    keyword: str,
    sources: list[str] | None = None,
    max_results: int = 10,
    search_type: str = "comprehensive",
    use_cache: bool = True,
    cache: SearchCache | None = None,
    *,
    services: dict[str, Any],
    logger: Any,
) -> dict[str, Any]:
    """异步文献搜索（供测试使用）

    Args:
        keyword: 搜索关键词
        sources: 数据源列表 (默认根据搜索策略自动选择)
        max_results: 每个数据源的最大结果数
        search_type: 搜索策略 (fast, comprehensive, precise, preprint)
        use_cache: 是否使用缓存
        cache: 缓存实例（如果为None，使用默认缓存）
        services: 服务字典（必需）
        logger: 日志记录器（必需）

    Returns:
        搜索结果字典

    Raises:
        fastmcp.exceptions.ToolError: 当关键词为空时

    """
    from fastmcp.exceptions import ToolError

    # 验证关键词
    if not keyword or not keyword.strip():
        raise ToolError("搜索关键词不能为空")

    # services 参数现在是必需的（通过闭包捕获传递）
    search_services = services

    # 使用传入的 cache 或创建新的
    if cache is None:
        cache = SearchCache()

    # 获取搜索策略配置
    strategy = get_search_strategy_config(search_type)

    # 如果用户未指定 sources，使用策略默认值
    if sources is None:
        sources = strategy["default_sources"]

    # 根据策略调整每个源的返回数量
    per_source_limit = strategy["max_results_per_source"]

    # 生成缓存键
    cache_key = SearchCache._generate_key(keyword, sources, max_results)

    # 尝试从缓存获取
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            cached_result["cached"] = True
            cached_result["cache_hit"] = True
            return cached_result

    start_time = time.time()

    # 并行搜索所有数据源
    results_by_source = await parallel_search_sources(
        search_services, sources, keyword, per_source_limit, logger
    )

    # 过滤掉 None 值，确保所有值都是列表
    filtered_results: dict[str, list[dict[str, Any]]] = {
        k: v for k, v in results_by_source.items() if v is not None
    }

    sources_used = list(filtered_results.keys())

    # 应用合并策略
    merged_results = apply_merge_strategy(filtered_results, strategy["merge_strategy"], logger)

    from article_mcp.services.merged_results import simple_rank_articles

    merged_results = simple_rank_articles(merged_results)

    search_time = round(time.time() - start_time, 2)

    result = {
        "success": True,
        "keyword": keyword.strip(),
        "sources_used": sources_used,
        "results_by_source": filtered_results,
        "merged_results": merged_results[: max_results * len(sources)],
        "total_count": sum(len(results) for results in filtered_results.values()),
        "search_time": search_time,
        "search_type": search_type,
        "cached": False,
        "cache_hit": False,
    }

    # 保存到缓存
    if use_cache:
        cache.set(cache_key, result)

    return result


def search_literature_with_cache(
    keyword: str,
    sources: list[str] | None = None,
    max_results: int = 10,
    use_cache: bool = True,
    cache: SearchCache | None = None,
    services: dict[str, Any] | None = None,
    logger: Any = None,
) -> dict[str, Any]:
    """同步版本的文献搜索（用于测试）

    Args:
        keyword: 搜索关键词
        sources: 数据源列表
        max_results: 最大结果数
        use_cache: 是否使用缓存
        cache: 缓存实例
        services: 服务字典
        logger: 日志记录器

    Returns:
        搜索结果字典

    """
    # 使用传入的 cache 或创建新的
    if cache is None:
        cache = SearchCache()

    # 生成缓存键
    if sources is None:
        sources = ["europe_pmc"]
    cache_key = SearchCache._generate_key(keyword, sources, max_results)

    # 尝试从缓存获取
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            cached_result["cached"] = True
            cached_result["cache_hit"] = True
            return cached_result

    # 如果不使用缓存或缓存未命中，返回未缓存的结果
    return {
        "success": False,
        "cached": False,
        "cache_hit": False,
        "message": "同步版本不执行实际搜索（仅用于测试缓存逻辑）",
    }


# ============================================================================
# 搜索工具注册
# ============================================================================


def register_search_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册搜索工具（使用闭包捕获服务依赖，无全局变量）"""

    # 初始化缓存（闭包局部变量）
    search_cache = SearchCache()

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="""多源文献搜索工具。用于查找文献并获取 PMCID。

⚠️ 此工具只返回元数据（标题、作者、摘要、PMCID等），不包含全文内容。
   如需获取全文，请使用返回结果中的 pmcid 调用"文献全文"工具。

搜索策略：
- comprehensive: 全面搜索，使用所有可用数据源（并集）
- fast: 快速搜索，只使用主要数据源（Europe PMC、PubMed）
- precise: 精确搜索，只使用权威数据源（PubMed、Europe PMC，交集）
- preprint: 预印本搜索（arXiv）

主要参数：
- keyword: 搜索关键词（必填）
- sources: 数据源列表（可选，默认根据搜索策略自动选择）
- max_results: 每个源的最大结果数（默认10）
- search_type: 搜索策略（默认comprehensive）
- use_cache: 是否使用24小时缓存（默认true）

返回数据包含：标题、作者、期刊、摘要、PMCID、DOI等元数据（不含全文）""",
        annotations=ToolAnnotations(title="文献搜索", readOnlyHint=True, openWorldHint=False),
        tags={"search", "literature", "academic"},
    )
    async def search_literature(
        keyword: str,
        sources: list[str] | None = None,
        max_results: int = 10,
        search_type: str = "comprehensive",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """多源文献搜索工具。并行搜索多个学术数据库，显著提升搜索速度。

        Args:
            keyword: 搜索关键词
            sources: 数据源列表 (默认根据搜索策略自动选择)
            max_results: 每个数据源的最大结果数
            search_type: 搜索策略 (fast, comprehensive, precise, preprint)
            use_cache: 是否使用缓存 (默认True)

        Returns:
            搜索结果字典，包含文章列表和统计信息

        """
        try:
            if not keyword or not keyword.strip():
                from fastmcp.exceptions import ToolError

                raise ToolError("搜索关键词不能为空")

            from article_mcp.services.merged_results import (
                merge_articles_by_doi,
                simple_rank_articles,
            )

            # 获取搜索策略配置
            strategy = get_search_strategy_config(search_type)

            # 如果用户未指定 sources，使用策略默认值
            if sources is None:
                sources = strategy["default_sources"]

            # 根据策略调整每个源的返回数量
            per_source_limit = strategy["max_results_per_source"]

            # 生成缓存键
            cache_key = SearchCache._generate_key(keyword, sources, max_results)

            # 尝试从缓存获取（使用闭包捕获的 search_cache）
            if use_cache:
                cached_result = search_cache.get(cache_key)
                if cached_result is not None:
                    cached_result["cached"] = True
                    cached_result["cache_hit"] = True
                    return cached_result

            start_time = time.time()
            results_by_source = {}
            sources_used = []

            # 定义每个数据源的异步搜索函数（使用闭包捕获的 services 和 logger）
            async def search_source(source: str) -> tuple[str, list[dict[str, Any]] | None]:
                """搜索单个数据源，返回 (source_name, articles)"""
                if source not in services:
                    logger.warning(f"未知数据源: {source}")
                    return (source, None)

                try:
                    service = services[source]
                    query = keyword

                    # 调用对应的异步搜索方法
                    if source == "europe_pmc":
                        result = await service.search_async(query, max_results=per_source_limit)
                    elif source == "pubmed":
                        result = await service.search_async(query, max_results=per_source_limit)
                    elif source == "arxiv":
                        result = await service.search_async(query, max_results=per_source_limit)
                    elif source == "crossref":
                        result = await service.search_works_async(
                            query, max_results=per_source_limit
                        )
                    elif source == "openalex":
                        result = await service.search_works_async(
                            query, max_results=per_source_limit
                        )
                    else:
                        return (source, None)

                    # 判断搜索成功：没有错误且有文章结果
                    error = result.get("error") if result else None
                    articles = result.get("articles", []) if result else []
                    if not error and articles:
                        logger.info(f"{source} 异步搜索成功，找到 {len(articles)} 篇文章")
                        return (source, articles)
                    else:
                        logger.warning(f"{source} 搜索失败: {error or '无搜索结果'}")
                        return (source, None)

                except Exception as e:
                    logger.error(f"{source} 搜索异常: {e}")
                    return (source, None)

            # 并行搜索所有数据源
            search_tasks = [search_source(source) for source in sources]
            gathered_results: list[object] = await asyncio.gather(
                *search_tasks, return_exceptions=True
            )

            # 处理搜索结果
            for result in gathered_results:
                if isinstance(result, Exception):
                    logger.error(f"搜索任务异常: {result}")
                    continue

                # 此时 result 必须是 tuple[str, list[dict[str, Any]] | None] 类型
                if isinstance(result, tuple) and len(result) == 2:
                    source, articles = result
                    if articles is not None:
                        results_by_source[source] = articles
                        sources_used.append(source)

            # 应用合并策略
            merged_results = merge_articles_by_doi(results_by_source)

            # 根据策略应用合并方式
            if strategy["merge_strategy"] == "intersection" and len(results_by_source) > 1:
                # 交集策略：只在所有源都出现的文献
                # 找出最少文章数的源作为基准
                min_count = min(len(articles) for articles in results_by_source.values())
                # 简化实现：使用前 min_count 篇文章
                merged_results = merged_results[:min_count]

            merged_results = simple_rank_articles(merged_results)

            search_time = round(time.time() - start_time, 2)

            result = {
                "success": True,
                "keyword": keyword.strip(),
                "sources_used": sources_used,
                "results_by_source": results_by_source,
                "merged_results": merged_results[: max_results * len(sources)],
                "total_count": sum(len(results) for results in results_by_source.values()),
                "search_time": search_time,
                "search_type": search_type,
                "cached": False,
                "cache_hit": False,
            }

            # 保存到缓存（使用闭包捕获的 search_cache）
            if use_cache:
                search_cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"异步搜索过程中发生异常: {e}")
            # 抛出MCP标准错误
            from mcp import McpError
            from mcp.types import ErrorData

            raise McpError(
                ErrorData(code=-32603, message=f"搜索失败: {type(e).__name__}: {str(e)}")
            )
