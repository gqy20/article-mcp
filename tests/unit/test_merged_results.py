"""
合并结果工具单元测试
"""

from src.merged_results import deduplicate_articles
from src.merged_results import extract_identifier_type
from src.merged_results import merge_articles_by_doi
from src.merged_results import merge_citation_results
from src.merged_results import merge_reference_results
from src.merged_results import merge_same_doi_articles
from src.merged_results import simple_rank_articles


class TestMergeResults:
    """合并结果工具测试类"""

    def test_merge_articles_by_doi_empty(self):
        """测试合并空的文章列表"""
        result = merge_articles_by_doi({})
        assert result == []

    def test_merge_articles_by_doi_single_source(self):
        """测试单个数据源的合并"""
        articles_by_source = {
            "europe_pmc": [
                {
                    "title": "Test Article",
                    "doi": "10.1234/test",
                    "authors": ["Author One"],
                    "source": "europe_pmc",
                }
            ]
        }

        result = merge_articles_by_doi(articles_by_source)

        assert len(result) == 1
        assert result[0]["title"] == "Test Article"
        assert result[0]["doi"] == "10.1234/test"

    def test_merge_articles_by_doi_multiple_sources(self):
        """测试多个数据源的合并"""
        articles_by_source = {
            "europe_pmc": [
                {
                    "title": "Test Article",
                    "doi": "10.1234/test",
                    "authors": ["Author One"],
                    "source": "europe_pmc",
                    "abstract": "Abstract from Europe PMC",
                }
            ],
            "pubmed": [
                {
                    "title": "Test Article",
                    "doi": "10.1234/test",
                    "authors": ["Author One", "Author Two"],
                    "source": "pubmed",
                    "publication_date": "2023-01-01",
                }
            ],
        }

        result = merge_articles_by_doi(articles_by_source)

        assert len(result) == 1
        # 合并后的文章应该包含所有来源的信息
        merged_article = result[0]
        assert merged_article["doi"] == "10.1234/test"
        assert "abstract" in merged_article
        assert "publication_date" in merged_article

    def test_merge_articles_by_doi_different_dois(self):
        """测试不同DOI的文章不会被合并"""
        articles_by_source = {
            "europe_pmc": [
                {
                    "title": "Article 1",
                    "doi": "10.1234/article1",
                    "authors": ["Author One"],
                    "source": "europe_pmc",
                },
                {
                    "title": "Article 2",
                    "doi": "10.5678/article2",
                    "authors": ["Author Two"],
                    "source": "europe_pmc",
                },
            ]
        }

        result = merge_articles_by_doi(articles_by_source)

        assert len(result) == 2
        assert result[0]["doi"] == "10.1234/article1"
        assert result[1]["doi"] == "10.5678/article2"

    def test_deduplicate_articles(self):
        """测试文章去重"""
        articles = [
            {"title": "Article 1", "doi": "10.1234/test1"},
            {"title": "Article 2", "doi": "10.1234/test1"},  # 重复 DOI
            {"title": "Article 3", "doi": "10.5678/test3"},
            {"title": "Article 4", "doi": None},  # 无 DOI，应该保留
        ]

        result = deduplicate_articles(articles)

        # 应该保留无DOI的文章和第一个重复DOI的文章
        assert len(result) == 3
        dois = [article.get("doi") for article in result if article.get("doi")]
        assert "10.1234/test1" in dois
        assert "10.5678/test3" in dois

    def test_merge_same_doi_articles_single(self):
        """测试单篇相同DOI的文章合并"""
        articles = [
            {
                "title": "Test Article",
                "doi": "10.1234/test",
                "authors": ["Author One"],
                "source_from": "europe_pmc",
                "data_sources": {"europe_pmc": {"abstract": "Test abstract"}},
            }
        ]

        result = merge_same_doi_articles(articles)

        assert result["doi"] == "10.1234/test"
        assert result["sources"] == ["europe_pmc"]
        assert "europe_pmc" in result["data_sources"]

    def test_merge_same_doi_articles_multiple(self):
        """测试多篇相同DOI的文章合并"""
        articles = [
            {
                "title": "Test Article",
                "doi": "10.1234/test",
                "authors": ["Author One"],
                "source_from": "europe_pmc",
                "data_sources": {"europe_pmc": {"abstract": "Abstract from PMC"}},
            },
            {
                "title": "Test Article",
                "doi": "10.1234/test",
                "authors": ["Author One", "Author Two"],
                "source_from": "pubmed",
                "data_sources": {"pubmed": {"publication_date": "2023-01-01"}},
            },
        ]

        result = merge_same_doi_articles(articles)

        assert result["doi"] == "10.1234/test"
        assert set(result["sources"]) == {"europe_pmc", "pubmed"}
        assert "abstract" in result
        assert "publication_date" in result

    def test_simple_rank_articles(self):
        """测试文章简单排序"""
        articles = [
            {"title": "Low Quality Article", "doi": "10.1234/low", "source": "low_quality"},
            {"title": "High Quality Article", "doi": "10.5678/high", "source": "nature"},
            {"title": "Medium Quality Article", "doi": "10.9012/medium", "source": "pubmed"},
        ]

        result = simple_rank_articles(articles)

        # 高质量期刊的文章应该排在前面
        assert result[0]["doi"] == "10.5678/high"
        assert result[1]["doi"] == "10.9012/medium"
        assert result[2]["doi"] == "10.1234/low"

    def test_extract_identifier_type(self):
        """测试标识符类型提取"""
        # DOI
        assert extract_identifier_type("10.1234/article.2023") == "doi"
        assert extract_identifier_type("https://doi.org/10.1234/article") == "doi"

        # PMID
        assert extract_identifier_type("12345678") == "pmid"
        assert extract_identifier_type("PMID:12345678") == "pmid"

        # PMCID
        assert extract_identifier_type("PMC123456") == "pmcid"
        assert extract_identifier_type("PMC12345678") == "pmcid"

        # arXiv
        assert extract_identifier_type("arXiv:2301.00001") == "arxiv_id"
        assert extract_identifier_type("2301.00001v1") == "arxiv_id"

        # 无效标识符
        assert extract_identifier_type("") == "unknown"
        assert extract_identifier_type("invalid") == "unknown"
        assert extract_identifier_type("10.1234") == "unknown"

    def test_merge_reference_results(self):
        """测试参考文献结果合并"""
        reference_results = {
            "europe_pmc": {
                "success": True,
                "references": [
                    {"doi": "10.1234/ref1", "title": "Reference 1"},
                    {"doi": "10.5678/ref2", "title": "Reference 2"},
                ],
                "total_count": 2,
            },
            "crossref": {
                "success": True,
                "references": [
                    {"doi": "10.1234/ref1", "title": "Reference 1 (from CrossRef)"},
                    {"doi": "10.9012/ref3", "title": "Reference 3"},
                ],
                "total_count": 2,
            },
        }

        result = merge_reference_results(reference_results)

        assert result["total_count"] == 3  # 去重后
        assert len(result["merged_references"]) == 3
        assert result["sources_used"] == ["europe_pmc", "crossref"]

    def test_merge_reference_results_empty(self):
        """测试空参考文献结果合并"""
        reference_results = {}

        result = merge_reference_results(reference_results)

        assert result["total_count"] == 0
        assert result["merged_references"] == []
        assert result["sources_used"] == []

    def test_merge_citation_results(self):
        """测试引用文献结果合并"""
        citation_results = {
            "openalex": {
                "success": True,
                "citations": [
                    {"doi": "10.1234/cite1", "title": "Citation 1"},
                    {"doi": "10.5678/cite2", "title": "Citation 2"},
                ],
                "total_count": 2,
            }
        }

        result = merge_citation_results(citation_results)

        assert result["total_count"] == 2
        assert len(result["merged_citations"]) == 2
        assert result["sources_used"] == ["openalex"]

    def test_merge_citation_results_empty(self):
        """测试空引用文献结果合并"""
        citation_results = {}

        result = merge_citation_results(citation_results)

        assert result["total_count"] == 0
        assert result["merged_citations"] == []
        assert result["sources_used"] == []

    def test_merge_articles_by_doi_with_none_dois(self):
        """测试包含 None DOI 的文章合并"""
        articles_by_source = {
            "europe_pmc": [
                {
                    "title": "Article with DOI",
                    "doi": "10.1234/test",
                    "authors": ["Author One"],
                    "source": "europe_pmc",
                },
                {
                    "title": "Article without DOI",
                    "doi": None,
                    "authors": ["Author Two"],
                    "source": "europe_pmc",
                },
            ]
        }

        result = merge_articles_by_doi(articles_by_source)

        # 两篇文章都应该被保留，None DOI 的不会被去重
        assert len(result) == 2
        doi_articles = [a for a in result if a.get("doi")]
        no_doi_articles = [a for a in result if not a.get("doi")]
        assert len(doi_articles) == 1
        assert len(no_doi_articles) == 1
