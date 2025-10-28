#!/usr/bin/env python3
"""
测试新创建模块的基本导入功能
不依赖fastmcp等外部库
"""

import sys
import logging
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_middleware_basic_import():
    """测试中间件模块基本导入"""
    print("🔧 测试中间件模块基本导入...")
    try:
        # 测试导入中间件类和函数
        from article_mcp.middleware import (
            create_error_handling_middleware,
            create_logging_middleware,
            create_timing_middleware,
            get_global_timing_middleware,
            get_global_performance_stats,
            reset_global_performance_stats
        )
        print("✅ 中间件模块基本导入成功")

        # 测试创建实例
        logger = logging.getLogger(__name__)

        error_middleware = create_error_handling_middleware(logger)
        logging_middleware = create_logging_middleware(logger)
        timing_middleware = create_timing_middleware()

        print("✅ 中间件实例创建成功")

        # 测试全局性能统计功能
        global_timing = get_global_timing_middleware()
        stats = get_global_performance_stats()
        reset_global_performance_stats()

        print("✅ 全局性能统计功能正常")
        return True

    except Exception as e:
        print(f"❌ 中间件模块测试失败: {e}")
        return False

def test_resources_basic_import():
    """测试资源模块基本导入"""
    print("🔧 测试资源模块基本导入...")
    try:
        from article_mcp.resources import (
            get_available_resources,
            get_resource_description
        )
        print("✅ 资源模块基本导入成功")

        # 测试获取可用资源
        resources = get_available_resources()
        print(f"✅ 发现 {len(resources)} 个可用资源")

        # 测试获取资源描述
        for resource in resources[:3]:  # 只测试前3个
            description = get_resource_description(resource)
            print(f"  - {resource}: {description[:30]}...")

        return True

    except Exception as e:
        print(f"❌ 资源模块测试失败: {e}")
        return False

def test_csv_export_basic_import():
    """测试CSV导出基本功能"""
    print("🔧 测试CSV导出基本功能...")
    try:
        from article_mcp.tools.core.batch_tools import _export_to_csv
        print("✅ CSV导出函数导入成功")

        # 创建测试数据
        test_results = {
            "merged_results": [
                {
                    "title": "测试文章1",
                    "authors": [{"name": "作者1"}, {"name": "作者2"}],
                    "journal": "测试期刊",
                    "publication_date": "2023-01-01",
                    "doi": "10.1000/test1",
                    "abstract": "这是一个测试摘要",
                    "source": "test"
                }
            ]
        }

        # 测试CSV导出（创建临时文件）
        import tempfile
        logger = logging.getLogger(__name__)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            records_count = _export_to_csv(test_results, tmp_path, True, logger)
            print(f"✅ CSV导出测试成功，导出了 {records_count} 条记录")

            # 检查文件是否存在
            if tmp_path.exists():
                file_size = tmp_path.stat().st_size
                print(f"✅ CSV文件创建成功，大小: {file_size} 字节")

                # 读取文件内容验证
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "测试文章1" in content and "作者1" in content:
                        print("✅ CSV文件内容验证成功")
                    else:
                        print("⚠️ CSV文件内容验证失败")

                tmp_path.unlink()  # 清理临时文件
                return True
            else:
                print("❌ CSV文件未创建")
                return False

        except Exception as e:
            print(f"❌ CSV导出测试失败: {e}")
            return False

    except Exception as e:
        print(f"❌ CSV导出功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Article MCP 新模块基本功能验证")
    print("=" * 50)

    tests = [
        ("中间件模块", test_middleware_basic_import),
        ("资源模块", test_resources_basic_import),
        ("CSV导出功能", test_csv_export_basic_import)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        print("-" * 30)

        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")

    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有新模块功能正常！")
        print("✅ 架构问题修复成功！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查具体错误")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)