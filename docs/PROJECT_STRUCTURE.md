# 📁 项目结构说明

## 🗂️ 目录结构

```
article-mcp/
├── src/article_mcp/          # 核心源代码
│   ├── __init__.py          # 包初始化
│   ├── cli.py               # CLI入口点和MCP服务器创建
│   ├── __main__.py          # Python模块执行支持
│   ├── services/            # 服务层
│   │   ├── europe_pmc.py    # Europe PMC API集成
│   │   ├── pubmed_search.py # PubMed搜索服务
│   │   ├── crossref_service.py # CrossRef API服务
│   │   ├── openalex_service.py # OpenAlex API服务
│   │   ├── reference_service.py # 参考文献服务
│   │   ├── literature_relation_service.py # 文献关系服务
│   │   ├── merged_results.py # 结果合并和去重
│   │   └── [其他服务模块...]
│   └── tools/               # MCP工具实现
│       ├── core/            # 核心工具注册
│       │   ├── search_tools.py # 文献搜索工具
│       │   ├── article_tools.py # 文章详情工具
│       │   ├── reference_tools.py # 参考文献工具
│       │   ├── relation_tools.py # 文献关系分析工具
│       │   ├── quality_tools.py # 期刊质量工具
│       │   └── batch_tools.py # 批量处理工具
│       └── [其他工具模块...]
├── scripts/                 # 测试和实用脚本
│   ├── quick_test.py        # 快速功能测试
│   ├── test_working_functions.py # 核心功能测试
│   ├── run_all_tests.py     # 完整测试套件
│   ├── test_performance.py  # 性能测试
│   ├── test_pytest_suite.py # pytest测试套件
│   ├── test_complete_literature_analysis.py # 完整文献分析测试
│   └── test_fixed_api_integration.py # API集成修复测试
├── tests/                   # 正式测试套件
│   ├── unit/                # 单元测试
│   │   ├── test_services.py # 服务单元测试
│   │   ├── test_openalex_service.py # OpenAlex服务测试
│   │   ├── test_crossref_service.py # CrossRef服务测试
│   │   ├── test_cli.py      # CLI测试
│   │   ├── test_merged_results.py # 结果合并测试
│   │   ├── test_tool_core.py # 工具核心测试
│   │   └── test_six_tools.py # 六个工具测试
│   ├── integration/         # 集成测试
│   │   ├── test_real_api.py # 真实API测试
│   │   ├── test_mcp_integration.py # MCP集成测试
│   │   └── test_six_tools_integration.py # 工具集成测试
│   ├── utils/               # 测试工具
│   │   └── test_helpers.py  # 测试辅助函数
│   ├── test_cherry_studio_simulation.py # Cherry Studio兼容性测试
│   ├── test_complete_http_client.py # HTTP客户端测试
│   └── test_relation_tools.py # 关系工具测试
├── src/resource/            # 资源文件
│   └── journal_info.json    # 期刊信息数据
├── docs/                    # 文档目录
│   └── [文档文件...]
└── [项目配置文件...]
```

## 📋 核心文件说明

### 🚀 核心代码文件
- **`src/article_mcp/cli.py`**: 主要的MCP服务器创建和配置
- **`src/article_mcp/__main__.py`**: 支持Python模块执行
- **`src/article_mcp/services/`**: 所有API服务实现
- **`src/article_mcp/tools/core/`**: MCP工具注册和实现

### 🧪 测试文件分类

#### Scripts目录（开发和调试测试）
- **快速测试**: `quick_test.py`
- **功能测试**: `test_working_functions.py`
- **完整测试**: `run_all_tests.py`
- **专项测试**:
  - `test_complete_literature_analysis.py` - 文献分析完整测试
  - `test_fixed_api_integration.py` - API集成修复验证

#### Tests目录（正式测试套件）
- **单元测试**: `tests/unit/` - 各个组件的独立测试
- **集成测试**: `tests/integration/` - 端到端功能测试
- **兼容性测试**:
  - `test_cherry_studio_simulation.py` - Cherry Studio兼容性
  - `test_complete_http_client.py` - HTTP协议测试
  - `test_relation_tools.py` - 关系分析功能测试

### 📖 文档文件
- **`README.md`**: 项目主要说明文档
- **`CLAUDE.md`**: Claude Code开发指导
- **`CHANGELOG.md`**: 版本变更记录
- **`API_Integration_Fix_Report.md`**: API修复技术报告
- **`PROJECT_STRUCTURE.md`**: 本文档，项目结构说明

### ⚙️ 配置文件
- **`pyproject.toml`**: 项目配置和依赖管理
- **`setup.py`**: 包安装配置
- **`uv.lock`**: 依赖锁定文件（如使用uv）

## 🎯 文件组织原则

### 📂 位置选择标准

**根目录文件**:
- 只保留核心配置和重要文档
- 避免在根目录放置测试或示例文件

**Scripts目录**:
- 开发和调试用的测试脚本
- 完整的功能验证测试
- API集成测试

**Tests目录**:
- 正式的单元测试和集成测试
- 特定客户端兼容性测试
- 性能和协议测试

### 🔄 文件命名规范

**测试文件**:
- 开发测试: `test_功能描述.py`
- 单元测试: `test_模块名.py`
- 集成测试: `test_功能名_integration.py`
- 兼容性测试: `test_客户端名_simulation.py`

**服务文件**:
- API服务: `服务名_service.py`
- 工具模块: `功能名_tools.py`

## 🚀 使用指南

### 日常开发测试
```bash
# 快速功能验证
uv run python scripts/quick_test.py

# 核心功能测试
uv run python scripts/test_working_functions.py

# API集成测试
uv run python scripts/test_fixed_api_integration.py
```

### 完整测试验证
```bash
# 运行所有测试
uv run python scripts/run_all_tests.py

# 运行正式测试套件
uv run pytest tests/

# 性能测试
uv run python scripts/test_performance.py
```

### 兼容性测试
```bash
# Cherry Studio兼容性
uv run python tests/test_cherry_studio_simulation.py

# HTTP协议测试
uv run python tests/test_complete_http_client.py
```

## 📊 统计信息

- **源代码模块**: 20+ 个
- **测试文件**: 8 个（scripts: 5个, tests: 3个）
- **服务集成**: 6个主要API服务
- **文档文件**: 4个核心文档
- **工具功能**: 6个主要MCP工具

---

**最后更新**: 2025-10-27
**维护者**: Claude Code
**项目版本**: v0.1.5+
