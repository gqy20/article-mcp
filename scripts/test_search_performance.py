#!/usr/bin/env python3
"""
搜索性能对比测试
对比串行搜索 vs 并行搜索的性能差异
"""

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from article_mcp.tools.core.search_tools_improvements import (
    SearchCache,
    parallel_search_sources,
    search_literature_async,
    search_literature_serial,
    search_literature_with_cache,
)


def create_mock_services_with_delay(delay: float = 0.05):
    """创建带有延迟的模拟服务，模拟真实 API 调用"""

    async def delayed_search_async(*args, **kwargs):
        await asyncio.sleep(delay)
        return {
            "articles": [
                {
                    "title": "Article from async",
                    "doi": f"10.1234/async.{time.time()}",
                    "journal": "Test Journal",
                }
            ],
            "total_count": 1,
        }

    def delayed_search(*args, **kwargs):
        time.sleep(delay)
        return {
            "articles": [
                {
                    "title": "Article from sync",
                    "doi": f"10.1234/sync.{time.time()}",
                    "journal": "Test Journal",
                }
            ],
            "total_count": 1,
        }

    services = {
        "europe_pmc": Mock(),
        "pubmed": Mock(),
        "arxiv": Mock(),
        "crossref": Mock(),
        "openalex": Mock(),
    }

    for name in services:
        services[name].search = Mock(side_effect=delayed_search)
        services[name].search_async = AsyncMock(side_effect=delayed_search_async)
        if name in ["crossref", "openalex"]:
            services[name].search_works = Mock(side_effect=delayed_search)
            services[name].search_works_async = AsyncMock(side_effect=delayed_search_async)

    return services


