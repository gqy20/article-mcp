# Europe PMC 文献搜索 MCP 服务器

基于 FastMCP 框架开发的文献搜索工具，可以通过 MCP 协议与 AI 助手集成。

## 功能特性

- 🔍 搜索 Europe PMC 文献数据库
- 📄 获取文献详细信息
- 📚 获取参考文献列表 (通过DOI)
- ⚡ 异步并行优化版本（提升5-10倍性能）
- 🔗 支持多种标识符 (PMID, PMCID, DOI)
- 📅 支持日期范围过滤
- 💾 智能缓存机制（24小时）
- 🌐 支持 stdio 和 HTTP 两种传输方式
- 📊 详细性能统计信息

## 安装依赖

### 使用 uv (推荐)

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用 pip
pip install uv

# 初始化项目
uv sync

# 或者创建虚拟环境
uv venv
uv pip install -e .
```

### 使用 pip

```bash
pip install fastmcp requests python-dateutil
```

## 使用方法

### 1. 使用 main.py 统一入口 (推荐)

```bash
# 显示帮助信息
uv run --no-project python main.py --help

# 显示项目信息
uv run --no-project python main.py info

# 运行测试
uv run --no-project python main.py test

# 启动服务器 (stdio 模式)
uv run --no-project python main.py server

# 启动服务器 (SSE 模式)
uv run --no-project python main.py server --transport sse --host 0.0.0.0 --port 9000

# 启动服务器 (Streamable HTTP 模式)
uv run --no-project python main.py server --transport streamable-http --host 0.0.0.0 --port 9000
```

### 2. 使用已安装的脚本

```bash
# 如果安装了包，可以直接使用
europe-pmc-mcp --help
```

### 3. 传统方式 (仅在没有 uv 时使用)

```bash
# 运行测试
python main.py test

# 启动服务器
python main.py server
```

### 4. 配置 Claude Desktop

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "europe-pmc": {
      "command": "uv",
      "args": ["run", "--no-project", "python", "/path/to/your/project/main.py", "server"],
      "env": {}
    }
  }
}
```

或者使用传统方式：

```json
{
  "mcpServers": {
    "europe-pmc": {
      "command": "python",
      "args": ["/path/to/your/project/main.py", "server"],
      "env": {}
    }
  }
}
```

## 可用工具

### 1. search_europe_pmc

搜索 Europe PMC 文献数据库

**参数:**
- `keyword` (必需): 搜索关键词
- `email` (可选): 用户邮箱地址
- `start_date` (可选): 搜索起始日期 (YYYY-MM-DD)
- `end_date` (可选): 搜索结束日期 (YYYY-MM-DD)
- `max_results` (可选): 最大结果数 (默认10)

**示例:**
```json
{
  "keyword": "machine learning",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "max_results": 20
}
```

### 2. get_article_details

获取特定文献的详细信息

**参数:**
- `pmid` (必需): 文献的 PMID 或标识符

**示例:**
```json
{
  "pmid": "12345678"
}
```

### 3. get_references_by_doi

通过DOI获取参考文献列表（同步版本）

**参数:**
- `doi` (必需): 文献的 DOI 标识符

**示例:**
```json
{
  "doi": "10.1126/science.adf6218"
}
```

### 4. get_references_by_doi_async

通过DOI获取参考文献列表（异步并行优化版本）

**参数:**
- `doi` (必需): 文献的 DOI 标识符

**特性:**
- 🚀 5-10倍性能提升
- 💾 智能缓存机制
- 📊 详细性能统计
- 🔄 并行处理多个API调用

**示例:**
```json
{
  "doi": "10.1126/science.adf6218"
}
```

## 性能测试

运行性能比较测试：

```bash
# 使用默认测试DOI
uv run --no-project python test_performance_comparison.py

# 使用自定义DOI
uv run --no-project python test_performance_comparison.py "10.1126/science.adf6218"
```

## API速率限制优化

本项目遵循官方API速率限制建议：

- **Crossref API**: 50 requests/second (添加mailto头部进入polite池)
- **Europe PMC API**: 1 request/second (保守策略)
- **智能缓存**: 24小时本地缓存避免重复调用
- **分批处理**: 控制并发数量避免过载

## 返回数据格式

每篇文献包含以下字段：

- `pmid`: PubMed ID
- `pmid_link`: 文献链接
- `title`: 标题
- `authors`: 作者列表
- `journal_name`: 期刊名称
- `journal_volume`: 卷号
- `journal_issue`: 期号
- `journal_pages`: 页码
- `publication_date`: 发表日期
- `abstract`: 摘要
- `doi`: DOI 标识符
- `pmcid`: PMC ID

## 注意事项

1. 默认搜索范围为最近3年的文献
2. 推荐提供邮箱地址以提高API请求成功率
3. 单次搜索最多返回指定数量的结果
4. 脚本包含重试机制，网络问题会自动重试

## 故障排除

1. **网络连接问题**: 检查网络连接和防火墙设置
2. **API限制**: 如果遇到请求限制，可以提供邮箱地址
3. **日期格式错误**: 确保日期格式为 YYYY-MM-DD, YYYY/MM/DD 或 YYYYMMDD

## 许可证

本项目遵循 MIT 许可证。
