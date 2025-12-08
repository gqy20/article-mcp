# Article MCP 文献搜索服务器

[![MCP Server](https://glama.ai/mcp/servers/@gqy20/article-mcp/badge)](https://glama.ai/mcp/servers/@gqy20/article-mcp)

> 🔬 基于 FastMCP 框架开发的专业文献搜索工具，可与 Claude Desktop、Cherry Studio 等 AI 助手无缝集成

## 🚀 快速开始

### 0️⃣ 安装 uv 工具

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1️⃣ 安装依赖

#### 方式一：直接使用 PyPI 包（推荐）

```bash
# 直接运行，无需安装依赖
uvx article-mcp server
```

#### 方式二：本地开发环境

```bash
# 克隆项目到本地
git clone https://github.com/gqy20/article-mcp.git
cd article-mcp

# 安装项目依赖
uv sync

# 或使用 pip 安装依赖
pip install fastmcp requests python-dateutil aiohttp markdownify
```

### 2️⃣ 启动服务器

#### 使用 PyPI 包（推荐）

```bash
# 直接运行 PyPI 包
uvx article-mcp server
```

#### 本地开发

```bash
# 启动 MCP 服务器 (推荐新入口点)
uv run python -m article_mcp server

# 或使用 Python
python -m article_mcp server

# 兼容性入口点 (仍然支持)
uv run main.py server
python main.py server
```

### 3️⃣ 配置 AI 客户端

#### Claude Desktop 配置

编辑 Claude Desktop 配置文件，添加：

##### 方式一：使用 PyPI 包（推荐）

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "article-mcp",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

##### 方式二：本地开发

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/article-mcp",
        "main.py",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### Cherry Studio 配置

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "article-mcp",
        "server",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

> **重要提示**：为了确保在 Cherry Studio 中正常工作，必须设置 `PYTHONIOENCODING=utf-8` 环境变量以正确处理 Unicode 字符。

### 4️⃣ 开始使用

配置完成后，重启你的 AI 客户端，即可使用以下功能：

- 🔍 多源文献搜索 (`search_literature`)
- 📄 获取文献详情 (`get_article_details`)
- 📚 获取参考文献 (`get_references`)
- 🔗 文献关系分析 (`get_literature_relations`)
- ⭐ 期刊质量评估 (`get_journal_quality`)
- 📊 批量结果导出 (`export_batch_results`)

---

## 📋 完整功能列表

### 🔍 核心搜索工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `search_literature` | 多源文献搜索工具。搜索学术数据库文献，支持关键词检索和结果合并。 | `keyword`, `sources[]`, `max_results`, `search_type` |
| `get_article_details` | 获取文献详情工具。通过DOI、PMID等标识符获取文献的详细信息。 | `identifier`, `id_type`, `sources[]`, `include_quality_metrics` |

### 📚 参考文献工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_references` | 获取参考文献工具。通过文献标识符获取完整参考文献列表。 | `identifier`, `id_type`, `sources[]`, `max_results`, `include_metadata` |

### 🔗 文献关系分析工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_literature_relations` | 文献关系分析工具。分析文献间的引用关系、相似性和合作网络。 | `identifier/identifiers`, `id_type`, `relation_types[]`, `max_results`, `analysis_type` |

### ⭐ 质量评估工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_journal_quality` | 期刊质量评估工具。评估期刊的学术质量和影响力指标。 | `journal_name`, `operation`, `evaluation_criteria[]`, `include_metrics[]` |

### 📊 批量处理工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `export_batch_results` | 通用结果导出工具。导出批量处理结果为JSON或CSV格式文件。 | `results`, `format_type`, `output_path`, `include_metadata` |

---

## ⚡ 性能特性

- 🚀 **高性能并行处理** - 比传统方法快 30-50%
- 💾 **智能缓存机制** - 24小时本地缓存，避免重复请求
- 🔄 **批量处理优化** - 支持最多20个DOI同时处理
- 🛡️ **自动重试机制** - 网络异常自动重试
- 📊 **详细性能统计** - 实时监控API调用情况

---

## 🔧 高级配置

### 环境变量

```bash
export PYTHONUNBUFFERED=1     # 禁用Python输出缓冲
export UV_LINK_MODE=copy      # uv链接模式(可选)
export EASYSCHOLAR_SECRET_KEY=your_secret_key  # EasyScholar API密钥(可选)
```

### MCP 配置集成 (v0.1.1 新功能)

现在支持从 MCP 客户端配置文件中读取 EasyScholar API 密钥，无需通过环境变量传递。

#### Claude Desktop 配置

编辑 `~/.config/claude-desktop/config.json` 文件：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "EASYSCHOLAR_SECRET_KEY": "your_easyscholar_api_key_here"
      }
    }
  }
}
```

#### 密钥优先级

1. **MCP配置文件**中的密钥（最高优先级）
2. **函数参数**中的密钥
3. **环境变量**中的密钥

#### 支持的工具

- `get_journal_quality` - 获取期刊质量评估信息
- `evaluate_articles_quality` - 批量评估文献的期刊质量

配置完成后重启 MCP 客户端即可生效。

### 传输模式

```bash
# STDIO 模式 (推荐用于桌面AI客户端)
uv run python -m article_mcp server --transport stdio

