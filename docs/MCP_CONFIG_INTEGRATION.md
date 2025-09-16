# MCP配置集成功能说明

## 功能概述

Article MCP 现在支持从 MCP 客户端配置文件中读取 EasyScholar API 密钥，无需通过环境变量传递。

## 配置方法

### Claude Desktop 配置

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

## 密钥优先级

1. **MCP配置文件**中的密钥（最高优先级）
2. **函数参数**中的密钥
3. **环境变量**中的密钥

## 支持的工具

以下工具现在支持从MCP配置中读取密钥：

- `get_journal_quality` - 获取期刊质量评估信息
- `evaluate_articles_quality` - 批量评估文献的期刊质量

## 配置文件路径

系统会自动查找以下位置的配置文件：

1. `~/.config/claude-desktop/config.json`
2. `~/.config/claude/config.json`
3. `~/.claude/config.json`
4. `CLAUDE_CONFIG_PATH` 环境变量指定的路径

## 使用示例

### 原有方式（仍然支持）

```json
{
  "keyword": "machine learning",
  "secret_key": "your_api_key"
}
```

### 新方式（推荐）

在 MCP 配置中设置密钥后，工具函数可以不传递密钥参数：

```json
{
  "keyword": "machine learning"
}
```

系统会自动从MCP配置中读取密钥。

## 测试配置

重启MCP客户端后，使用 `get_journal_quality` 工具测试配置是否生效：

```json
{
  "journal_name": "Nature"
}
```

如果配置正确，工具会使用MCP配置中的密钥进行期刊质量查询。