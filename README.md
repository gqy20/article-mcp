# Europe PMC 文献搜索 MCP 服务器

> 🔬 基于 FastMCP 框架开发的专业文献搜索工具，可与 Claude Desktop、Cherry Studio 等 AI 助手无缝集成

## 🚀 快速开始

### 0️⃣ 克隆项目

```bash
# 克隆项目到本地
git clone https://github.com/gqy20/article-mcp.git
cd article-mcp
```

### 1️⃣ 安装依赖

```bash
# 方法一：使用 uv (推荐)
curl -LsSf https://astral.sh/uv/install.sh | sh  # 安装 uv
uv sync  # 安装项目依赖

# 方法二：使用 pip
pip install fastmcp requests python-dateutil aiohttp
```

### 2️⃣ 启动服务器

```bash
# 启动 MCP 服务器
uv run main.py server

# 或使用 Python
python main.py server
```

### 3️⃣ 配置 AI 客户端

#### Claude Desktop 配置

编辑 Claude Desktop 配置文件，添加：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:\\你的项目路径\\article-mcp",
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
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "你的项目路径\\article-mcp",
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

### 4️⃣ 开始使用

配置完成后，重启你的 AI 客户端，即可使用以下功能：

- 🔍 搜索学术文献 (`search_europe_pmc`)
- 📄 获取文献详情 (`get_article_details`)  
- 📚 获取参考文献 (`get_references_by_doi`)
- 🔗 批量处理DOI (`batch_enrich_references_by_dois`)
- 📰 搜索arXiv预印本 (`search_arxiv_papers`)
- ⭐ 评估期刊质量 (`get_journal_quality`)

---

## 📋 完整功能列表

### 核心搜索工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `search_europe_pmc` | 搜索 Europe PMC 文献数据库 | `keyword`, `start_date`, `end_date`, `max_results` |
| `get_article_details` | 获取特定文献详细信息 | `pmid` |
| `search_arxiv_papers` | 搜索 arXiv 预印本文献 | `keyword`, `start_date`, `end_date`, `max_results` |

### 参考文献工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_references_by_doi` | 通过DOI获取参考文献列表 | `doi` |
| `batch_enrich_references_by_dois` | 批量补全多个DOI参考文献 | `dois[]` (最多20个) |
| `get_similar_articles` | 获取相似文章推荐 | `doi`, `max_results` |
| `get_citing_articles` | 获取引用该文献的文章 | `pmid`, `max_results` |

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
```

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

## 📖 使用示例

### 搜索文献

```json
{
  "keyword": "machine learning cancer detection",
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "max_results": 20
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

---

## 🛠️ 开发与测试

### 运行测试

```bash
# 运行功能测试
uv run main.py test

# 性能测试
uv run python test_performance_comparison.py

# 查看项目信息
uv run main.py info
```

### 故障排除

| 问题 | 解决方案 |
|------|---------|
| `cannot import name 'hdrs' from 'aiohttp'` | 运行 `uv sync --upgrade` 更新依赖 |
| `MCP服务器启动失败` | 检查路径配置，确保使用绝对路径 |
| `API请求失败` | 提供邮箱地址，检查网络连接 |
| `找不到uv命令` | 使用完整路径：`C:\Users\用户名\.local\bin\uv.exe` |

### 项目结构

```
mcp1/
├── main.py              # 主入口文件
├── src/                 # 核心服务模块
│   ├── europe_pmc.py    # Europe PMC API
│   ├── reference_service.py  # 参考文献服务
│   └── pubmed_search.py # PubMed搜索
├── pyproject.toml       # 项目配置
├── uv.lock             # 依赖锁定文件
└── README.md           # 项目文档
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

- 📧 提交 Issue：[GitHub Issues](https://github.com/your-repo/issues)
- 📚 文档：[项目Wiki](https://github.com/your-repo/wiki)
- 💬 讨论：[GitHub Discussions](https://github.com/your-repo/discussions)
