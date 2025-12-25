#!/usr/bin/env python3
"""search_literature 工具改进测试 - TDD 驱动
测试方案 A 的三个改进:
1. asyncio 并行搜索
2. search_type 搜索策略
3. 缓存机制
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入被测试的模块（功能已合并到 search_tools.py）
from article_mcp.tools.core.search_tools import (
    SEARCH_STRATEGIES,
    SearchCache,
    apply_merge_strategy,
    get_cache_key,
    get_search_strategy_config,
    parallel_search_sources,
    search_literature_async,
    search_literature_with_cache,
)

# ============================================================================
# Fixture 定义
# ============================================================================


@pytest.fixture
def mock_logger():
    """提供测试用的 logger"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_search_services():
    """提供模拟的搜索服务集合（支持异步）"""
    services = {}

    # Europe PMC 服务
    europe_pmc = Mock()
    europe_pmc.search = Mock(
        return_value={
            "articles": [
                {
                    "title": "Machine Learning in Healthcare from Europe PMC",
                    "authors": ["AI Researcher"],
                    "doi": "10.1234/ml.health.epmc.2023",
                    "journal_name": "Health AI Journal",
                    "publication_date": "2023-06-15",
                    "pmid": "37891234",
                }
            ],
            "total_count": 1,
        }
    )
    europe_pmc.search_async = AsyncMock(
        return_value={
            "articles": [
                {
                    "title": "Machine Learning in Healthcare from Europe PMC",
                    "authors": ["AI Researcher"],
                    "doi": "10.1234/ml.health.epmc.2023",
                    "journal_name": "Health AI Journal",
                    "publication_date": "2023-06-15",
                    "pmid": "37891234",
                }
            ],
            "total_count": 1,
        }
    )
    services["europe_pmc"] = europe_pmc

    # PubMed 服务
    pubmed = Mock()
    pubmed.search = Mock(
        return_value={
            "articles": [
                {
                    "title": "Deep Learning Applications from PubMed",
                    "authors": ["ML Specialist"],
                    "doi": "10.5678/dl.apps.pubmed.2023",
                    "journal": "Machine Learning Today",
                    "publication_date": "2023-05-20",
                    "pmid": "37654321",
                }
            ],
            "total_count": 1,
        }
    )
    pubmed.search_async = AsyncMock(
        return_value={
            "articles": [
                {
                    "title": "Deep Learning Applications from PubMed",
                    "authors": ["ML Specialist"],
                    "doi": "10.5678/dl.apps.pubmed.2023",
                    "journal": "Machine Learning Today",
                    "publication_date": "2023-05-20",
                    "pmid": "37654321",
                }
            ],
            "total_count": 1,
        }
    )
    services["pubmed"] = pubmed

    # arXiv 服务
    arxiv = Mock()
    arxiv.search = Mock(
        return_value={
            "articles": [
                {
                    "title": "Neural Network Theory from arXiv",
                    "authors": ["Theory Expert"],
                    "doi": "10.9999/nn.theory.arxiv.2023",
                    "journal": "arXiv preprint",
                    "publication_date": "2023",
                }
            ],
            "total_count": 1,
        }
    )
    arxiv.search_async = AsyncMock(
        return_value={
            "articles": [
                {
                    "title": "Neural Network Theory from arXiv",
                    "authors": ["Theory Expert"],
                    "doi": "10.9999/nn.theory.arxiv.2023",
                    "journal": "arXiv preprint",
                    "publication_date": "2023",
                }
            ],
            "total_count": 1,
        }
    )
    services["arxiv"] = arxiv

    # CrossRef 服务
    crossref = Mock()
    crossref.search_works = Mock(
        return_value={
            "articles": [
                {
                    "title": "AI Ethics from CrossRef",
                    "authors": ["Ethics Researcher"],
                    "doi": "10.3456/ai.ethics.crossref.2023",
                    "journal": "Ethics in AI Journal",
                    "publication_date": "2023",
                }
            ],
            "total_count": 1,
        }
    )
    crossref.search_works_async = AsyncMock(
        return_value={
            "articles": [
                {
                    "title": "AI Ethics from CrossRef",
                    "authors": ["Ethics Researcher"],
                    "doi": "10.3456/ai.ethics.crossref.2023",
                    "journal": "Ethics in AI Journal",
                    "publication_date": "2023",
                }
            ],
            "total_count": 1,
        }
    )
    services["crossref"] = crossref

    # OpenAlex 服务
    openalex = Mock()
    openalex.search_works = Mock(
        return_value={
            "articles": [
                {
                    "title": "Computer Vision Advances from OpenAlex",
                    "authors": ["CV Expert"],
                    "doi": "10.7890/cv.adv.openalex.2023",
                    "journal": "Computer Vision Today",
                    "publication_date": "2023",
                }
            ],
            "total_count": 1,
        }
    )
    openalex.search_works_async = AsyncMock(
        return_value={
            "articles": [
                {
                    "title": "Computer Vision Advances from OpenAlex",
                    "authors": ["CV Expert"],
                    "doi": "10.7890/cv.adv.openalex.2023",
                    "journal": "Computer Vision Today",
                    "publication_date": "2023",
                }
            ],
            "total_count": 1,
        }
    )
    services["openalex"] = openalex

    return services


