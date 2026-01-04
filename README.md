# Article MCP 文献搜索服务器

[![MCP Server](https://glama.ai/mcp/servers/@gqy20/article-mcp/badge)](https://glama.ai/mcp/servers/@gqy20/article-mcp)

基于 FastMCP v2.13+ 的异步文献搜索工具，集成 Europe PMC、PubMed、arXiv、CrossRef、OpenAlex 等数据源。

## 快速开始

```bash
# 安装
uvx article-mcp

# 或本地开发
git clone https://github.com/gqy20/article-mcp.git && cd article-mcp
uv sync
uv run python -m article_mcp
```

## 配置

### Claude Desktop

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp"],
      "env": {
        "EASYSCHOLAR_SECRET_KEY": "your_key_here"
      }
    }
  }
}
```

`EASYSCHOLAR_SECRET_KEY` 为可选项，访问 [EasyScholar](https://www.easyscholar.cc) 注册获取。

### Cherry Studio

同上，如遇 Unicode 问题添加 `env: {"PYTHONIOENCODING": "utf-8"}`

## 5 个核心工具

| 工具 | 功能 | 数据源 | 主要参数 |
|------|------|--------|----------|
| `search_literature` | 多源文献搜索 | Europe PMC, PubMed, arXiv, CrossRef, OpenAlex | `keyword`, `max_results` |
| `get_article_details` | 获取文献详情（支持参数容错） | Europe PMC, CrossRef, OpenAlex, arXiv, PubMed | `identifier`, `id_type`, `sources` |
| `get_references` | 获取参考文献 | Europe PMC, CrossRef, PubMed | `identifier`, `max_results` |
| `get_literature_relations` | 文献关系分析 | Europe PMC, PubMed, CrossRef, OpenAlex | `identifiers`, `relation_types` |
| `get_journal_quality` | 期刊质量评估 | EasyScholar, OpenAlex | `journal_name`, `include_metrics` |

## 数据源说明

### Europe PMC
- **内容**：生物医学文献全文、摘要
- **限制**：1 req/s
- **用途**：搜索、全文获取、参考文献

### PubMed
- **内容**：生物医学文献摘要
- **限制**：无严格限制
- **用途**：搜索补充

### arXiv
- **内容**：预印本论文
- **限制**：3 req/request
- **用途**：预印本搜索

### CrossRef
- **内容**：跨出版社元数据
- **限制**：50 req/s
- **用途**：参考文献查询

### OpenAlex
- **内容**：开放学术图谱
- **限制**：无限制
- **用途**：引用关系、h 指标

### EasyScholar
- **内容**：期刊质量指标
- **限制**：建议配置密钥
- **用途**：影响因子、分区

## 使用示例

```json
// 搜索（默认使用 Europe PMC + PubMed）
{"keyword": "machine learning", "max_results": 10}

// 指定数据源搜索
{"keyword": "cancer", "sources": ["europe_pmc", "arxiv"]}

// 获取全文
{"pmcid": "PMC1234567"}

// 获取指定章节
{"pmcid": "PMC1234567", "sections": ["methods", "results"]}

// 批量获取
{"pmcid": ["PMC123", "PMC456"]}

// 获取参考文献（默认 Europe PMC + CrossRef）
{"identifier": "10.1038/nature12373", "max_results": 20}

// 文献关系分析
{"identifiers": "10.1038/nature12373", "relation_types": ["references", "similar"]}

// 期刊质量（EasyScholar + OpenAlex 双源）
{"journal_name": "Nature", "include_metrics": ["impact_factor", "h_index"]}
```

## 参数容错特性

`get_article_details` 工具会自动修正以下格式错误：

| 输入 | 自动修正为 |
|------|-----------|
| `"pmcid": "[\"a\", \"b\"]"` | `["a", "b"]` |
| `"sections": "methods"` | `["methods"]` |

## API 限制汇总

| API | 限制 | 用途 |
|-----|------|------|
| Europe PMC | 1 req/s | 全文、参考文献 |
| Crossref | 50 req/s | 参考文献 |
| arXiv | 3 req/request | 预印本 |
| OpenAlex | 无限制 | 引用关系、指标 |
| EasyScholar | 建议配置密钥 | 期刊质量 |

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| `cannot import 'hdrs' from 'aiohttp'` | `uv sync --upgrade` |
| MCP 服务器启动失败 | 检查配置中的路径是否使用绝对路径 |
| API 请求失败 | 检查网络连接 |
| 期刊质量数据缺失 | 配置 `EASYSCHOLAR_SECRET_KEY` |

## 许可证

MIT License