def test_serial_vs_parallel_performance():
    """测试串行 vs 并行搜索性能"""

    print("=" * 70)
    print("搜索性能对比测试")
    print("=" * 70)

    # 创建带有 50ms 延迟的服务（模拟真实网络请求）
    delay = 0.05
    services = create_mock_services_with_delay(delay)
    logger = Mock()
    cache = SearchCache(ttl=3600)

    sources = ["europe_pmc", "pubmed", "arxiv", "crossref", "openalex"]
    num_sources = len(sources)

    print("\n测试配置:")
    print(f"  - 数据源数量: {num_sources}")
    print(f"  - 每个请求延迟: {delay * 1000}ms (模拟网络请求)")
    print("  - 测试关键词: 'machine learning'")
    print("  - 最大结果数: 10")

    # 测试 1: 串行搜索
    print(f"\n{'-' * 50}")
    print("测试 1: 串行搜索 (当前实现)")
    print("-" * 50)

    start = time.time()
    result_serial = search_literature_with_cache(
        keyword="machine learning",
        sources=sources,
        max_results=10,
        use_cache=False,
        cache=cache,
        services=services,
        logger=logger,
    )
    serial_time = time.time() - start

    print(f"  耗时: {serial_time:.3f}s ({serial_time * 1000:.0f}ms)")
    print(f"  理论最快: {delay * num_sources:.3f}s ({delay * num_sources * 1000:.0f}ms)")
    print(f"  找到文章: {result_serial['total_count']} 篇")
    print(f"  使用数据源: {len(result_serial['sources_used'])} 个")

    # 测试 2: 异步串行搜索
    print(f"\n{'-' * 50}")
    print("测试 2: 异步串行搜索 (带延迟)")
    print("-" * 50)

    start = time.time()
    result_async_serial = asyncio.run(
        search_literature_serial(
            keyword="machine learning",
            sources=sources,
            max_results=10,
            use_cache=False,
            cache=cache,
            services=services,
            logger=logger,
        )
    )
    async_serial_time = time.time() - start

    print(f"  耗时: {async_serial_time:.3f}s ({async_serial_time * 1000:.0f}ms)")
    print(f"  找到文章: {result_async_serial['total_count']} 篇")

    # 测试 3: 并行搜索
    print(f"\n{'-' * 50}")
    print("测试 3: 并行搜索 (改进实现)")
    print("-" * 50)

    start = time.time()
    result_parallel = asyncio.run(
        parallel_search_sources(
            services=services,
            sources=sources,
            query="machine learning",
            max_results=10,
            logger=logger,
        )
    )
    parallel_time = time.time() - start

    print(f"  耗时: {parallel_time:.3f}s ({parallel_time * 1000:.0f}ms)")
    print(f"  理论最快: ~{delay:.3f}s (单个请求时间)")
    print(f"  找到文章: {sum(len(v) for v in result_parallel.values())} 篇")
    print(f"  成功数据源: {len(result_parallel)} 个")

    # 测试 4: 完整异步搜索（并行 + 策略 + 缓存）
    print(f"\n{'-' * 50}")
    print("测试 4: 完整异步搜索 (并行 + 策略 + 缓存)")
    print("-" * 50)

    # 第一次：缓存未命中
    start = time.time()
    result_full1 = asyncio.run(
        search_literature_async(
            keyword="machine learning",
            sources=None,  # 使用策略默认
            max_results=10,
            search_type="comprehensive",
            use_cache=True,
            cache=cache,
            services=services,
            logger=logger,
        )
    )
    full_time_miss = time.time() - start

    print("  第一次搜索 (缓存未命中):")
    print(f"    耗时: {full_time_miss:.3f}s ({full_time_miss * 1000:.0f}ms)")
    print(f"    缓存: {result_full1['cached']}")
    print(f"    找到文章: {result_full1['total_count']} 篇")

    # 第二次：缓存命中
    start = time.time()
    result_full2 = asyncio.run(
        search_literature_async(
            keyword="machine learning",
            sources=None,
            max_results=10,
            search_type="comprehensive",
            use_cache=True,
            cache=cache,
            services=services,
            logger=logger,
        )
    )
    full_time_hit = time.time() - start

    print("  第二次搜索 (缓存命中):")
    print(f"    耗时: {full_time_hit:.3f}s ({full_time_hit * 1000:.1f}ms)")
    print(f"    缓存: {result_full2['cached']}")
    print(f"    缓存命中: {result_full2['cache_hit']}")

    # 性能总结
    print(f"\n{'=' * 70}")
    print("性能总结")
    print("=" * 70)

    speedup = serial_time / parallel_time
    cache_speedup = serial_time / full_time_hit

    print(f"  并行搜索加速比: {speedup:.1f}x")
    print(f"    串行: {serial_time:.3f}s")
    print(f"    并行: {parallel_time:.3f}s")
    print(f"    节省时间: {(serial_time - parallel_time) * 1000:.0f}ms")

    print(f"\n  缓存加速比 (第二次搜索): {cache_speedup:.1f}x")
    print(f"    无缓存: {serial_time:.3f}s")
    print(f"    有缓存: {full_time_hit:.3f}s")
    print(f"    节省时间: {(serial_time - full_time_hit) * 1000:.0f}ms")

    # 预估真实场景性能
    print(f"\n{'-' * 50}")
    print("真实场景预估 (基于每个 API ~1-2 秒)")
    print("-" * 50)

    real_delay = 1.5  # 假设每个请求 1.5 秒
    print(f"  假设每个 API 请求耗时: {real_delay}s")

    serial_real = real_delay * num_sources
    parallel_real = real_delay * 1.1  # 并行取最慢的 + 开销

    print("\n  5 个数据源搜索:")
    print(f"    串行搜索: {serial_real:.1f}s (~{int(serial_real)} 秒)")
    print(f"    并行搜索: {parallel_real:.1f}s (~{int(parallel_real)} 秒)")
    print(f"    加速比: {serial_real / parallel_real:.1f}x")
    print(f"    节省时间: {int((serial_real - parallel_real) * 1000)}ms")