@pytest.fixture
def search_cache(tmp_path):
    """提供测试用的缓存目录"""
    cache_dir = tmp_path / ".article_mcp_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


# ============================================================================
# 测试类 1: 异步并行搜索功能
# ============================================================================


class TestAsyncParallelSearch:
    """测试异步并行搜索功能"""

    @pytest.mark.asyncio
    async def test_parallel_search_executes_concurrently(self, mock_search_services, mock_logger):
        """测试并行搜索是否真正并发执行"""
        # 导入需要测试的模块

        # 为每个服务添加延迟，模拟真实 API 调用
        async def delayed_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return {
                "articles": [{"title": "Delayed Result", "doi": "10.1234/delayed"}],
                "total_count": 1,
            }

        for service in mock_search_services.values():
            if hasattr(service, "search_async"):
                service.search_async = AsyncMock(side_effect=delayed_search)

        # 测试并行搜索
        sources = ["europe_pmc", "pubmed", "arxiv"]
        query = "machine learning"
        max_results = 10

        start_time = time.time()
        results = await parallel_search_sources(
            mock_search_services, sources, query, max_results, mock_logger
        )
        elapsed_time = time.time() - start_time

        # 验证并行执行：时间应该接近单个请求的时间，而非串行累加
        # 串行执行约需 0.3 秒 (3 * 0.1)，并行执行约需 0.1 秒
        assert elapsed_time < 0.2, f"并行搜索耗时 {elapsed_time:.2f}s，应小于 0.2s"
        assert len(results) == 3
        assert "europe_pmc" in results
        assert "pubmed" in results
        assert "arxiv" in results

    @pytest.mark.asyncio
    async def test_parallel_search_handles_partial_failure(self, mock_search_services, mock_logger):
        """测试并行搜索时部分服务失败的处理"""

        # 让 pubmed 搜索失败
        async def failing_search(*args, **kwargs):
            raise Exception("PubMed API Error")

        mock_search_services["pubmed"].search_async = AsyncMock(side_effect=failing_search)

        sources = ["europe_pmc", "pubmed", "arxiv"]
        query = "machine learning"
        max_results = 10

        results = await parallel_search_sources(
            mock_search_services, sources, query, max_results, mock_logger
        )

        # 验证：成功的源应该返回结果，失败的源应该被跳过
        assert "europe_pmc" in results
        assert "arxiv" in results
        # pubmed 失败，可能不在结果中或者结果为空
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_parallel_search_with_unknown_source(self, mock_search_services, mock_logger):
        """测试并行搜索遇到未知数据源的处理"""
        sources = ["europe_pmc", "unknown_source", "arxiv"]
        query = "machine learning"
        max_results = 10

        results = await parallel_search_sources(
            mock_search_services, sources, query, max_results, mock_logger
        )

        # 验证：未知源应该被跳过，其他源正常工作
        assert "europe_pmc" in results
        assert "arxiv" in results
        assert "unknown_source" not in results
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_parallel_search_empty_sources_list(self, mock_search_services, mock_logger):
        """测试空的源列表"""
        sources = []
        query = "machine learning"
        max_results = 10

        results = await parallel_search_sources(
            mock_search_services, sources, query, max_results, mock_logger
        )

        assert results == {}


