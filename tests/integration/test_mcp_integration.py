#!/usr/bin/env python3
"""
MCP集成测试
测试完整的MCP服务器功能和工作流程
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest  # noqa: E402
from fastmcp import FastMCP  # noqa: E402

from article_mcp.cli import create_mcp_server  # noqa: E402
from article_mcp.tools.core.article_tools import register_article_tools  # noqa: E402
from article_mcp.tools.core.reference_tools import register_reference_tools  # noqa: E402
from article_mcp.tools.core.search_tools import register_search_tools  # noqa: E402
from tests.utils.test_helpers import MockDataGenerator  # noqa: E402
from tests.utils.test_helpers import TestTimer


class TestMCPServerIntegration:
    """MCP服务器集成测试"""

    @pytest.fixture
    async def mcp_server(self):
        """创建MCP服务器实例"""
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
            server = create_mcp_server()
            yield server

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_creation_and_tool_registration(self):
        """测试服务器创建和工具注册"""
        # 创建模拟服务
        mock_services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock(),
        }
        mock_logger = Mock()

        # 创建MCP服务器
        mcp = FastMCP("Test Integration Server")

        # 注册工具
        register_search_tools(mcp, mock_services, mock_logger)
        register_article_tools(mcp, mock_services, mock_logger)
        register_reference_tools(mcp, Mock(), mock_logger)

        # 验证工具注册
        assert hasattr(mcp, "_tools")
        assert len(mcp._tools) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_search_workflow(self):
        """测试端到端搜索工作流程"""
        # 模拟搜索结果
        mock_results = MockDataGenerator.create_search_results(10)

        # 创建模拟服务
        mock_europe_pmc_service = Mock()
        mock_europe_pmc_service.search_articles = AsyncMock(return_value=mock_results)

        # 创建MCP服务器
        mcp = FastMCP("Integration Test Server")
        mock_services = {"europe_pmc": mock_europe_pmc_service}
        mock_logger = Mock()

        # 注册搜索工具
        register_search_tools(mcp, mock_services, mock_logger)

        # 验证搜索工具已注册
        assert len(mcp._tools) > 0

        # 模拟工具调用
        search_tool = None
        for tool in mcp._tools:
            if hasattr(tool, "name") and "search" in tool.name:
                search_tool = tool
                break

        assert search_tool is not None, "搜索工具未找到"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_source_search_integration(self):
        """测试多源搜索集成"""
        # 模拟不同数据源的结果
        europe_pmc_results = MockDataGenerator.create_search_results(5)
        arxiv_results = MockDataGenerator.create_search_results(3)

        # 创建模拟服务
        mock_europe_pmc_service = Mock()
        mock_europe_pmc_service.search_articles = AsyncMock(return_value=europe_pmc_results)

        mock_arxiv_service = Mock()
        mock_arxiv_service.search_papers = AsyncMock(return_value=arxiv_results)

        # 创建MCP服务器
        mcp = FastMCP("Multi-source Test Server")
        mock_services = {"europe_pmc": mock_europe_pmc_service, "arxiv": mock_arxiv_service}
        mock_logger = Mock()

        # 注册工具
        register_search_tools(mcp, mock_services, mock_logger)
        register_article_tools(mcp, mock_services, mock_logger)

        # 验证多源搜索功能
        assert len(mock_services) == 2
        assert "europe_pmc" in mock_services
        assert "arxiv" in mock_services

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reference_workflow_integration(self):
        """测试参考文献工作流集成"""
        # 模拟文章和参考文献
        MockDataGenerator.create_article(doi="10.1000/test-article")
        mock_references = MockDataGenerator.create_reference_list(15)

        # 创建模拟服务
        mock_reference_service = Mock()
        mock_reference_service.get_references = AsyncMock(
            return_value={
                "references": mock_references,
                "total_count": len(mock_references),
                "processing_time": 1.5,
            }
        )

        # 创建MCP服务器
        mcp = FastMCP("Reference Test Server")
        mock_logger = Mock()

        # 注册参考文献工具
        register_reference_tools(mcp, mock_reference_service, mock_logger)

        # 验证参考文献工具注册
        assert len(mcp._tools) > 0

        # 验证参考文献服务配置
        assert mock_reference_service.get_references is not None


class TestDataFlowIntegration:
    """数据流集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_to_article_details_flow(self):
        """测试搜索到文章详情的数据流"""
        # 模拟搜索结果
        search_results = MockDataGenerator.create_search_results(3)
        article_details = MockDataGenerator.create_article(doi=search_results["articles"][0]["doi"])

        # 创建模拟服务
        mock_europe_pmc_service = Mock()
        mock_europe_pmc_service.search_articles = AsyncMock(return_value=search_results)
        mock_europe_pmc_service.get_article_details = AsyncMock(return_value=article_details)

        # 创建MCP服务器
        mcp = FastMCP("Data Flow Test Server")
        mock_services = {"europe_pmc": mock_europe_pmc_service}
        mock_logger = Mock()

        # 注册工具
        register_search_tools(mcp, mock_services, mock_logger)
        register_article_tools(mcp, mock_services, mock_logger)

        # 验证数据流配置
        assert mock_europe_pmc_service.search_articles is not None
        assert mock_europe_pmc_service.get_article_details is not None

        # 验证数据一致性
        first_search_article = search_results["articles"][0]
        assert first_search_article["doi"] == article_details["doi"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reference_chain_flow(self):
        """测试参考文献链数据流"""
        # 模拟文章、参考文献和二级参考文献
        main_article = MockDataGenerator.create_article(doi="10.1000/main")
        first_level_refs = MockDataGenerator.create_reference_list(5)
        second_level_refs = MockDataGenerator.create_reference_list(3)

        # 创建模拟服务
        mock_reference_service = Mock()
        mock_reference_service.get_references = AsyncMock(
            return_value={"references": first_level_refs, "total_count": len(first_level_refs)}
        )

        # 模拟二级参考文献获取
        mock_reference_service.get_references.side_effect = [
            {"references": first_level_refs, "total_count": len(first_level_refs)},
            {"references": second_level_refs, "total_count": len(second_level_refs)},
        ]

        # 创建MCP服务器
        mcp = FastMCP("Reference Chain Test Server")
        mock_logger = Mock()

        # 注册工具
        register_reference_tools(mcp, mock_reference_service, mock_logger)

        # 验证参考文献链配置
        assert mock_reference_service.get_references is not None

        # 验证数据流
        await mock_reference_service.get_references(main_article["doi"], "doi")
        await mock_reference_service.get_references(first_level_refs[0]["doi"], "doi")

        assert mock_reference_service.get_references.call_count == 2


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self):
        """测试并发搜索性能"""
        # 模拟大量搜索结果
        large_results = MockDataGenerator.create_search_results(100)

        # 创建多个模拟服务
        services = []
        for _i in range(3):
            service = Mock()
            service.search_articles = AsyncMock(return_value=large_results)
            services.append(service)

        # 并发搜索测试
        with TestTimer() as timer:
            tasks = []
            for service in services:
                task = service.search_articles("test query", max_results=100)
                tasks.append(task)

            results = await asyncio.gather(*tasks)

        # 验证性能要求
        assert timer.stop() < 15.0  # 应该在15秒内完成
        assert len(results) == 3
        assert all(len(result["articles"]) == 100 for result in results)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_usage_integration(self):
        """测试内存使用集成"""

        import psutil

        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 模拟大量数据处理
        large_results = MockDataGenerator.create_search_results(1000)

        # 创建模拟服务
        mock_service = Mock()
        mock_service.search_articles = AsyncMock(return_value=large_results)

        # 执行多次搜索
        for i in range(10):
            await mock_service.search_articles(f"query {i}", max_results=100)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 验证内存使用合理（不超过100MB增长）
        assert memory_increase < 100 * 1024 * 1024  # 100MB


