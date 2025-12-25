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

### 🔍 工具1: 多源文献搜索 (`search_literature`)

**功能描述**: 并行搜索多个学术数据库，支持关键词检索和智能结果合并

**支持的数据源**: Europe PMC, PubMed, arXiv, CrossRef, OpenAlex

**搜索策略**:
| 策略 | 说明 | 数据源 | 合并方式 |
|------|------|--------|----------|
| `comprehensive` | 全面搜索，使用所有可用数据源 | 全部5个源 | 并集 |
| `fast` | 快速搜索，只使用主要数据源 | Europe PMC, PubMed | 并集 |
| `precise` | 精确搜索，只使用权威数据源 | PubMed, Europe PMC | 交集 |
| `preprint` | 预印本搜索 | arXiv | 并集 |

**主要参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | string | 必填 | 搜索关键词 |
| `sources` | list[] | 自动选择 | 数据源列表 |
| `max_results` | int | 10 | 每个源的最大结果数 |
| `search_type` | string | `comprehensive` | 搜索策略 |
| `use_cache` | bool | true | 是否使用24小时缓存 |

**返回数据**:
```json
{
  "success": true,
  "keyword": "机器学习",
  "sources_used": ["europe_pmc", "pubmed", "arxiv"],
  "merged_results": [...],
  "total_count": 25,
  "search_time": 1.23,
  "cache_hit": false
}
```

---

### 📄 工具2: 获取文献详情 (`get_article_details`)

**功能描述**: 通过 DOI、PMID、PMCID 或 arXiv ID 获取文献详细信息

**主要参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `identifier` | string | 必填 | 文献标识符 |
| `id_type` | string | `auto` | 标识符类型: `auto`/`doi`/`pmid`/`pmcid`/`arxiv_id` |
| `sources` | list[] | `["europe_pmc", "crossref"]` | 数据源列表 |
| `include_quality_metrics` | bool | false | 是否包含期刊质量指标 |

**返回数据**:
```json
{
  "success": true,
  "identifier": "10.1038/nature12373",
  "id_type": "doi",
  "sources_found": ["europe_pmc", "crossref"],
  "merged_detail": {
    "title": "...",
    "authors": [...],
    "abstract": "...",
    "journal": "...",
    "publication_date": "...",
    "doi": "..."
  },
  "quality_metrics": {...},
  "processing_time": 0.45
}
```

---

### 📚 工具3: 获取参考文献 (`get_references`)

**功能描述**: 获取指定文献引用的所有参考文献，支持智能去重

**主要参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `identifier` | string | 必填 | 文献标识符 |
| `id_type` | string | `auto` | 标识符类型 |
| `sources` | list[] | `["europe_pmc", "crossref"]` | 数据源列表 |
| `max_results` | int | 20 | 最大参考文献数量 (建议20-100) |
| `include_metadata` | bool | true | 是否包含详细元数据 |

**去重规则**: 优先按 DOI 去重，其次按标题去重；按数据源优先级排序

**返回数据**:
```json
{
  "success": true,
  "identifier": "10.1038/nature12373",
  "sources_used": ["europe_pmc"],
  "merged_references": [
    {
      "title": "...",
      "authors": [...],
      "journal": "...",
      "doi": "...",
      "pmid": "...",
      "source": "europe_pmc",
      "abstract": "..."
    }
  ],
  "total_count": 20,
  "processing_time": 0.67
}
```

---

### 🔗 工具4: 文献关系分析 (`get_literature_relations`)

**功能描述**: 分析文献间的引用关系、相似性和合作网络

**关系类型**:
| 类型 | 说明 | 数据来源 |
|------|------|----------|
| `references` | 该文献引用的参考文献 | Europe PMC, CrossRef |
| `similar` | 相似文献 | Europe PMC |
| `citing` | 引用该文献的文献 | Europe PMC, OpenAlex |

**主要参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `identifiers` | string/list[] | 必填 | 文献标识符 (单个或列表) |
| `id_type` | string | `auto` | 标识符类型 |
| `relation_types` | list[] | `["references", "similar", "citing"]` | 关系类型 |
| `max_results` | int | 20 | 每种关系类型最大结果数 |
| `sources` | list[] | 全部源 | 数据源列表 |
| `analysis_type` | string | `basic` | `basic`(基本)/`comprehensive`(全面)/`network`(网络) |
| `max_depth` | int | 1 | 分析深度 |

**分析模式**:
- **单个文献**: 传入单个标识符，返回该文献的所有关系
- **批量分析**: 传入标识符列表 + `analysis_type="basic"`
- **网络分析**: 传入标识符列表 + `analysis_type="network"`

**返回数据 (单个文献)**:
```json
{
  "success": true,
  "identifier": "10.1038/nature12373",
  "relations": {
    "references": [...],
    "similar": [...],
    "citing": [...]
  },
  "statistics": {
    "references_count": 30,
    "similar_count": 10,
    "citing_count": 5,
    "total_relations": 45
  },
  "processing_time": 1.23
}
```

---

### ⭐ 工具5: 期刊质量评估 (`get_journal_quality`)

**功能描述**: 评估期刊的学术质量和影响力指标，集成 EasyScholar + OpenAlex 双数据源

**支持的指标**:

