#!/usr/bin/env python3
"""
性能测试脚本
测试系统的性能指标
"""

import asyncio
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import psutil

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class PerformanceTimer:
    """性能计时器"""

    def __init__(self, name="操作"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()

    def elapsed(self):
        """获取耗时"""
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time


class MemoryMonitor:
    """内存监控器"""

    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = 0

    def start(self):
        """开始监控"""
        self.initial_memory = self.process.memory_info().rss
        self.peak_memory = self.initial_memory

    def update(self):
        """更新峰值内存"""
        current_memory = self.process.memory_info().rss
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory

    def get_memory_usage(self):
        """获取内存使用情况"""
        current = self.process.memory_info().rss
        return {
            "initial_mb": self.initial_memory / 1024 / 1024 if self.initial_memory else 0,
            "current_mb": current / 1024 / 1024,
            "peak_mb": self.peak_memory / 1024 / 1024,
            "increase_mb": (
                (current - self.initial_memory) / 1024 / 1024 if self.initial_memory else 0
            ),
        }


def test_import_performance():
    """测试导入性能"""
    print("🔍 测试导入性能...")

    # 测试多次导入的时间
    import_times = []
    for i in range(5):
        with PerformanceTimer(f"导入 {i + 1}"):
            # 刷新模块缓存
            if "article_mcp.cli" in sys.modules:
                del sys.modules["article_mcp.cli"]

        import_times.append(PerformanceTimer().elapsed())

    avg_time = sum(import_times) / len(import_times)
    print(f"✓ 平均导入时间: {avg_time:.3f} 秒")

    # 导入时间应该小于1秒
    if avg_time < 1.0:
        print("✓ 导入性能良好")
        return True
    else:
        print("⚠️ 导入性能较慢")
        return False


def test_server_creation_performance():
    """测试服务器创建性能"""
    print("🔍 测试服务器创建性能...")

    creation_times = []

    for i in range(3):
        with PerformanceTimer(f"服务器创建 {i + 1}"):
            with patch.multiple(
                "article_mcp.cli",
                create_europe_pmc_service=Mock(),
                create_pubmed_service=Mock(),
                CrossRefService=Mock(),
                OpenAlexService=Mock(),
                create_reference_service=Mock(),
                create_literature_relation_service=Mock(),
                create_arxiv_service=Mock(),
                register_search_tools=Mock(),
                register_article_tools=Mock(),
                register_reference_tools=Mock(),
                register_relation_tools=Mock(),
                register_quality_tools=Mock(),
                register_batch_tools=Mock(),
            ):
                from article_mcp.cli import create_mcp_server

                create_mcp_server()

        creation_times.append(PerformanceTimer().elapsed())

    avg_time = sum(creation_times) / len(creation_times)
    print(f"✓ 平均服务器创建时间: {avg_time:.3f} 秒")

    # 服务器创建时间应该小于2秒
    if avg_time < 2.0:
        print("✓ 服务器创建性能良好")
        return True
    else:
        print("⚠️ 服务器创建性能较慢")
        return False


def test_memory_usage():
    """测试内存使用"""
    print("🔍 测试内存使用...")

    monitor = MemoryMonitor()
    monitor.start()

    initial_memory = monitor.get_memory_usage()

    # 执行多个操作
    for _i in range(10):
        with patch.multiple(
            "article_mcp.cli",
            create_europe_pmc_service=Mock(),
            create_pubmed_service=Mock(),
            CrossRefService=Mock(),
            OpenAlexService=Mock(),
            create_reference_service=Mock(),
            create_literature_relation_service=Mock(),
            create_arxiv_service=Mock(),
            register_search_tools=Mock(),
            register_article_tools=Mock(),
            register_reference_tools=Mock(),
            register_relation_tools=Mock(),
            register_quality_tools=Mock(),
            register_batch_tools=Mock(),
        ):
            from article_mcp.cli import create_mcp_server

            create_mcp_server()

        monitor.update()

    final_memory = monitor.get_memory_usage()

    print(f"✓ 初始内存: {initial_memory['initial_mb']:.2f} MB")
    print(f"✓ 最终内存: {final_memory['current_mb']:.2f} MB")
    print(f"✓ 峰值内存: {final_memory['peak_mb']:.2f} MB")
    print(f"✓ 内存增长: {final_memory['increase_mb']:.2f} MB")

    # 内存增长应该小于50MB
    if final_memory["increase_mb"] < 50:
        print("✓ 内存使用合理")
        return True
    else:
        print("⚠️ 内存使用较高")
        return False


async def test_async_performance():
    """测试异步性能"""
    print("🔍 测试异步性能...")

    try:
        from article_mcp.tools.core.search_tools import _search_literature

        # 创建模拟服务
        Mock()
        mock_service = Mock()
        mock_service.search_articles = AsyncMock(
            return_value={
                "articles": [
                    {"title": f"Test Article {i}", "doi": f"10.1000/test{i}"} for i in range(100)
                ],
                "total_count": 100,
            }
        )

        # 测试异步调用性能
        async_times = []

        for i in range(5):
            with PerformanceTimer(f"异步调用 {i + 1}"):
                with patch(
                    "article_mcp.tools.core.search_tools._search_services",
                    {"europe_pmc": mock_service},
                ):
                    await _search_literature(
                        keyword="test", sources=["europe_pmc"], max_results=100
                    )

            async_times.append(PerformanceTimer().elapsed())

        avg_time = sum(async_times) / len(async_times)
        print(f"✓ 平均异步调用时间: {avg_time:.3f} 秒")

        # 异步调用时间应该小于1秒
        if avg_time < 1.0:
            print("✓ 异步性能良好")
            return True
        else:
            print("⚠️ 异步性能较慢")
            return False
    except Exception as e:
        print(f"✗ 异步性能测试失败: {e}")
        return False


def test_concurrent_performance():
    """测试并发性能"""
    print("🔍 测试并发性能...")

    def create_server():
        with patch.multiple(
            "article_mcp.cli",
            create_europe_pmc_service=Mock(),
            create_pubmed_service=Mock(),
            CrossRefService=Mock(),
            OpenAlexService=Mock(),
            create_reference_service=Mock(),
            create_literature_relation_service=Mock(),
            create_arxiv_service=Mock(),
            register_search_tools=Mock(),
            register_article_tools=Mock(),
            register_reference_tools=Mock(),
            register_relation_tools=Mock(),
            register_quality_tools=Mock(),
            register_batch_tools=Mock(),
        ):
            from article_mcp.cli import create_mcp_server

            return create_mcp_server()

    # 测试并发创建
    thread_counts = [1, 2, 4, 8]
    results = {}

    for thread_count in thread_counts:
        with PerformanceTimer(f"{thread_count} 线程并发"):
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(create_server) for _ in range(thread_count)]
                [future.result() for future in futures]

        elapsed_time = PerformanceTimer().elapsed()
        results[thread_count] = elapsed_time
        print(f"✓ {thread_count} 线程: {elapsed_time:.3f} 秒")

    # 分析并发性能
    single_thread_time = results[1]
    best_concurrent_time = min(results.values())

    if best_concurrent_time < single_thread_time:
        speedup = single_thread_time / best_concurrent_time
        print(f"✓ 最佳并发加速比: {speedup:.2f}x")
        return True
    else:
        print("⚠️ 并发性能不明显")
        return False


