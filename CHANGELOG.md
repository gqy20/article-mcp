# 版本更新说明

## v0.1.1

### 新增功能

#### MCP 配置集成
- 新增从 MCP 客户端配置文件中读取 EasyScholar API 密钥的功能
- 支持配置优先级：MCP配置文件 > 函数参数 > 环境变量
- 支持多个配置文件路径自动查找

#### 支持的配置文件路径
- `~/.config/claude-desktop/config.json`
- `~/.config/claude/config.json`
- `~/.claude/config.json`
- `CLAUDE_CONFIG_PATH` 环境变量指定的路径

#### 配置示例
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

### 支持的工具
- `get_journal_quality` - 获取期刊质量评估信息
- `evaluate_articles_quality` - 批量评估文献的期刊质量

### 向后兼容性
- 完全兼容原有的环境变量配置方式
- 完全兼容原有的函数参数传递方式
- 保持了所有原有功能不变

### 技术改进
- 新增 `src/mcp_config.py` 配置管理模块
- 更新了质量评估工具的密钥获取逻辑
- 优化了配置读取性能和缓存机制

### 文档更新
- 更新了 README.md，添加了 MCP 配置集成说明
- 更新了 CLAUDE.md，添加了配置管理说明
- 新增了 `docs/MCP_CONFIG_INTEGRATION.md` 详细使用指南

### 测试
- 新增了完整的配置集成测试
- 测试覆盖了配置加载、优先级、工具集成等功能
- 所有测试通过，功能稳定可靠

## 发布说明

### 标签格式
- 使用语义化版本控制：`v0.1.1`
- 推送标签后自动触发 GitHub Actions 发布流程

### 发布流程
1. 代码合并到 main 分支
2. 创建并推送版本标签：`git tag v0.1.1 && git push origin v0.1.1`
3. GitHub Actions 自动构建并发布到 PyPI
4. 用户可以通过 `uvx article-mcp` 使用最新版本

### 注意事项
- 确保 `PYPI_API_TOKEN` 密钥已正确配置
- 发布前请运行完整测试确保功能正常
- 发布后请通知用户更新并说明新功能