| 指标名称 | 数据源 | 说明 |
|---------|--------|------|
| **EasyScholar 提供的指标** |
| `impact_factor` | EasyScholar | 影响因子 |
| `quartile` | EasyScholar | SCI分区 (Q1-Q4) |
| `jci` | EasyScholar | JCI指数 |
| `cas_zone` | EasyScholar | 中科院分区 (完整) |
| `cas_zone_base` | EasyScholar | 中科院基础版分区 |
| `cas_zone_small` | EasyScholar | 中科院小类分区 |
| `cas_zone_top` | EasyScholar | TOP期刊标识 |
| **OpenAlex 提供的指标 (自动补充)** |
| `h_index` | OpenAlex | h指数 |
| `citation_rate` | OpenAlex | 引用率 (2年平均) |
| `cited_by_count` | OpenAlex | 总引用数 |
| `works_count` | OpenAlex | 总文章数 |
| `i10_index` | OpenAlex | i10指数 |

**主要参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `journal_name` | string/list[] | 必填 | 期刊名称 (单个或列表) |
| `include_metrics` | list[] | `["impact_factor", "quartile", "jci"]` | 返回的指标列表 |
| `use_cache` | bool | true | 是否使用24小时缓存 |
| `sort_by` | string | null | 排序字段 (仅批量): `impact_factor`/`quartile`/`jci` |
| `sort_order` | string | `desc` | 排序顺序: `desc`(降序)/`asc`(升序) |

**使用示例**:
```python
# 单个期刊查询
get_journal_quality("Nature")

# 批量期刊查询
get_journal_quality(["Nature", "Science", "Cell"])

# 批量查询并按影响因子降序排序
get_journal_quality(["Nature", "Science"], sort_by="impact_factor", sort_order="desc")

# 指定返回指标
get_journal_quality("Nature", include_metrics=["impact_factor", "cas_zone", "h_index"])
```

**返回数据 (单个期刊)**:
```json
{
  "success": true,
  "journal_name": "Nature",
  "quality_metrics": {
    "impact_factor": 49.962,
    "quartile": "Q1",
    "jci": 26.85,
    "cas_zone": "1区TOP"
  },
  "openalex_metrics": {
    "h_index": 1811,
    "citation_rate": 21.9,
    "cited_by_count": 26225053,
    "works_count": 446231,
    "i10_index": 118873
  },
  "cache_hit": false,
  "processing_time": 0.34
}
```

---

## ⚡ 性能特性

- 🚀 **高性能并行处理** - 异步并行查询多个数据源，比传统方法快 30-50%
- 💾 **智能缓存机制** - 24小时本地缓存，避免重复API请求
- 🔄 **批量处理优化** - 支持批量文献查询和关系分析
- 🛡️ **自动重试机制** - 网络异常自动重试
- 📊 **详细性能统计** - 实时监控API调用情况和缓存命中率

---

## 📈 OpenAlex 集成

项目已集成 OpenAlex API 作为免费数据源，提供以下额外指标：

| 指标 | 说明 | 示例值 (Nature) |
|------|------|-----------------|
| `h_index` | h指数 | 1811 |
| `citation_rate` | 引用率 (2年平均) | 21.9 |
| `cited_by_count` | 总引用数 | 26,225,053 |
| `works_count` | 总文章数 | 446,231 |
| `i10_index` | i10指数 | 118,873 |

这些指标会自动补充到期刊质量评估结果中，无需额外配置。

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

集成 EasyScholar 密钥后，以下工具将获得更完整的数据：
- `get_journal_quality` - 获取期刊质量评估信息（影响因子、分区等）

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

| API | 限制 | 说明 |
|-----|------|------|
| **Crossref** | 50 req/s | 提供邮箱可获得更高限额 |
| **Europe PMC** | 1 req/s | 保守策略，避免过载 |
| **arXiv** | 3 req/request | 官方限制 |
| **OpenAlex** | 无限制 | 礼貌使用，建议添加 `mailto` 参数 |
| **EasyScholar** | 未知 | 建议配置密钥获得稳定服务 |

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
│       │   ├── openalex_metrics_service.py # OpenAlex 指标补充
│       │   ├── easyscholar_service.py      # EasyScholar 服务
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
│       │   │   └── quality_tools.py       # 质量评估工具注册
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

### 期刊质量评估 (单个期刊)

```json
{
  "journal_name": "Nature",
  "include_metrics": ["impact_factor", "quartile", "cas_zone", "h_index"]
}
```

### 期刊质量评估 (批量 + 排序)

```json
{
  "journal_name": ["Nature", "Science", "Cell"],
  "include_metrics": ["impact_factor", "quartile", "h_index"],
  "sort_by": "impact_factor",
  "sort_order": "desc"
}
```

### 文献关系分析 (单个文献)

```json
{
  "identifiers": "10.1038/nature12373",
  "id_type": "doi",
  "relation_types": ["references", "similar", "citing"],
  "max_results": 20
}
```

### 文献关系分析 (批量分析)

```json
{
  "identifiers": ["10.1038/nature12373", "10.1038/nature12374"],
  "id_type": "doi",
  "relation_types": ["references", "similar"],
  "analysis_type": "basic",
  "max_results": 15
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
