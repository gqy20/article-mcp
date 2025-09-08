# Cherry Studio 配置指南

## 问题诊断

如果你遇到以下错误：
```
Connectivity check failed for europe-pmc-reference: Error: Error invoking remote method 'mcp:check-connectivity': TypeError: Cannot read properties of undefined (reading 'getServerKey')
```

这通常是配置文件或依赖项问题导致的。

## 解决方案

### 1. 首先修复代码问题
确保 `main.py` 已经修复了 `List` 类型导入问题（已自动修复）。

### 2. 配置文件选项

我提供了三个配置文件供你选择：

#### 方案 1：使用 `mcp_config.json`（推荐）
```json
{
  "mcpServers": {
    "europe-pmc-reference": {
      "command": "uv",
      "args": [
        "--directory",
        "D:\\C\\Documents\\Program\\Python_file\\mcp_serve\\mcp1",
        "run",
        "main.py",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "UV_LINK_MODE": "copy"
      }
    }
  }
}
```

#### 方案 2：使用 `mcp_config_cherry_studio.json`
```json
{
  "mcpServers": {
    "europe-pmc-reference": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:\\C\\Documents\\Program\\Python_file\\mcp_serve\\mcp1",
        "main.py",
        "server",
        "--transport",
        "stdio"
      ],
      "cwd": "D:\\C\\Documents\\Program\\Python_file\\mcp_serve\\mcp1",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "UV_LINK_MODE": "copy",
        "PATH": "%PATH%"
      }
    }
  }
}
```

#### 方案 3：使用 `mcp_config_simple.json`（简单版本）
```json
{
  "mcpServers": {
    "europe-pmc-reference": {
      "command": "python",
      "args": [
        "main.py",
        "server"
      ],
      "cwd": "D:\\C\\Documents\\Program\\Python_file\\mcp_serve\\mcp1",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. 测试步骤

在使用Cherry Studio之前，先在命令行中测试：

1. 打开PowerShell或命令提示符
2. 导航到项目目录：
   ```
   cd "D:\C\Documents\Program\Python_file\mcp_serve\mcp1"
   ```

3. 测试服务器是否能正常启动：
   ```
   uv run main.py test
   ```

4. 如果测试成功，尝试启动服务器：
   ```
   uv run main.py server
   ```

### 4. Cherry Studio 配置

1. 打开 Cherry Studio
2. 进入设置/配置
3. 找到 MCP 服务器配置选项
4. 粘贴以上配置文件之一
5. 保存并重启 Cherry Studio

### 5. 常见问题解决

#### 问题1：路径问题
- 确保路径中使用双反斜杠 `\\` 而不是单正斜杠 `/`
- 确保路径真实存在

#### 问题2：UV 命令找不到
- 确保已安装 UV：`pip install uv`
- 或者使用方案3（直接使用Python）

#### 问题3：Python 环境问题
- 确保Python环境中安装了所有依赖
- 运行 `uv sync` 同步依赖

### 6. 验证配置

配置成功后，你应该能在Cherry Studio中看到以下8个工具：

1. `search_europe_pmc` - 搜索文献（同步版本）
2. `search_europe_pmc_async` - 搜索文献（异步高性能版本）
3. `get_article_details` - 获取文献详情（同步版本）
4. `get_article_details_async` - 获取文献详情（异步版本）
5. `get_references_by_doi` - 获取参考文献（同步版本）
6. `get_references_by_doi_async` - 获取参考文献（异步版本）
7. `get_references_by_doi_batch_optimized` - 批量优化参考文献获取
8. `batch_enrich_references_by_dois` - 批量DOI处理（最新添加）

### 7. 如果仍然有问题

如果仍然遇到连接问题，请检查：
- Cherry Studio 的日志文件
- 确保防火墙不阻止连接
- 尝试重启 Cherry Studio
- 检查是否有其他MCP服务器冲突

建议按顺序尝试三个配置文件，通常 `mcp_config.json` 应该能正常工作。 