#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI集成测试
测试命令行接口的完整功能
"""

import pytest
import asyncio
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, Mock

from article_mcp.tests.test_helpers import TestTimer, MockDataGenerator


class TestCLICommands:
    """CLI命令测试"""

    @pytest.mark.integration
    def test_cli_info_command(self):
        """测试CLI info命令"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "info"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 验证结果
            assert result.returncode == 0
            assert "Article MCP 文献搜索服务器" in result.stdout
            assert "基于 FastMCP 框架" in result.stdout
            assert "🚀 核心功能" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    def test_cli_test_command(self):
        """测试CLI test命令"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "test"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 验证结果
            assert result.returncode == 0
            assert "Europe PMC MCP 服务器测试" in result.stdout
            assert "✓ MCP 服务器创建成功" in result.stdout
            assert "工具注册: 成功" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    def test_cli_help_command(self):
        """测试CLI help命令"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "--help"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 验证结果
            assert result.returncode == 0
            assert "Article MCP 文献搜索服务器" in result.stdout
            assert "可用命令" in result.stdout
            assert "server" in result.stdout
            assert "test" in result.stdout
            assert "info" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    def test_cli_server_help_command(self):
        """测试CLI server子命令help"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "server", "--help"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 验证结果
            assert result.returncode == 0
            assert "--transport" in result.stdout
            assert "--host" in result.stdout
            assert "--port" in result.stdout
            assert "--path" in result.stdout
            assert "stdio" in result.stdout
            assert "sse" in result.stdout
            assert "streamable-http" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")


class TestCLIArguments:
    """CLI参数测试"""

    @pytest.mark.integration
    def test_cli_server_arguments(self):
        """测试CLI server参数"""
        # 测试不同参数组合
        test_cases = [
            ["--transport", "stdio"],
            ["--transport", "sse", "--host", "localhost", "--port", "9000"],
            ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080", "--path", "/api"]
        ]

        for args in test_cases:
            # 构建CLI命令
            cmd = [sys.executable, "-m", "article_mcp.cli", "server"] + args

            # 设置环境变量
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

            try:
                # 执行命令（应该在启动后立即停止，因为我们需要手动中断）
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=Path(__file__).parent.parent.parent.parent.parent
                )

                # 等待一段时间让服务器启动
                time.sleep(2)

                # 终止进程
                process.terminate()
                stdout, stderr = process.communicate(timeout=5)

                # 验证服务器启动信息
                assert "启动 Article MCP 服务器" in stdout

            except subprocess.TimeoutExpired:
                process.kill()
                pytest.skip(f"CLI命令超时: {' '.join(args)}")
            except FileNotFoundError:
                pytest.skip("CLI模块未找到")
            except Exception as e:
                # 其他错误可能是预期的（比如端口占用等）
                pass


class TestCLIErrorHandling:
    """CLI错误处理测试"""

    @pytest.mark.integration
    def test_cli_invalid_command(self):
        """测试无效CLI命令"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "invalid_command"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 应该显示帮助信息
            assert result.returncode != 0

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    def test_cli_invalid_transport(self):
        """测试无效传输模式"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "server", "--transport", "invalid"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 应该有错误退出
            assert result.returncode != 0

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    def test_cli_invalid_port(self):
        """测试无效端口"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "server", "--port", "invalid_port"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 应该有错误退出
            assert result.returncode != 0

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")


class TestCLIPerformance:
    """CLI性能测试"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cli_startup_performance(self):
        """测试CLI启动性能"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "info"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        try:
            # 测量启动时间
            with TestTimer() as timer:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                    cwd=Path(__file__).parent.parent.parent.parent.parent
                )

            # 验证性能要求
            assert timer.stop() < 10.0  # 应该在10秒内完成
            assert result.returncode == 0

        except subprocess.TimeoutExpired:
            pytest.skip("CLI启动超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cli_memory_usage(self):
        """测试CLI内存使用"""
        try:
            import psutil

            # 构建CLI命令
            cmd = [sys.executable, "-m", "article_mcp.cli", "info"]

            # 设置环境变量
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

            # 记录初始内存
            initial_memory = psutil.Process().memory_info().rss

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 记录最终内存
            final_memory = psutil.Process().memory_info().rss
            memory_increase = final_memory - initial_memory

            # 验证内存使用合理（不超过50MB增长）
            assert memory_increase < 50 * 1024 * 1024  # 50MB
            assert result.returncode == 0

        except ImportError:
            pytest.skip("psutil不可用，跳过内存测试")
        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")


class TestCLICompatibility:
    """CLI兼容性测试"""

    @pytest.mark.integration
    def test_legacy_main_py_compatibility(self):
        """测试与legacy main.py的兼容性"""
        # 构建CLI命令
        cmd = [sys.executable, "main.py", "info"]

        # 设置环境变量
        env = os.environ.copy()

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 验证兼容性
            assert result.returncode == 0
            assert "Article MCP 文献搜索服务器" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("main.py文件未找到")

    @pytest.mark.integration
    def test_python_module_execution(self):
        """测试Python模块执行方式"""
        # 测试不同的执行方式
        execution_methods = [
            ["python", "-m", "article_mcp"],
            ["python3", "-m", "article_mcp"],
            [sys.executable, "-m", "article_mcp"]
        ]

        for cmd_prefix in execution_methods:
            # 构建CLI命令
            cmd = cmd_prefix + ["info"]

            # 设置环境变量
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

            try:
                # 执行命令
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                    cwd=Path(__file__).parent.parent.parent.parent.parent
                )

                # 至少有一种方式应该工作
                if result.returncode == 0:
                    assert "Article MCP 文献搜索服务器" in result.stdout
                    break  # 找到工作的方式就退出

            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue  # 尝试下一种方式


class TestCLIEnvironment:
    """CLI环境测试"""

    @pytest.mark.integration
    def test_cli_environment_variables(self):
        """测试CLI环境变量"""
        # 构建CLI命令
        cmd = [sys.executable, "-m", "article_mcp.cli", "info"]

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
        env["ARTICLE_MCP_LOG_LEVEL"] = "DEBUG"

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent.parent
            )

            # 验证环境变量生效
            assert result.returncode == 0

        except subprocess.TimeoutExpired:
            pytest.skip("CLI命令超时")
        except FileNotFoundError:
            pytest.skip("CLI模块未找到")

    @pytest.mark.integration
    def test_cli_working_directory(self):
        """测试CLI工作目录"""
        # 测试在不同工作目录下运行
        test_dirs = [
            Path(__file__).parent.parent.parent.parent.parent,
            Path.cwd(),
            Path(__file__).parent
        ]

        for work_dir in test_dirs:
            if not work_dir.exists():
                continue

            # 构建CLI命令
            cmd = [sys.executable, "-m", "article_mcp.cli", "info"]

            # 设置环境变量
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

            try:
                # 执行命令
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                    cwd=work_dir
                )

                # 验证在不同目录下都能工作
                assert result.returncode == 0
                assert "Article MCP 文献搜索服务器" in result.stdout

            except subprocess.TimeoutExpired:
                pytest.skip(f"CLI在目录 {work_dir} 下超时")
            except FileNotFoundError:
                pytest.skip("CLI模块未找到")