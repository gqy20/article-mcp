# 📁 项目结构说明

## 🗂️ 目录结构

```
article-mcp/
├── src/article_mcp/          # 核心源代码
│   ├── __init__.py           # 包初始化（含 __version__）
│   ├── cli.py                # CLI入口点和MCP服务器创建
│   ├── __main__.py           # Python模块执行支持
│   ├── middleware/           # 中间件层
│   │   ├── __init__.py       # MCPErrorHandlingMiddleware
│   │   └── logging.py        # 日志与耗时统计中间件
│   ├── resources/            # MCP 资源层
│   │   ├── config_resources.py   # config://version、config://status、config://tools
│   │   └── journal_resources.py  # journals://{journal_name}/quality、stats://cache
│   ├── services/             # 服务层
│   │   ├── api_utils.py      # 统一 HTTP 客户端（同步 + 异步）
│   │   ├── arxiv_search.py   # arXiv 检索
│   │   ├── crossref_service.py # CrossRef API服务
│   │   ├── easyscholar_service.py # EasyScholar 期刊指标
│   │   ├── europe_pmc.py     # Europe PMC API集成
│   │   ├── html_to_markdown.py # HTML → Markdown 转换
│   │   ├── merged_results.py # 结果合并和去重
│   │   ├── openalex_metrics_service.py # OpenAlex 期刊指标补充
│   │   ├── openalex_service.py # OpenAlex API服务
│   │   ├── pubmed_search.py  # PubMed搜索服务
│   │   ├── reference_service.py # 参考文献服务
│   │   └── similar_articles.py # 相似文献推荐
│   └── tools/core/           # MCP工具实现（5 个核心工具）
│       ├── article_tools.py  # get_article_details
│       ├── quality_tools.py  # get_journal_quality
│       ├── reference_tools.py # get_references
│       ├── relation_tools.py # get_literature_relations
│       └── search_tools.py   # search_literature
├── scripts/                  # 非 pytest 的辅助脚本
│   ├── test_fastmcp_compliance.py # FastMCP 合规性检查（CI smoke 作业）
│   ├── simulate_cherry_studio.py  # Cherry Studio 客户端兼容性模拟
│   ├── clean_pytest_cache.py  # 清理 pytest 临时目录
│   └── manual/               # 需要手工前置条件（本地服务 / 真实 API）的脚本
├── tests/                    # 正式测试套件（pytest）
│   ├── conftest.py           # 全局 fixture
│   ├── unit/                 # 单元测试
│   │   ├── services/         # 各服务的单元测试
│   │   └── tools/            # 工具层单元测试
│   ├── integration/          # 集成测试（打真实 API，标记 integration + network）
│   ├── utils/                # 测试辅助
│   └── verification/         # 验证类测试
├── docs/                     # 文档目录
│   └── archive/              # 历史归档（一次性修复报告）
└── [项目配置文件...]
```

## 📋 核心文件说明

### 🚀 核心代码文件
- **`src/article_mcp/cli.py`**: 主要的MCP服务器创建和配置
- **`src/article_mcp/__main__.py`**: 支持Python模块执行
- **`src/article_mcp/services/`**: 所有API服务实现
- **`src/article_mcp/tools/core/`**: MCP工具注册和实现

### 🧪 测试文件分类

#### Scripts目录（非 pytest 辅助脚本）
- **合规性检查**: `test_fastmcp_compliance.py` —— CI smoke 作业调用
- **客户端兼容性**: `simulate_cherry_studio.py` —— 模拟 MCP 客户端握手
- **维护工具**: `clean_pytest_cache.py`
- **手工脚本**: `manual/` —— 需要本地服务或真实 API，不进 CI

#### Tests目录（正式测试套件，pytest）
- **单元测试**: `tests/unit/` - 各个组件的独立测试
- **集成测试**: `tests/integration/` - 端到端功能测试（打真实 API）
- **网络用例**: 打了真实外部 API 的用例统一标 `@pytest.mark.network`，
  CI 用 `pytest -m "not network"` 排除，避免受外部限流影响

### ⚙️ 配置文件
- **`pyproject.toml`**: 项目配置和依赖管理
- **`uv.lock`**: 依赖锁定文件（`uv sync` 会严格按它安装）
- **`pytest.ini` / `mypy.ini`**: pytest 与 mypy 的唯一配置来源

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

### 日常开发
```bash
uv sync --extra dev

# 全量测试
uv run pytest

# 跳过打真实外部 API 的用例（CI 用的就是这个）
uv run pytest -m "not network"

# 单个文件 / 单个用例
uv run pytest tests/unit/test_six_tools.py
uv run pytest tests/unit/test_six_tools.py -k test_all_tools_registered
```

### 质量检查
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/test_fastmcp_compliance.py
```

> ruff 0.17 起会格式化 Markdown 里的 Python 代码块，因此 `ruff format .` 与 CI 的
> `ruff format --check .` 覆盖范围一致（含 `docs/`）。
