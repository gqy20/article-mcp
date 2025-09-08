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
| `get_article_details` | 获取特定文献详细信息（支持PMID、DOI、PMCID） | `identifier`, `id_type`, `mode` |
| `search_arxiv_papers` | 搜索 arXiv 预印本文献 | `keyword`, `start_date`, `end_date`, `max_results` |

### 参考文献工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|----------|
| `get_references_by_doi` | 通过DOI获取参考文献列表 | `doi` |
| `batch_enrich_references_by_dois` | 批量补全多个DOI参考文献 | `dois[]` (最多20个) |
| `get_similar_articles` | 获取相似文章推荐 | `identifier`, `id_type`, `max_results` |
| `get_citing_articles` | 获取引用该文献的文章 | `identifier`, `id_type`, `max_results` |
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

#### 获取文献的所有关联信息

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi",
  "max_results": 10
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

## 🌐 魔搭MCP广场部署

### 快速托管到魔搭MCP广场

魔搭（ModelScope）MCP广场为MCP服务提供云托管服务，基于阿里云函数计算，支持：
- ⚡ 毫秒级弹性启动
- 🔒 多租安全隔离  
- 🌐 自动生成SSE服务地址
- 🛡️ 内置Bearer鉴权能力
- 📊 按实际调用计费

### 部署步骤

1. **访问魔搭MCP广场**：[https://modelscope.cn/mcp](https://modelscope.cn/mcp)

2. **添加MCP服务**，使用以下配置：

#### 推荐配置（完整版）

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "main.py",
        "server"
      ],
      "repository": "https://github.com/gqy20/article-mcp.git",
      "branch": "master",
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "protocol": "stdio",
      "runtime": "debian12",
      "metadata": {
        "name": "文献检索MCP",
        "description": "基于Europe PMC、arXiv等多个数据源的学术文献搜索工具",
        "version": "0.2.0",
        "author": "gqy20",
        "category": "学术工具",
        "tags": ["文献检索", "学术搜索", "Europe PMC", "arXiv", "引用分析"]
      }
    }
  }
}
```

#### 简化配置（最小版）

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "main.py",
        "server"
      ],
      "repository": "https://github.com/gqy20/article-mcp.git",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

3. **提交配置**，魔搭将自动：
   - 拉取GitHub仓库代码
   - 安装依赖（通过uv）
   - 部署到函数计算
   - 生成SSE服务地址

4. **测试服务**：在MCP Playground中测试您的服务

### 特性优势

- 🚀 **秒级部署**：约1秒完成MCP服务部署
- 📦 **零运维**：无需管理服务器和基础设施
- 🔄 **自动转换**：STDIO模式自动转换为SSE服务
- 💰 **按需付费**：仅为实际使用时长付费
- 🛡️ **安全隔离**：每个租户独立的SSE地址和运行环境

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

### NPM 包装器

为兼容性提供了 NPM 包装器：

```bash
# 使用npx运行
npx @gqy20/article-mcp-wrapper@latest server
```

### 魔搭MCP广场配置选项

根据部署检测要求，提供三种配置方案：

#### 🥇 方案1：使用 uvx（推荐）

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/gqy20/article-mcp.git",
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

#### 🥈 方案2：使用 npx

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@gqy20/article-mcp-wrapper@latest",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

#### 🥉 方案3：GitHub 仓库（需手动审核）

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/gqy20/article-mcp.git",
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

### 发布说明

- **PyPI 包名**: `article-mcp`
- **NPM 包名**: `@gqy20/article-mcp-wrapper`
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

- 📧 提交 Issue：[GitHub Issues](https://github.com/your-repo/issues)
- 📚 文档：[项目Wiki](https://github.com/your-repo/wiki)
- 💬 讨论：[GitHub Discussions](https://github.com/your-repo/discussions)

---

## 📖 使用示例

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

### 获取文献的所有关联信息

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi",
  "max_results": 10
}
```
