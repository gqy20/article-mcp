# Article MCP - 学术文献搜索MCP服务器

## 项目概述

Article MCP 是一个基于 FastMCP 框架开发的专业学术文献搜索工具，可与 Claude Desktop、Cherry Studio 等 AI 助手无缝集成。项目提供统一的 MCP (Model Context Protocol) 服务器接口，支持搜索 Europe PMC、arXiv 等多个学术数据库。

### 核心特性
- 🔍 **多数据库搜索** - 支持 Europe PMC、arXiv、PubMed 等学术数据库
- ⚡ **高性能优化** - 异步并行处理，比传统方法快 6-50 倍
- 💾 **智能缓存** - 24小时本地缓存，避免重复API请求
- 🔄 **批量处理** - 支持最多20个DOI同时处理
- 🛡️ **容错机制** - 自动重试、并发控制、完整的异常处理
- 🌐 **多传输模式** - 支持 stdio、SSE、Streamable HTTP

## 项目结构

```
article-mcp/
├── main.py                    # 🚀 主入口文件，统一命令行接口
├── pyproject.toml            # 📦 uv 项目配置和依赖管理
├── bin/article-mcp.js        # 🔄 NPM 包装器，支持多平台部署
├── src/                      # 🔧 核心服务模块
│   ├── europe_pmc.py        # Europe PMC API 服务（高性能优化版）
│   ├── arxiv_search.py      # arXiv 搜索服务
│   ├── pubmed_search.py     # PubMed 搜索服务
│   ├── reference_service.py # 参考文献处理服务
│   ├── literature_relation_service.py # 文献关联分析服务
│   └── resource/            # 📊 数据资源（期刊信息等）
├── tool_modules/            # 🛠️ MCP 工具模块
│   ├── search_tools.py      # 搜索工具（Europe PMC、arXiv）
│   ├── article_detail_tools.py # 文献详情工具
│   ├── reference_tools.py   # 参考文献工具
│   ├── relation_tools.py    # 文献关联工具
│   └── quality_tools.py     # 期刊质量评估工具
├── json/                    # ⚙️ MCP 配置文件模板
├── docs/                    # 📖 项目文档和使用指南
├── tests/                   # 🧪 测试文件
└── output/                  # 📤 输出目录
```

## 快速开始

### 环境要求
- Python ≥ 3.10
- uv (推荐) 或 pip

### 安装和启动

```bash
# 使用 uv (推荐)
uv sync                    # 安装依赖
uv run main.py server      # 启动服务器

# 使用 pip
pip install fastmcp requests python-dateutil aiohttp
python main.py server      # 启动服务器
```

### 基本命令

```bash
# 启动 MCP 服务器（stdio 模式，推荐用于桌面AI客户端）
python main.py server

# 启动 SSE 服务器（用于Web应用）
python main.py server --transport sse --host 0.0.0.0 --port 9000

# 启动 Streamable HTTP 服务器（用于API集成）
python main.py server --transport streamable-http --host 0.0.0.0 --port 9000

# 运行测试
python main.py test

# 显示项目信息
python main.py info
```

## MCP 工具功能

### 核心搜索工具

| 工具名称 | 功能描述 | 性能特点 |
|---------|---------|----------|
| `search_europe_pmc` | 搜索 Europe PMC 文献数据库 | 比传统方法快30-50%，支持缓存和并发 |
| `search_arxiv_papers` | 搜索 arXiv 预印本文献 | 支持关键词、日期范围过滤 |
| `get_article_details` | 获取文献详细信息 | 比传统方法快20-40%，支持缓存和重试 |

### 参考文献工具

| 工具名称 | 功能描述 | 性能特点 |
|---------|---------|----------|
| `get_references_by_doi` | 通过DOI获取参考文献 | 比传统方法快10-15倍，批量查询 |
| `batch_enrich_references_by_dois` | 批量补全多个DOI参考文献 | 支持最多20个DOI同时处理 |

### 文献关联分析

| 工具名称 | 功能描述 | 数据来源 |
|---------|---------|----------|
| `get_similar_articles` | 获取相似文章推荐 | 基于PubMed相关文章算法 |
| `get_citing_articles` | 获取引用该文献的文章 | PubMed + Europe PMC |
| `get_literature_relations` | 一站式获取所有关联信息 | 综合所有数据源 |

### 期刊质量评估

