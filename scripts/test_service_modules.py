#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务模块测试脚本
测试各种服务模块的基本功能
"""

import sys
import os
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_service_imports():
    """测试服务模块导入"""
    print("🔍 测试服务模块导入...")

    services = [
        ('europe_pmc', 'EuropePMCService'),
        ('arxiv_search', 'create_arxiv_service'),
        ('crossref_service', 'CrossRefService'),
        ('openalex_service', 'OpenAlexService'),
        ('reference_service', 'create_reference_service'),
        ('pubmed_search', 'create_pubmed_service'),
        ('literature_relation_service', 'create_literature_relation_service')
    ]

    success_count = 0
    for module_name, class_name in services:
        try:
            module = __import__(f'article_mcp.services.{module_name}', fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name} 导入成功")
            success_count += 1
        except (ImportError, AttributeError) as e:
            print(f"✗ {module_name}.{class_name} 导入失败: {e}")

    return success_count == len(services)


def test_europe_pmc_service():
    """测试Europe PMC服务"""
    print("🔍 测试Europe PMC服务...")

    try:
        from article_mcp.services.europe_pmc import EuropePMCService

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = EuropePMCService(mock_logger)

        # 验证基本属性
        assert hasattr(service, 'base_url')
        assert hasattr(service, 'cache')
        assert hasattr(service, 'search_semaphore')

        print("✓ Europe PMC服务初始化成功")
        return True
    except Exception as e:
        print(f"✗ Europe PMC服务测试失败: {e}")
        return False


def test_arxiv_service():
    """测试ArXiv服务"""
    print("🔍 测试ArXiv服务...")

    try:
        from article_mcp.services.arxiv_search import create_arxiv_service

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = create_arxiv_service(mock_logger)

        # 验证基本属性
        assert service is not None
        assert hasattr(service, 'search_papers')

        print("✓ ArXiv服务创建成功")
        return True
    except Exception as e:
        print(f"✗ ArXiv服务测试失败: {e}")
        return False


def test_crossref_service():
    """测试CrossRef服务"""
    print("🔍 测试CrossRef服务...")

    try:
        from article_mcp.services.crossref_service import CrossRefService

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = CrossRefService(mock_logger)

        # 验证基本属性
        assert hasattr(service, 'base_url')
        assert hasattr(service, '_make_request')

        print("✓ CrossRef服务初始化成功")
        return True
    except Exception as e:
        print(f"✗ CrossRef服务测试失败: {e}")
        return False


def test_openalex_service():
    """测试OpenAlex服务"""
    print("🔍 测试OpenAlex服务...")

    try:
        from article_mcp.services.openalex_service import OpenAlexService

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = OpenAlexService(mock_logger)

        # 验证基本属性
        assert hasattr(service, 'base_url')
        assert hasattr(service, '_make_request')

        print("✓ OpenAlex服务初始化成功")
        return True
    except Exception as e:
        print(f"✗ OpenAlex服务测试失败: {e}")
        return False


def test_reference_service():
    """测试参考文献服务"""
    print("🔍 测试参考文献服务...")

    try:
        from article_mcp.services.reference_service import create_reference_service

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = create_reference_service(mock_logger)

        # 验证基本属性
        assert service is not None
        assert hasattr(service, 'get_references')

        print("✓ 参考文献服务创建成功")
        return True
    except Exception as e:
        print(f"✗ 参考文献服务测试失败: {e}")
        return False


def test_pubmed_service():
    """测试PubMed服务"""
    print("🔍 测试PubMed服务...")

    try:
        from article_mcp.services.pubmed_search import create_pubmed_service

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = create_pubmed_service(mock_logger)

        # 验证基本属性
        assert service is not None
        assert hasattr(service, 'search')
        assert hasattr(service, 'get_article_details')

        print("✓ PubMed服务创建成功")
        return True
    except Exception as e:
        print(f"✗ PubMed服务测试失败: {e}")
        return False


async def test_async_service_functionality():
    """测试异步服务功能"""
    print("🔍 测试异步服务功能...")

    try:
        from article_mcp.services.europe_pmc import EuropePMCService

        # 创建模拟logger
        mock_logger = Mock()

        # 创建服务实例
        service = EuropePMCService(mock_logger)

        # 验证异步方法存在
        assert hasattr(service, 'search_async')
        assert hasattr(service, 'get_article_details_async')

        print("✓ 异步服务功能正常")
        return True
    except Exception as e:
        print(f"✗ 异步服务功能测试失败: {e}")
        return False


def test_service_error_handling():
    """测试服务错误处理"""
    print("🔍 测试服务错误处理...")

    try:
        from article_mcp.services.europe_pmc import EuropePMCService
        from article_mcp.services.error_utils import APIError, NetworkError

        # 验证错误类存在
        assert APIError is not None
        assert NetworkError is not None

        # 测试错误实例化
        api_error = APIError("Test API Error", 500)
        network_error = NetworkError("Test Network Error")

        assert str(api_error) == "Test API Error"
        assert str(network_error) == "Test Network Error"

        print("✓ 服务错误处理正常")
        return True
    except Exception as e:
        print(f"✗ 服务错误处理测试失败: {e}")
        return False


def test_service_configurations():
    """测试服务配置"""
    print("🔍 测试服务配置...")

    try:
        from article_mcp.services.mcp_config import get_mcp_config

        # 测试配置获取（可能为空，但不应该出错）
        config = get_mcp_config()

        # 验证配置返回的是字典
        assert isinstance(config, dict)

        print("✓ 服务配置正常")
        return True
    except Exception as e:
        print(f"✗ 服务配置测试失败: {e}")
        return False


async def main():
    """运行所有服务模块测试"""
    print("=" * 60)
    print("🔧 Article MCP 服务模块测试")
    print("=" * 60)

    tests = [
        test_service_imports,
        test_europe_pmc_service,
        test_arxiv_service,
        test_crossref_service,
        test_openalex_service,
        test_reference_service,
        test_pubmed_service,
        test_service_error_handling,
        test_service_configurations
    ]

    # 添加异步测试
    async_tests = [test_async_service_functionality]

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
    print(f"📊 服务模块测试结果: {passed}/{total} 通过")
    print(f"⏱️  总耗时: {duration:.2f} 秒")

    if passed == total:
        print("🎉 所有服务模块测试通过!")
        return 0
    else:
        print("❌ 部分服务模块测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))