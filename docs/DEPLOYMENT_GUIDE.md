# Article MCP v2.0 部署指南

## 新架构概览

Article MCP v2.0 采用6工具统一架构，替代了原来分散的10个工具：

### 核心工具 (6个)

1. **search_literature** - 统一多源文献搜索
2. **get_article_details** - 统一文献详情获取
3. **get_references** - 参考文献获取
4. **get_literature_relations** - 文献关系分析
5. **get_journal_quality** - 期刊质量评估
6. **batch_search_literature** - 批量处理工具

### 集成的数据源

- Europe PMC
- PubMed
- arXiv
- CrossRef
- OpenAlex

## 部署步骤

### 1. 安装依赖

```bash
# 使用uv (推荐)
uv sync

# 或使用pip
pip install -e .
```

### 2. MCP客户端配置

#### Claude Desktop配置示例

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

#### Cherry Studio配置示例

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server", "--transport", "stdio"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. 启动服务器

```bash
# 标准启动 (stdio模式，推荐)
uvx article-mcp server

# 本地开发
uv run main.py server

# SSE模式 (用于Web客户端)
uv run main.py server --transport sse --host 0.0.0.0 --port 9000

# Streamable HTTP模式
uv run main.py server --transport streamable-http --host 0.0.0.0 --port 9000
```

### 4. 验证部署

```bash
# 显示项目信息
uvx article-mcp info

# 运行测试
uvx article-mcp test
```

## 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `PYTHONUNBUFFERED` | 禁用Python输出缓冲 | - | 推荐 |
| `EASYSCHOLAR_SECRET_KEY` | EasyScholar API密钥 | - | 可选 |
| `CLAUDE_CONFIG_PATH` | Claude配置文件路径 | - | 可选 |

### MCP配置文件优先级

1. MCP配置文件中的密钥 (最高优先级)
2. 函数参数中的密钥
3. 环境变量中的密钥 (最低优先级)

## 工具使用示例

### 1. 文献搜索

```python
# 搜索文献
result = mcp.call_tool("search_literature", {
    "keyword": "machine learning in biology",
    "sources": ["europe_pmc", "pubmed"],
    "max_results": 10
})
```

### 2. 获取文章详情

```python
# 获取文章详情
result = mcp.call_tool("get_article_details", {
    "identifier": "10.1038/s41586-021-03819-2",
    "id_type": "doi",
    "include_quality_metrics": True
})
```

### 3. 质量评估

```python
# 期刊质量评估
result = mcp.call_tool("get_journal_quality", {
    "journal_name": "Nature",
    "include_metrics": ["impact_factor", "quartile", "jci"]
})
```

### 4. 批量处理

```python
# 批量搜索
result = mcp.call_tool("batch_search_literature", {
    "queries": ["CRISPR", "machine learning", "evolution"],
    "max_results_per_query": 5,
    "parallel": True
})
```

## 性能优化

### 缓存策略

- 24小时智能缓存
- LRU缓存机制
- 缓存命中率统计

### 并发控制

- 最大并发数限制
- 请求速率控制
- 自动重试机制

### 性能指标

- 比传统方法快30-50%
- 批量处理提升10-15倍性能
- 支持最多20个DOI同时处理

## 故障排除

### 常见问题

1. **ImportError: No module named 'fastmcp'**
   ```bash
   pip install fastmcp>=2.13.0
   ```

2. **API密钥错误**
   - 检查MCP配置文件中的密钥设置
   - 确认EasyScholar API密钥有效

3. **网络连接问题**
   - 检查防火墙设置
   - 确认代理配置

4. **性能问题**
   - 启用缓存
   - 减少并发数
   - 使用批量处理

### 日志调试

```bash
# 启用详细日志
export PYTHONUNBUFFERED=1
uv run main.py server --transport stdio
```

## 升级指南

### 从v1.x升级到v2.0

1. **备份现有配置**
   ```bash
   cp ~/.config/claude-desktop/config.json config_backup.json
   ```

2. **更新依赖**
   ```bash
   uv sync
   ```

3. **更新工具调用**
   - 旧工具: `search_europe_pmc` → 新工具: `search_literature`
   - 旧工具: `get_article_details` (保持不变)
   - 旧工具: `get_references_by_doi` → 新工具: `get_references`

4. **验证新功能**
   ```bash
   uvx article-mcp test
   ```

## 支持

- GitHub: https://github.com/gqy20/article-mcp
- Issues: https://github.com/gqy20/article-mcp/issues
- 文档: https://github.com/gqy20/article-mcp/blob/main/README.md