# ============================================================================
# 测试类 2: search_type 搜索策略
# ============================================================================


class TestSearchTypeStrategies:
    """测试 search_type 搜索策略"""

    @pytest.mark.unit
    def test_comprehensive_search_type(self, mock_search_services, mock_logger):
        """测试 comprehensive 搜索类型：使用全部数据源"""
        strategy = get_search_strategy_config("comprehensive")

        # 验证策略配置
        assert strategy["name"] == "comprehensive"
        assert strategy["description"] == "全面搜索，使用所有可用数据源"
        assert set(strategy["default_sources"]) == {
            "europe_pmc",
            "pubmed",
            "arxiv",
            "crossref",
            "openalex",
        }
        assert strategy["max_results_per_source"] == 10
        assert strategy["merge_strategy"] == "union"

    @pytest.mark.unit
    def test_fast_search_type(self, mock_search_services, mock_logger):
        """测试 fast 搜索类型：只使用主要数据源"""
        strategy = get_search_strategy_config("fast")

        # 验证策略配置
        assert strategy["name"] == "fast"
        assert strategy["description"] == "快速搜索，只使用主要数据源"
        assert set(strategy["default_sources"]) == {"europe_pmc", "pubmed"}
        assert strategy["max_results_per_source"] == 5  # 较少结果数
        assert strategy["merge_strategy"] == "union"

    @pytest.mark.unit
    def test_precise_search_type(self, mock_search_services, mock_logger):
        """测试 precise 搜索类型：使用权威数据源，交集合并"""
        strategy = get_search_strategy_config("precise")

        # 验证策略配置
        assert strategy["name"] == "precise"
        assert strategy["description"] == "精确搜索，使用权威数据源"
        assert set(strategy["default_sources"]) == {"pubmed", "europe_pmc"}
        assert strategy["max_results_per_source"] == 10
        assert strategy["merge_strategy"] == "intersection"

    @pytest.mark.unit
    def test_preprint_search_type(self, mock_search_services, mock_logger):
        """测试 preprint 搜索类型：只使用预印本平台"""
        strategy = get_search_strategy_config("preprint")

        # 验证策略配置
        assert strategy["name"] == "preprint"
        assert strategy["description"] == "预印本搜索"
        assert "arxiv" in strategy["default_sources"]
        assert strategy["merge_strategy"] == "union"

    @pytest.mark.unit
    def test_invalid_search_type_defaults_to_comprehensive(self, mock_search_services, mock_logger):
        """测试无效搜索类型回退到 comprehensive"""
        strategy = get_search_strategy_config("invalid_type")

        # 应该回退到 comprehensive
        assert strategy["name"] == "comprehensive"

    @pytest.mark.unit
    def test_union_merge_strategy(self, mock_logger):
        """测试并集合并策略"""
        results_by_source = {
            "europe_pmc": [
                {"title": "Article 1", "doi": "10.1111/article1"},
                {"title": "Article 2", "doi": "10.1111/article2"},
            ],
            "pubmed": [
                {"title": "Article 3", "doi": "10.1111/article3"},
                {"title": "Article 4", "doi": "10.1111/article4"},
            ],
        }

        merged = apply_merge_strategy(results_by_source, "union", mock_logger)

        # 并集应该包含所有文章
        assert len(merged) == 4

    @pytest.mark.unit
    def test_intersection_merge_strategy(self, mock_logger):
        """测试交集合并策略"""
        # 模拟相同的文章出现在多个源
        results_by_source = {
            "europe_pmc": [
                {"title": "Common Article", "doi": "10.1111/common"},
                {"title": "EPMC Only", "doi": "10.1111/epmc_only"},
            ],
            "pubmed": [
                {"title": "Common Article", "doi": "10.1111/common"},
                {"title": "PubMed Only", "doi": "10.1111/pubmed_only"},
            ],
        }

        merged = apply_merge_strategy(results_by_source, "intersection", mock_logger)

        # 交集应该只包含在所有源中都出现的文章
        assert len(merged) == 1
        assert merged[0]["doi"] == "10.1111/common"

    @pytest.mark.unit
    def test_search_type_affects_max_results_per_source(self, mock_search_services, mock_logger):
        """测试搜索类型影响每个源的最大结果数"""
        comprehensive = get_search_strategy_config("comprehensive")
        fast = get_search_strategy_config("fast")

        # fast 策略每个源返回的结果应该更少
        assert fast["max_results_per_source"] < comprehensive["max_results_per_source"]


