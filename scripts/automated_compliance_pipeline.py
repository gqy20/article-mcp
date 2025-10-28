#!/usr/bin/env python3
"""
自动化合规性测试流水线

整合所有合规性测试，提供完整的自动化测试流程。
适用于CI/CD环境和本地开发验证。
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestResult(Enum):
    """测试结果枚举"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestSuite:
    """测试套件数据类"""
    name: str
    description: str
    script_path: str
    timeout: int = 300
    required: bool = True
    dependencies: List[str] = None


class AutomatedCompliancePipeline:
    """自动化合规性测试流水线"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.results = {}
        self.start_time = time.time()

        # 定义测试套件
        self.test_suites = [
            TestSuite(
                name="FastMCP基础合规性",
                description="验证基础FastMCP规范符合性",
                script_path="scripts/test_fastmcp_compliance.py",
                timeout=300,
                required=True
            ),
            TestSuite(
                name="增强型错误处理",
                description="深度测试错误处理机制",
                script_path="scripts/enhanced_error_handling_test.py",
                timeout=300,
                required=True
            ),
            TestSuite(
                name="基础功能测试",
                description="验证核心功能正确性",
                script_path="scripts/test_basic_functionality.py",
                timeout=300,
                required=True
            ),
            TestSuite(
                name="性能基准测试",
                description="验证性能指标",
                script_path="scripts/test_performance.py",
                timeout=600,
                required=False
            ),
            TestSuite(
                name="CLI功能测试",
                description="验证命令行接口",
                script_path="scripts/test_cli_functions.py",
                timeout=300,
                required=True
            ),
            TestSuite(
                name="服务模块测试",
                description="验证服务层功能",
                script_path="scripts/test_service_modules.py",
                timeout=300,
                required=True
            )
        ]

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("AutomatedCompliancePipeline")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def run_test_suite(self, test_suite: TestSuite) -> Dict[str, Any]:
        """运行单个测试套件"""
        self.logger.info(f"🧪 开始执行测试套件: {test_suite.name}")
        self.logger.info(f"📝 描述: {test_suite.description}")

        start_time = time.time()
        result = {
            "name": test_suite.name,
            "description": test_suite.description,
            "status": TestResult.RUNNING.value if hasattr(TestResult, 'RUNNING') else "RUNNING",
            "start_time": start_time,
            "end_time": None,
            "duration": None,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error": None
        }

        try:
            # 运行测试脚本
            process = await asyncio.create_subprocess_exec(
                "uv", "run", "python", test_suite.script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=test_suite.timeout
                )

                result["stdout"] = stdout.decode('utf-8', errors='ignore')
                result["stderr"] = stderr.decode('utf-8', errors='ignore')
                result["exit_code"] = process.returncode

                if process.returncode == 0:
                    result["status"] = TestResult.PASSED.value
                    self.logger.info(f"✅ 测试套件 '{test_suite.name}' 通过")
                else:
                    result["status"] = TestResult.FAILED.value
                    self.logger.error(f"❌ 测试套件 '{test_suite.name}' 失败，退出码: {process.returncode}")

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                result["status"] = TestResult.FAILED.value
                result["error"] = f"测试超时 ({test_suite.timeout}秒)"
                self.logger.error(f"⏰ 测试套件 '{test_suite.name}' 超时")

        except Exception as e:
            result["status"] = TestResult.ERROR.value
            result["error"] = str(e)
            self.logger.error(f"💥 测试套件 '{test_suite.name}' 执行异常: {e}")

        finally:
            result["end_time"] = time.time()
            result["duration"] = round(result["end_time"] - start_time, 2)

        return result

    def extract_score_from_report(self, test_name: str, output: str) -> Optional[int]:
        """从测试输出中提取合规性得分"""
        if "FastMCP规范合规性测试报告" in output:
            lines = output.split('\n')
            for line in lines:
                if "总体合规性得分" in line:
                    import re
                    match = re.search(r'(\d+)/100', line)
                    if match:
                        return int(match.group(1))
        elif "错误处理测试报告" in output:
            lines = output.split('\n')
            for line in lines:
                if "总体错误处理得分" in line:
                    import re
                    match = re.search(r'(\d+)/100', line)
                    if match:
                        return int(match.group(1))
        return None

    def generate_summary_report(self) -> Dict[str, Any]:
        """生成汇总报告"""
        total_duration = time.time() - self.start_time

        passed_suites = sum(1 for r in self.results.values() if r["status"] == TestResult.PASSED.value)
        failed_suites = sum(1 for r in self.results.values() if r["status"] == TestResult.FAILED.value)
        error_suites = sum(1 for r in self.results.values() if r["status"] == TestResult.ERROR.value)
        total_suites = len(self.results)

        # 计算合规性得分
        compliance_scores = []
        for name, result in self.results.items():
            stdout = result.get("stdout", "")
            if stdout:
                score = self.extract_score_from_report(name, stdout)
                if score is not None:
                    compliance_scores.append(score)

        avg_compliance_score = sum(compliance_scores) // len(compliance_scores) if compliance_scores else 0

        summary = {
            "pipeline_name": "FastMCP自动化合规性测试流水线",
            "execution_time": {
                "start_time": self.start_time,
                "end_time": time.time(),
                "total_duration": round(total_duration, 2)
            },
            "test_suites": {
                "total": total_suites,
                "passed": passed_suites,
                "failed": failed_suites,
                "errors": error_suites,
                "success_rate": round((passed_suites / total_suites) * 100, 2) if total_suites > 0 else 0
            },
            "compliance_scores": {
                "individual_scores": compliance_scores,
                "average_score": avg_compliance_score,
                "grade": self._get_grade(avg_compliance_score)
            },
            "overall_status": "PASSED" if failed_suites == 0 and error_suites == 0 else "FAILED",
            "detailed_results": self.results
        }

        return summary

    def _get_grade(self, score: int) -> str:
        """根据得分获取等级"""
        if score >= 95:
            return "A+ (优秀)"
        elif score >= 90:
            return "A (优秀)"
        elif score >= 85:
            return "B+ (良好)"
        elif score >= 80:
            return "B (良好)"
        elif score >= 75:
            return "C+ (合格)"
        elif score >= 70:
            return "C (合格)"
        elif score >= 60:
            return "D (需要改进)"
        else:
            return "F (不合格)"

    def generate_report(self, summary: Dict[str, Any]) -> str:
        """生成格式化的报告"""
        report = []
        report.append("=" * 80)
        report.append("🚀 FastMCP自动化合规性测试流水线报告")
        report.append("=" * 80)
        report.append("")

        # 执行时间
        exec_time = summary["execution_time"]
        report.append(f"⏱️  执行时间: {round(exec_time['total_duration'], 2)}秒")
        report.append(f"📅 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exec_time['start_time']))}")
        report.append(f"🏁 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exec_time['end_time']))}")
        report.append("")

        # 测试套件结果
        test_stats = summary["test_suites"]
        report.append(f"📊 测试套件统计:")
        report.append(f"   总计: {test_stats['total']}")
        report.append(f"   通过: {test_stats['passed']} ✅")
        report.append(f"   失败: {test_stats['failed']} ❌")
        report.append(f"   错误: {test_stats['errors']} 💥")
        report.append(f"   成功率: {test_stats['success_rate']}%")
        report.append("")

        # 合规性得分
        compliance = summary["compliance_scores"]
        report.append(f"🎯 合规性评估:")
        report.append(f"   平均得分: {compliance['average_score']}/100")
        report.append(f"   评级: {compliance['grade']}")

        if compliance['individual_scores']:
            report.append(f"   各项得分: {', '.join(map(str, compliance['individual_scores']))}")
        report.append("")

        # 总体状态
        overall_status = summary["overall_status"]
        status_icon = "✅" if overall_status == "PASSED" else "❌"
        report.append(f"{status_icon} 总体状态: {overall_status}")
        report.append("")

        # 详细结果
        report.append("📋 详细测试结果:")
        report.append("-" * 80)

        for test_name, result in summary["detailed_results"].items():
            status_icon = {
                "PASSED": "✅",
                "FAILED": "❌",
                "ERROR": "💥",
                "SKIPPED": "⏭️"
            }.get(result["status"], "❓")

            report.append(f"{status_icon} {test_name}")
            report.append(f"   状态: {result['status']}")
            report.append(f"   耗时: {result['duration']}秒")

            if result.get("error"):
                report.append(f"   错误: {result['error']}")

            # 提取得分
            score = self.extract_score_from_report(test_name, result["stdout"])
            if score:
                report.append(f"   得分: {score}/100")

            report.append("")

        # 改进建议
        if overall_status == "FAILED":
            report.append("🔧 改进建议:")
            failed_tests = [name for name, result in summary["detailed_results"].items()
                          if result["status"] in ["FAILED", "ERROR"]]

            for test_name in failed_tests:
                result = summary["detailed_results"][test_name]
                if result.get("stderr"):
                    report.append(f"   - {test_name}: 检查错误日志")
                else:
                    report.append(f"   - {test_name}: 重新运行测试")

            report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    async def run_pipeline(self) -> Dict[str, Any]:
        """运行完整的测试流水线"""
        self.logger.info("🚀 启动FastMCP自动化合规性测试流水线")
        self.logger.info(f"📋 计划执行 {len(self.test_suites)} 个测试套件")

        for test_suite in self.test_suites:
            self.logger.info("-" * 60)

            # 检查脚本是否存在
            script_path = Path(test_suite.script_path)
            if not script_path.exists():
                self.logger.warning(f"⚠️ 测试脚本不存在: {test_suite.script_path}")
                if test_suite.required:
                    self.results[test_suite.name] = {
                        "name": test_suite.name,
                        "status": TestResult.ERROR.value,
                        "error": f"测试脚本不存在: {test_suite.script_path}",
                        "duration": 0
                    }
                else:
                    self.results[test_suite.name] = {
                        "name": test_suite.name,
                        "status": TestResult.SKIPPED.value,
                        "error": f"测试脚本不存在: {test_suite.script_path}",
                        "duration": 0
                    }
                continue

            # 运行测试套件
            result = await self.run_test_suite(test_suite)
            self.results[test_suite.name] = result

            # 如果是必需的测试且失败了，决定是否继续
            if test_suite.required and result["status"] in [TestResult.FAILED.value, TestResult.ERROR.value]:
                self.logger.warning(f"⚠️ 必需测试失败: {test_suite.name}")
                # 继续执行其他测试以获得完整报告

        self.logger.info("-" * 60)
        self.logger.info("🏁 所有测试套件执行完成")

        # 生成汇总报告
        summary = self.generate_summary_report()

        # 输出报告
        report_text = self.generate_report(summary)
        print(report_text)

        # 保存报告
        self.save_reports(summary, report_text)

        return summary

    def save_reports(self, summary: Dict[str, Any], report_text: str):
        """保存报告文件"""
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        # 保存JSON格式的详细报告
        json_report_path = reports_dir / f"compliance_pipeline_report_{int(time.time())}.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # 保存文本格式的报告
        text_report_path = reports_dir / f"compliance_pipeline_report_{int(time.time())}.txt"
        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        # 保存最新报告（固定文件名）
        latest_json_path = reports_dir / "latest_compliance_report.json"
        latest_text_path = reports_dir / "latest_compliance_report.txt"

        with open(latest_json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        with open(latest_text_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        self.logger.info(f"📄 报告已保存:")
        self.logger.info(f"   JSON: {json_report_path}")
        self.logger.info(f"   文本: {text_report_path}")
        self.logger.info(f"   最新JSON: {latest_json_path}")
        self.logger.info(f"   最新文本: {latest_text_path}")


async def main():
    """主函数"""
    pipeline = AutomatedCompliancePipeline()

    try:
        summary = await pipeline.run_pipeline()

        # 根据测试结果设置退出码
        if summary["overall_status"] == "PASSED":
            print("🎉 自动化合规性测试流水线执行成功！")
            sys.exit(0)
        else:
            print("❌ 自动化合规性测试流水线执行失败！")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  测试流水线被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"💥 测试流水线执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())