"""
search_literature 工具改进实现
基于 TDD 驱动开发，实现以下改进:
1. asyncio 并行搜索
2. search_type 搜索策略
3. 缓存机制

此文件包含新功能，待测试通过后可合并到 search_tools.py
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError


# ============================================================================
# 搜索策略配置
# ============================================================================

# 定义搜索策略
SEARCH_STRATEGIES = {
    "comprehensive": {
        "name": "comprehensive",
        "description": "全面搜索，使用所有可用数据源",
        "default_sources": ["europe_pmc", "pubmed", "arxiv", "crossref", "openalex"],
        "max_results_per_source": 10,  # 每个源返回的最大结果数
        "merge_strategy": "union",  # 并集合并
    },
    "fast": {
        "name": "fast",
        "description": "快速搜索，只使用主要数据源",
        "default_sources": ["europe_pmc", "pubmed"],
        "max_results_per_source": 5,  # 较少结果数以加快速度
        "merge_strategy": "union",
    },
    "precise": {
        "name": "precise",
        "description": "精确搜索，使用权威数据源",
        "default_sources": ["pubmed", "europe_pmc"],
        "max_results_per_source": 10,
        "merge_strategy": "intersection",  # 交集：只在多个源都出现的文献
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
        # 无效类型回退到 comprehensive
        strategy = SEARCH_STRATEGIES["comprehensive"]
    return strategy.copy()


# ============================================================================
# 缓存机制
# ============================================================================

class SearchCache:
    """搜索缓存管理器"""

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
        """获取缓存文件路径

        使用前两位作为子目录，避免单个目录文件过多
        """
        subdir = self.cache_dir / cache_key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{cache_key}.json"

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """从缓存获取结果

        Args:
            cache_key: 缓存键

        Returns:
            缓存的结果，如果不存在或已过期则返回 None
        """
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self._stats["misses"] += 1
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查是否过期
            if time.time() > cache_data.get("expiry_time", 0):
                # 缓存过期，删除文件
                cache_path.unlink()
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return cache_data.get("result")

        except (json.JSONDecodeError, KeyError, ValueError):
            # 缓存文件损坏，删除并返回 None
            try:
                cache_path.unlink()
            except Exception:
                pass
            self._stats["misses"] += 1
            return None

    def set(self, cache_key: str, result: dict[str, Any]) -> None:
        """保存结果到缓存

        Args:
            cache_key: 缓存键
            result: 要缓存的结果
        """
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            "result": result,
            "cached_at": time.time(),
            "expiry_time": time.time() + self.ttl,
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except (OSError, IOError) as e:
            logging.getLogger(__name__).warning(f"保存缓存失败: {e}")

    def clear(self, pattern: str | None = None) -> int:
        """清理缓存

        Args:
            pattern: 可选的模式匹配，只清理包含该模式的缓存

        Returns:
            清理的缓存文件数量
        """
        cleared = 0
        for cache_file in self.cache_dir.rglob("*.json"):
            if pattern is None or pattern in cache_file.name:
                try:
                    cache_file.unlink()
                    cleared += 1
                except OSError:
                    pass
        return cleared

    def get_stats(self) -> dict[str, int]:
        """获取缓存统计信息

        Returns:
            包含 hits, misses, total_keys 的字典
        """
        total_keys = sum(1 for _ in self.cache_dir.rglob("*.json"))
        return {
            **self._stats,
            "total_keys": total_keys,
        }

    @staticmethod
    def _generate_key(keyword: str, sources: list[str], max_results: int) -> str:
        """生成缓存键（静态方法供外部使用）

        Args:
            keyword: 搜索关键词
            sources: 数据源列表
            max_results: 最大结果数

        Returns:
            缓存键（SHA256 哈希）
        """
        params = {
            "keyword": keyword.strip().lower(),
            "sources": sorted(sources),  # 排序确保顺序不影响键
            "max_results": max_results,
            "version": "v1",
        }
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(params_str.encode()).hexdigest()


def get_cache_key(keyword: str, sources: list[str], max_results: int) -> str:
    """生成缓存键

    Args:
        keyword: 搜索关键词
        sources: 数据源列表
        max_results: 最大结果数

    Returns:
        缓存键（SHA256 哈希）
    """
    return SearchCache._generate_key(keyword, sources, max_results)


# ============================================================================
# 异步并行搜索
# ============================================================================

async def parallel_search_sources(
    services: dict[str, Any],
    sources: list[str],
    query: str,
    max_results: int,
    logger: logging.Logger,
) -> dict[str, dict[str, Any]]:
    """并行搜索多个数据源

    Args:
        services: 服务字典
        sources: 要搜索的数据源列表
        query: 搜索查询
        max_results: 每个源的最大结果数
        logger: 日志记录器

    Returns:
        数据源到搜索结果的映射
    """
    results = {}

    async def search_single_source(source: str) -> tuple[str, dict[str, Any] | None]:
        """搜索单个数据源"""
        if source not in services:
            logger.warning(f"未知数据源: {source}")
            return (source, None)

        try:
            service = services[source]

            # 尝试使用异步方法
            if hasattr(service, "search_async"):
                result = await service.search_async(query, max_results=max_results)
            elif source == "europe_pmc":
                result = service.search(query, max_results=max_results)
            elif source == "pubmed":
                result = service.search(query, max_results=max_results)
            elif source == "arxiv":
                result = service.search(query, max_results=max_results)
            elif source == "crossref":
                result = service.search_works(query, max_results=max_results)
            elif source == "openalex":
                result = service.search_works(query, max_results=max_results)
            else:
                logger.warning(f"不支持的数据源: {source}")
                return (source, None)

            return (source, result)

        except Exception as e:
            logger.error(f"{source} 搜索异常: {e}")
            return (source, None)

    # 创建所有搜索任务
    tasks = [search_single_source(source) for source in sources]

    # 并行执行所有任务
    search_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    for item in search_results:
        if isinstance(item, Exception):
            logger.error(f"搜索任务异常: {item}")
            continue

        source, result = item
        if result is None:
            continue

        # 判断搜索成功
        error = result.get("error")
        articles = result.get("articles", [])
        if not error and articles:
            results[source] = articles
            logger.info(f"{source} 搜索成功，找到 {len(articles)} 篇文章")
        else:
            logger.warning(f"{source} 搜索失败: {error or '无搜索结果'}")

    return results


# ============================================================================
# 合并策略
# ============================================================================

def apply_merge_strategy(
    results_by_source: dict[str, list[dict[str, Any]]],
    merge_strategy: str,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """应用合并策略

    Args:
        results_by_source: 各数据源的搜索结果
        merge_strategy: 合并策略 (union 或 intersection)
        logger: 日志记录器

    Returns:
        合并后的结果列表
    """
    if merge_strategy == "intersection":
        return _intersection_merge(results_by_source, logger)
    else:
        # 默认使用并集
        return _union_merge(results_by_source, logger)


def _union_merge(
    results_by_source: dict[str, list[dict[str, Any]]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """并集合并：返回所有文章，去重"""
    from article_mcp.services.merged_results import merge_articles_by_doi
    return merge_articles_by_doi(results_by_source)


def _intersection_merge(
    results_by_source: dict[str, list[dict[str, Any]]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """交集合并：只返回在所有数据源中都出现的文章

    使用 DOI 作为判断依据
    """
    if not results_by_source:
        return []

    # 收集每个源的 DOI 集合
    doi_sets = {}
    for source, articles in results_by_source.items():
        doi_sets[source] = {
            article.get("doi") for article in articles if article.get("doi")
        }

    # 找出在所有源中都出现的 DOI
    if not doi_sets:
        return []

    common_dois = set.intersection(*doi_sets.values())

    # 收集对应的文章
    common_articles = []
    seen_dois = set()

    for source, articles in results_by_source.items():
        for article in articles:
            doi = article.get("doi")
            if doi in common_dois and doi not in seen_dois:
                article["source"] = source
                common_articles.append(article)
                seen_dois.add(doi)

    logger.info(f"交集合并：{len(common_articles)} 篇文章在所有数据源中都出现")
    return common_articles


# ============================================================================
# 完整的异步搜索函数
# ============================================================================

async def search_literature_async(
    keyword: str,
    sources: list[str] | None = None,
    max_results: int = 10,
    search_type: str = "comprehensive",
    use_cache: bool = True,
    cache: SearchCache | None = None,
    services: dict[str, Any] | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """异步文献搜索（支持并行、策略、缓存）

    Args:
        keyword: 搜索关键词
        sources: 数据源列表，None 则使用策略默认值
        max_results: 最大结果数
        search_type: 搜索策略 (comprehensive, fast, precise, preprint)
        use_cache: 是否使用缓存
        cache: 缓存实例，None 则创建新实例
        services: 服务字典
        logger: 日志记录器

    Returns:
        搜索结果字典
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # 参数验证
    if not keyword or not keyword.strip():
        raise ToolError("搜索关键词不能为空")

    if services is None:
        raise ToolError("服务字典不能为空")

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
    cache_key = get_cache_key(keyword, sources, max_results)

    # 尝试从缓存获取
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            cached_result["cached"] = True
            cached_result["cache_hit"] = True
            return cached_result

    # 缓存未命中，执行搜索
    start_time = time.time()

    # 并行搜索所有数据源
    results_by_source = await parallel_search_sources(
        services, sources, keyword.strip(), per_source_limit, logger
    )

    sources_used = list(results_by_source.keys())

    # 应用合并策略
    from article_mcp.services.merged_results import simple_rank_articles

    merged_results = apply_merge_strategy(results_by_source, strategy["merge_strategy"], logger)
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

    # 保存到缓存
    if use_cache:
        cache.set(cache_key, result)

    return result