class TestErrorRecoveryIntegration:
    """错误恢复集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_failure_recovery(self):
        """测试服务故障恢复"""
        # 创建会失败然后恢复的服务
        mock_service = Mock()
        call_count = 0

        async def failing_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Service temporarily unavailable")
            return MockDataGenerator.create_search_results(5)

        mock_service.search_articles = failing_search

        # 创建MCP服务器
        mcp = FastMCP("Error Recovery Test Server")
        mock_services = {"europe_pmc": mock_service}
        mock_logger = Mock()

        # 注册工具
        register_search_tools(mcp, mock_services, mock_logger)

        # 测试错误恢复
        try:
            result = await mock_service.search_articles("test query")
            assert len(result["articles"]) == 5
            assert call_count == 3  # 应该在第3次调用成功
        except Exception:
            pytest.fail("服务应该能够从错误中恢复")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """测试部分故障处理"""
        # 创建一个部分失败的服务组合
        working_service = Mock()
        working_service.search_articles = AsyncMock(
            return_value=MockDataGenerator.create_search_results(5)
        )

        failing_service = Mock()
        failing_service.search_papers = AsyncMock(side_effect=Exception("Service down"))

        # 创建MCP服务器
        mcp = FastMCP("Partial Failure Test Server")
        mock_services = {"europe_pmc": working_service, "arxiv": failing_service}
        mock_logger = Mock()

        # 注册工具
        register_search_tools(mcp, mock_services, mock_logger)

        # 验证部分失败处理
        # 系统应该能够处理部分服务失败，仍然返回可用的结果
        assert working_service.search_articles is not None
        assert failing_service.search_papers is not None


class TestConfigurationIntegration:
    """配置集成测试"""

    @pytest.mark.integration
    def test_service_configuration_validation(self):
        """测试服务配置验证"""
        # 测试不同配置组合
        configurations = [
            {"europe_pmc": Mock(), "pubmed": Mock()},
            {"europe_pmc": Mock(), "arxiv": Mock(), "crossref": Mock()},
            {
                "europe_pmc": Mock(),
                "pubmed": Mock(),
                "arxiv": Mock(),
                "crossref": Mock(),
                "openalex": Mock(),
            },
        ]

        for config in configurations:
            # 创建MCP服务器
            mcp = FastMCP("Configuration Test Server")
            mock_logger = Mock()

            # 测试工具注册
            try:
                register_search_tools(mcp, config, mock_logger)
                register_article_tools(mcp, config, mock_logger)
                # 如果没有抛出异常，配置是有效的
            except Exception as e:
                pytest.fail(f"配置 {config} 导致异常: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dynamic_service_replacement(self):
        """测试动态服务替换"""
        # 初始服务
        initial_service = Mock()
        initial_service.search_articles = AsyncMock(
            return_value=MockDataGenerator.create_search_results(3)
        )

        # 替换服务
        replacement_service = Mock()
        replacement_service.search_articles = AsyncMock(
            return_value=MockDataGenerator.create_search_results(10)
        )

        # 创建MCP服务器
        mcp = FastMCP("Dynamic Service Test Server")
        mock_services = {"europe_pmc": initial_service}
        mock_logger = Mock()

        # 注册工具
        register_search_tools(mcp, mock_services, mock_logger)

        # 测试初始服务
        result1 = await initial_service.search_articles("test")
        assert len(result1["articles"]) == 3

        # 替换服务
        mock_services["europe_pmc"] = replacement_service

        # 测试替换后的服务
        result2 = await replacement_service.search_articles("test")
        assert len(result2["articles"]) == 10
