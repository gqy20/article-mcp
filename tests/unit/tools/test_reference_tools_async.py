#!/usr/bin/env python3
"""Reference Tools 异步测试
测试 get_references 工具的异步版本
"""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, Mock

import pytest

from article_mcp.tools.core import reference_tools


@pytest.fixture
def logger():
    """提供测试用的 logger"""
    return logging.getLogger(__name__)


@pytest.fixture
def mock_reference_service():
    """模拟 reference 服务"""
    service = Mock()
    # 异步方法
    service.get_references_by_doi_async = AsyncMock(
        return_value={
            "success": True,
            "references": [
                {
                    "title": "Reference 1",
                    "authors": ["Author One"],
                    "doi": "10.1111/ref1.2020",
                    "journal": "Journal One",
                    "publication_date": "2020-01-01",
                },
                {
                    "title": "Reference 2",
                    "authors": ["Author Two"],
                    "doi": "10.2222/ref2.2021",
                    "journal": "Journal Two",
                    "publication_date": "2021-06-15",
                },
            ],
        }
    )
    service.get_references_crossref_async = AsyncMock(
        return_value=[
            {
                "title": "CrossRef Reference 1",
                "authors": ["CR Author"],
                "doi": "10.3333/crref1.2022",
                "journal": "CR Journal",
                "publication_date": "2022-03-01",
            }
        ]
    )
    return service


@pytest.fixture
def mock_services(mock_reference_service):
    """模拟服务字典"""
    return {"reference": mock_reference_service}