# SSE 模式 (用于Web应用)
uv run python -m article_mcp server --transport sse --host 0.0.0.0 --port 9000

# HTTP 模式 (用于API集成)
uv run python -m article_mcp server --transport streamable-http --host 0.0.0.0 --port 9000
```

### API 限制与优化

- **Crossref API**: 50 requests/second (建议提供邮箱获得更高限额)
- **Europe PMC API**: 1 request/second (保守策略)
- **arXiv API**: 3 seconds/request (官方限制)

---

## 🛠️ 开发与测试

### 运行测试

项目提供了完整的测试套件来验证功能：

```bash
# 核心功能测试（推荐日常使用）
uv run python scripts/test_working_functions.py

# 快速测试（功能验证）
uv run python scripts/quick_test.py

# 完整测试套件
uv run python scripts/run_all_tests.py

# 分类测试
uv run python scripts/test_basic_functionality.py  # 基础功能测试
uv run python scripts/test_cli_functions.py       # CLI功能测试
uv run python scripts/test_service_modules.py     # 服务模块测试
uv run python scripts/test_integration.py         # 集成测试
uv run python scripts/test_performance.py         # 性能测试
```

### 项目信息

```bash
# 查看项目信息
uv run python -m article_mcp info

# 或使用 PyPI 包
uvx article-mcp info

# 查看帮助
uv run python -m article_mcp --help
```

### 故障排除

| 问题 | 解决方案 |
|------|---------|
| `cannot import name 'hdrs' from 'aiohttp'` | 运行 `uv sync --upgrade` 更新依赖 |
| `MCP服务器启动失败` | 检查路径配置，确保使用绝对路径 |
| `API请求失败` | 提供邮箱地址，检查网络连接 |
| `找不到uv命令` | 使用完整路径：`~/.local/bin/uv` |

### 项目结构

```
article-mcp/
├── main.py              # 兼容性入口文件（向后兼容）
├── pyproject.toml       # 项目配置文件
├── README.md            # 项目文档
├── src/                 # 源代码根目录
│   └── article_mcp/     # 主包（标准Python src layout）
│       ├── __init__.py  # 包初始化
│       ├── cli.py       # CLI入口点和MCP服务器创建
│       ├── __main__.py  # Python模块执行入口
│       ├── services/    # 服务层
│       │   ├── europe_pmc.py              # Europe PMC API 集成
│       │   ├── arxiv_search.py            # arXiv 搜索服务
│       │   ├── pubmed_search.py           # PubMed 搜索服务
│       │   ├── reference_service.py       # 参考文献管理
│       │   ├── literature_relation_service.py # 文献关系分析
│       │   ├── crossref_service.py        # Crossref 服务
│       │   ├── openalex_service.py        # OpenAlex 服务
│       │   ├── api_utils.py               # API 工具类
│       │   ├── mcp_config.py              # MCP 配置管理
│       │   ├── error_utils.py             # 错误处理工具
│       │   ├── html_to_markdown.py        # HTML 转换工具
│       │   ├── merged_results.py          # 结果合并工具
│       │   └── similar_articles.py        # 相似文章工具
│       ├── tools/       # 工具层（MCP工具注册）
│       │   ├── core/                      # 核心工具模块
│       │   │   ├── search_tools.py        # 搜索工具注册
│       │   │   ├── article_tools.py       # 文章工具注册
│       │   │   ├── reference_tools.py     # 参考文献工具注册
│       │   │   ├── relation_tools.py      # 关系分析工具注册
│       │   │   ├── quality_tools.py       # 质量评估工具注册
│       │   │   └── batch_tools.py         # 批量处理工具注册
│       │   ├── article_detail_tools.py    # 文章详情工具
│       │   ├── quality_tools.py           # 质量工具
│       │   ├── reference_tools.py         # 参考文献工具
│       │   ├── relation_tools.py          # 关系工具
│       │   └── search_tools.py            # 搜索工具
│       └── legacy/       # 向后兼容模块
│           └── __init__.py
├── src/resource/        # 资源文件目录
│   └── journal_info.json  # 期刊信息缓存
├── tests/               # 测试套件
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── utils/           # 测试工具
├── scripts/             # 测试脚本
│   ├── test_working_functions.py  # 核心功能测试
│   ├── test_basic_functionality.py # 基础功能测试
│   ├── test_cli_functions.py      # CLI功能测试
│   ├── test_service_modules.py    # 服务模块测试
│   ├── test_integration.py        # 集成测试
│   ├── test_performance.py        # 性能测试
│   ├── run_all_tests.py           # 完整测试套件
│   └── quick_test.py              # 快速测试
└── docs/                # 文档目录
```

---

## 📄 返回数据格式

每篇文献包含以下标准字段：

```json
{
  "pmid": "文献ID",
  "title": "文献标题",
  "authors": ["作者1", "作者2"],
  "journal_name": "期刊名称",
  "publication_date": "发表日期",
  "abstract": "摘要",
  "doi": "DOI标识符",
  "pmid_link": "文献链接"
}
```

---

## 📦 发布包管理

### PyPI 包发布

项目已发布到 PyPI，支持通过 `uvx` 命令直接运行：

```bash
# 从PyPI安装后直接运行（推荐）
uvx article-mcp server

