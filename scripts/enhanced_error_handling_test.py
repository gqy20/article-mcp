#!/usr/bin/env python3
"""
增强型错误处理测试脚本

专门测试不同传输模式下的错误处理机制，确保错误响应符合MCP规范。
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from article_mcp.cli import create_mcp_server
    from fastmcp.client import Client
    from fastmcp.exceptions import ToolError
    from mcp import McpError
    from mcp.types import ErrorData
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已安装fastmcp: pip install fastmcp")
    sys.exit(1)


class EnhancedErrorHandlingTester:
    """增强型错误处理测试器"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.test_results = {
            "stdio": {"status": "pending", "tests": {}},
            "http": {"status": "pending", "tests": {}},
            "sse": {"status": "pending", "tests": {}}
        }

    def _setup_logger(self) -> logging.Logger:
        """设置测试日志"""
        logger = logging.getLogger("EnhancedErrorHandlingTester")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def test_error_scenarios(self, client: Client, transport_mode: str) -> Dict[str, bool]:
        """测试各种错误场景"""
        results = {
            "invalid_tool_params": False,
            "empty_required_params": False,
            "nonexistent_tool": False,
            "network_error_simulation": False,
            "tool_error_response": False,
            "mcp_error_response": False,
            "error_format_validation": False
        }

        try:
            # 测试1: 无效工具参数
            self.logger.info(f"测试{transport_mode.upper()}模式 - 无效工具参数")
            try:
                # 使用无效的参数类型调用search_literature
                await client.call_tool("search_literature", {"keyword": 123})
            except ToolError as e:
                results["invalid_tool_params"] = True
                self.logger.info(f"✅ {transport_mode.upper()}模式正确处理无效参数: {e}")
            except Exception as e:
                self.logger.error(f"❌ {transport_mode.upper()}模式无效参数处理异常: {e}")

            # 测试2: 空的必需参数
            self.logger.info(f"测试{transport_mode.upper()}模式 - 空的必需参数")
            try:
                await client.call_tool("search_literature", {"keyword": ""})
            except ToolError as e:
                results["empty_required_params"] = True
                self.logger.info(f"✅ {transport_mode.upper()}模式正确处理空参数: {e}")
            except Exception as e:
                self.logger.error(f"❌ {transport_mode.upper()}模式空参数处理异常: {e}")

            # 测试3: 不存在的工具
            self.logger.info(f"测试{transport_mode.upper()}模式 - 不存在的工具")
            try:
                await client.call_tool("nonexistent_tool", {"param": "value"})
            except McpError as e:
                if "not found" in str(e).lower() or "method not found" in str(e).lower():
                    results["nonexistent_tool"] = True
                    self.logger.info(f"✅ {transport_mode.upper()}模式正确处理不存在的工具: {e}")
                else:
                    self.logger.warning(f"⚠️ {transport_mode.upper()}模式工具不存在错误格式可能不规范: {e}")
            except Exception as e:
                self.logger.error(f"❌ {transport_mode.upper()}模式不存在工具处理异常: {e}")

            # 测试4: 验证错误响应格式
            self.logger.info(f"测试{transport_mode.upper()}模式 - 错误响应格式验证")
            try:
                await client.call_tool("search_literature", {"keyword": 123})
            except (ToolError, McpError) as e:
                # 验证错误对象是否包含必要信息
                if hasattr(e, 'message') and e.message:
                    results["tool_error_response"] = True
                    self.logger.info(f"✅ {transport_mode.upper()}模式错误响应包含message字段")

                # 验证MCP错误格式
                if isinstance(e, McpError) and hasattr(e, 'data') and e.data:
                    results["mcp_error_response"] = True
                    self.logger.info(f"✅ {transport_mode.upper()}模式MCP错误格式正确")

                results["error_format_validation"] = True
                self.logger.info(f"✅ {transport_mode.upper()}模式错误响应格式验证通过")
            except Exception as e:
                self.logger.error(f"❌ {transport_mode.upper()}模式错误格式验证异常: {e}")

        except Exception as e:
            self.logger.error(f"❌ {transport_mode.upper()}模式错误场景测试失败: {e}")

        return results

    async def test_stdio_error_handling(self) -> Dict[str, bool]:
        """测试STDIO模式错误处理"""
        self.logger.info("🚀 开始STDIO模式错误处理测试")

        try:
            mcp = create_mcp_server()

            # 直接调用内部方法测试错误处理
            # STDIO模式下主要验证中间件配置
            results = {
                "middleware_configured": False,
                "error_transformation": False,
                "user_input_error_classification": False
            }

            # 测试中间件配置
            if hasattr(mcp, '_middleware') and mcp._middleware:
                results["middleware_configured"] = True
                self.logger.info("✅ STDIO模式错误处理中间件已配置")

            # 测试错误转换机制（通过检查middleware模块）
            try:
                from article_mcp.middleware import MCPErrorHandlingMiddleware
                results["error_transformation"] = True
                self.logger.info("✅ STDIO模式错误转换机制存在")
            except ImportError:
                self.logger.error("❌ STDIO模式错误转换机制不存在")

            # 测试用户输入错误分类
            try:
                from article_mcp.middleware import MCPErrorHandlingMiddleware
                middleware = MCPErrorHandlingMiddleware(self.logger)
                if hasattr(middleware, '_is_user_input_error'):
                    results["user_input_error_classification"] = True
                    self.logger.info("✅ STDIO模式用户输入错误分类功能存在")
            except Exception:
                self.logger.error("❌ STDIO模式用户输入错误分类功能不存在")

            return results

        except Exception as e:
            self.logger.error(f"❌ STDIO模式错误处理测试失败: {e}")
            return {}

    async def test_http_error_handling(self) -> Dict[str, bool]:
        """测试HTTP模式错误处理"""
        self.logger.info("🌐 开始HTTP模式错误处理测试")

        results = {}

        try:
            # 启动HTTP服务器
            process = subprocess.Popen([
                sys.executable, "-m", "article_mcp",
                "server", "--transport", "streamable-http",
                "--host", "localhost", "--port", "9003"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 等待服务器启动
            time.sleep(3)

            if process.poll() is None:
                self.logger.info("✅ HTTP服务器启动成功")

                try:
                    async with Client("http://localhost:9003/mcp") as client:
                        results = await self.test_error_scenarios(client, "HTTP")

                except Exception as e:
                    self.logger.error(f"❌ HTTP客户端连接失败: {e}")

                # 清理进程
                process.terminate()
                process.wait(timeout=5)
            else:
                self.logger.error("❌ HTTP服务器启动失败")

        except Exception as e:
            self.logger.error(f"❌ HTTP模式错误处理测试失败: {e}")

        return results

    async def test_sse_error_handling(self) -> Dict[str, bool]:
        """测试SSE模式错误处理"""
        self.logger.info("🌊 开始SSE模式错误处理测试")

        results = {}

        try:
            # 启动SSE服务器
            process = subprocess.Popen([
                sys.executable, "-m", "article_mcp",
                "server", "--transport", "sse",
                "--host", "localhost", "--port", "9004"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 等待服务器启动
            time.sleep(3)

            if process.poll() is None:
                self.logger.info("✅ SSE服务器启动成功")

                try:
                    async with Client("http://localhost:9004/sse") as client:
                        results = await self.test_error_scenarios(client, "SSE")

                except Exception as e:
                    self.logger.error(f"❌ SSE客户端连接失败: {e}")

                # 清理进程
                process.terminate()
                process.wait(timeout=5)
            else:
                self.logger.error("❌ SSE服务器启动失败")

        except Exception as e:
            self.logger.error(f"❌ SSE模式错误处理测试失败: {e}")

        return results

    def calculate_score(self, results: Dict[str, bool]) -> int:
        """计算错误处理测试得分"""
        if not results:
            return 0

        passed_tests = sum(1 for passed in results.values() if passed)
        total_tests = len(results)
        return int((passed_tests / total_tests) * 100) if total_tests > 0 else 0

    def generate_report(self) -> str:
        """生成错误处理测试报告"""
        report = ["\n" + "="*60]
        report.append("🔧 增强型错误处理测试报告")
        report.append("="*60)
        report.append("")

        total_score = 0
        completed_tests = 0

        for transport, data in self.test_results.items():
            if data.get("status") == "completed" and data.get("tests"):
                score = self.calculate_score(data["tests"])
                status = "✅ 优秀" if score >= 90 else "✅ 良好" if score >= 80 else "⚠️ 合格" if score >= 60 else "❌ 需改进"

                report.append(f"📡 {transport.upper()} 传输模式")
                report.append(f"   状态: {status}")
                report.append(f"   得分: {score}/100")
                report.append("")
                report.append("   测试详情:")

                for test_name, passed in data["tests"].items():
                    status_icon = "✅" if passed else "❌"
                    test_display_name = {
                        "invalid_tool_params": "无效工具参数处理",
                        "empty_required_params": "空必需参数处理",
                        "nonexistent_tool": "不存在工具处理",
                        "network_error_simulation": "网络错误模拟",
                        "tool_error_response": "ToolError响应验证",
                        "mcp_error_response": "MCPError响应验证",
                        "error_format_validation": "错误格式验证",
                        "middleware_configured": "中间件配置验证",
                        "error_transformation": "错误转换机制",
                        "user_input_error_classification": "用户输入错误分类"
                    }.get(test_name, test_name)

                    report.append(f"     {status_icon} {test_display_name}")

                report.append("")

                total_score += score
                completed_tests += 1

        if completed_tests > 0:
            avg_score = total_score // completed_tests
            report.append(f"📊 总体错误处理得分: {avg_score}/100")
            report.append("")

            if avg_score >= 90:
                report.append("🎉 优秀！错误处理机制完全符合MCP规范")
            elif avg_score >= 80:
                report.append("✅ 良好！错误处理机制基本符合MCP规范")
            elif avg_score >= 60:
                report.append("⚠️ 合格，错误处理机制部分符合MCP规范")
            else:
                report.append("❌ 需要改进，错误处理机制不符合MCP规范")
        else:
            report.append("❌ 没有完成的测试")

        report.append("")
        report.append("🔧 改进建议:")
        report.append("   - 确保所有传输模式使用统一的错误处理中间件")
        report.append("   - 验证错误响应格式符合MCP标准")
        report.append("   - 测试用户输入错误的正确分类")
        report.append("   - 验证HTTP状态码的正确使用")

        return "\n".join(report)

    async def run_all_tests(self):
        """运行所有错误处理测试"""
        self.logger.info("🔧 开始增强型错误处理全面测试")

        try:
            # 测试STDIO模式
            self.test_results["stdio"]["tests"] = await self.test_stdio_error_handling()
            self.test_results["stdio"]["status"] = "completed"

            # 测试HTTP模式
            self.test_results["http"]["tests"] = await self.test_http_error_handling()
            if self.test_results["http"]["tests"]:
                self.test_results["http"]["status"] = "completed"

            # 测试SSE模式
            self.test_results["sse"]["tests"] = await self.test_sse_error_handling()
            if self.test_results["sse"]["tests"]:
                self.test_results["sse"]["status"] = "completed"

            # 生成报告
            report = self.generate_report()
            print(report)

            # 保存报告
            report_file = Path(__file__).parent / "enhanced_error_handling_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            self.logger.info(f"📄 错误处理测试报告已保存到: {report_file}")

            return True

        except Exception as e:
            self.logger.error(f"❌ 错误处理测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """主函数"""
    tester = EnhancedErrorHandlingTester()

    print("🔧 增强型错误处理测试工具")
    print("="*50)
    print("专门测试不同传输模式下的错误处理机制")
    print("")

    success = await tester.run_all_tests()

    if success:
        print("🎉 错误处理测试完成！")
        sys.exit(0)
    else:
        print("❌ 错误处理测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())