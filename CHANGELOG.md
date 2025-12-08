# 版本更新说明

## v0.1.9

### 修复问题
- **Cherry Studio等客户端emoji编码兼容性问题修复** (closes #4)
  - 添加PYTHONIOENCODING=utf-8环境变量设置，确保Unicode字符正确处理
  - 实现safe_print函数处理编码异常，提供编码安全的输出机制
  - 将CLI启动信息中的emoji替换为文本标识符，避免编码冲突
  - 修复在Cherry Studio中mcp:list-tools调用失败的问题

### 新增功能
- **Glama MCP服务器目录徽章**
  - 添加来自PR #3的MCP服务器徽章，提升项目在MCP生态系统中的可见性
  - 徽章链接到Glama MCP服务器目录，提供额外的质量认证和服务器特性展示

### 改进
- **项目许可证文件添加**
  - 添加标准MIT许可证文件，确保符合GitHub开源项目要求
  - 提供清晰的法律条款和使用权限
  - 符合开源社区最佳实践

### 测试验证
- HTTP模式服务器成功启动并响应MCP协议调用
- 文献搜索功能正常工作（测试了"泛基因组"和"pan-genome"搜索）
- 与Cherry Studio等AI客户端完全兼容

### 文档更新
- 为所有客户端配置示例添加PYTHONIOENCODING=utf-8环境变量说明
- 添加Cherry Studio专用的重要提示和编码兼容性说明

## v0.1.1

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