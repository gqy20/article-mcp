# Article MCP 文献搜索服务器

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
# 启动 MCP 服务器
uv run main.py server

# 或使用 Python
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
        "PYTHONUNBUFFERED": "1"
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
        "PYTHONUNBUFFERED": "1"
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
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 4️⃣ 开始使用

配置完成后，重启你的 AI 客户端，即可使用以下功能：

- 🔍 搜索学术文献 (`search_europe_pmc`)
- 📄 获取文献详情 (`get_article_details`)  
- 📚 获取参考文献 (`get_references_by_doi`)
- 🔗 批量处理DOI (`batch_enrich_references_by_dois`)
- 📰 搜索arXiv预印本 (`search_arxiv_papers`)
- ⭐ 评估期刊质量 (`get_journal_quality`)
- 🔗 获取相似文章 (`get_similar_articles`)
- 🔗 获取引用文献 (`get_citing_articles`)
- 🔄 获取所有关联信息 (`get_literature_relations`)

---

## 📋 完整功能列表

### 核心搜索工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `search_europe_pmc` | 搜索 Europe PMC 文献数据库（高性能优化版本） | `keyword`, `email`, `start_date`, `end_date`, `max_results` |
| `get_article_details` | 获取特定文献详细信息（高性能优化版本） | `identifier`, `id_type`, `mode`, `include_fulltext` |
| `search_arxiv_papers` | 搜索 arXiv 预印本文献 | `keyword`, `email`, `start_date`, `end_date`, `max_results` |

### 参考文献工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_references_by_doi` | 通过DOI获取参考文献列表（批量优化版本） | `doi` |
| `batch_enrich_references_by_dois` | 批量补全多个DOI参考文献（超高性能版本） | `dois[]` (最多20个), `email` |
| `get_similar_articles` | 获取相似文章推荐（基于PubMed相关文章算法） | `identifier`, `id_type`, `email`, `max_results` |
| `get_citing_articles` | 获取引用该文献的文章 | `identifier`, `id_type`, `max_results`, `email` |
| `get_literature_relations` | 获取文献的所有关联信息 | `identifier`, `id_type`, `max_results` |

### 质量评估工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_journal_quality` | 获取期刊影响因子、分区等 | `journal_name`, `secret_key` |
| `evaluate_articles_quality` | 批量评估文献期刊质量 | `articles[]`, `secret_key` |

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
uv run main.py server --transport stdio

# SSE 模式 (用于Web应用)
uv run main.py server --transport sse --host 0.0.0.0 --port 9000

# HTTP 模式 (用于API集成)
uv run main.py server --transport streamable-http --host 0.0.0.0 --port 9000
```

### API 限制与优化

- **Crossref API**: 50 requests/second (建议提供邮箱获得更高限额)
- **Europe PMC API**: 1 request/second (保守策略)
- **arXiv API**: 3 seconds/request (官方限制)

---

## 🛠️ 开发与测试

### 运行测试

```bash
# 运行功能测试
uv run main.py test

# 查看项目信息
uv run main.py info

# 或使用 PyPI 包
uvx article-mcp info
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
├── main.py              # 主入口文件
├── pyproject.toml       # 项目配置文件
├── README.md            # 项目文档
├── src/                 # 核心服务模块
│   ├── europe_pmc.py    # Europe PMC API 接口
│   ├── reference_service.py  # 参考文献服务
│   ├── pubmed_search.py # PubMed 搜索服务
│   ├── similar_articles.py   # 相似文章获取
│   ├── arxiv_search.py  # arXiv 搜索服务
│   ├── literature_relation_service.py  # 文献关联服务
│   └── resource/        # 资源文件目录
│       └── journal_info.json  # 期刊信息缓存
└── tool_modules/        # 工具模块
    ├── search_tools.py       # 搜索工具
    ├── article_detail_tools.py  # 文献详情工具
    ├── reference_tools.py    # 参考文献工具
    ├── relation_tools.py     # 关联文献工具
    └── quality_tools.py      # 期刊质量工具
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
        "PYTHONUNBUFFERED": "1"
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
        "main.py",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
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
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

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

### 搜索 Europe PMC 文献

```json
{
  "keyword": "machine learning cancer detection",
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "max_results": 20
}
```

### 获取文献详情（通过PMID）

```json
{
  "identifier": "12345678",
  "id_type": "pmid"
}
```

### 获取文献详情（通过DOI）

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi"
}
```

### 获取文献详情（通过PMCID）

```json
{
  "identifier": "PMC1234567",
  "id_type": "pmcid"
}
```

### 获取文献详情（异步模式）

```json
{
  "identifier": "12345678",
  "id_type": "pmid",
  "mode": "async"
}
```

### 批量获取参考文献

```json
{
  "dois": [
    "10.1126/science.adf6218",
    "10.1038/s41586-020-2649-2",
    "10.1056/NEJMoa2034577"
  ],
  "email": "your.email@example.com"
}
```

### 期刊质量评估

```json
{
  "journal_name": "Nature",
  "secret_key": "your_easyscholar_key"
}
```

### 获取文献的所有关联信息

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi",
  "max_results": 10
}
```
