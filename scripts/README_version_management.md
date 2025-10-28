# 版本管理指南

## 🎯 统一版本管理方案

本项目采用 **单一权威源 + 自动同步** 的版本管理策略：

- **权威版本源**: `pyproject.toml` 中的 `version` 字段
- **同步工具**: `scripts/sync_version.py`
- **管理工具**: `uv version` 命令

## 🚀 推荐工作流

### 1. 日常版本更新

```bash
# 方法一：使用uv直接更新（推荐）
uv version --bump patch    # 补丁版本 (0.1.5 -> 0.1.6)
uv version --bump minor    # 次版本 (0.1.5 -> 0.2.0)
uv version --bump major    # 主版本 (0.1.5 -> 1.0.0)

# 方法二：手动设置特定版本
uv version 1.0.0          # 设置为 1.0.0

# 同步到所有相关文件
python scripts/sync_version.py sync
```

### 2. 检查版本一致性

```bash
# 检查所有文件版本号是否一致
python scripts/sync_version.py check

# 查看当前版本
uv version --short
```

## 📁 版本号分布

版本号会自动同步到以下文件：

- `pyproject.toml` - 权威版本源
- `src/article_mcp/__init__.py` - 包版本导出
- `src/article_mcp/cli.py` - FastMCP服务器版本
- `src/article_mcp/resources/config_resources.py` - 资源配置版本
- `tests/__init__.py` - 测试版本

## ⚠️ 注意事项

1. **永远不要手动修改** 除 `pyproject.toml` 外的版本号
2. **版本号格式**：遵循语义化版本号 (MAJOR.MINOR.PATCH)
3. **更新顺序**：先更新 `pyproject.toml`，再运行同步脚本
4. **一致性检查**：定期运行 `python scripts/sync_version.py check`

## 🔧 工具命令参考

### uv version 命令

```bash
uv version                    # 显示项目版本
uv version --short           # 只显示版本号
uv version --dry-run         # 模拟更新
uv version --bump patch      # 递增补丁版本
uv version 1.2.3            # 设置特定版本
```

### sync_version.py 脚本

```bash
python scripts/sync_version.py sync    # 同步版本号
python scripts/sync_version.py check   # 检查一致性
```

## 🎉 最佳实践

1. **开发阶段**：使用 `uv version --bump patch` 快速迭代
2. **发布阶段**：手动设置语义化版本号
3. **持续集成**：在CI/CD中加入版本一致性检查
4. **文档更新**：版本号更新后自动同步到相关文档

这样设计确保了版本号的统一管理，避免了手动维护多个文件版本号的繁琐工作。