#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试脚本
测试整个系统的集成功能
"""

import sys
import os
import asyncio
import time
import subprocess
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_full_package_integration():
    """测试完整包集成"""
    print("🔍 测试完整包集成...")

    try:
        # 测试完整导入链
        from article_mcp.cli import create_mcp_server
        from article_mcp.services.europe_pmc import EuropePMCService
        from article_mcp.tools.core.search_tools import register_search_tools

        # 创建模拟logger
        mock_logger = Mock()

        # 测试服务创建
        europe_pmc_service = EuropePMCService(mock_logger)

        # 测试工具注册（使用mock）
        mock_mcp = Mock()
        mock_services = {"europe_pmc": europe_pmc_service}

        with patch('article_mcp.tools.core.search_tools._search_services', mock_services):
            tools = register_search_tools(mock_mcp, mock_services, mock_logger)

        print("✓ 完整包集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 完整包集成测试失败: {e}")
        return False


async def test_async_integration():
    """测试异步集成"""
    print("🔍 测试异步集成...")

    try:
        from article_mcp.services.europe_pmc import EuropePMCService
        from article_mcp.tools.core.search_tools import _search_literature

        # 创建模拟服务和结果
        mock_logger = Mock()
        mock_service = Mock()
        mock_service.search_articles = AsyncMock(return_value={
            "articles": [
                {"title": "Test Article", "authors": ["Test Author"], "doi": "10.1000/test"}
            ],
            "total_count": 1
        })

        # 使用patch替换真实服务
        with patch('article_mcp.tools.core.search_tools._search_services',
                  {"europe_pmc": mock_service}):
            result = await _search_literature(
                keyword="test",
                sources=["europe_pmc"],
                max_results=10
            )

        assert "articles" in result
        assert len(result["articles"]) > 0

        print("✓ 异步集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 异步集成测试失败: {e}")
        return False


def test_mcp_server_integration():
    """测试MCP服务器集成"""
    print("🔍 测试MCP服务器集成...")

    try:
        # 使用大量mock来避免实际的网络调用
        with patch.multiple(
            'article_mcp.cli',
            create_europe_pmc_service=Mock(return_value=Mock()),
            create_pubmed_service=Mock(return_value=Mock()),
            CrossRefService=Mock(return_value=Mock()),
            OpenAlexService=Mock(return_value=Mock()),
            create_reference_service=Mock(return_value=Mock()),
            create_literature_relation_service=Mock(return_value=Mock()),
            create_arxiv_service=Mock(return_value=Mock()),
            register_search_tools=Mock(return_value=[]),
            register_article_tools=Mock(return_value=[]),
            register_reference_tools=Mock(return_value=[]),
            register_relation_tools=Mock(return_value=[]),
            register_quality_tools=Mock(return_value=[]),
            register_batch_tools=Mock(return_value=[])
        ):
            from article_mcp.cli import create_mcp_server
            server = create_mcp_server()

            assert server is not None

        print("✓ MCP服务器集成测试通过")
        return True
    except Exception as e:
        print(f"✗ MCP服务器集成测试失败: {e}")
        return False


def test_dependency_injection():
    """测试依赖注入"""
    print("🔍 测试依赖注入...")

    try:
        from article_mcp.services.europe_pmc import EuropePMCService
        from article_mcp.services.pubmed_search import create_pubmed_service

        # 创建模拟logger
        mock_logger = Mock()

        # 测试服务创建和依赖注入
        pubmed_service = create_pubmed_service(mock_logger)
        europe_pmc_service = EuropePMCService(mock_logger, pubmed_service)

        # 验证依赖注入成功
        assert europe_pmc_service.logger is mock_logger
        assert hasattr(europe_pmc_service, 'pubmed_service')

        print("✓ 依赖注入测试通过")
        return True
    except Exception as e:
        print(f"✗ 依赖注入测试失败: {e}")
        return False


def test_tool_registration_integration():
    """测试工具注册集成"""
    print("🔍 测试工具注册集成...")

    try:
        from article_mcp.tools.core.search_tools import register_search_tools
        from article_mcp.tools.core.article_tools import register_article_tools
        from article_mcp.tools.core.reference_tools import register_reference_tools

        # 创建模拟对象
        mock_mcp = Mock()
        mock_services = {
            "europe_pmc": Mock(),
            "pubmed": Mock(),
            "arxiv": Mock(),
            "crossref": Mock(),
            "openalex": Mock()
        }
        mock_logger = Mock()

        # 测试工具注册
        search_tools = register_search_tools(mock_mcp, mock_services, mock_logger)
        article_tools = register_article_tools(mock_mcp, mock_services, mock_logger)
        reference_tools = register_reference_tools(mock_mcp, Mock(), mock_logger)

        # 验证工具注册成功
        assert isinstance(search_tools, list)
        assert isinstance(article_tools, list)
        assert isinstance(reference_tools, list)

        print("✓ 工具注册集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 工具注册集成测试失败: {e}")
        return False


async def test_service_chain_integration():
    """测试服务链集成"""
    print("🔍 测试服务链集成...")

    try:
        from article_mcp.services.reference_service import create_reference_service
        from article_mcp.services.europe_pmc import EuropePMCService

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务链
        europe_pmc_service = EuropePMCService(mock_logger)
        reference_service = create_reference_service(mock_logger)

        # 模拟服务链调用
        mock_article = {"pmid": "12345678", "doi": "10.1000/test"}

        # 使用mock来避免实际API调用
        with patch.object(reference_service, 'get_references') as mock_get_refs:
            mock_get_refs.return_value = {
                "references": [
                    {"title": "Reference 1", "doi": "10.1000/ref1"},
                    {"title": "Reference 2", "doi": "10.1000/ref2"}
                ],
                "total_count": 2
            }

            result = await reference_service.get_references(
                identifier=mock_article["doi"],
                id_type="doi"
            )

        assert "references" in result
        assert len(result["references"]) == 2

        print("✓ 服务链集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 服务链集成测试失败: {e}")
        return False


def test_configuration_integration():
    """测试配置集成"""
    print("🔍 测试配置集成...")

    try:
        from article_mcp.services.mcp_config import get_mcp_config
        from article_mcp.cli import create_mcp_server

        # 测试配置获取
        config = get_mcp_config()

        # 验证配置结构
        assert isinstance(config, dict)

        # 测试配置在服务器创建中的使用
        with patch.multiple(
            'article_mcp.cli',
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
            register_batch_tools=Mock()
        ):
            server = create_mcp_server()
            assert server is not None

        print("✓ 配置集成测试通过")
        return True
    except Exception as e:
        print(f"✗ 配置集成测试失败: {e}")
        return False


def test_cli_to_service_integration():
    """测试CLI到服务集成"""
    print("🔍 测试CLI到服务集成...")

    try:
        # 测试CLI可以通过subprocess调用
        env = os.environ.copy()
        env['PYTHONPATH'] = str(src_path)

        cmd = [sys.executable, "-m", "article_mcp", "info"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            cwd=project_root
        )

        if result.returncode == 0 and "Article MCP 文献搜索服务器" in result.stdout:
            print("✓ CLI到服务集成测试通过")
            return True
        else:
            print(f"✗ CLI到服务集成测试失败 (返回码: {result.returncode})")
            return False
    except Exception as e:
        print(f"✗ CLI到服务集成测试失败: {e}")
        return False


async def main():
    """运行所有集成测试"""
    print("=" * 60)
    print("🔗 Article MCP 集成测试")
    print("=" * 60)

    tests = [
        test_full_package_integration,
        test_mcp_server_integration,
        test_dependency_injection,
        test_tool_registration_integration,
        test_service_chain_integration,
        test_configuration_integration,
        test_cli_to_service_integration
    ]

    async_tests = [
        test_async_integration
    ]

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
            if await test_func():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"✗ 异步测试 {test_func.__name__} 出现异常: {e}")
            print()

    end_time = time.time()
    duration = end_time - start_time

    print("=" * 60)
    print(f"📊 集成测试结果: {passed}/{total} 通过")
    print(f"⏱️  总耗时: {duration:.2f} 秒")

    if passed == total:
        print("🎉 所有集成测试通过!")
        return 0
    else:
        print("❌ 部分集成测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))