@pytest.mark.asyncio
class TestGetReferencesAsync:
    """测试异步 get_references 工具"""

    async def test_get_references_by_doi_success(
        self, mock_services, mock_reference_service, logger
    ):
        """测试通过 DOI 成功获取参考文献"""
        # 调用工具
        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            sources=["europe_pmc"],
            max_results=20,
            include_metadata=True,
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert result["total_count"] == 2
        assert len(result["merged_references"]) == 2
        assert result["sources_used"] == ["europe_pmc"]
        assert "references_by_source" in result
        assert result["processing_time"] >= 0

        # 验证异步方法被调用
        mock_reference_service.get_references_by_doi_async.assert_awaited_once_with(
            "10.1234/test.article.2023"
        )

    async def test_get_references_multiple_sources(
        self, mock_services, mock_reference_service, logger
    ):
        """测试从多个数据源获取参考文献"""
        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            id_type="doi",
            sources=["europe_pmc", "crossref"],
            max_results=50,
            services=mock_services,
            logger=logger,
        )

        # 验证结果
        assert result["success"] is True
        assert len(result["sources_used"]) == 2
        assert "europe_pmc" in result["sources_used"]
        assert "crossref" in result["sources_used"]
        assert result["total_count"] == 3  # 2 from europe_pmc + 1 from crossref

        # 验证两个异步方法都被调用
        mock_reference_service.get_references_by_doi_async.assert_awaited_once()
        mock_reference_service.get_references_crossref_async.assert_awaited_once()

    async def test_get_references_deduplication(
        self, mock_services, mock_reference_service, logger
    ):
        """测试参考文献去重功能"""
        # 设置返回重复的参考文献
        mock_reference_service.get_references_by_doi_async.return_value = {
            "success": True,
            "references": [
                {
                    "title": "Same Article",
                    "authors": ["Author One"],
                    "doi": "10.1111/same.2020",
                    "journal": "Journal One",
                },
                {
                    "title": "Same Article",
                    "authors": ["Author One"],
                    "doi": "10.1111/same.2020",  # 重复
                    "journal": "Journal One",
                },
                {
                    "title": "Different Article",
                    "authors": ["Author Two"],
                    "doi": "10.2222/diff.2021",
                    "journal": "Journal Two",
                },
            ],
        }

        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            services=mock_services,
            logger=logger,
        )

        # 验证去重后只有2条
        assert result["total_count"] == 2
        dois = [ref["doi"] for ref in result["merged_references"]]
        assert len(dois) == len(set(dois))  # 确保 DOI 唯一

    async def test_get_references_max_results_limit(
        self, mock_services, mock_reference_service, logger
    ):
        """测试最大结果数量限制"""
        # 设置返回大量参考文献
        many_references = [
            {
                "title": f"Reference {i}",
                "authors": [f"Author {i}"],
                "doi": f"10.1234/ref{i}.2023",
                "journal": "Test Journal",
            }
            for i in range(50)
        ]
        mock_reference_service.get_references_by_doi_async.return_value = {
            "success": True,
            "references": many_references,
        }

        max_results = 20
        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            max_results=max_results,
            services=mock_services,
            logger=logger,
        )

        # 验证结果被限制
        assert result["total_count"] == max_results
        assert len(result["merged_references"]) == max_results

    async def test_get_references_empty_identifier(self, mock_services, logger):
        """测试空标识符错误处理"""
        result = await reference_tools.get_references_async(
            identifier="",
            id_type="doi",
            services=mock_services,
            logger=logger,
        )

        # 验证错误处理
        assert result["success"] is False
        assert "文献标识符不能为空" in result["error"]
        assert result["total_count"] == 0
        assert result["sources_used"] == []

    async def test_get_references_auto_id_type(self, mock_services, logger):
        """测试自动标识符类型识别"""
        test_cases = [
            ("10.1234/test.doi", "doi"),
            ("12345678", "pmid"),
            ("PMC123456", "pmcid"),
            ("arXiv:2301.00001", "arxiv_id"),
        ]

        for identifier, expected_type in test_cases:
            # 测试标识符类型提取
            extracted_type = reference_tools._extract_identifier_type(identifier)
            assert extracted_type == expected_type, (
                f"Expected {expected_type} for {identifier}, got {extracted_type}"
            )

    async def test_get_references_no_data_source_error(
        self, mock_services, mock_reference_service, logger
    ):
        """测试数据源返回无数据时的处理"""
        # 设置返回空结果
        mock_reference_service.get_references_by_doi_async.return_value = {
            "success": True,
            "references": [],
        }

        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            services=mock_services,
            logger=logger,
        )

        # 验证空结果处理
        assert result["success"] is False  # 没有参考文献时返回 False
        assert result["total_count"] == 0
        assert result["sources_used"] == []  # 没有成功获取数据的数据源

    async def test_get_references_service_error_handling(
        self, mock_services, mock_reference_service, logger
    ):
        """测试服务异常处理"""
        # 设置服务抛出异常
        mock_reference_service.get_references_by_doi_async.side_effect = Exception("API Error")

        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            services=mock_services,
            logger=logger,
        )

        # 验证错误处理 - 应该优雅地处理异常，返回空结果
        assert result["total_count"] == 0
        assert result["sources_used"] == []

    async def test_get_references_include_metadata(
        self, mock_services, mock_reference_service, logger
    ):
        """测试包含元数据的参考文献"""
        mock_reference_service.get_references_by_doi_async.return_value = {
            "success": True,
            "references": [
                {
                    "title": "Reference with Metadata",
                    "authors": ["Author One"],
                    "doi": "10.1111/ref1.2020",
                    "journal": "Journal One",
                    "publication_date": "2020-01-01",
                    "abstract": "This is an abstract",
                    "volume": "10",
                    "issue": "1",
                    "pages": "1-10",
                    "issn": "1234-5678",
                    "publisher": "Test Publisher",
                },
            ],
        }

        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            include_metadata=True,
            services=mock_services,
            logger=logger,
        )

        # 验证元数据被包含
        ref = result["merged_references"][0]
        assert "abstract" in ref
        assert ref["abstract"] == "This is an abstract"
        assert ref["volume"] == "10"
        assert ref["issue"] == "1"
        assert ref["pages"] == "1-10"
        assert ref["issn"] == "1234-5678"
        assert ref["publisher"] == "Test Publisher"

    async def test_get_references_exclude_metadata(
        self, mock_services, mock_reference_service, logger
    ):
        """测试不包含元数据的参考文献"""
        mock_reference_service.get_references_by_doi_async.return_value = {
            "success": True,
            "references": [
                {
                    "title": "Reference without Metadata",
                    "authors": ["Author One"],
                    "doi": "10.1111/ref1.2020",
                    "journal": "Journal One",
                    "publication_date": "2020-01-01",
                    "abstract": "This abstract should not be included",
                },
            ],
        }

        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            include_metadata=False,
            services=mock_services,
            logger=logger,
        )

        # 验证元数据不被包含
        ref = result["merged_references"][0]
        assert "abstract" not in ref
        assert "volume" not in ref
        assert "issue" not in ref
        # 但基本字段应该存在
        assert ref["title"] == "Reference without Metadata"
        assert ref["doi"] == "10.1111/ref1.2020"

    async def test_get_references_default_sources(
        self, mock_services, mock_reference_service, logger
    ):
        """测试默认数据源"""
        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            # 不指定 sources，应该使用默认值
            services=mock_services,
            logger=logger,
        )

        # 验证默认使用 europe_pmc 和 crossref
        assert "europe_pmc" in result["sources_used"] or "crossref" in result["sources_used"]

    async def test_get_references_source_priority_sorting(
        self, mock_services, mock_reference_service, logger
    ):
        """测试数据源优先级排序"""
        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc", "crossref"],
            services=mock_services,
            logger=logger,
        )

        # 验证排序：europe_pmc > crossref
        sources_in_order = [ref["source"] for ref in result["merged_references"]]
        # europe_pmc 应该在 crossref 之前（如果都存在）
        if "europe_pmc" in sources_in_order and "crossref" in sources_in_order:
            europe_pmc_idx = sources_in_order.index("europe_pmc")
            crossref_idx = sources_in_order.index("crossref")
            assert europe_pmc_idx < crossref_idx

    async def test_get_references_parallel_execution(
        self, mock_services, mock_reference_service, logger
    ):
        """测试并行执行多个数据源"""

        # 设置延迟以验证并行执行
        async def delayed_europe_pmc(doi):
            await asyncio.sleep(0.1)
            return {
                "success": True,
                "references": [{"title": "Europe PMC Ref", "doi": "10.1111/epmc.2023"}],
            }

        async def delayed_crossref(doi):
            await asyncio.sleep(0.1)
            return [{"title": "CrossRef Ref", "doi": "10.2222/cr.2023"}]

        mock_reference_service.get_references_by_doi_async = delayed_europe_pmc
        mock_reference_service.get_references_crossref_async = delayed_crossref

        start = time.time()
        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc", "crossref"],
            services=mock_services,
            logger=logger,
        )
        elapsed = time.time() - start

        # 并行执行应该比串行快（两个0.1秒的延迟并行执行应该 < 0.2秒）
        assert elapsed < 0.18, f"Parallel execution took {elapsed}s, expected < 0.18s"
        assert result["total_count"] == 2

    async def test_get_references_title_deduplication(
        self, mock_services, mock_reference_service, logger
    ):
        """测试基于标题的去重"""
        # 设置返回相同标题但不同DOI的参考文献
        mock_reference_service.get_references_by_doi_async.return_value = {
            "success": True,
            "references": [
                {
                    "title": "Same Title",
                    "authors": ["Author One"],
                    "doi": "10.1111/same1.2020",  # 不同DOI
                    "journal": "Journal One",
                },
                {
                    "title": "same title",  # 相同标题（大小写不同）
                    "authors": ["Author Two"],
                    "doi": "10.2222/same2.2020",
                    "journal": "Journal Two",
                },
                {
                    "title": "Different Title",
                    "authors": ["Author Three"],
                    "doi": "10.3333/diff.2020",
                    "journal": "Journal Three",
                },
            ],
        }

        result = await reference_tools.get_references_async(
            identifier="10.1234/test.article.2023",
            sources=["europe_pmc"],
            services=mock_services,
            logger=logger,
        )

        # 验证基于标题的去重
        assert result["total_count"] == 2  # "same title" 应该被去重


