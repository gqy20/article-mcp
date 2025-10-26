#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本
测试 article-mcp 包的核心功能
"""

import sys
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_package_import():
    """测试包导入功能"""
    print("🔍 测试包导入功能...")

    try:
        from article_mcp.cli import create_mcp_server, show_info
        from article_mcp import __version__
        print("✓ 包导入成功")
        return True
    except ImportError as e:
        print(f"✗ 包导入失败: {e}")
        return False


def test_server_creation():
    """测试MCP服务器创建"""
    print("🔍 测试MCP服务器创建...")

    try:
        # 使用mock来避免实际的服务创建
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
            from article_mcp.cli import create_mcp_server
            server = create_mcp_server()
            print("✓ MCP服务器创建成功")
            return True
    except Exception as e:
        print(f"✗ MCP服务器创建失败: {e}")
        return False


def test_service_imports():
    """测试服务模块导入"""
    print("🔍 测试服务模块导入...")

    services_to_test = [
        'article_mcp.services.europe_pmc',
        'article_mcp.services.arxiv_search',
        'article_mcp.services.crossref_service',
        'article_mcp.services.openalex_service',
        'article_mcp.services.reference_service',
        'article_mcp.services.pubmed_search'
    ]

    success_count = 0
    for service in services_to_test:
        try:
            __import__(service)
            print(f"✓ {service} 导入成功")
            success_count += 1
        except ImportError as e:
            print(f"✗ {service} 导入失败: {e}")

    return success_count == len(services_to_test)


def test_tool_imports():
    """测试工具模块导入"""
    print("🔍 测试工具模块导入...")

    tools_to_test = [
        'article_mcp.tools.core.search_tools',
        'article_mcp.tools.core.article_tools',
        'article_mcp.tools.core.reference_tools',
        'article_mcp.tools.core.quality_tools'
    ]

    success_count = 0
    for tool in tools_to_test:
        try:
            __import__(tool)
            print(f"✓ {tool} 导入成功")
            success_count += 1
        except ImportError as e:
            print(f"✗ {tool} 导入失败: {e}")

    return success_count == len(tools_to_test)


def test_cli_help():
    """测试CLI帮助功能"""
    print("🔍 测试CLI帮助功能...")

    try:
        from article_mcp.cli import show_info
        print("✓ CLI帮助功能正常")
        return True
    except Exception as e:
        print(f"✗ CLI帮助功能失败: {e}")
        return False


def test_package_structure():
    """测试包结构完整性"""
    print("🔍 测试包结构完整性...")

    required_files = [
        "src/article_mcp/__init__.py",
        "src/article_mcp/cli.py",
        "src/article_mcp/__main__.py",
        "src/article_mcp/services/__init__.py",
        "src/article_mcp/tools/__init__.py",
        "src/article_mcp/tools/core/__init__.py"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ 缺少必要文件: {missing_files}")
        return False
    else:
        print("✓ 包结构完整")
        return True


def main():
    """运行所有基础功能测试"""
    print("=" * 60)
    print("🧪 Article MCP 基础功能测试")
    print("=" * 60)

    tests = [
        test_package_import,
        test_server_creation,
        test_service_imports,
        test_tool_imports,
        test_cli_help,
        test_package_structure
    ]

    passed = 0
    total = len(tests)

    start_time = time.time()

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"✗ 测试 {test_func.__name__} 出现异常: {e}")
            print()

    end_time = time.time()
    duration = end_time - start_time

    print("=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    print(f"⏱️  总耗时: {duration:.2f} 秒")

    if passed == total:
        print("🎉 所有基础功能测试通过!")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())