# 或先安装后运行
pip install article-mcp
article-mcp server

# 本地开发测试
uvx --from . article-mcp server
```

### 配置说明

有三种推荐的配置方式：

#### 🥇 方案1：使用 PyPI 包（推荐）

这是最简单和推荐的方式，直接使用已发布的 PyPI 包：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "article-mcp",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### 🥈 方案2：本地开发

如果您想运行本地代码或进行开发：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/article-mcp",
        "python",
        "-m",
        "article_mcp",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### 🥉 方案3：Cherry Studio 配置

针对 Cherry Studio 的特定配置：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "article-mcp",
        "server",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

> **编码兼容性说明**：Cherry Studio 需要 `PYTHONIOENCODING=utf-8` 环境变量来正确处理 Unicode 字符，避免工具列表加载失败。

### 发布说明

- **PyPI 包名**: `article-mcp`
- **版本管理**: 统一使用语义化版本控制
- **自动更新**: 使用 `@latest` 标签确保获取最新版本

---

## 📜 许可证

本项目遵循 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📞 支持

- 📧 提交 Issue：[GitHub Issues](https://github.com/gqy20/article-mcp/issues)
- 📚 文档：查看 README 和源代码注释
- 💬 讨论：[GitHub Discussions](https://github.com/gqy20/article-mcp/discussions)

---

## 📖 使用示例

### 多源文献搜索

```json
{
  "keyword": "machine learning cancer detection",
  "sources": ["europe_pmc", "pubmed", "arxiv"],
  "max_results": 20,
  "search_type": "comprehensive"
}
```

### 获取文献详情（通过DOI）

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi",
  "sources": ["europe_pmc", "crossref"],
  "include_quality_metrics": true
}
```

### 获取文献详情（通过PMID）

```json
{
  "identifier": "12345678",
  "id_type": "pmid",
  "sources": ["europe_pmc"],
  "include_quality_metrics": false
}
```

### 获取参考文献

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi",
  "sources": ["europe_pmc", "crossref"],
  "max_results": 50,
  "include_metadata": true
}
```

### 文献关系分析（单个文献）

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi",
  "relation_types": ["references", "similar", "citing"],
  "max_results": 20,
  "analysis_type": "basic"
}
```

### 文献关系分析（批量分析）

```json
{
  "identifiers": ["10.1000/xyz123", "10.1000/abc456"],
  "id_type": "doi",
  "relation_types": ["references", "similar"],
  "max_results": 15,
  "analysis_type": "basic"
}
```

### 期刊质量评估

```json
{
  "journal_name": "Nature",
  "operation": "quality",
  "evaluation_criteria": ["impact_factor", "quartile", "jci"],
  "include_metrics": ["impact_factor", "quartile", "jci", "分区"]
}
```

### 批量期刊质量评估

```json
{
  "journal_name": ["Nature", "Science", "Cell"],
  "operation": "quality",
  "include_metrics": ["impact_factor", "quartile"]
}
```

### 导出搜索结果

```json
{
  "results": {
    "merged_results": [
      {
        "title": "论文标题",
        "authors": [{"name": "作者1"}, {"name": "作者2"}],
        "journal": "期刊名称",
        "publication_date": "2024-01-01",
        "doi": "10.1000/example123",
        "pmid": "12345678",
        "abstract": "论文摘要..."
      }
    ],
    "total_count": 1,
    "search_time": 1.2
  },
  "format_type": "json",
  "include_metadata": true
}
```
