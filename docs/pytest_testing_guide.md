# 6工具架构pytest测试套件指南

## 概述

本文档介绍为Article MCP项目6工具架构设计的完整pytest测试套件。测试套件涵盖单元测试、集成测试、性能测试和真实场景测试。

## 测试架构

### 测试层次结构

```
tests/
├── conftest.py                 # 全局测试配置和fixtures
├── unit/                       # 单元测试
│   ├── test_six_tools.py       # 6工具核心功能测试
│   ├── test_tool_core.py       # 工具核心逻辑测试
│   ├── test_cli.py             # CLI功能测试
│   └── test_services.py        # 服务层测试
├── integration/               # 集成测试
│   └── test_six_tools_integration.py  # 6工具集成测试
└── utils/                     # 测试工具和辅助函数
    └── test_helpers.py         # 测试辅助工具
```

### 6工具架构测试覆盖

1. **search_literature** - 统一多源文献搜索工具
2. **get_article_details** - 统一文献详情获取工具
3. **get_references** - 参考文献获取工具
4. **get_literature_relations** - 文献关系分析工具
5. **get_journal_quality** - 期刊质量评估工具
6. **export_batch_results** - 通用结果导出工具

## 运行测试

### 基本测试命令

```bash
# 运行所有测试
python -m pytest

# 运行特定类型的测试
python -m pytest -m unit        # 单元测试
python -m pytest -m integration # 集成测试
python -m pytest -m performance # 性能测试

# 运行特定工具的测试
python -m pytest -m search_tools
python -m pytest -m article_tools
python -m pytest -m reference_tools
python -m pytest -m relation_tools
python -m pytest -m quality_tools
python -m pytest -m batch_tools

# 运行6工具架构专用测试
python -m pytest -m six_tools
python -m pytest -m workflow
```

### 工作流程场景测试

```bash
# 研究者文献综述场景
python -m pytest -m researcher_scenario

# 学生作业场景
python -m pytest -m student_scenario

# 临床证据搜索场景
python -m pytest -m clinical_scenario
```

### 覆盖率测试

```bash
# 生成覆盖率报告
python -m pytest --cov=src/article_mcp --cov-report=html

# 生成覆盖率报告并设置阈值
python -m pytest --cov=src/article_mcp --cov-fail-under=80
```

### 并行测试

```bash
# 并行执行测试（需要安装pytest-xdist）
python -m pytest -n auto
```

## 测试配置

### pytest.ini配置

```ini
[tool:pytest]
# 测试发现
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# 输出配置
addopts = -v --tb=short --strict-markers --cov=src/article_mcp --cov-fail-under=80

# 标记定义
markers =
    unit: 单元测试
    integration: 集成测试
    performance: 性能测试
    six_tools: 6工具架构测试
    workflow: 工作流程测试
    search_tools: 搜索工具测试
    article_tools: 文章工具测试
    # ... 更多标记
```

### 环境变量

```bash
# 测试环境变量
export PYTHONPATH=src
export TESTING=1
export CACHE_TEST_MODE=1
export DISABLE_NETWORK_CALLS=1
export PYTHONUNBUFFERED=1
```

## 测试标记系统

### 测试类型标记

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.system` - 系统测试
- `@pytest.mark.performance` - 性能测试
- `@pytest.mark.stress` - 压力测试

### 工具特定标记

- `@pytest.mark.search_tools` - 搜索工具测试
- `@pytest.mark.article_tools` - 文章工具测试
- `@pytest.mark.reference_tools` - 参考文献工具测试
- `@pytest.mark.relation_tools` - 关系分析工具测试
- `@pytest.mark.quality_tools` - 质量评估工具测试
- `@pytest.mark.batch_tools` - 批量工具测试

### 6工具架构标记

- `@pytest.mark.six_tools` - 6工具架构测试
- `@pytest.mark.workflow` - 工作流程测试
- `@pytest.mark.regression` - 回归测试

### 场景标记

- `@pytest.mark.researcher_scenario` - 研究者文献综述场景
- `@pytest.mark.student_scenario` - 学生作业场景
- `@pytest.mark.clinical_scenario` - 临床证据搜索场景

## Fixtures

### 全局Fixtures

- `logger` - 测试用日志记录器
- `mock_crossref_service` - 模拟CrossRef服务
- `mock_openalex_service` - 模拟OpenAlex服务
- `mock_europe_pmc_service` - 模拟Europe PMC服务
- `mock_pubmed_service` - 模拟PubMed服务

### 6工具专用Fixtures

- `six_tool_services` - 6工具完整服务集合
- `mock_mcp_tools` - 模拟6个MCP工具
- `workflow_test_data` - 完整工作流程测试数据
- `performance_test_data` - 性能测试数据
- `error_scenarios` - 错误场景数据

### 测试辅助Fixtures

- `six_tool_helper` - 6工具测试辅助工具
- `workflow_tester` - 工作流程测试器
- `performance_monitor` - 性能监控器

## 测试用例示例

### 单元测试示例

```python
import pytest
from tests.utils.test_helpers import SixToolTestHelper

