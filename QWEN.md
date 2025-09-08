# Article MCP 文献搜索服务器 - 项目上下文

## 项目概述

这是一个基于 FastMCP 框架开发的专业文献搜索工具，可与 Claude Desktop、Cherry Studio 等 AI 助手无缝集成。该项目提供多种学术文献数据库的搜索和获取功能，包括 Europe PMC、PubMed、arXiv 等。

### 核心功能

1. **文献搜索**：支持通过关键词在 Europe PMC 和 PubMed 中搜索学术文献
2. **文献详情获取**：通过 PMID、DOI 或 PMCID 获取特定文献的详细信息
3. **参考文献获取**：通过 DOI 获取文献的参考文献列表
4. **批量处理**：支持批量补全多个 DOI 的参考文献信息
5. **相似文章推荐**：根据 DOI 获取与之相似的文章
6. **期刊质量评估**：获取期刊的影响因子、分区等质量指标
7. **引用文献获取**：获取引用特定文献的其他文献信息
8. **arXiv 预印本搜索**：搜索 arXiv 数据库中的预印本论文

## 目录结构

```
article-mcp/
├── main.py              # 主入口文件
├── pyproject.toml       # 项目配置文件
├── README.md            # 项目文档
├── QWEN.md              # 当前文件（项目上下文）
├── json/                # 配置文件目录
│   ├── mcp_config.json          # PyPI包部署配置
│   ├── mcp_config_local.json    # 本地开发配置
│   └── mcp_config_cherry_studio.json  # Cherry Studio配置
├── src/                 # 核心服务模块
│   ├── europe_pmc.py    # Europe PMC API 接口
│   ├── reference_service.py  # 参考文献服务
│   ├── pubmed_search.py # PubMed 搜索服务
│   ├── similar_articles.py   # 相似文章获取
│   ├── arxiv_search.py  # arXiv 搜索服务
│   ├── literature_relation_service.py  # 文献关联服务
│   ├── html_to_markdown.py  # HTML转Markdown工具
│   └── resource/        # 资源文件目录
│       └── journal_info.json  # 期刊信息缓存
└── tool_modules/        # 工具模块
    ├── search_tools.py       # 搜索工具
    ├── article_detail_tools.py  # 文献详情工具
    ├── reference_tools.py    # 参考文献工具
    ├── relation_tools.py     # 关联文献工具
    └── quality_tools.py      # 期刊质量工具
```

## 技术栈

- **编程语言**：Python 3.10+
- **框架**：FastMCP
- **依赖库**：
  - fastmcp>=2.0.0（MCP框架）
  - requests>=2.25.0（HTTP请求）
  - python-dateutil>=2.8.0（日期处理）
  - urllib3>=1.26.0（HTTP库）
  - aiohttp>=3.9.0（异步HTTP请求）
  - markdownify>=0.12.0（HTML转Markdown）

## 核心模块说明

### 1. Europe PMC 服务 (src/europe_pmc.py)

提供对 Europe PMC 文献数据库的访问功能：
- 同步和异步搜索文献
- 获取文献详细信息
- 批量查询多个 DOI（性能优化版本，比传统方法快 10-15 倍）
- 支持缓存机制（24小时智能缓存）
- 并发控制和速率限制

### 2. 参考文献服务 (src/reference_service.py)

处理参考文献的获取和补全：
- 通过 DOI 获取参考文献列表
- 使用 Crossref 和 Europe PMC 补全参考文献信息
- 批量补全多个 DOI 的参考文献（超高性能版本，比逐个查询快 10-15 倍）
- 参考文献去重处理
- 支持最多 20 个 DOI 的批量处理

### 3. PubMed 搜索服务 (src/pubmed_search.py)

提供对 PubMed 文献数据库的访问功能：
- 关键词搜索 PubMed 文献
- 获取文献详细信息
- 获取引用特定文献的其他文献
- 期刊质量评估（影响因子、分区等）
- 批量评估文献的期刊质量

### 4. 相似文章服务 (src/similar_articles.py)

基于 PubMed 相关文章算法查找相似文献：
- 根据 DOI 获取相似文章
- 自动过滤最近 5 年内的文献
- 批量获取相关文章的详细信息

### 5. arXiv 搜索服务 (src/arxiv_search.py)

搜索 arXiv 预印本数据库：
- 支持关键词搜索
- 日期范围过滤
- 自动重试和错误恢复机制
- 分页获取大量结果

### 6. 文献关联服务 (src/literature_relation_service.py)

统一处理文献的各种关联信息：
- 获取参考文献
- 获取相似文章
- 获取引用文献
- 一站式获取所有关联信息

## 构建和运行

### 安装依赖

推荐使用 uv 工具管理依赖：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

或者使用 pip：

```bash
pip install fastmcp requests python-dateutil aiohttp markdownify
```

### 启动服务器

```bash
# 使用 uv 启动
uv run main.py server

# 或使用 Python 启动
python main.py server
```

### 支持的传输模式

1. **STDIO 模式**（默认）：用于桌面 AI 客户端
   ```bash
   uv run main.py server --transport stdio
   ```

2. **SSE 模式**：用于 Web 应用
   ```bash
   uv run main.py server --transport sse --host 0.0.0.0 --port 9000
   ```

3. **HTTP 模式**：用于 API 集成
   ```bash
   uv run main.py server --transport streamable-http --host 0.0.0.0 --port 9000
   ```

## 部署方式

项目支持多种部署方式，配置文件位于 `json/` 目录中：

### 1. PyPI 包部署 (推荐)
使用已发布的 PyPI 包进行部署：
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

### 2. 本地开发部署
直接运行本地代码：
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

### 3. Cherry Studio 配置
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

## 开发和测试

### 运行测试

```bash
# 运行功能测试
uv run main.py test

# 查看项目信息
uv run main.py info
```

### 开发约定

1. **模块化设计**：使用 `src/` 目录存放核心服务，`tool_modules/` 目录存放 MCP 工具注册
2. **依赖管理**：使用 `pyproject.toml` 管理项目依赖
3. **编码规范**：遵循 Python 标准编码规范
4. **版本控制**：使用 git 进行版本控制，忽略 `__pycache__`、`.venv` 等生成文件

## API 限制和优化

- **Crossref API**：50 requests/second（建议提供邮箱获得更高限额）
- **Europe PMC API**：1 request/second（保守策略）
- **arXiv API**：3 seconds/request（官方限制）

## 性能特点

- **高性能并行处理**：比传统方法快 30-50%
- **智能缓存机制**：24 小时本地缓存，避免重复请求
- **批量处理优化**：支持最多 20 个 DOI 同时处理
- **自动重试机制**：网络异常自动重试
- **详细性能统计**：实时监控 API 调用情况

## 环境变量

```bash
export PYTHONUNBUFFERED=1     # 禁用Python输出缓冲
export UV_LINK_MODE=copy      # uv链接模式(可选)
export EASYSCHOLAR_SECRET_KEY=your_secret_key  # EasyScholar API密钥(可选)
```

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| `cannot import name 'hdrs' from 'aiohttp'` | 运行 `uv sync --upgrade` 更新依赖 |
| `MCP服务器启动失败` | 检查路径配置，确保使用绝对路径 |
| `API请求失败` | 提供邮箱地址，检查网络连接 |
| `找不到uv命令` | 使用完整路径：`~/.local/bin/uv` |