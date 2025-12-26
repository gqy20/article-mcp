#!/usr/bin/env python3
"""Relation Tools 异步测试
测试 get_literature_relations 工具的内部函数
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from article_mcp.tools.core import reference_tools, relation_tools


@pytest.fixture
def logger():
    """提供测试用的 logger"""
    return logging.getLogger(__name__)


@pytest.fixture
def mock_crossref_service():
    """模拟 CrossRef 服务"""
    service = Mock()
    service.get_references = Mock(
        return_value={
            "success": True,
            "references": [
                {
                    "title": "Reference 1",
                    "doi": "10.1111/ref1.2020",
                    "journal": "Journal One",
                },
                {
                    "title": "Reference 2",
                    "doi": "10.2222/ref2.2021",
                    "journal": "Journal Two",
                },
            ],
        }
    )
    return service


@pytest.fixture
def mock_openalex_service():
    """模拟 OpenAlex 服务"""
    service = Mock()
    service.get_citations = Mock(
        return_value={
            "success": True,
            "citations": [
                {
                    "title": "Citing Article 1",
                    "doi": "10.3333/cite1.2022",
                }
            ],
        }
    )
    return service


@pytest.fixture
def mock_pubmed_service():
    """模拟 PubMed 服务"""
    service = Mock()
    return service


@pytest.fixture
def mock_reference_service():
    """模拟 Reference 服务（工具3需要）"""
    service = Mock()
    service.get_references_by_doi_async = AsyncMock(
        return_value={
            "references": [
                {
                    "title": "Reference 1",
                    "doi": "10.1111/ref1.2020",
                    "journal": "Journal One",
                    "authors": ["Author A"],
                },
                {
                    "title": "Reference 2",
                    "doi": "10.2222/ref2.2021",
                    "journal": "Journal Two",
                    "authors": ["Author B"],
                },
            ]
        }
    )
    service.get_references_crossref_async = AsyncMock(
        return_value=[
            {
                "title": "Reference 1",
                "doi": "10.1111/ref1.2020",
                "journal": "Journal One",
                "authors": ["Author A"],
            },
            {
                "title": "Reference 2",
                "doi": "10.2222/ref2.2021",
                "journal": "Journal Two",
                "authors": ["Author B"],
            },
        ]
    )
    return service


@pytest.fixture
def mock_services(
    mock_crossref_service, mock_openalex_service, mock_pubmed_service, mock_reference_service
):
    """模拟服务字典"""
    return {
        "crossref": mock_crossref_service,
        "openalex": mock_openalex_service,
        "pubmed": mock_pubmed_service,
        "reference": mock_reference_service,
    }


@pytest.mark.asyncio
class TestSingleLiteratureRelations:
    """测试 _single_literature_relations 函数"""

    async def test_single_literature_relations_success(
        self, mock_services, mock_crossref_service, logger
    ):
        """测试单个文献的关系分析"""
        # 注册服务（工具3需要）
        reference_tools._reference_services = mock_services

        # 直接调用内部函数
        result = await relation_tools._single_literature_relations(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            relation_types=["references"],
            max_results=20,
            sources=["crossref"],
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert result["identifier"] == "10.1234/test.article.2023"
        assert "relations" in result
        assert "references" in result["relations"]
        assert result["statistics"]["references_count"] == 2

    async def test_single_literature_relations_multiple_relation_types(
        self, mock_services, mock_crossref_service, mock_openalex_service, logger
    ):
        """测试多种关系类型分析"""
        # 注册服务（工具3需要）
        reference_tools._reference_services = mock_services

        result = await relation_tools._single_literature_relations(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            relation_types=["references", "citing"],
            max_results=20,
            sources=["crossref", "openalex"],
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert "references" in result["relations"]
        assert "citing" in result["relations"]
        assert result["statistics"]["total_relations"] == 3

    async def test_single_literature_relations_auto_id_type(self, mock_services, logger):
        """测试自动标识符类型识别"""
        test_cases = [
            ("10.1234/test.doi", "doi"),
            ("12345678", "pmid"),
            ("PMC123456", "pmcid"),
            ("arXiv:2301.00001", "arxiv_id"),
        ]

        for identifier, expected_type in test_cases:
            result = await relation_tools._single_literature_relations(
                identifier=identifier,
                id_type="auto",
                relation_types=["references"],
                max_results=20,
                sources=["crossref"],
                services=mock_services,
                logger=logger,
            )
            assert result["id_type"] == expected_type

    async def test_single_literature_relations_empty_identifier(self, mock_services, logger):
        """测试空标识符错误处理"""
        result = await relation_tools._single_literature_relations(
            identifier="",
            id_type="doi",
            relation_types=["references"],
            max_results=20,
            sources=["crossref"],
            services=mock_services,
            logger=logger,
        )

        # 验证错误处理
        assert result["success"] is False
        assert "文献标识符不能为空" in result.get("error", "")
        assert result["relations"] == {}

    async def test_single_literature_relations_citing_articles(
        self, mock_services, mock_openalex_service, logger
    ):
        """测试获取引用文献功能（修复后）"""
        # 更新 mock 返回更完整的引用文献数据
        mock_openalex_service.get_citations = Mock(
            return_value={
                "success": True,
                "citations": [
                    {
                        "title": "Citing Article 1: Cancer Research",
                        "authors": ["Author One", "Author Two"],
                        "doi": "10.3333/cite1.2022",
                        "journal": "Nature",
                        "publication_year": "2022",
                        "source": "openalex",
                    },
                    {
                        "title": "Citing Article 2: Angiogenesis Study",
                        "authors": ["Author Three"],
                        "doi": "10.4444/cite2.2023",
                        "journal": "Cell",
                        "publication_year": "2023",
                        "source": "openalex",
                    },
                ],
                "total_count": 2,
            }
        )

        result = await relation_tools._single_literature_relations(
            identifier="10.1038/nature10144",
            id_type="doi",
            relation_types=["citing"],
            max_results=10,
            sources=["openalex"],
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert "citing" in result["relations"]
        assert len(result["relations"]["citing"]) == 2
        assert result["statistics"]["citing_count"] == 2
        assert result["statistics"]["total_relations"] == 2

        # 验证引用文献数据完整性
        citing_1 = result["relations"]["citing"][0]
        assert citing_1["title"] == "Citing Article 1: Cancer Research"
        assert citing_1["journal"] == "Nature"
        assert citing_1["publication_year"] == "2022"

        # 验证服务方法被调用
        mock_openalex_service.get_citations.assert_called_once_with("10.1038/nature10144", 10)


@pytest.mark.asyncio
class TestBatchLiteratureRelations:
    """测试 _batch_literature_relations 函数"""

    async def test_batch_literature_relations_success(
        self, mock_services, mock_crossref_service, logger
    ):
        """测试批量文献关系分析"""
        identifiers = ["10.1234/test.1", "10.1234/test.2"]

        result = await relation_tools._batch_literature_relations(
            identifiers=identifiers,
            id_type="doi",
            relation_types=["references"],
            max_results=20,
            sources=["crossref"],
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert result["total_identifiers"] == 2
        assert result["successful_analyses"] == 2
        assert "batch_results" in result
        assert len(result["batch_results"]) == 2

    async def test_batch_literature_relations_empty_list(self, mock_services, logger):
        """测试空列表错误处理"""
        result = await relation_tools._batch_literature_relations(
            identifiers=[],
            id_type="doi",
            relation_types=["references"],
            max_results=20,
            sources=["crossref"],
            services=mock_services,
            logger=logger,
        )

        # 验证错误处理
        assert result["success"] is False
        assert "文献标识符列表不能为空" in result.get("error", "")


@pytest.mark.asyncio
class TestAnalyzeLiteratureNetwork:
    """测试 _analyze_literature_network 函数"""

    async def test_analyze_literature_network_success(self, mock_services, logger):
        """测试文献网络分析"""
        identifiers = ["10.1234/test.1", "10.1234/test.2"]

        result = await relation_tools._analyze_literature_network(
            identifiers=identifiers,
            analysis_type="citation",
            max_depth=1,
            max_results=20,
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert "network_data" in result
        assert "nodes" in result["network_data"]
        assert "edges" in result["network_data"]
        assert "analysis_metrics" in result
        # 应该有至少2个种子节点
        assert len(result["network_data"]["nodes"]) >= 2

    async def test_analyze_literature_network_comprehensive(self, mock_services, logger):
        """测试综合网络分析"""
        identifiers = ["10.1234/test.1"]

        result = await relation_tools._analyze_literature_network(
            identifiers=identifiers,
            analysis_type="comprehensive",
            max_depth=1,
            max_results=20,
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert result["network_data"]["analysis_type"] == "comprehensive"
        assert "clusters" in result["network_data"]
        assert result["analysis_metrics"]["total_nodes"] >= 1


# 测试辅助函数
class TestHelperFunctions:
    """测试辅助函数"""

    def test_extract_identifier_type_simple_doi(self):
        """测试 DOI 类型识别（使用 _extract_identifier_type_simple）"""
        test_cases = [
            "10.1234/test.doi",
            "doi:10.1234/test.doi",
            "https://doi.org/10.1234/test.doi",
        ]
        for case in test_cases:
            result = relation_tools._extract_identifier_type_simple(case)
            assert result == "doi", f"Expected 'doi' for {case}, got {result}"

    def test_extract_identifier_type_simple_pmid(self):
        """测试 PMID 类型识别（使用 _extract_identifier_type_simple）"""
        test_cases = ["12345678", "pmid:12345678", "PMID:12345678"]
        for case in test_cases:
            result = relation_tools._extract_identifier_type_simple(case)
            assert result == "pmid", f"Expected 'pmid' for {case}, got {result}"

    def test_extract_identifier_type_simple_pmcid(self):
        """测试 PMCID 类型识别（使用 _extract_identifier_type_simple）"""
        test_cases = ["PMC123456", "pmcid:PMC123456", "PMCID:PMC123456"]
        for case in test_cases:
            result = relation_tools._extract_identifier_type_simple(case)
            assert result == "pmcid", f"Expected 'pmcid' for {case}, got {result}"

    def test_extract_identifier_type_simple_arxiv(self):
        """测试 arXiv 类型识别（使用 _extract_identifier_type_simple）"""
        test_cases = ["arXiv:2301.00001", "ARXIV:2301.00001"]
        for case in test_cases:
            result = relation_tools._extract_identifier_type_simple(case)
            assert result == "arxiv_id", f"Expected 'arxiv_id' for {case}, got {result}"

    def test_extract_identifier_type_simple_default(self):
        """测试默认类型（当作DOI）"""
        result = relation_tools._extract_identifier_type_simple("unknown.format")
        assert result == "doi"

    # 注意：_deduplicate_references 已被删除，去重逻辑现在由工具3处理
    # 或在 _get_similar_articles 中内联实现