class TestSearchLiteratureTool:
    @pytest.mark.unit
    @pytest.mark.search_tools
    def test_search_literature_basic(self, mock_search_services):
        """测试基本文献搜索功能"""
        # 测试实现
        pass

    @pytest.mark.unit
    def test_search_results_merging(self):
        """测试搜索结果合并逻辑"""
        # 测试数据合并和去重
        pass
```

### 集成测试示例

```python
import pytest
from tests.utils.test_helpers import WorkflowTester

class TestEndToEndWorkflow:
    @pytest.mark.integration
    @pytest.mark.workflow
    def test_researcher_workflow(self, mock_mcp_tools):
        """测试研究者文献综述工作流程"""
        tester = WorkflowTester()
        result = tester.test_workflow("researcher_review", mock_mcp_tools)
        assert result["workflow_success"]
```

### 性能测试示例

```python
import pytest
from tests.utils.test_helpers import PerformanceMonitor, TestTimer

class TestPerformance:
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_batch_processing(self):
        """测试大批量处理性能"""
        with PerformanceMonitor() as monitor:
            monitor.start_measurement("batch_processing")
            # 执行大批量操作
            monitor.end_measurement("batch_processing")
            monitor.assert_performance_within_limits("batch_processing", 5.0)
```

## 测试数据和模拟

### 模拟数据生成

```python
from tests.utils.test_helpers import MockDataGenerator

# 生成模拟文章数据
article = MockDataGenerator.create_article(
    title="Test Article",
    authors=["Author One", "Author Two"],
    doi="10.1234/test.2023"
)

# 生成模拟搜索结果
search_results = MockDataGenerator.create_search_results(count=10)
```

### 错误场景模拟

```python
from tests.utils.test_helpers import SixToolTestHelper

# 创建错误响应
error_response = SixToolTestHelper.create_error_response(
    tool_name="search_literature",
    error_type="NetworkError",
    message="API request failed"
)
```

## 持续集成

### GitHub Actions配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e .[dev]

    - name: Run tests
      run: |
        python -m pytest --cov=src/article_mcp --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 最佳实践

### 1. 测试命名规范

- 测试类：`TestClassName`
- 测试方法：`test_method_name_descriptive`
- 文件命名：`test_feature_name.py`

### 2. 测试组织

- 每个测试一个断言
- 使用描述性的测试名称
- 按功能模块组织测试

### 3. 模拟策略

- 优先使用Mock而不是真实API调用
- 使用fixtures提供可重用的测试数据
- 设置测试环境变量避免副作用

### 4. 性能考虑

- 使用`@pytest.mark.slow`标记耗时测试
- 设置合理的超时时间
- 并行执行独立测试

### 5. 错误处理

- 测试正常路径和错误路径
- 验证错误消息的准确性
- 测试恢复机制

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   export PYTHONPATH=src
   python -m pytest
   ```

2. **测试标记未定义**
   ```bash
   python -m pytest --markers
   ```

3. **覆盖率过低**
   ```bash
   python -m pytest --cov=src/article_mcp --cov-report=term-missing
   ```

4. **测试超时**
   ```bash
   python -m pytest --timeout=300
   ```

### 调试技巧

```bash
# 运行特定测试并显示输出
python -m pytest -s -v tests/unit/test_six_tools.py::TestSearchLiteratureTool::test_basic

# 停在第一个失败的测试
python -m pytest -x

# 只运行上次失败的测试
python -m pytest --lf

# 显示本地变量
python -m pytest --tb=long
```

## 扩展测试套件

### 添加新测试

1. 在相应的测试文件中添加测试类
2. 使用适当的标记装饰测试
3. 添加必要的fixtures
4. 更新文档

### 添加新工具测试

1. 创建`test_new_tool.py`
2. 实现基础功能测试
3. 添加集成测试
4. 更新工作流程场景

### 性能基准测试

1. 使用`@pytest.mark.performance`
2. 实现性能监控
3. 设置性能基准
4. 定期运行性能测试

## 总结

这个pytest测试套件为6工具架构提供了全面的测试覆盖，包括：

- ✅ 完整的单元测试覆盖
- ✅ 端到端集成测试
- ✅ 性能和压力测试
- ✅ 真实场景测试
- ✅ 错误处理和边界测试
- ✅ 配置和基础设施测试

通过遵循本指南，开发者可以有效地编写、运行和维护测试，确保6工具架构的稳定性和可靠性。