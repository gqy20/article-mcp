#!/usr/bin/env python3
"""关键词趋势分析工具测试 - TDD RED 阶段

核心功能：
1. 关键词频率统计：统计每个词的总出现次数
2. 年份趋势图：按年份聚合词频
3. 趋势分类：growing/consolidated/declining
4. 边界情况：空数据、无年份、停用词过滤
"""

import logging
from collections import Counter
from unittest.mock import Mock

import pytest

from article_mcp.tools.core import keyword_trends

# ============================================================================
# 测试数据
# ============================================================================

# 多年份文献数据（用于趋势分析）
SAMPLE_ARTICLES_MULTIPLE_YEARS = [
    {
        "title": "Deep Learning for Image Recognition",
        "abstract": "We propose a deep learning approach for image recognition using convolutional neural networks.",
        "authors": [{"name": "Alex Krizhevsky"}],
        "journal": "Nature",
        "publication_date": "2020-01-15",
        "year": 2020,
        "doi": "10.1234/test.2020",
    },
    {
        "title": "Machine Learning in Healthcare",
        "abstract": "This study explores machine learning applications in healthcare and medical diagnosis.",
        "authors": [{"name": "John Smith"}],
        "journal": "Nature Medicine",
        "publication_date": "2021-03-20",
        "year": 2021,
        "doi": "10.1234/test.2021",
    },
    {
        "title": "Transformers for Natural Language Processing",
        "abstract": "Transformer architectures have revolutionized natural language processing and machine learning.",
        "authors": [{"name": "Jane Doe"}],
        "journal": "Science",
        "publication_date": "2022-06-10",
        "year": 2022,
        "doi": "10.1234/test.2022",
    },
    {
        "title": "Large Language Models and Their Applications",
        "abstract": "Large language models based on transformers show remarkable capabilities in natural language understanding.",
        "authors": [{"name": "Bob Johnson"}],
        "journal": "Nature",
        "publication_date": "2023-08-25",
        "year": 2023,
        "doi": "10.1234/test.2023",
    },
]

# 包含作者关键词的数据
SAMPLE_ARTICLES_WITH_KEYWORDS = [
    {
        "title": "Neural Networks",
        "abstract": "Deep neural networks for pattern recognition.",
        "authors": [{"name": "Alice"}],
        "publication_date": "2020-01-01",
        "year": 2020,
        "keywords": ["neural networks", "deep learning", "AI"],
    },
    {
        "title": "Machine Learning Methods",
        "abstract": "Various machine learning algorithms.",
        "authors": [{"name": "Bob"}],
        "publication_date": "2021-01-01",
        "year": 2021,
        "keywords": ["machine learning", "neural networks", "data science"],
    },
]

# 边界情况数据
EMPTY_ARTICLES = []
ARTICLES_NO_ABSTRACT = [
    {"title": "No Abstract", "authors": [], "year": 2020, "publication_date": "2020-01-01"}
]
ARTICLES_NO_YEAR = [
    {
        "title": "No Year",
        "abstract": "Has abstract but no year field",
        "authors": [],
        "publication_date": "2020-01-01",
    }
]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def logger():
    return logging.getLogger(__name__)


# ============================================================================
# 核心功能测试 1: 关键词频率统计
# ============================================================================


@pytest.mark.asyncio
class TestKeywordFrequencyStatistics:
    """核心功能测试 1: 关键词频率统计"""

    async def test_basic_word_frequency_count(self, logger):
        """测试：基础词频统计"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(SAMPLE_ARTICLES_MULTIPLE_YEARS)

        # 验证返回结果
        assert result is not None
        assert "trends" in result
        assert len(result["trends"]) > 0

        # 验证高频词存在（基于测试数据）
        top_keywords = [t["keyword"] for t in result["trends"][:5]]
        assert "learning" in top_keywords or "machine" in top_keywords

    async def test_total_frequency_calculation(self, logger):
        """测试：总频率计算正确"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(SAMPLE_ARTICLES_MULTIPLE_YEARS)

        # "learning" 应该出现多次（在多个标题/摘要中）
        learning_trend = next((t for t in result["trends"] if t["keyword"] == "learning"), None)
        assert learning_trend is not None
        assert learning_trend["total_freq"] > 0

    async def test_case_insensitive_counting(self, logger):
        """测试：词频统计不区分大小写"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(SAMPLE_ARTICLES_MULTIPLE_YEARS)

        # Learning, learning, LEARNING 应该被合并统计
        learning_lower = next((t for t in result["trends"] if t["keyword"] == "learning"), None)
        learning_upper = next((t for t in result["trends"] if t["keyword"] == "Learning"), None)

        # 应该只有一种形式（小写）
        assert (learning_lower is not None and learning_upper is None) or (
            learning_lower is None and learning_upper is not None
        )


# ============================================================================
# 核心功能测试 2: 年份趋势图
# ============================================================================


@pytest.mark.asyncio
class TestYearlyTrends:
    """核心功能测试 2: 年份趋势图"""

    async def test_yearly_aggregation(self, logger):
        """测试：按年份聚合词频"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 验证 yearly_freq 字段存在
        assert "trends" in result
        for trend in result["trends"]:
            assert "yearly_freq" in trend

    async def test_yearly_freq_structure(self, logger):
        """测试：yearly_freq 数据结构正确"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 检查某个关键词的年份分布
        learning_trend = next((t for t in result["trends"] if t["keyword"] == "learning"), None)
        assert learning_trend is not None
        assert isinstance(learning_trend["yearly_freq"], dict)

        # 验证年份在范围内
        for year, freq in learning_trend["yearly_freq"].items():
            assert 2020 <= year <= 2023
            assert isinstance(freq, int)
            assert freq >= 0

    async def test_year_range_filtering(self, logger):
        """测试：year_range 参数过滤"""
        keyword_trends._logger = logger

        # 只分析 2021-2022 年
        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2021, 2022)
        )

        # 验证摘要中的年份范围
        assert result["summary"]["year_range"] == [2021, 2022]

    async def test_continuous_year_coverage(self, logger):
        """测试：年份连续性（没有gap）"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 验证每个趋势的年份是连续的
        for trend in result["trends"][:5]:  # 只检查前5个
            years = sorted(trend["yearly_freq"].keys())
            if years:
                # 验证年份是连续的（没有gap）
                for i in range(len(years) - 1):
                    assert years[i + 1] - years[i] == 1


