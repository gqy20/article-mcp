#!/usr/bin/env python3
"""
pytest测试套件验证脚本
验证6工具架构的pytest测试套件功能
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description, timeout=60):
    """运行命令并处理结果"""
    print(f"\n🔍 {description}")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 60)

    try:
        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=Path(__file__).parent.parent
        )
        end_time = time.time()

        print(f"耗时: {end_time - start_time:.2f}秒")

        if result.returncode == 0:
            print("✅ 成功")
            if result.stdout:
                print("输出:")
                print(result.stdout)
        else:
            print("❌ 失败")
            print("错误输出:")
            print(result.stderr)
            if result.stdout:
                print("标准输出:")
                print(result.stdout)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⏰ 超时")
        return False
    except Exception as e:
        print(f"💥 异常: {e}")
        return False


def check_test_files():
    """检查测试文件是否存在"""
    print("\n📁 检查测试文件结构")
    print("=" * 60)

    test_files = [
        "tests/conftest.py",
        "tests/unit/test_six_tools.py",
        "tests/unit/test_tool_core.py",
        "tests/integration/test_six_tools_integration.py",
        "tests/utils/test_helpers.py",
        "pytest.ini",
    ]

    missing_files = []
    for file_path in test_files:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (缺失)")
            missing_files.append(file_path)

    return len(missing_files) == 0


def main():
    """主测试函数"""
    print("🧪 6工具架构pytest测试套件验证")
    print("=" * 70)

    # 检查测试文件
    files_ok = check_test_files()
    if not files_ok:
        print("\n❌ 测试文件检查失败，请确保所有测试文件存在")
        return False

    # 设置Python路径
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    env = {
        "PYTHONPATH": str(src_path),
        "PYTHONUNBUFFERED": "1",
        "TESTING": "1",
        "CACHE_TEST_MODE": "1",
        "DISABLE_NETWORK_CALLS": "1",
    }

    success_count = 0
    total_tests = 0

    # 测试1: 检查pytest版本
    total_tests += 1
    if run_command([sys.executable, "-m", "pytest", "--version"], "检查pytest版本"):
        success_count += 1

    # 测试2: 验证测试发现
    total_tests += 1
    if run_command([sys.executable, "-m", "pytest", "--collect-only", "-q"], "验证测试发现"):
        success_count += 1

    # 测试3: 运行基础单元测试
    total_tests += 1
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/test_six_tools.py::TestSixToolIntegration::test_all_tools_registered",
        "-v",
        "--tb=short",
    ]

    # 设置环境变量
    import os

    old_env = os.environ.copy()
    os.environ.update(env)

    try:
        if run_command(cmd, "运行基础单元测试", timeout=30):
            success_count += 1
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    # 测试4: 运行配置验证测试
    total_tests += 1
    try:
        os.environ.update(env)
        if run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/test_cli.py::TestCLIBasics::test_create_mcp_server",
                "-v",
                "--tb=short",
            ],
            "运行配置验证测试",
            timeout=30,
        ):
            success_count += 1
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    # 测试5: 验证测试标记
    total_tests += 1
    try:
        os.environ.update(env)
        if run_command([sys.executable, "-m", "pytest", "--markers"], "验证测试标记"):
            success_count += 1
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    # 测试6: 检查测试覆盖率配置
    total_tests += 1
    try:
        os.environ.update(env)
        cov_check_cmd = [sys.executable, "-c", "import pytest_cov; print('pytest-cov available')"]
        if run_command(cov_check_cmd, "检查测试覆盖率依赖"):
            success_count += 1
    except ImportError:
        print("\n⚠️  pytest-cov 未安装，跳过覆盖率检查")
        total_tests -= 1  # 不计入总数
        success_count += 1  # 也不影响成功率
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    # 输出总结
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print(f"通过测试: {success_count}/{total_tests}")
    print(f"成功率: {(success_count / total_tests) * 100:.1f}%")

    if success_count == total_tests:
        print("🎉 所有测试验证通过！pytest测试套件配置正确")
        return True
    else:
        print("⚠️  部分测试验证失败，请检查配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
