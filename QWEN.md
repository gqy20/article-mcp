# Article MCP 文献搜索服务器 - 项目上下文

## 项目概述

这是一个基于 FastMCP 框架开发的专业文献搜索工具，可与 Claude Desktop、Cherry Studio 等 AI 助手无缝集成。该项目提供多种学术文献数据库的搜索和获取功能，包括 Europe PMC、PubMed、arXiv 等。

### 核心功能

1. **文献搜索**：支持通过关键词在 Europe PMC 和 PubMed 中搜索学术文献
2. **文献详情获取**：通过 PMID 获取特定文献的详细信息
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
├── src/                 # 核心服务模块
│   ├── europe_pmc.py    # Europe PMC API 接口
│   ├── reference_service.py  # 参考文献服务
│   ├── pubmed_search.py # PubMed 搜索服务
│   ├── similar_articles.py   # 相似文章获取
│   ├── arxiv_search.py  # arXiv 搜索服务
│   └── resource/        # 资源文件目录
├── tests/               # 测试文件
└── docs/                # 文档目录
```

## 技术栈

- **编程语言**：Python 3.10+
- **框架**：FastMCP
- **依赖库**：
  - requests（HTTP 请求）
  - aiohttp（异步 HTTP 请求）
  - python-dateutil（日期处理）
  - xml.etree.ElementTree（XML 解析）

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
pip install fastmcp requests python-dateutil aiohttp
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

## 开发和测试

### 运行测试

```bash
# 运行功能测试
uv run main.py test

# 查看项目信息
uv run main.py info
```

## API 限制和优化

- **Crossref API**：50 requests/second（建议提供邮箱获得更高限额）
- **Europe PMC API**：1 request/second（保守策略）
- **arXiv API**：3 seconds/request（官方限制）

## 配置客户端

### Claude Desktop 配置

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "你的项目路径/article-mcp",
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

### Cherry Studio 配置

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "你的项目路径/article-mcp",
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

## 魔搭 MCP 广场部署

项目支持部署到魔搭（ModelScope）MCP 广场，提供云托管服务：

1. 访问魔搭 MCP 广场：https://modelscope.cn/mcp
2. 添加 MCP 服务，使用推荐配置：
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
         "runtime": "debian12"
       }
     }
   }
   ```

## 性能特点

- **高性能并行处理**：比传统方法快 30-50%
- **智能缓存机制**：24 小时本地缓存，避免重复请求
- **批量处理优化**：支持最多 20 个 DOI 同时处理
- **自动重试机制**：网络异常自动重试
- **详细性能统计**：实时监控 API 调用情况

## 使用示例

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

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| `cannot import name 'hdrs' from 'aiohttp'` | 运行 `uv sync --upgrade` 更新依赖 |
| `MCP服务器启动失败` | 检查路径配置，确保使用绝对路径 |
| `API请求失败` | 提供邮箱地址，检查网络连接 |
| `找不到uv命令` | 使用完整路径：`C:\Users\用户名\.local\bin\uv.exe` |