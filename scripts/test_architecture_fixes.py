#!/usr/bin/env python3
"""
测试架构问题修复
验证middleware和resources模块的功能
"""

import sys
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_middleware_import():
    """测试中间件模块导入"""
    print("🔧 测试中间件模块导入...")
    try:
        from article_mcp.middleware import (
            MCPErrorHandlingMiddleware,
            LoggingMiddleware,
            TimingMiddleware,
            create_error_handling_middleware,
            create_logging_middleware,
            create_timing_middleware
        )
        print("✅ 中间件模块导入成功")

        # 测试创建中间件实例
        import logging
        logger = logging.getLogger(__name__)

        error_middleware = create_error_handling_middleware(logger)
        logging_middleware = create_logging_middleware(logger)
        timing_middleware = create_timing_middleware()

        print("✅ 中间件实例创建成功")
        return True

    except Exception as e:
        print(f"❌ 中间件模块测试失败: {e}")
        return False

def test_resources_import():
    """测试资源模块导入"""
    print("🔧 测试资源模块导入...")
    try:
        from article_mcp.resources import (
            register_config_resources,
            register_journal_resources,
            register_all_resources,
            get_available_resources,
            get_resource_description
        )
        print("✅ 资源模块导入成功")

        # 测试获取可用资源
        resources = get_available_resources()
        print(f"✅ 发现 {len(resources)} 个可用资源")

        # 测试获取资源描述
        for resource in resources[:3]:  # 只测试前3个
            description = get_resource_description(resource)
            print(f"  - {resource}: {description[:50]}...")

        return True

    except Exception as e:
        print(f"❌ 资源模块测试失败: {e}")
        return False

def test_csv_export_function():
    """测试CSV导出功能"""
    print("🔧 测试CSV导出功能...")
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
                },
                {
                    "title": "测试文章2",
                    "authors": [{"name": "作者3"}],
                    "journal": "另一个测试期刊",
                    "publication_date": "2023-02-01",
                    "doi": "10.1000/test2",
                    "abstract": "这是另一个测试摘要",
                    "source": "test"
                }
            ]
        }

        # 测试CSV导出（创建临时文件）
        import tempfile
        import logging
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

def test_mcp_server_creation():
    """测试MCP服务器创建（不启动）"""
    print("🔧 测试MCP服务器创建...")
    try:
        # 模拟缺失的fastmcp模块
        class MockFastMCP:
            def __init__(self, name, version="1.0"):
                self.name = name
                self.version = version
                self.tools = {}

            def add_middleware(self, middleware):
                pass

            def tool(self, description=None, annotations=None, tags=None):
                def decorator(func):
                    self.tools[func.__name__] = type('MockTool', (), {'description': description or ''})()
                    return func
                return decorator

            def resource(self, uri):
                def decorator(func):
                    return func
                return decorator

        # 临时替换fastmcp导入
        import article_mcp.cli
        original_fastmcp = None

        # 保存原始导入并替换
        import sys
        sys.modules['fastmcp'] = type('MockModule', (), {'FastMCP': MockFastMCP})()
        sys.modules['mcp'] = type('MockModule', (), {
            'types': type('MockTypes', (), {
                'ToolAnnotations': type('MockAnnotations', (), {})
            })(),
            'McpError': Exception,
            'ErrorData': type('MockErrorData', (), {})
        })()

        # 重新导入以使用模拟的fastmcp
        import importlib
        importlib.reload(article_mcp.cli)

        # 测试服务器创建
        mcp = article_mcp.cli.create_mcp_server()
        print(f"✅ MCP服务器创建成功，注册了 {len(mcp.tools)} 个工具")

        return True

    except Exception as e:
        print(f"❌ MCP服务器创建测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Article MCP 架构问题修复验证")
    print("=" * 60)

    tests = [
        ("中间件模块", test_middleware_import),
        ("资源模块", test_resources_import),
        ("CSV导出功能", test_csv_export_function),
        ("MCP服务器创建", test_mcp_server_creation)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        print("-" * 40)

        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"🎯 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有架构问题已成功修复！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查具体错误")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)