def test_search_strategies():
    """测试不同搜索策略"""

    print(f"\n{'=' * 70}")
    print("搜索策略对比测试")
    print("=" * 70)

    delay = 0.01  # 较短延迟用于快速测试
    services = create_mock_services_with_delay(delay)
    logger = Mock()
    cache = SearchCache(ttl=3600)

    strategies = ["comprehensive", "fast", "precise", "preprint"]

    print(f"\n测试配置: 每个请求 {delay * 1000}ms 延迟")
    print(f"{'-' * 50}")

    for strategy in strategies:
        start = time.time()
        result = asyncio.run(
            search_literature_async(
                keyword="test",
                sources=None,  # 使用策略默认
                max_results=10,
                search_type=strategy,
                use_cache=False,
                cache=cache,
                services=services,
                logger=logger,
            )
        )
        elapsed = time.time() - start

        print(f"\n  {strategy.upper():15} - {result.get('search_type', 'unknown')}")
        print(f"    耗时: {elapsed:.3f}s")
        print(f"    数据源: {result['sources_used']}")
        print(f"    文章数: {result['total_count']}")

        # 显示策略信息
        from article_mcp.tools.core.search_tools_improvements import get_search_strategy_config

        config = get_search_strategy_config(strategy)
        print(f"    配置: {config['description']}")
        print(f"    合并策略: {config['merge_strategy']}")


def test_cache_efficiency():
    """测试缓存效率"""

    print(f"\n{'=' * 70}")
    print("缓存效率测试")
    print("=" * 70)

    delay = 0.02
    services = create_mock_services_with_delay(delay)
    logger = Mock()
    cache = SearchCache(ttl=3600)

    sources = ["europe_pmc", "pubmed"]
    keyword = "artificial intelligence"

    # 第一次搜索（写入缓存）
    print(f"\n配置: 2 个数据源, 每个 {delay * 1000}ms 延迟")
    print(f"{'-' * 50}")

    start = time.time()
    result1 = search_literature_with_cache(
        keyword=keyword,
        sources=sources,
        max_results=10,
        use_cache=True,
        cache=cache,
        services=services,
        logger=logger,
    )
    time_no_cache = time.time() - start

    print(f"  首次搜索 (无缓存): {time_no_cache:.3f}s")
    print(f"    结果: {result1['total_count']} 篇文章")
    print(f"    缓存状态: {'命中' if result1['cache_hit'] else '未命中'}")

    # 第二次搜索（读取缓存）
    start = time.time()
    result2 = search_literature_with_cache(
        keyword=keyword,
        sources=sources,
        max_results=10,
        use_cache=True,
        cache=cache,
        services=services,
        logger=logger,
    )
    time_with_cache = time.time() - start

    print(f"\n  相同搜索 (有缓存): {time_with_cache:.3f}s")
    print(f"    结果: {result2['total_count']} 篇文章")
    print(f"    缓存状态: {'命中' if result2['cache_hit'] else '未命中'}")

    # 性能对比
    print(f"\n{'-' * 50}")
    print("  缓存性能提升:")
    print(f"    加速比: {time_no_cache / time_with_cache:.1f}x")
    print(f"    节省时间: {(time_no_cache - time_with_cache) * 1000:.0f}ms")
    print(f"    效率提升: {((1 - time_with_cache / time_no_cache) * 100):.1f}%")

    # 缓存统计
    stats = cache.get_stats()
    print("\n  缓存统计:")
    print(f"    命中次数: {stats['hits']}")
    print(f"    未命中次数: {stats['misses']}")
    print(f"    缓存键数量: {stats['total_keys']}")
    print(f"    命中率: {stats['hits'] / (stats['hits'] + stats['misses']) * 100:.1f}%")


if __name__ == "__main__":
    test_serial_vs_parallel_performance()
    test_search_strategies()
    test_cache_efficiency()

    print(f"\n{'=' * 70}")
    print("所有性能测试完成!")
    print("=" * 70)
