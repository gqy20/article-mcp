#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI功能测试脚本
测试命令行接口的各种功能
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def run_cli_command(args, timeout=30):
    """运行CLI命令并返回结果"""
    env = os.environ.copy()
    env['PYTHONPATH'] = str(src_path)

    try:
        cmd = [sys.executable, "-m", "article_mcp"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=project_root
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except Exception as e:
        return -1, "", f"命令执行错误: {e}"


def test_cli_info_command():
    """测试CLI info命令"""
    print("🔍 测试CLI info命令...")

    returncode, stdout, stderr = run_cli_command(["info"])

    if returncode == 0 and "Article MCP 文献搜索服务器" in stdout:
        print("✓ CLI info命令执行成功")
        return True
    else:
        print(f"✗ CLI info命令执行失败 (返回码: {returncode})")
        if stderr:
            print(f"  错误信息: {stderr}")
        return False


def test_cli_help_command():
    """测试CLI help命令"""
    print("🔍 测试CLI help命令...")

    returncode, stdout, stderr = run_cli_command(["--help"])

    if returncode == 0 and ("usage:" in stdout or "用法:" in stdout):
        print("✓ CLI help命令执行成功")
        return True
    else:
        print(f"✗ CLI help命令执行失败 (返回码: {returncode})")
        if stderr:
            print(f"  错误信息: {stderr}")
        return False


def test_cli_invalid_command():
    """测试无效命令处理"""
    print("🔍 测试无效命令处理...")

    returncode, stdout, stderr = run_cli_command(["invalid_command"])

    # 无效命令应该返回非零退出码
    if returncode != 0:
        print("✓ 无效命令正确处理")
        return True
    else:
        print("✗ 无效命令处理不正确")
        return False


def test_cli_version():
    """测试版本信息"""
    print("🔍 测试版本信息...")

    try:
        # 尝试从包中获取版本信息
        from article_mcp import __version__
        print(f"✓ 版本信息: {__version__}")
        return True
    except ImportError:
        # 如果没有版本信息，尝试从pyproject.toml读取
        try:
            pyproject_path = project_root / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.strip().startswith('version ='):
                            version = line.split('=')[1].strip().strip('"\'')
                            print(f"✓ 版本信息: {version}")
                            return True

            print("✗ 无法获取版本信息")
            return False
        except Exception as e:
            print(f"✗ 读取版本信息失败: {e}")
            return False


def test_cli_import_functionality():
    """测试CLI模块导入功能"""
    print("🔍 测试CLI模块导入功能...")

    try:
        # 测试主要函数是否可以导入
        from article_mcp.cli import (
            create_mcp_server,
            main,
            start_server,
            show_info,
            run_test
        )
        print("✓ CLI主要函数导入成功")
        return True
    except ImportError as e:
        print(f"✗ CLI函数导入失败: {e}")
        return False


def test_cli_module_execution():
    """测试CLI模块执行"""
    print("🔍 测试CLI模块执行...")

    try:
        # 测试python -m article_mcp执行
        returncode, stdout, stderr = run_cli_command([])

        # 没有参数时应该显示帮助信息或错误信息
        if returncode in [0, 1, 2]:  # 通常是0或1或2表示需要参数
            print("✓ CLI模块执行正常")
            return True
        else:
            print(f"✗ CLI模块执行异常 (返回码: {returncode})")
            return False
    except Exception as e:
        print(f"✗ CLI模块执行测试失败: {e}")
        return False


def test_cli_environment_variables():
    """测试环境变量处理"""
    print("🔍 测试环境变量处理...")

    env = os.environ.copy()
    env['PYTHONPATH'] = str(src_path)
    env['TESTING'] = '1'

    try:
        cmd = [sys.executable, "-m", "article_mcp", "info"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            cwd=project_root
        )

        if result.returncode == 0:
            print("✓ 环境变量处理正常")
            return True
        else:
            print(f"✗ 环境变量处理失败 (返回码: {result.returncode})")
            return False
    except Exception as e:
        print(f"✗ 环境变量测试失败: {e}")
        return False


def main():
    """运行所有CLI功能测试"""
    print("=" * 60)
    print("🖥️  Article MCP CLI功能测试")
    print("=" * 60)

    tests = [
        test_cli_import_functionality,
        test_cli_info_command,
        test_cli_help_command,
        test_cli_version,
        test_cli_module_execution,
        test_cli_invalid_command,
        test_cli_environment_variables
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
    print(f"📊 CLI测试结果: {passed}/{total} 通过")
    print(f"⏱️  总耗时: {duration:.2f} 秒")

    if passed == total:
        print("🎉 所有CLI功能测试通过!")
        return 0
    else:
        print("❌ 部分CLI测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())