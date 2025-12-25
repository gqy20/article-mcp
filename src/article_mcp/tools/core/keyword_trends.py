"""关键词趋势分析工具 - 核心工具6

设计原则：
1. 关键词频率统计：统计每个词的总出现次数
2. 年份趋势图：按年份聚合词频
3. 趋势分类：growing/consolidated/declining/stable
4. 支持多种字段：title, abstract, keywords
5. 边界情况：空数据、无年份、停用词过滤
"""

import logging
import re
from collections import Counter, defaultdict
from typing import Any

from fastmcp import FastMCP

# 全局服务实例
_logger = None


def register_keyword_trends_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    """注册关键词趋势分析工具"""
    global _logger
    _logger = logger

    from mcp.types import ToolAnnotations

    @mcp.tool(
        description="""关键词趋势分析工具。分析某领域近年来的热门话题变化。

主要参数：
- articles: 文献列表（必填）：包含 title, abstract, publication_date 等字段的文献字典列表
- field: 分析字段（默认abstract）：title/abstract/keywords/title,abstract
- year_range: 年份范围（可选）：[2020, 2024]，默认分析所有年份
- top_n: 返回前N个关键词（默认30）：只返回频率最高的N个关键词
- normalize: 是否归一化频率（默认false）：true返回相对频率，false返回原始计数
- min_word_length: 最小词长（默认3）：过滤短词
- min_docs: 最小文档数（默认2）：词至少出现在N篇文档中

返回数据：
- trends: 趋势列表，每个趋势包含：
  - keyword: 关键词
  - total_freq: 总频率
  - yearly_freq: 按年份的频率分布 {2020: 10, 2021: 15, ...}
  - trend_type: 趋势类型
  - growth_rate: 增长率
- summary: 摘要信息
  - total_papers: 总文献数
  - year_range: 年份范围
  - total_unique_keywords: 唯一关键词数

使用场景：
- 发现某领域的新兴热点（growing）
- 识别成熟概念（consolidated）
- 发现衰退话题（declining）

注意：
- 需要至少2篇文献才能进行趋势分析
- 停用词会被自动过滤""",
        annotations=ToolAnnotations(title="关键词趋势分析", readOnlyHint=True, openWorldHint=False),
        tags={"trends", "keywords", "analysis", "temporal"},
    )
    def analyze_keyword_trends(
        articles: list[dict[str, Any]],
        field: str = "abstract",
        year_range: tuple[int, int] | None = None,
        top_n: int = 30,
        normalize: bool = False,
        min_word_length: int = 3,
        min_docs: int = 2,
    ) -> dict[str, Any]:
        """关键词趋势分析工具。

        Args:
            articles: 文献列表
            field: 分析字段 ["title", "abstract", "keywords", "title,abstract"]
            year_range: 年份范围，如 (2020, 2024)
            top_n: 返回前N个关键词
            normalize: 是否归一化频率
            min_word_length: 最小词长
            min_docs: 最小文档数

        Returns:
            包含趋势和摘要的字典

        """
        return analyze_keyword_trends_async(
            articles=articles,
            field=field,
            year_range=year_range,
            top_n=top_n,
            normalize=normalize,
            min_word_length=min_word_length,
            min_docs=min_docs,
        )


