"""缓存并发安全测试 - TDD Red 阶段

此测试验证缓存文件在并发写入场景下的数据安全性。

测试场景：
1. 多个线程同时写入不同的期刊数据
2. 验证最终缓存包含所有写入的数据（无数据丢失）
3. 验证缓存文件格式正确（无损坏）
"""

import asyncio
import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from article_mcp.tools.core import quality_tools


@pytest.fixture
def temp_cache_dir():
    """创建临时缓存目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "journal_quality"
        cache_dir.mkdir(parents=True, exist_ok=True)
        yield cache_dir


@pytest.fixture
def mock_cache_env(temp_cache_dir):
    """设置环境变量指向临时缓存目录"""
    with patch.dict(os.environ, {"JOURNAL_CACHE_DIR": str(temp_cache_dir)}):
        # 重新加载模块以应用新的环境变量
        import importlib

        importlib.reload(quality_tools)
        yield


def test_concurrent_cache_writes_no_data_loss(mock_cache_env, temp_cache_dir):
    """测试：并发写入缓存时不应丢失数据

    TDD Red 阶段：此测试在无文件锁时会失败
    """
    # 准备测试数据：10个不同的期刊
    test_journals = {
        f"Journal {i}": {
            "success": True,
            "journal_name": f"Journal {i}",
            "quality_metrics": {"impact_factor": 10.0 + i},
            "ranking_info": {},
            "data_source": "test",
        }
        for i in range(10)
    }

    cache_file = temp_cache_dir / "journal_data.json"
    logger = MagicMock()

    # 定义写入函数（模拟并发场景）
    def write_journal_data(journal_name: str, data: dict):
        """模拟单个期刊的缓存写入操作"""
        quality_tools._save_to_file_cache(journal_name, data, logger)

    # 创建10个线程同时写入
    threads = []
    for journal_name, data in test_journals.items():
        thread = threading.Thread(target=write_journal_data, args=(journal_name, data))
        threads.append(thread)

    # 启动所有线程（并发执行）
    for thread in threads:
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join(timeout=10)

    # 验证缓存文件存在
    assert cache_file.exists(), "缓存文件应该存在"

    # 读取缓存文件内容
    with open(cache_file, encoding="utf-8") as f:
        cache_data = json.load(f)

    # 验证：所有期刊都应该被写入（无数据丢失）
    cached_journals = cache_data.get("journals", {})
    assert len(cached_journals) == 10, f"期望10个期刊，实际找到 {len(cached_journals)} 个"

    # 验证：每个期刊的数据都正确
    for journal_name, expected_data in test_journals.items():
        assert journal_name in cached_journals, f"期刊 '{journal_name}' 丢失"
        cached_entry = cached_journals[journal_name]
        assert "data" in cached_entry, f"期刊 '{journal_name}' 缺少 data 字段"

        # 验证数据内容正确
        actual_data = cached_entry["data"]
        assert actual_data["journal_name"] == expected_data["journal_name"]
        assert (
            actual_data["quality_metrics"]["impact_factor"]
            == expected_data["quality_metrics"]["impact_factor"]
        )


def test_concurrent_write_and_read(mock_cache_env, temp_cache_dir):
    """测试：并发读写混合场景下数据一致性

    TDD Red 阶段：验证读写并发时不会读到损坏的数据
    """
    cache_file = temp_cache_dir / "journal_data.json"
    logger = MagicMock()

    # 先预置一个期刊数据
    initial_data = {
        "success": True,
        "journal_name": "Initial Journal",
        "quality_metrics": {"impact_factor": 5.0},
        "ranking_info": {},
        "data_source": "test",
    }
    quality_tools._save_to_file_cache("Initial Journal", initial_data, logger)

    # 定义并发操作
    results = {"read_errors": 0, "write_errors": 0, "success_count": 0}
    lock = threading.Lock()

    def read_journal():
        """读取操作"""
        try:
            for _ in range(50):
                result = quality_tools._get_from_file_cache("Initial Journal", logger)
                if result is None:
                    with lock:
                        results["read_errors"] += 1
                with lock:
                    results["success_count"] += 1
        except Exception as e:
            with lock:
                results["read_errors"] += 1

    def write_journal(journal_id: int):
        """写入操作"""
        try:
            data = {
                "success": True,
                "journal_name": f"Journal {journal_id}",
                "quality_metrics": {"impact_factor": float(journal_id)},
                "ranking_info": {},
                "data_source": "test",
            }
            quality_tools._save_to_file_cache(f"Journal {journal_id}", data, logger)
            with lock:
                results["success_count"] += 1
        except Exception as e:
            with lock:
                results["write_errors"] += 1

    # 创建混合读写负载：1个读线程 + 5个写线程
    threads = []
    threads.append(threading.Thread(target=read_journal))
    for i in range(5):
        threads.append(threading.Thread(target=write_journal, args=(i,)))

    # 启动所有线程
    for thread in threads:
        thread.start()

    # 等待完成
    for thread in threads:
        thread.join(timeout=10)

    # 验证：不应该有读写错误
    assert results["read_errors"] == 0, f"发现 {results['read_errors']} 个读取错误"
    assert results["write_errors"] == 0, f"发现 {results['write_errors']} 个写入错误"

    # 验证：初始数据仍然存在
    final_result = quality_tools._get_from_file_cache("Initial Journal", logger)
    assert final_result is not None, "初始期刊数据丢失"
    assert final_result["journal_name"] == "Initial Journal"


def test_concurrent_same_journal_writes_last_write_wins(mock_cache_env, temp_cache_dir):
    """测试：并发写入同一期刊时，最后写入的数据应该胜出

    这是预期行为：后写入的数据覆盖先写入的数据。
    但关键是要保证数据完整性（不损坏）。
    """
    cache_file = temp_cache_dir / "journal_data.json"
    logger = MagicMock()

    # 所有线程写入同一个期刊，但值不同
    write_count = 20
    threads = []

    def write_journal_with_value(value: int):
        data = {
            "success": True,
            "journal_name": "Same Journal",
            "quality_metrics": {"impact_factor": float(value)},
            "ranking_info": {},
            "data_source": "test",
        }
        quality_tools._save_to_file_cache("Same Journal", data, logger)

    # 创建多个线程同时写入同一期刊
    for i in range(write_count):
        thread = threading.Thread(target=write_journal_with_value, args=(i,))
        threads.append(thread)

    # 并发启动
    for thread in threads:
        thread.start()

    # 等待完成
    for thread in threads:
        thread.join(timeout=10)

    # 验证：文件应该完整且可解析
    assert cache_file.exists(), "缓存文件应该存在"

    with open(cache_file, encoding="utf-8") as f:
        cache_data = json.load(f)  # 如果文件损坏会抛出异常

    # 验证：数据结构正确
    assert "journals" in cache_data
    assert "Same Journal" in cache_data["journals"]

    # 验证：impact_factor 应该是某个写入的值（0-19之一）
    cached_if = cache_data["journals"]["Same Journal"]["data"]["quality_metrics"]["impact_factor"]
    assert 0 <= cached_if < write_count, f"无效的 impact_factor 值: {cached_if}"