# ============================================================================
# 测试类 3: 缓存机制
# ============================================================================


class TestSearchCache:
    """测试搜索缓存机制"""

    @pytest.mark.unit
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        # 相同参数应该生成相同的缓存键
        key1 = get_cache_key("machine learning", ["europe_pmc", "pubmed"], 10)
        key2 = get_cache_key("machine learning", ["europe_pmc", "pubmed"], 10)

        assert key1 == key2

        # 不同参数应该生成不同的缓存键
        key3 = get_cache_key("deep learning", ["europe_pmc", "pubmed"], 10)
        key4 = get_cache_key("machine learning", ["europe_pmc"], 10)
        key5 = get_cache_key("machine learning", ["europe_pmc", "pubmed"], 20)

        assert key1 != key3
        assert key1 != key4
        assert key1 != key5

        # sources 顺序不应该影响缓存键
        key6 = get_cache_key("ml", ["pubmed", "europe_pmc"], 10)
        key7 = get_cache_key("ml", ["europe_pmc", "pubmed"], 10)
        assert key6 == key7

    @pytest.mark.unit
    def test_cache_save_and_retrieve(self, search_cache, mock_logger):
        """测试缓存保存和读取"""
        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 保存测试结果
        cache_key = "test_key_123"
        test_result = {
            "success": True,
            "keyword": "machine learning",
            "sources_used": ["europe_pmc", "pubmed"],
            "merged_results": [{"title": "Test Article", "doi": "10.1234/test"}],
            "total_count": 1,
        }

        cache.set(cache_key, test_result)

        # 验证缓存文件存在
        cache_file = search_cache / cache_key[:2] / f"{cache_key}.json"
        assert cache_file.exists()

        # 读取缓存
        retrieved = cache.get(cache_key)

        assert retrieved is not None
        assert retrieved["success"] == test_result["success"]
        assert retrieved["keyword"] == test_result["keyword"]
        assert len(retrieved["merged_results"]) == 1

    @pytest.mark.unit
    def test_cache_expiration(self, search_cache, mock_logger):
        """测试缓存过期"""
        import time

        # 创建一个很快过期的缓存
        cache = SearchCache(cache_dir=str(search_cache), ttl=1)

        cache_key = "expiring_key"
        test_result = {"success": True, "cached": True}

        cache.set(cache_key, test_result)

        # 立即读取应该成功
        retrieved = cache.get(cache_key)
        assert retrieved is not None

        # 等待过期
        time.sleep(1.1)

        # 过期后读取应该返回 None
        retrieved_expired = cache.get(cache_key)
        assert retrieved_expired is None

    @pytest.mark.unit
    def test_cache_miss(self, search_cache, mock_logger):
        """测试缓存未命中"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 读取不存在的缓存
        retrieved = cache.get("nonexistent_key")

        assert retrieved is None

    @pytest.mark.unit
    def test_cache_clear(self, search_cache, mock_logger):
        """测试缓存清理"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 保存多个缓存项
        for i in range(5):
            cache.set(f"key_{i}", {"data": i})

        # 清理所有缓存
        cleared_count = cache.clear()
        assert cleared_count >= 5

        # 验证缓存已清空
        for i in range(5):
            retrieved = cache.get(f"key_{i}")
            assert retrieved is None

    @pytest.mark.unit
    def test_cache_clear_with_pattern(self, search_cache, mock_logger):
        """测试带模式的缓存清理"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 保存不同类型的缓存
        cache.set("search_ml_123", {"query": "ml"})
        cache.set("search_dl_456", {"query": "dl"})
        cache.set("export_789", {"type": "export"})

        # 只清理搜索相关的缓存
        cleared_count = cache.clear(pattern="search")
        assert cleared_count == 2

        # 验证
        assert cache.get("search_ml_123") is None
        assert cache.get("search_dl_456") is None
        assert cache.get("export_789") is not None

    @pytest.mark.unit
    def test_cache_hit_tracking(self, search_cache, mock_logger):
        """测试缓存命中统计"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 初始统计
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total_keys"] == 0

        # 保存缓存
        cache.set("test_key", {"data": "test"})

        # 缓存命中
        cache.get("test_key")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

        # 缓存未命中
        cache.get("nonexistent_key")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_keys"] == 1

    @pytest.mark.unit
    def test_use_cache_parameter(self, mock_search_services, mock_logger, search_cache):
        """测试 use_cache 参数控制是否使用缓存"""
        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 预先填充缓存
        cache_key = cache._generate_key("machine learning", ["europe_pmc"], 10)
        cached_result = {
            "success": True,
            "keyword": "machine learning",
            "sources_used": ["europe_pmc"],
            "merged_results": [{"title": "Cached Article"}],
            "total_count": 1,
            "cached": True,
        }
        cache.set(cache_key, cached_result)

        # use_cache=True 应该从缓存获取
        result_with_cache = search_literature_with_cache(
            "machine learning",
            sources=["europe_pmc"],
            max_results=10,
            use_cache=True,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        assert result_with_cache["cached"] is True
        assert result_with_cache["cache_hit"] is True

        # use_cache=False 应该执行实际搜索（不使用缓存）
        result_without_cache = search_literature_with_cache(
            "machine learning",
            sources=["europe_pmc"],
            max_results=10,
            use_cache=False,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        assert result_without_cache.get("cached") is not True

    @pytest.mark.unit
    def test_cache_metadata(self, search_cache, mock_logger):
        """测试缓存元数据"""
        import time

        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        cache_key = "metadata_test"
        test_result = {"success": True, "data": "test"}

        before_save = time.time()
        cache.set(cache_key, test_result)
        after_save = time.time()

        # 读取缓存文件验证元数据
        cache_file = search_cache / cache_key[:2] / f"{cache_key}.json"
        with open(cache_file, encoding="utf-8") as f:
            cache_data = json.load(f)

        assert "result" in cache_data
        assert "cached_at" in cache_data
        assert "expiry_time" in cache_data
        assert before_save <= cache_data["cached_at"] <= after_save


# ============================================================================
# 测试类 4: 集成测试
# ============================================================================


class TestSearchImprovementsIntegration:
    """搜索改进功能的集成测试"""

    @pytest.mark.asyncio
    async def test_full_async_search_with_strategy_and_cache(
        self, mock_search_services, search_cache, mock_logger
    ):
        """测试完整的异步搜索流程：策略 + 缓存"""
        # SearchCache is already imported at the top of the file

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 第一次搜索（缓存未命中）
        result1 = await search_literature_async(
            keyword="machine learning",
            sources=None,  # 使用策略默认值
            max_results=10,
            search_type="fast",
            use_cache=True,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        assert result1["success"] is True
        assert result1["cached"] is False
        assert result1["cache_hit"] is False
        assert result1["search_type"] == "fast"
        # fast 策略只使用 europe_pmc 和 pubmed
        assert set(result1["sources_used"]) <= {"europe_pmc", "pubmed"}

        # 第二次搜索（缓存命中）
        result2 = await search_literature_async(
            keyword="machine learning",
            sources=None,
            max_results=10,
            search_type="fast",
            use_cache=True,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        assert result2["success"] is True
        assert result2["cached"] is True
        assert result2["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_search_strategies_affect_sources_used(self, mock_search_services, mock_logger):
        """测试不同搜索策略使用不同的数据源"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        # 创建临时缓存
        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # comprehensive 策略
        result_comprehensive = await search_literature_async(
            keyword="test",
            sources=None,
            max_results=10,
            search_type="comprehensive",
            use_cache=False,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        # fast 策略
        result_fast = await search_literature_async(
            keyword="test",
            sources=None,
            max_results=10,
            search_type="fast",
            use_cache=False,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        # comprehensive 应该使用更多数据源
        assert len(result_comprehensive["sources_used"]) >= len(result_fast["sources_used"])

    @pytest.mark.asyncio
    async def test_parallel_search_performance_improvement(
        self, mock_search_services, mock_logger, search_cache
    ):
        """测试并行搜索的性能改进"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 添加延迟模拟真实 API 调用
        async def delayed_search(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms 延迟
            return {
                "articles": [{"title": "Delayed", "doi": "10.1234/delayed"}],
                "total_count": 1,
            }

        for service in mock_search_services.values():
            if hasattr(service, "search_async"):
                service.search_async = AsyncMock(side_effect=delayed_search)

        # 测试异步并行搜索
        start_async = time.time()
        result_async = await search_literature_async(
            keyword="performance test",
            sources=["europe_pmc", "pubmed", "arxiv", "crossref"],
            max_results=5,
            use_cache=False,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )
        async_time = time.time() - start_async

        # 验证：并行搜索时间应该远小于串行搜索时间
        # 4 个源，每个 50ms：串行约 200ms，并行约 50ms
        assert async_time < 0.15, f"异步搜索耗时 {async_time:.2f}s，应小于 0.15s"
        assert result_async["success"] is True


# ============================================================================
# 测试类 5: 边界情况和错误处理
# ============================================================================


class TestSearchImprovementsEdgeCases:
    """测试边界情况和错误处理"""

    @pytest.mark.asyncio
    async def test_empty_keyword_raises_error(self, mock_search_services, mock_logger):
        """测试空关键词抛出错误"""
        from fastmcp.exceptions import ToolError

        # SearchCache is already imported at the top of the file

        cache = SearchCache(ttl=3600)

        with pytest.raises(ToolError, match="搜索关键词不能为空"):
            await search_literature_async(
                keyword="",
                services=mock_search_services,
                cache=cache,
                logger=mock_logger,
            )

    @pytest.mark.asyncio
    async def test_all_sources_fail_gracefully(self, mock_search_services, mock_logger):
        """测试所有数据源都失败时的优雅处理"""
        # SearchCache is already imported at the top of the file

        cache = SearchCache(ttl=3600)

        # 让所有服务都失败
        async def failing_search(*args, **kwargs):
            raise Exception("All services down")

        for service in mock_search_services.values():
            if hasattr(service, "search_async"):
                service.search_async = AsyncMock(side_effect=failing_search)

        result = await search_literature_async(
            keyword="test",
            sources=["europe_pmc", "pubmed"],
            use_cache=False,
            cache=cache,
            services=mock_search_services,
            logger=mock_logger,
        )

        # 应该返回空结果而非抛出异常
        assert result["total_count"] == 0
        assert len(result["sources_used"]) == 0
        assert result["success"] is True  # 请求成功，但无结果

    @pytest.mark.unit
    def test_cache_corruption_handling(self, search_cache, mock_logger):
        """测试缓存损坏时的处理"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 创建损坏的缓存文件
        cache_key = "corrupted_key"
        cache_file = search_cache / cache_key[:2] / f"{cache_key}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_file, "w") as f:
            f.write("invalid json content {{{")

        # 读取损坏的缓存应该返回 None 而非抛出异常
        result = cache.get(cache_key)
        assert result is None

    @pytest.mark.unit
    def test_cache_with_none_result(self, search_cache, mock_logger):
        """测试缓存 None 值"""
        from article_mcp.tools.core.search_tools import (
            SearchCache,
        )

        cache = SearchCache(cache_dir=str(search_cache), ttl=3600)

        # 保存 None 结果（表示搜索失败但应缓存）
        cache.set("none_result", None)

        # 读取应该返回 None
        result = cache.get("none_result")
        assert result is None

        # 验证缓存存在
        cache_file = search_cache / "no" / "none_result.json"
        # 文件应该存在（即使内容为 null）
        assert cache_file.exists() is True or cache_file.parent.exists()
