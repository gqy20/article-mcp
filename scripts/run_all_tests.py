#!/usr/bin/env python3
"""
运行所有测试的主脚本
"""

import subprocess
import sys
import time
from pathlib import Path

# 获取脚本目录
script_dir = Path(__file__).parent

# 测试脚本列表 - 只包含实际存在的测试文件
test_scripts = [
    ("核心功能测试", "test_working_functions.py"),
    ("架构修复测试", "test_architecture_fixes.py"),
    ("模块导入测试", "test_module_imports.py"),
    ("简单导入测试", "test_simple_imports.py"),
    ("FastMCP合规性测试", "test_fastmcp_compliance.py"),
    ("性能测试", "test_performance.py"),
]


def run_test_script(script_name, description):
    """运行单个测试脚本"""
    print(f"🚀 开始运行: {description}")
    print("=" * 60)

    script_path = script_dir / script_name
    if not script_path.exists():
        print(f"✗ 测试脚本不存在: {script_path}")
        return False, 0

    try:
        # 运行测试脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120,  # 2分钟超时
            cwd=script_dir.parent,
        )

        # 输出测试结果
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        print("=" * 60)
        if result.returncode == 0:
            print(f"✅ {description} - 通过")
            return True, result.returncode
        else:
            print(f"❌ {description} - 失败 (返回码: {result.returncode})")
            return False, result.returncode

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False, -1
    except Exception as e:
        print(f"💥 {description} - 异常: {e}")
        return False, -1


def main():
    """运行所有测试"""
    print("🧪 Article MCP 完整测试套件")
    print("=" * 60)
    print("开始时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    start_time = time.time()
    passed_count = 0
    total_count = len(test_scripts)

    # 运行所有测试
    for description, script_name in test_scripts:
        success, return_code = run_test_script(script_name, description)
        if success:
            passed_count += 1
        print()  # 空行分隔

    end_time = time.time()
    duration = end_time - start_time

    # 输出总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"总测试数: {total_count}")
    print(f"通过数: {passed_count}")
    print(f"失败数: {total_count - passed_count}")
    print(f"总耗时: {duration:.2f} 秒")
    print(f"成功率: {(passed_count / total_count) * 100:.1f}%")
    print("结束时间:", time.strftime("%Y-%m-%d %H:%M:%S"))

    if passed_count == total_count:
        print("\n🎉 所有测试通过! 项目状态良好。")
        return 0
    else:
        print(f"\n⚠️  有 {total_count - passed_count} 个测试失败，需要检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