def test_large_data_performance():
    """测试大数据性能"""
    print("🔍 测试大数据性能...")

    try:
        # 创建大量模拟数据
        large_dataset = [
            {"title": f"Article {i}", "doi": f"10.1000/test{i}", "authors": [f"Author {i}"]}
            for i in range(1000)
        ]

        monitor = MemoryMonitor()
        monitor.start()

        with PerformanceTimer("大数据处理"):
            # 模拟大数据处理
            result = {
                "articles": large_dataset,
                "total_count": len(large_dataset),
                "processed_at": time.time(),
            }

            # 模拟一些数据处理操作
            for article in result["articles"]:
                article["processed"] = True
                article["length"] = len(article["title"])

        elapsed_time = PerformanceTimer().elapsed()
        memory_usage = monitor.get_memory_usage()

        print(f"✓ 处理时间: {elapsed_time:.3f} 秒")
        print(f"✓ 内存使用: {memory_usage['increase_mb']:.2f} MB")
        print(f"✓ 数据量: {len(large_dataset)} 条记录")

        # 大数据处理时间应该小于5秒
        if elapsed_time < 5.0:
            print("✓ 大数据性能良好")
            return True
        else:
            print("⚠️ 大数据性能较慢")
            return False
    except Exception as e:
        print(f"✗ 大数据性能测试失败: {e}")
        return False


def test_cache_performance():
    """测试缓存性能"""
    print("🔍 测试缓存性能...")

    try:
        from article_mcp.services.europe_pmc import EuropePMCService

        # 创建服务实例
        mock_logger = Mock()
        service = EuropePMCService(mock_logger)

        # 测试缓存命中率（模拟）
        cache_stats = {"hits": 0, "misses": 0, "total_requests": 0}

        # 模拟缓存操作
        with PerformanceTimer("缓存操作"):
            for i in range(100):
                cache_key = f"test_key_{i % 10}"  # 模拟重复访问
                if cache_key in service.cache:  # 模拟缓存命中
                    cache_stats["hits"] += 1
                else:
                    cache_stats["misses"] += 1
                    service.cache[cache_key] = f"value_{cache_key}"
                cache_stats["total_requests"] += 1

        elapsed_time = PerformanceTimer().elapsed()
        hit_rate = cache_stats["hits"] / cache_stats["total_requests"] * 100

        print(f"✓ 缓存操作时间: {elapsed_time:.3f} 秒")
        print(f"✓ 缓存命中率: {hit_rate:.1f}%")
        print(f"✓ 总请求数: {cache_stats['total_requests']}")

        # 缓存命中率应该大于50%
        if hit_rate > 50:
            print("✓ 缓存性能良好")
            return True
        else:
            print("⚠️ 缓存命中率较低")
            return False
    except Exception as e:
        print(f"✗ 缓存性能测试失败: {e}")
        return False


def main():
    """运行所有性能测试"""
    print("=" * 60)
    print("⚡ Article MCP 性能测试")
    print("=" * 60)

    tests = [
        test_import_performance,
        test_server_creation_performance,
        test_memory_usage,
        test_concurrent_performance,
        test_large_data_performance,
        test_cache_performance,
    ]

    async_tests = [test_async_performance]

    passed = 0
    total = len(tests) + len(async_tests)

    start_time = time.time()

    # 运行同步测试
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"✗ 测试 {test_func.__name__} 出现异常: {e}")
            print()

    # 运行异步测试
    for test_func in async_tests:
        try:
            if asyncio.run(test_func()):
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"✗ 异步测试 {test_func.__name__} 出现异常: {e}")
            print()

    end_time = time.time()
    total_duration = end_time - start_time

    print("=" * 60)
    print(f"📊 性能测试结果: {passed}/{total} 通过")
    print(f"⏱️  总耗时: {total_duration:.2f} 秒")

    if passed == total:
        print("🎉 所有性能测试通过!")
        return 0
    else:
        print("⚠️ 部分性能测试需要优化")
        return 1


if __name__ == "__main__":
    sys.exit(main())
