#!/usr/bin/env python3
"""
快速验证脚本
运行最基本的功能测试来快速验证项目状态
注意：这是test_working_functions.py的简化版本，用于快速检查
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_package_import():
    """测试包导入"""
    print("🔍 测试包导入...")
    try:
        import importlib.util

        spec = importlib.util.find_spec("article_mcp.cli")
        if spec is None:
            raise ImportError("article_mcp.cli not found")

        print("✅ 包导入成功")
        return True
    except ImportError as e:
        print(f"❌ 包导入失败: {e}")
        return False


def test_server_creation():
    """测试服务器创建"""
    print("🔍 测试服务器创建...")
    try:
        # 需要mock所有在cli.py中导入的模块
        with patch("article_mcp.services.europe_pmc.create_europe_pmc_service", Mock()):
            with patch("article_mcp.services.pubmed_search.create_pubmed_service", Mock()):
                with patch("article_mcp.services.crossref_service.CrossRefService", Mock()):
                    with patch("article_mcp.services.openalex_service.OpenAlexService", Mock()):
                        with patch(
                            "article_mcp.services.reference_service.create_reference_service",
                            Mock(),
                        ):
                            with patch(
                                "article_mcp.services.literature_relation_service.create_literature_relation_service",
                                Mock(),
                            ):
                                with patch(
                                    "article_mcp.services.arxiv_search.create_arxiv_service", Mock()
                                ):
                                    with patch(
                                        "article_mcp.tools.core.search_tools.register_search_tools",
                                        Mock(),
                                    ):
                                        with patch(
                                            "article_mcp.tools.core.article_tools.register_article_tools",
                                            Mock(),
                                        ):
                                            with patch(
                                                "article_mcp.tools.core.reference_tools.register_reference_tools",
                                                Mock(),
                                            ):
                                                with patch(
                                                    "article_mcp.tools.core.relation_tools.register_relation_tools",
                                                    Mock(),
                                                ):
                                                    with patch(
                                                        "article_mcp.tools.core.quality_tools.register_quality_tools",
                                                        Mock(),
                                                    ):
                                                        with patch(
                                                            "article_mcp.tools.core.batch_tools.register_batch_tools",
                                                            Mock(),
                                                        ):
                                                            from article_mcp.cli import (
                                                                create_mcp_server,
                                                            )

                                                            create_mcp_server()
        print("✅ 服务器创建成功")
        return True
    except Exception as e:
        print(f"❌ 服务器创建失败: {e}")
        return False


def test_cli_command():
    """测试CLI命令"""
    print("🔍 测试CLI命令...")
    try:
        import subprocess

        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_path)

        cmd = [sys.executable, "-m", "article_mcp", "info"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, env=env, cwd=project_root
        )

        if result.returncode == 0 and "Article MCP 文献搜索服务器" in result.stdout:
            print("✅ CLI命令正常")
            return True
        else:
            print(f"❌ CLI命令失败 (返回码: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ CLI命令测试失败: {e}")
        return False


def test_service_imports():
    """测试服务导入"""
    print("🔍 测试服务导入...")
    services = [
        ("europe_pmc", "EuropePMCService"),
        ("arxiv_search", "create_arxiv_service"),
        ("crossref_service", "CrossRefService"),
    ]

    success_count = 0
    for module_name, class_name in services:
        try:
            module = __import__(f"article_mcp.services.{module_name}", fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
            success_count += 1
        except (ImportError, AttributeError) as e:
            print(f"❌ {module_name}.{class_name}: {e}")

    if success_count == len(services):
        print("✅ 所有服务导入成功")
        return True
    else:
        print(f"❌ 只有 {success_count}/{len(services)} 个服务导入成功")
        return False


def main():
    """运行快速测试"""
    print("⚡ Article MCP 快速测试")
    print("=" * 40)

    tests = [test_package_import, test_server_creation, test_cli_command, test_service_imports]

    passed = 0
    start_time = time.time()

    for test in tests:
        if test():
            passed += 1
        print()

    duration = time.time() - start_time

    print("=" * 40)
    print(f"结果: {passed}/{len(tests)} 通过")
    print(f"耗时: {duration:.2f} 秒")

    if passed == len(tests):
        print("🎉 快速测试通过!")
        return 0
    else:
        print("❌ 快速测试失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