| 工具名称 | 功能描述 | 数据来源 |
|---------|---------|----------|
| `get_journal_quality` | 获取期刊影响因子、分区等 | 本地缓存 + EasyScholar API |
| `evaluate_articles_quality` | 批量评估文献期刊质量 | 智能缓存，批量处理 |

## 配置指南

### Claude Desktop 配置

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/article-mcp",
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

### 环境变量

```bash
export PYTHONUNBUFFERED=1     # 禁用Python输出缓冲
export EASYSCHOLAR_SECRET_KEY=your_key  # EasyScholar API密钥（可选）
```

## 性能优化

### 异步并行处理
- 使用 `asyncio` 和 `aiohttp` 实现并发请求
- 信号量控制并发数量（默认3个并发）
- 批量处理优化，减少API调用次数

### 智能缓存机制
- 24小时本地缓存，避免重复API请求
- 缓存键基于请求参数生成
- 支持缓存命中统计

### 容错和重试
- 自动重试机制（最多3次，指数退避）
- 网络异常处理
- API速率限制遵循

## 部署方案

### 本地部署
```bash
# 克隆项目
git clone https://github.com/gqy20/article-mcp.git
cd article-mcp

# 安装依赖
uv sync

# 启动服务器
uv run main.py server
```

### 魔搭MCP广场部署
支持一键部署到阿里云函数计算，提供：
- ⚡ 毫秒级弹性启动
- 🔒 多租安全隔离
- 🌐 自动生成SSE服务地址
- 🛡️ 内置Bearer鉴权

### NPM 包装器
```bash
# 使用npx直接运行
npx @gqy20/article-mcp-wrapper@latest server
```

### UVX 安装（推荐）
```bash
# 直接通过uvx安装并运行（无需克隆项目）
uvx --from git+https://github.com/gqy20/article-mcp.git article-mcp server

# 或从PyPI安装
pip install article-mcp
article-mcp server
```

## 开发规范

### 代码风格
- 使用 Black 格式化（line-length: 88）
- 类型注解（Python 3.10+）
- 异步优先设计

### 模块化架构
- **服务层** (`src/`): 核心业务逻辑
- **工具层** (`tool_modules/`): MCP工具封装
- **统一入口** (`main.py`): 命令行接口

### 错误处理
- 完整的异常捕获和日志记录
- 用户友好的错误信息
- 详细的调试信息（开发模式）

## API 限制和优化

| API 服务 | 限制 | 优化策略 |
|---------|------|----------|
| Europe PMC | 1 request/second | 保守策略，自动延迟 |
| Crossref | 50 requests/second | 建议提供邮箱获得更高限额 |
| arXiv | 3 seconds/request | 官方限制，无法优化 |

## 测试和验证

```bash
# 运行功能测试
python main.py test

# 性能对比测试
python test_performance_comparison.py

# 手动测试示例
python -c "
import asyncio
from src.europe_pmc import create_europe_pmc_service
service = create_europe_pmc_service()
results = asyncio.run(service.search_europe_pmc_async('machine learning', max_results=5))
print(f'找到 {len(results)} 篇文献')
"
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| `cannot import name 'hdrs' from 'aiohttp'` | 运行 `uv sync --upgrade` 更新依赖 |
| MCP服务器启动失败 | 检查路径配置，确保使用绝对路径 |
| API请求失败 | 提供邮箱地址，检查网络连接 |
| 找不到uv命令 | 使用完整路径或pip安装方式 |

## 相关文档

- [快速开始指南](docs/发布部署指南.md)
- [功能使用示例](docs/参考文献功能使用示例.md)
- [期刊质量评估指南](docs/期刊质量评估功能使用指南.md)
- [相似文章功能指南](docs/相似文章功能使用指南.md)
- [arXiv搜索功能指南](docs/arXiv_搜索功能使用指南.md)
- [Cherry Studio配置指南](docs/Cherry_Studio_配置指南.md)
- [魔搭MCP广场部署总结](docs/魔搭MCP广场部署总结.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献和支持

- 📧 提交 Issue: [GitHub Issues](https://github.com/gqy20/article-mcp/issues)
- 📚 项目文档: [GitHub Wiki](https://github.com/gqy20/article-mcp/wiki)
- 💬 讨论区: [GitHub Discussions](https://github.com/gqy20/article-mcp/discussions)