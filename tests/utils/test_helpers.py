#!/usr/bin/env python3
"""
测试辅助工具和模拟数据生成器
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class MockDataGenerator:
    """模拟数据生成器"""

    @staticmethod
    def create_article(
        title: str = "Test Article",
        authors: list[str] = None,
        doi: str = "10.1000/test",
        pmid: str = "12345678",
        pmcid: str = "PMC1234567",
        **kwargs,
    ) -> dict[str, Any]:
        """创建模拟文章数据"""
        if authors is None:
            authors = ["Test Author", "Second Author"]

        article = {
            "title": title,
            "authors": authors,
            "doi": doi,
            "pmid": pmid,
            "pmcid": pmcid,
            "journal": kwargs.get("journal", "Test Journal"),
            "publication_date": kwargs.get("publication_date", "2023-01-01"),
            "abstract": kwargs.get("abstract", "This is a test article abstract."),
            "keywords": kwargs.get("keywords", ["test", "article"]),
            "url": kwargs.get("url", f"https://doi.org/{doi}"),
            "source": kwargs.get("source", "test"),
        }

        # 添加额外字段
        article.update(kwargs)
        return article

    @staticmethod
    def create_search_results(count: int = 5, **kwargs) -> dict[str, Any]:
        """创建模拟搜索结果"""
        articles = []
        for i in range(count):
            article = MockDataGenerator.create_article(
                title=f"Test Article {i+1}",
                doi=f"10.1000/test-{i+1}",
                pmid=f"{12345678+i}",
                **kwargs,
            )
            articles.append(article)

        return {
            "articles": articles,
            "total_count": count,
            "query": kwargs.get("query", "test query"),
            "search_time": kwargs.get("search_time", 1.5),
        }

    @staticmethod
    def create_reference_list(count: int = 10, **kwargs) -> list[dict[str, Any]]:
        """创建模拟参考文献列表"""
        references = []
        for i in range(count):
            ref = MockDataGenerator.create_article(
                title=f"Reference Article {i+1}",
                doi=f"10.1000/ref-{i+1}",
                pmid=f"{20000000+i}",
                **kwargs,
            )
            references.append(ref)
        return references


class TestTimer:
    """测试计时器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    def stop(self) -> float:
        """停止计时并返回耗时"""
        if self.end_time is None:
            self.end_time = time.time()
        return self.end_time - self.start_time

    def elapsed(self) -> float:
        """获取已经过的时间"""
        current_time = time.time()
        return current_time - self.start_time if self.start_time else 0


class MockResponse:
    """模拟HTTP响应"""

    def __init__(
        self,
        json_data: dict[str, Any] = None,
        status_code: int = 200,
        text: str = "",
        ok: bool = True,
    ):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.ok = ok

    def json(self) -> dict[str, Any]:
        return self.json_data


def create_mock_service(service_class, **method_returns):
    """创建模拟服务实例"""
    service = Mock(spec=service_class)

    for method_name, return_value in method_returns.items():
        mock_method = Mock(return_value=return_value)
        if asyncio.iscoroutinefunction(return_value) or hasattr(return_value, "__await__"):
            mock_method = asyncio.coroutine(lambda r=return_value: r)()
        setattr(service, method_name, mock_method)

    return service


def assert_valid_article_structure(article: dict[str, Any]) -> None:
    """验证文章结构的有效性"""
    required_fields = ["title", "authors"]
    for field in required_fields:
        assert field in article, f"文章缺少必需字段: {field}"
        assert article[field], f"文章字段 {field} 不能为空"

    # 验证作者字段
    assert isinstance(article["authors"], list), "作者字段必须是列表"
    assert len(article["authors"]) > 0, "作者列表不能为空"

    # 验证可选的标识符字段
    for id_field in ["doi", "pmid", "pmcid"]:
        if id_field in article and article[id_field]:
            assert isinstance(article[id_field], str), f"{id_field} 必须是字符串"


def assert_valid_search_results(results: dict[str, Any]) -> None:
    """验证搜索结果结构的有效性"""
    required_fields = ["articles", "total_count"]
    for field in required_fields:
        assert field in results, f"搜索结果缺少必需字段: {field}"

    assert isinstance(results["articles"], list), "articles 字段必须是列表"
    assert isinstance(results["total_count"], int), "total_count 必须是整数"
    assert results["total_count"] >= 0, "total_count 不能为负数"

    # 验证文章数量一致性
    if "articles" in results:
        actual_count = len(results["articles"])
        assert results["total_count"] >= actual_count, "total_count 应该大于等于实际文章数量"

    # 验证每篇文章的结构
    for i, article in enumerate(results["articles"]):
        try:
            assert_valid_article_structure(article)
        except AssertionError as e:
            raise AssertionError(f"第 {i+1} 篇文章结构无效: {e}")


def run_async_with_timeout(coro, timeout: float = 10.0):
    """运行异步协程并设置超时"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
    except asyncio.TimeoutError:
        raise TimeoutError(f"操作在 {timeout} 秒后超时")
    finally:
        if not loop.is_running():
            loop.close()


# 测试标记
pytest_plugins = ["pytest_asyncio"]

# 默认配置
DEFAULT_TEST_CONFIG = {
    "test_keyword": "machine learning",
    "test_doi": "10.1000/test-article",
    "test_pmid": "12345678",
    "max_results": 10,
    "timeout": 30.0,
}


@pytest.fixture
def mock_logger():
    """模拟日志记录器fixture"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def test_config():
    """测试配置fixture"""
    return DEFAULT_TEST_CONFIG.copy()


@pytest.fixture
def mock_search_results():
    """模拟搜索结果fixture"""
    return MockDataGenerator.create_search_results(5)


@pytest.fixture
def mock_article_details():
    """模拟文章详情fixture"""
    return MockDataGenerator.create_article()


@pytest.fixture
def mock_reference_list():
    """模拟参考文献列表fixture"""
    return MockDataGenerator.create_reference_list(10)