# ============================================================================
# 核心功能测试 3: 趋势分类
# ============================================================================


@pytest.mark.asyncio
class TestTrendClassification:
    """核心功能测试 3: 趋势分类"""

    async def test_trend_type_field_exists(self, logger):
        """测试：trend_type 字段存在"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 验证每个趋势都有类型
        for trend in result["trends"]:
            assert "trend_type" in trend
            assert trend["trend_type"] in ["growing", "consolidated", "declining", "stable"]

    async def test_growth_rate_calculation(self, logger):
        """测试：增长率计算"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 验证 growth_rate 字段
        for trend in result["trends"]:
            assert "growth_rate" in trend
            assert isinstance(trend["growth_rate"], (int, float))

    async def test_growing_keywords_identified(self, logger):
        """测试：识别增长型关键词"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 应该有增长型关键词
        growing_keywords = [t for t in result["trends"] if t["trend_type"] == "growing"]
        assert len(growing_keywords) > 0

    async def test_declining_keywords_identified(self, logger):
        """测试：识别衰退型关键词"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, year_range=(2020, 2023)
        )

        # 应该有衰退型关键词（早期出现后期消失）
        declining_keywords = [t for t in result["trends"] if t["trend_type"] == "declining"]
        # 可能没有明显的衰退型，但不应该报错
        assert isinstance(declining_keywords, list)


# ============================================================================
# 核心功能测试 4: 字段选择
# ============================================================================


@pytest.mark.asyncio
class TestFieldSelection:
    """核心功能测试 4: 字段选择"""

    async def test_abstract_field_default(self, logger):
        """测试：默认使用 abstract 字段"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(SAMPLE_ARTICLES_MULTIPLE_YEARS)

        # 验证有结果（基于摘要中的词）
        assert len(result["trends"]) > 0

    async def test_title_field(self, logger):
        """测试：使用 title 字段"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, field="title"
        )

        # 验证有结果（基于标题中的词）
        assert len(result["trends"]) > 0
        # 标题中的词应该被统计
        keywords = [t["keyword"] for t in result["trends"]]
        assert "learning" in keywords or "transformers" in keywords

    async def test_keywords_field(self, logger):
        """测试：使用 keywords 字段（作者关键词）"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_WITH_KEYWORDS, field="keywords"
        )

        # 验证关键词被统计
        keywords = [t["keyword"] for t in result["trends"]]
        assert "neural networks" in keywords or "machine learning" in keywords

    async def test_combined_fields(self, logger):
        """测试：组合多个字段"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, field="title,abstract"
        )

        # 验证有结果
        assert len(result["trends"]) > 0


# ============================================================================
# 边界情况测试
# ============================================================================


@pytest.mark.asyncio
class TestEdgeCases:
    """边界情况测试"""

    async def test_empty_articles_returns_empty_result(self, logger):
        """测试：空文献列表返回空结果"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(EMPTY_ARTICLES)

        assert result["trends"] == []
        assert result["summary"]["total_papers"] == 0

    async def test_no_abstract_handles_gracefully(self, logger):
        """测试：无摘要的文献不报错"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(ARTICLES_NO_ABSTRACT)

        # 应该有结果（基于标题）
        assert result is not None
        assert "trends" in result

    async def test_no_year_defaults_to_all(self, logger):
        """测试：无年份的文献使用默认处理"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(ARTICLES_NO_YEAR)

        # 不应该报错，返回空或默认年份
        assert result is not None
        assert "trends" in result


# ============================================================================
# 参数测试
# ============================================================================


@pytest.mark.asyncio
class TestParameters:
    """参数测试"""

    async def test_top_n_limits_results(self, logger):
        """测试：top_n 参数限制结果数量"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, top_n=5
        )

        # 验证最多返回5个
        assert len(result["trends"]) <= 5

    async def test_normalize_false_returns_raw_counts(self, logger):
        """测试：normalize=False 返回原始计数"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, normalize=False
        )

        # 验证频率是整数
        for trend in result["trends"]:
            assert isinstance(trend["total_freq"], int)

    async def test_min_word_length_filter(self, logger):
        """测试：min_word_length 过滤短词"""
        keyword_trends._logger = logger

        result = keyword_trends.analyze_keyword_trends_async(
            SAMPLE_ARTICLES_MULTIPLE_YEARS, min_word_length=5
        )

        # 验证没有短词
        for trend in result["trends"]:
            assert len(trend["keyword"]) >= 5


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