# 测试辅助函数
class TestHelperFunctions:
    """测试辅助函数"""

    def test_extract_identifier_type_doi(self):
        """测试 DOI 类型识别"""
        test_cases = [
            "10.1234/test.doi",
            "doi:10.1234/test.doi",
            "https://doi.org/10.1234/test.doi",
        ]
        for case in test_cases:
            result = reference_tools._extract_identifier_type(case)
            assert result == "doi", f"Expected 'doi' for {case}, got {result}"

    def test_extract_identifier_type_pmid(self):
        """测试 PMID 类型识别"""
        test_cases = ["12345678", "pmid:12345678", "PMID:12345678"]
        for case in test_cases:
            result = reference_tools._extract_identifier_type(case)
            assert result == "pmid", f"Expected 'pmid' for {case}, got {result}"

    def test_extract_identifier_type_pmcid(self):
        """测试 PMCID 类型识别"""
        test_cases = ["PMC123456", "pmcid:PMC123456", "PMCID:PMC123456"]
        for case in test_cases:
            result = reference_tools._extract_identifier_type(case)
            assert result == "pmcid", f"Expected 'pmcid' for {case}, got {result}"

    def test_extract_identifier_type_arxiv(self):
        """测试 arXiv 类型识别"""
        test_cases = ["arXiv:2301.00001", "ARXIV:2301.00001"]
        for case in test_cases:
            result = reference_tools._extract_identifier_type(case)
            assert result == "arxiv_id", f"Expected 'arxiv_id' for {case}, got {result}"

    def test_extract_identifier_type_default(self):
        """测试默认类型（当作DOI）"""
        result = reference_tools._extract_identifier_type("unknown.format")
        assert result == "doi"