def analyze_keyword_trends_async(
    articles: list[dict[str, Any]],
    field: str = "abstract",
    year_range: tuple[int, int] | None = None,
    top_n: int = 30,
    normalize: bool = False,
    min_word_length: int = 3,
    min_docs: int = 2,
) -> dict[str, Any]:
    """异步分析关键词趋势。

    Args:
        articles: 文献列表
        field: 分析字段
        year_range: 年份范围
        top_n: 返回前N个关键词
        normalize: 是否归一化频率
        min_word_length: 最小词长
        min_docs: 最小文档数

    Returns:
        趋势分析结果

    """
    logger = _logger or logging.getLogger(__name__)

    try:
        # 边界情况：空文献列表
        if not articles:
            return {
                "trends": [],
                "summary": {
                    "total_papers": 0,
                    "year_range": year_range or [],
                    "total_unique_keywords": 0,
                },
            }

        # 1. 提取文本并分词
        docs_by_year = defaultdict(list)
        all_years = set()

        for article in articles:
            # 获取年份
            year = _extract_year(article)
            if year is None:
                continue

            # 应用年份范围过滤
            if year_range:
                if not (year_range[0] <= year <= year_range[1]):
                    continue

            all_years.add(year)

            # 提取文本
            text, is_keywords = _extract_text(article, field)
            tokens = _tokenize(text, min_word_length, is_keywords)

            if tokens:
                docs_by_year[year].append(tokens)

        # 如果没有有效年份，使用全部数据作为单一年份
        if not docs_by_year:
            logger.warning("没有找到有效年份的数据，将全部数据作为单一年份处理")
            tokens_list = []
            for article in articles:
                text, is_keywords = _extract_text(article, field)
                tokens = _tokenize(text, min_word_length, is_keywords)
                if tokens:
                    tokens_list.append(tokens)
            if tokens_list:
                docs_by_year[0] = tokens_list

        # 2. 计算词频（按年份）
        yearly_freq = defaultdict(lambda: defaultdict(int))
        total_freq = defaultdict(int)

        for year, token_list in docs_by_year.items():
            year_counter = Counter()
            for tokens in token_list:
                year_counter.update(tokens)
            for word, count in year_counter.items():
                yearly_freq[word][year] += count
                total_freq[word] += count

        # 3. 过滤：词至少出现在 min_docs 篇文档中
        doc_counts = defaultdict(int)
        for _year, token_list in docs_by_year.items():
            words_in_year = set()
            for tokens in token_list:
                words_in_year.update(tokens)
            for word in words_in_year:
                doc_counts[word] += 1

        # 过滤
        filtered_words = {word for word, count in doc_counts.items() if count >= min_docs}
        total_freq = {k: v for k, v in total_freq.items() if k in filtered_words}
        yearly_freq = {
            word: {y: c for y, c in freq.items() if word in filtered_words}
            for word, freq in yearly_freq.items()
            if word in filtered_words
        }

        # 4. 计算趋势指标
        trends = []
        for word, freq in sorted(total_freq.items(), key=lambda x: -x[1])[:top_n]:
            yearly = dict(yearly_freq[word])

            # 确保所有年份都有值（填充0）
            if docs_by_year:
                for y in sorted(docs_by_year.keys()):
                    if y not in yearly:
                        yearly[y] = 0

            # 分类趋势
            trend_type, growth_rate = _classify_trend(yearly)

            trends.append(
                {
                    "keyword": word,
                    "total_freq": freq,
                    "yearly_freq": yearly,
                    "trend_type": trend_type,
                    "growth_rate": growth_rate,
                }
            )

        # 5. 构建摘要
        actual_year_range = sorted(docs_by_year.keys()) if docs_by_year else (year_range or [])

        return {
            "trends": trends,
            "summary": {
                "total_papers": len(articles),
                "year_range": list(actual_year_range),
                "total_unique_keywords": len(total_freq),
            },
        }

    except Exception as e:
        logger.error(f"分析关键词趋势异常: {e}")
        return {
            "trends": [],
            "summary": {
                "total_papers": len(articles) if articles else 0,
                "year_range": year_range or [],
                "total_unique_keywords": 0,
                "error": str(e),
            },
        }


def _extract_year(article: dict[str, Any]) -> int | None:
    """从文章中提取年份"""
    # 优先使用 year 字段
    if "year" in article:
        return article.get("year")

    # 从 publication_date 提取
    pub_date = article.get("publication_date", "")
    if pub_date:
        match = re.search(r"(\d{4})", pub_date)
        if match:
            return int(match.group(1))

    return None


def _extract_text(article: dict[str, Any], field: str) -> tuple[str, bool]:
    """从文章中提取指定字段的文本

    Returns:
        (文本内容, 是否为关键词字段)
        关键词字段返回 True，表示不应拆分短语

    """
    fields = field.split(",")

    parts = []
    is_keywords_field = False

    for f in fields:
        f = f.strip()
        if f == "keywords":
            # 关键词字段是列表，保留短语
            is_keywords_field = True
            keywords = article.get("keywords", [])
            if isinstance(keywords, list):
                # 关键词列表直接使用，用逗号分隔以便后续解析
                parts.append(", ".join(keywords))
        else:
            # 普通文本字段
            parts.append(article.get(f, ""))

    return " ".join(parts), is_keywords_field


def _tokenize(text: str, min_word_length: int = 3, is_keywords_field: bool = False) -> list[str]:
    """分词并过滤

    Args:
        text: 输入文本
        min_word_length: 最小词长
        is_keywords_field: 是否为关键词字段（保留短语）

    Returns:
        词列表（小写）

    """
    if not text:
        return []

    if is_keywords_field:
        # 关键词字段：保留短语（用空格分隔的）
        # 按逗号或分号分割关键词
        keywords = re.split(r"[,;]", text.lower())
        result = []
        for kw in keywords:
            kw = kw.strip()
            # 过滤短词和空词
            if kw and len(kw) >= min_word_length:
                result.append(kw)
        return result
    else:
        # 普通文本字段：分词
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        # 过滤短词
        words = [w for w in words if len(w) >= min_word_length]
        return words


def _classify_trend(yearly_freq: dict[int, int]) -> tuple[str, float]:
    """分类趋势并计算增长率

    Args:
        yearly_freq: 按年份的频率分布

    Returns:
        (趋势类型, 增长率)

    """
    if not yearly_freq or len(yearly_freq) < 2:
        return "stable", 0.0

    years = sorted(yearly_freq.keys())
    freqs = [yearly_freq[y] for y in years]

    # 计算增长率（线性回归斜率）
    if len(years) >= 2:
        n = len(years)
        sum_x = sum(years)
        sum_y = sum(freqs)
        sum_xy = sum(y * f for y, f in zip(years, freqs, strict=True))
        sum_x2 = sum(y * y for y in years)

        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            # 归一化斜率
            mean_y = sum_y / n if n > 0 else 1
            growth_rate = slope / mean_y if mean_y > 0 else 0
        else:
            growth_rate = 0
    else:
        growth_rate = 0

    # 分类趋势
    if growth_rate > 0.05:  # 增长率 > 5%
        trend_type = "growing"
    elif growth_rate < -0.05:  # 增长率 < -5%
        trend_type = "declining"
    else:
        trend_type = "consolidated"

    return trend_type, round(growth_rate, 4)
