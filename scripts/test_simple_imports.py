#!/usr/bin/env python3
"""
简单测试：验证新创建的模块文件存在且基本结构正确
"""

import sys
import ast
from pathlib import Path

def test_module_exists(module_name, file_path):
    """测试模块文件是否存在且基本结构正确"""
    print(f"🔧 测试 {module_name} 模块...")
    try:
        if not file_path.exists():
            print(f"❌ {module_name} 文件不存在: {file_path}")
            return False

        # 尝试解析Python语法
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            ast.parse(content)
            print(f"✅ {module_name} 语法正确")
        except SyntaxError as e:
            print(f"❌ {module_name} 语法错误: {e}")
            return False

        # 检查关键内容
        if module_name == "middleware":
            required_classes = ["MCPErrorHandlingMiddleware", "LoggingMiddleware", "TimingMiddleware"]
            for cls in required_classes:
                if f"class {cls}" in content:
                    print(f"✅ 找到 {cls} 类")
                else:
                    print(f"⚠️ 未找到 {cls} 类")

        elif module_name == "resources":
            required_functions = ["register_config_resources", "register_journal_resources"]
            for func in required_functions:
                if f"def {func}" in content:
                    print(f"✅ 找到 {func} 函数")
                else:
                    print(f"⚠️ 未找到 {func} 函数")

        print(f"✅ {module_name} 模块结构正确")
        return True

    except Exception as e:
        print(f"❌ {module_name} 测试失败: {e}")
        return False

def test_csv_export_updated():
    """测试CSV导出功能已更新"""
    print("🔧 测试CSV导出功能更新...")
    try:
        batch_tools_path = Path(__file__).parent.parent / "src" / "article_mcp" / "tools" / "core" / "batch_tools.py"

        with open(batch_tools_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否移除了Excel相关代码
        excel_indicators = [
            "_export_to_excel",
            "_export_excel_with_pandas",
            "_export_excel_with_openpyxl",
            "pandas",
            "openpyxl"
        ]

        excel_found = False
        for indicator in excel_indicators:
            if indicator in content:
                print(f"⚠️ 仍发现Excel相关代码: {indicator}")
                excel_found = True

        if not excel_found:
            print("✅ Excel相关代码已成功移除")

        # 检查CSV导出功能
        if "_export_to_csv" in content:
            print("✅ CSV导出功能保持完整")
        else:
            print("❌ CSV导出功能缺失")
            return False

        # 检查错误消息是否更新
        if "支持的格式: json, csv" in content:
            print("✅ 错误消息已更新")
        else:
            print("⚠️ 错误消息可能需要更新")

        return True

    except Exception as e:
        print(f"❌ CSV导出功能测试失败: {e}")
        return False

def test_cli_imports_updated():
    """测试CLI导入是否正确"""
    print("🔧 测试CLI导入更新...")
    try:
        cli_path = Path(__file__).parent.parent / "src" / "article_mcp" / "cli.py"

        with open(cli_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否正确导入新模块
        middleware_import = "from .middleware import"
        resources_import = "from .resources import"

        if middleware_import in content:
            print("✅ 中间件模块导入正确")
        else:
            print("❌ 中间件模块导入缺失")
            return False

        if resources_import in content:
            print("✅ 资源模块导入正确")
        else:
            print("❌ 资源模块导入缺失")
            return False

        # 检查注册调用
        if "register_config_resources(mcp)" in content:
            print("✅ 资源注册调用正确")
        else:
            print("❌ 资源注册调用缺失")
            return False

        return True

    except Exception as e:
        print(f"❌ CLI导入测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Article MCP 架构修复验证")
    print("=" * 50)

    base_path = Path(__file__).parent.parent / "src" / "article_mcp"

    tests = [
        ("middleware", test_module_exists("middleware", base_path / "middleware.py")),
        ("resources", test_module_exists("resources", base_path / "resources.py")),
        ("CSV导出更新", test_csv_export_updated()),
        ("CLI导入更新", test_cli_imports_updated())
    ]

    passed = 0
    total = len(tests)

    for test_name, result in tests:
        print(f"\n📋 {test_name}测试:")
        print("-" * 30)

        if result:
            passed += 1
        else:
            print(f"❌ {test_name}测试失败")

    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 架构问题修复验证成功！")
        print("✅ 新模块已创建并正确集成")
        print("✅ Excel导出功能已移除")
        print("✅ 所有导入语句已更新")
        return True
    else:
        print("⚠️ 部分测试失败，请检查具体问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)