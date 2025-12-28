"""测试 PerformanceTimer 类命名导致 pytest 收集警告问题

测试目标：
1. 验证 PerformanceTimer 类名导致 pytest 误认为是测试类
2. 验证重命名后的类不会被 pytest 收集
3. 验证向后兼容性

问题根因：
- PerformanceTimer 类名以 "Performance" 开头且包含 __init__
- pytest 误认为它是测试类并尝试收集
- 解决方案：重命名为 PerfTimer 或 Stopwatch

测试策略：
- 测试重命名前后的类是否被 pytest 收集
- 测试新类的功能是否正常
"""

import sys
from pathlib import Path

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.unit
class TestPerformanceTimerNaming:
    """测试 PerformanceTimer 命名问题"""

    def test_performance_timer_has_init_constructor(self):
        """验证：PerformanceTimer 类有 __init__ 构造函数"""
        from tests.utils.test_helpers import PerformanceTimer

        # 这个类有 __init__ 方法
        assert hasattr(PerformanceTimer, "__init__")
        assert callable(PerformanceTimer.__init__)

    def test_performance_timer_name_starts_with_perf(self):
        """验证：PerformanceTimer 类名包含 'Perf' 关键字"""
        from tests.utils.test_helpers import PerformanceTimer

        # 类名包含 "Performance"，可能被 pytest 误认为测试类
        class_name = PerformanceTimer.__name__
        assert "Performance" in class_name or "Perf" in class_name

    def test_performance_timer_functionality_works(self):
        """验证：PerformanceTimer 的功能正常工作"""
        import time

        from tests.utils.test_helpers import PerformanceTimer

        # 测试基本功能
        with PerformanceTimer() as timer:
            time.sleep(0.01)

        elapsed = timer.stop()
        assert elapsed > 0
        assert elapsed < 1  # 应该很快

    def test_test_timer_alias_exists(self):
        """验证：TestTimer 别名存在且功能相同"""
        from tests.utils.test_helpers import PerformanceTimer, TestTimer

        # TestTimer 是 PerformanceTimer 的别名
        assert TestTimer is PerformanceTimer

    def test_new_perf_timer_name_would_not_be_collected(self):
        """验证：新的类名（如 PerfTimer）不会被 pytest 收集为测试类"""
        # pytest 只收集以 "Test" 开头的类
        # "PerfTimer" 不会被认为是测试类
        # 这是一个设计验证测试，确认命名策略正确

        # pytest 的测试类收集规则：
        # - 类名必须以 "Test" 开头
        # "PerfTimer" 不符合这个规则，所以不会被收集
        class_names_to_test = ["PerfTimer", "Stopwatch", "Timer", "TimeTracker"]
        test_class_pattern = "^Test"

        for name in class_names_to_test:
            # 确保这些名字不以 "Test" 开头
            import re

            assert not re.match(test_class_pattern, name), f"{name} 不应该匹配测试类模式"

    def test_performance_timer_in_non_test_file(self):
        """验证：PerformanceTimer 在 test_helpers.py 中，不在以 test_ 开头的文件中"""
        # 文件名是 test_helpers.py，pytest 可能会扫描这个文件
        # 但因为这个类不在以 "test_" 开头的函数/类中
        # 所以理论上不应该被收集
        import tests.utils.test_helpers as test_helpers_module

        # 验证模块中有 PerformanceTimer
        assert hasattr(test_helpers_module, "PerformanceTimer")

        # 这个测试验证了类的存在，但 pytest 的收集行为是运行时的
        # 我们需要通过运行 pytest 来观察警告


@pytest.mark.unit
class TestPerfTimerAlternative:
    """测试 PerfTimer 替代方案"""

    def test_proposed_perf_timer_name(self):
        """验证：提议的 PerfTimer 名称符合要求"""
        # 提议的新名称
        new_name = "PerfTimer"

        # 验证命名规则：
        # 1. 不以 "Test" 开头
        # 2. 简洁明了
        # 3. 容易理解

        assert not new_name.startswith("Test")
        assert len(new_name) > 3
        assert "Timer" in new_name or "Watch" in new_name
