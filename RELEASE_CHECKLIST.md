# 发布检查清单 v0.1.1

## 发布前检查

### 1. 版本信息
- [x] pyproject.toml 版本已更新为 0.1.1
- [x] README.md 已更新说明新功能
- [x] CLAUDE.md 已更新配置集成说明
- [x] CHANGELOG.md 已创建

### 2. 功能测试
- [x] MCP 配置加载功能正常
- [x] 密钥优先级正确 (MCP配置 > 参数 > 环境变量)
- [x] 质量评估工具功能正常
- [x] 向后兼容性测试通过

### 3. 代码质量
- [x] 新增代码符合项目规范
- [x] 没有新增的 MCP 工具，保持简洁
- [x] 配置管理模块设计合理

### 4. 文档更新
- [x] README.md 添加了 MCP 配置集成说明
- [x] 创建了详细的使用指南
- [x] 更新了 CLAUDE.md 开发文档

## 发布步骤

### 1. 创建版本标签
```bash
git tag v0.1.1
git push origin v0.1.1
```

### 2. 验证 GitHub Actions
- [ ] 检查 https://github.com/gqy20/article-mcp/actions
- [ ] 确认构建流程正常
- [ ] 确认 PyPI 发布成功

### 3. 发布后验证
- [ ] 测试 PyPI 包安装: `pip install article-mcp==0.1.1`
- [ ] 测试 uvx 运行: `uvx article-mcp info`
- [ ] 验证新功能正常工作

## 新功能说明

### MCP 配置集成
- 用户现在可以在 Claude Desktop 配置文件中设置 EasyScholar 密钥
- 无需再通过环境变量传递，使用更方便
- 支持多种配置文件路径自动查找

### 配置示例
```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "EASYSCHOLAR_SECRET_KEY": "your_key_here"
      }
    }
  }
}
```

## 注意事项

1. **向后兼容**: 保持了所有原有功能和API不变
2. **配置优先级**: MCP配置 > 函数参数 > 环境变量
3. **安全性**: 配置文件权限需要正确设置
4. **文档**: 已更新所有相关文档