# ============================================================================
# 同步包装函数（向后兼容）
# ============================================================================

def search_literature_with_cache(
    keyword: str,
    sources: list[str] | None = None,
    max_results: int = 10,
    search_type: str = "comprehensive",
    use_cache: bool = True,
    cache: SearchCache | None = None,
    services: dict[str, Any] | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """同步文献搜索（支持缓存和策略，但串行执行）

    这是向后兼容的包装函数，使用串行搜索而非并行。

    Args:
        keyword: 搜索关键词
        sources: 数据源列表
        max_results: 最大结果数
        search_type: 搜索策略
        use_cache: 是否使用缓存
        cache: 缓存实例
        services: 服务字典
        logger: 日志记录器

    Returns:
        搜索结果字典
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # 参数验证
    if not keyword or not keyword.strip():
        raise ToolError("搜索关键词不能为空")

    if services is None:
        raise ToolError("服务字典不能为空")

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
    cache_key = get_cache_key(keyword, sources, max_results)

    # 尝试从缓存获取
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            cached_result["cached"] = True
            cached_result["cache_hit"] = True
            return cached_result

    # 缓存未命中，执行串行搜索
    start_time = time.time()
    results_by_source = {}
    sources_used = []

    # 串行搜索每个数据源
    for source in sources:
        if source not in services:
            logger.warning(f"未知数据源: {source}")
            continue

        try:
            service = services[source]
            query = keyword.strip()

            if source == "europe_pmc":
                result = service.search(query, max_results=per_source_limit)
            elif source == "pubmed":
                result = service.search(query, max_results=per_source_limit)
            elif source == "arxiv":
                result = service.search(query, max_results=per_source_limit)
            elif source == "crossref":
                result = service.search_works(query, max_results=per_source_limit)
            elif source == "openalex":
                result = service.search_works(query, max_results=per_source_limit)
            else:
                continue

            error = result.get("error")
            articles = result.get("articles", [])
            if not error and articles:
                results_by_source[source] = articles
                sources_used.append(source)
                logger.info(f"{source} 搜索成功，找到 {len(articles)} 篇文章")

        except Exception as e:
            logger.error(f"{source} 搜索异常: {e}")
            continue

    # 应用合并策略
    from article_mcp.services.merged_results import simple_rank_articles

    merged_results = apply_merge_strategy(results_by_source, strategy["merge_strategy"], logger)
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

    # 保存到缓存
    if use_cache:
        cache.set(cache_key, result)

    return result


# ============================================================================
# 串行搜索函数（用于性能对比测试）
# ============================================================================

async def search_literature_serial(
    keyword: str,
    sources: list[str] | None = None,
    max_results: int = 10,
    use_cache: bool = False,
    cache: SearchCache | None = None,
    services: dict[str, Any] | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """串行文献搜索（用于性能对比）

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
    if logger is None:
        logger = logging.getLogger(__name__)

    if services is None:
        raise ToolError("服务字典不能为空")

    if cache is None:
        cache = SearchCache()

    if sources is None:
        sources = ["europe_pmc", "pubmed"]

    cache_key = get_cache_key(keyword, sources, max_results)

    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    start_time = time.time()
    results_by_source = {}
    sources_used = []

    # 串行搜索，每个源之间添加延迟模拟真实场景
    for source in sources:
        if source not in services:
            continue

        # 模拟网络延迟
        await asyncio.sleep(0.05)

        try:
            service = services[source]
            query = keyword.strip()

            if source == "europe_pmc":
                result = service.search(query, max_results=max_results)
            elif source == "pubmed":
                result = service.search(query, max_results=max_results)
            elif source == "arxiv":
                result = service.search(query, max_results=max_results)
            elif source == "crossref":
                result = service.search_works(query, max_results=max_results)
            elif source == "openalex":
                result = service.search_works(query, max_results=max_results)
            else:
                continue

            error = result.get("error")
            articles = result.get("articles", [])
            if not error and articles:
                results_by_source[source] = articles
                sources_used.append(source)

        except Exception as e:
            logger.error(f"{source} 搜索异常: {e}")

    from article_mcp.services.merged_results import merge_articles_by_doi, simple_rank_articles

    merged_results = merge_articles_by_doi(results_by_source)
    merged_results = simple_rank_articles(merged_results)

    result = {
        "success": True,
        "keyword": keyword.strip(),
        "sources_used": sources_used,
        "results_by_source": results_by_source,
        "merged_results": merged_results[: max_results * len(sources)],
        "total_count": sum(len(results) for results in results_by_source.values()),
        "search_time": round(time.time() - start_time, 2),
    }

    if use_cache:
        cache.set(cache_key, result)

    return result
