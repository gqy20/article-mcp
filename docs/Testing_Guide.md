# Article MCP 测试指南

## 概述

本文档介绍Article MCP项目的完整测试架构，包括测试基础设施、pytest测试套件和最佳实践。

## 🏗️ 测试架构

### 测试层次结构

```
tests/
├── conftest.py                 # 全局测试配置和fixtures
├── __init__.py
├── unit/                       # 单元测试
│   ├── test_search_tools.py     # 搜索工具单元测试
│   ├── test_article_detail_tools.py  # 文章详情工具测试
│   ├── test_reference_tools.py  # 参考文献工具测试
│   ├── test_relation_tools.py   # 文献关系工具测试
│   ├── test_quality_tools.py    # 质量评估工具测试
│   ├── test_tool_core.py       # 工具核心逻辑测试
│   ├── test_cli.py             # CLI功能测试
│   └── test_services.py        # 服务层测试
├── integration/               # 集成测试
│   └── test_six_tools_integration.py  # 6工具集成测试
│   └── test_mcp_integration.py     # MCP集成测试
├── utils/                     # 测试工具
│   └── test_helpers.py         # 测试辅助函数
└── performance/               # 性能测试
    └── test_performance.py     # 性能基准测试
```

### 6工具架构测试覆盖

Article MCP采用6工具统一架构，测试套件专门针对此设计：

#### 核心工具 (6个)
1. **search_literature** - 统一多源文献搜索
2. **get_article_details** - 统一文献详情获取
3. **get_references** - 参考文献获取
4. **get_literature_relations** - 文献关系分析
5. **get_journal_quality** - 期刊质量评估
6. **batch_search_literature** - 批量处理工具

## 🧪 测试类型

### 1. 单元测试
**位置**: `tests/unit/`

**覆盖内容**:
- 各个工具的核心功能测试
- 服务层的独立功能测试
- CLI命令处理测试
- 错误处理和边界条件测试

**示例测试**:
```python
def test_search_literature():
    """测试文献搜索工具"""
    # 测试基本搜索功能
    result = search_literature(keyword="machine learning")
    assert result["success"]
    assert len(result["articles"]) > 0
```

### 2. 集成测试
**位置**: `tests/integration/`

**覆盖内容**:
- 多个工具的协作测试
- MCP协议集成测试
- 端到端功能验证
- 真实API调用测试

### 3. 性能测试
**位置**: `tests/performance/`

**覆盖内容**:
- 响应时间基准测试
- 并发处理能力测试
- 内存使用监控
- API调用效率测试

## 🔧 测试配置

### pytest配置

主要配置文件：

#### `conftest.py` - 全局配置
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    return Mock()

@pytest.fixture
def sample_article_data():
    """示例文章数据"""
    return {
        "pmid": "12345678",
        "title": "Test Article",
        "authors": ["Test Author"],
        "abstract": "Test abstract"
    }
```

#### `pytest.ini` - pytest配置
```ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --strict-config --color=yes --durations=10
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试（超过5秒）
    network: 需要网络连接的测试
```

## 🚀 运行测试

### 基本测试命令

```bash
# 运行所有测试
pytest

# 运行特定类型的测试
pytest -m unit              # 只运行单元测试
pytest -m integration       # 只运行集成测试
pytest -m "not slow"         # 排除慢速测试

# 运行特定测试文件
pytest tests/unit/test_search_tools.py
pytest tests/integration/

# 详细输出
pytest -v

# 显示测试覆盖率
pytest --cov=src/article_mcp
```

### 调试和开发测试

```bash
# 运行特定测试并显示输出
pytest tests/unit/test_search_tools.py::test_search_literature -s

# 在第一个失败时停止
pytest -x

# 只运行上次失败的测试
pytest --lf

# 并行运行测试（需要安装pytest-xdist）
pytest -n auto
```

## 📊 测试最佳实践

### 1. 测试命名规范

```python
# 测试类
class TestSearchTools:
    pass

# 测试方法
def test_search_literature_success():
    """测试成功的文献搜索"""
    pass

def test_search_literature_empty_keyword():
    """测试空关键词处理"""
    pass
```

### 2. 测试数据管理

```python
# 使用fixtures提供测试数据
@pytest.fixture
def mock_search_response():
    return {
        "success": True,
        "articles": [...]
    }

# 使用参数化测试
@pytest.mark.parametrize("keyword,expected_count", [
    ("machine learning", 10),
    ("cancer", 15),
    ("", 0)
])
def test_search_with_different_keywords(keyword, expected_count):
    result = search_literature(keyword=keyword)
    assert len(result["articles"]) >= expected_count
```

### 3. Mock和外部依赖

```python
# Mock外部API调用
@patch('src.article_mcp.services.europe_pmc.EuropePMCService.search')
def test_search_with_mocked_api(mock_search):
    mock_search.return_value = {"success": True, "articles": []}

    result = search_literature("test keyword")
    assert result["success"]
    mock_search.assert_called_once()
```

## 🔍 测试数据源

### 模拟数据
- 使用固定的测试PMID、DOI、PMCID
- 提供标准的测试响应格式
- 维护测试数据的一致性

### 真实API测试
- 使用专门的测试环境配置
- 限制API调用频率，避免触发限制
- 使用缓存机制减少重复调用

## 📈 持续集成

### GitHub Actions配置示例

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest --cov=src/article_mcp
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## 📋 测试清单

### 新功能测试清单
- [ ] 单元测试覆盖核心逻辑
- [ ] 集成测试验证协作流程
- [ ] 错误处理测试覆盖异常情况
- [ ] 性能测试确保响应时间
- [ ] 文档测试确保示例正确

### 发布前测试清单
- [ ] 所有单元测试通过
- [ ] 集成测试验证端到端功能
- [ ] 性能测试满足基准要求
- [ ] 测试覆盖率达到80%以上
- [ ] 文档中的示例经过验证

## 🛠️ 测试工具

### 推荐的pytest插件

```bash
pip install pytest-cov          # 测试覆盖率
pip install pytest-mock         # Mock支持
pip install pytest-xdist        # 并行测试
pip install pytest-benchmark    # 性能基准测试
pip install pytest-html         # HTML报告
```

### 有用的测试命令

```bash
# 生成HTML测试报告
pytest --html=reports/test_report.html

# 性能基准测试
pytest --benchmark-only

# 生成覆盖率报告
pytest --cov=src/article_mcp --cov-report=html
```

## 📚 相关资源

- [pytest官方文档](https://docs.pytest.org/)
- [Mock使用指南](https://docs.python.org/3/library/unittest.mock.html)
- [测试覆盖率工具](https://pytest-cov.readthedocs.io/)

---

**最后更新**: 2025-10-27
**维护者**: Claude Code
**测试架构**: 6工具统一架构