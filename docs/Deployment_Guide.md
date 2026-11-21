# Article MCP 部署指南

## 📋 概述

本指南介绍Article MCP项目的多种部署方式，包括PyPI发布、NPM发布和魔搭MCP广场部署。

## 🏗️ 项目架构

### 6工具统一架构 (v2.0+)

Article MCP采用6工具统一架构，替代了原来分散的多个工具：

#### 核心工具 (6个)
1. **search_literature** - 统一多源文献搜索
2. **get_article_details** - 统一文献详情获取
3. **get_references** - 参考文献获取
4. **get_literature_relations** - 文献关系分析
5. **get_journal_quality** - 期刊质量评估
6. **batch_search_literature** - 批量处理工具

#### 集成的数据源
- Europe PMC
- PubMed
- arXiv
- CrossRef
- OpenAlex

## 🐍 PyPI 发布 (推荐)

### 前提条件
- Python 3.11+
- uv 包管理器
- PyPI 账号和 API Token
- 项目代码已推送到 GitHub

### 发布步骤

#### 1. 准备发布环境
```bash
# 确保uv已安装
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步项目依赖（含开发依赖，用于跑测试与合规性检查）
uv sync --extra dev

# 测试项目运行
uv run article-mcp test
```

#### 2. 构建和发布
```bash
# 构建包
uv build

# 发布到PyPI
uv publish --token pypi-xxxxx

# 或使用传统方式
python -m build
python -m twine upload dist/*
```

#### 3. 使用PyPI包
```bash
# 直接运行（推荐）
uvx article-mcp server

# 或安装后运行
pip install article-mcp
article-mcp server

# 本地测试
uvx --from . article-mcp server
```

### PyPI配置示例

#### Claude Desktop配置
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

#### Cherry Studio配置
```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": [
        "article-mcp",
        "server",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## 📦 NPM 发布 (备选)

### 前提条件
- Node.js 16+
- npm 账号
- 项目代码已推送到GitHub

### NPM包结构
需要创建JavaScript包装器来调用Python包。

### 发布步骤
```bash
# 构建NPM包
npm run build

# 发布到NPM
npm publish

# 使用NPM包
npx @gqy20/article-mcp-wrapper server
```

## 🌐 魔搭MCP广场部署

### 部署要求分析

根据[魔搭官方文档](https://modelscope.cn/headlines/article/1439)，**核心约束**：

> **当前只有command字段键值为npx和uvx的服务配置能够成功通过自动化检测**

这意味着使用 `uv run` 的配置**无法通过检测**！

### 解决方案

#### 🥇 方案1：PyPI + uvx (强烈推荐)
- **发布平台**: PyPI (Python Package Index)
- **包名**: `article-mcp`
- **运行命令**: `uvx article-mcp@latest server`
- **优势**: 原生Python包，性能最佳

#### 🥈 方案2：NPM + npx (备选)
- **发布平台**: NPM (Node Package Manager)
- **包名**: `@gqy20/article-mcp-wrapper`
- **运行命令**: `npx @gqy20/article-mcp-wrapper@latest server`
- **优势**: 兼容性强，NPM生态成熟

### 魔搭配置示例

#### uvx配置 (推荐)
```json
{
  "name": "article-mcp",
  "version": "1.0.0",
  "description": "学术文献搜索MCP服务器",
  "author": "gqy20",
  "license": "MIT",
  "command": "uvx",
  "args": [
    "article-mcp@latest",
    "server"
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  },
  "tags": [
    "mcp",
    "literature",
    "academic",
    "search"
  ],
  "repository": "https://github.com/gqy20/article-mcp",
  "homepage": "https://github.com/gqy20/article-mcp"
}
```

#### npx配置 (备选)
```json
{
  "name": "article-mcp",
  "version": "1.0.0",
  "description": "学术文献搜索MCP服务器",
  "author": "gqy20",
  "license": "MIT",
  "command": "npx",
  "args": [
    "@gqy20/article-mcp-wrapper@latest",
    "server"
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  },
  "tags": [
    "mcp",
    "literature",
    "academic",
    "search"
  ],
  "repository": "https://github.com/gqy20/article-mcp",
  "homepage": "https://github.com/gqy20/article-mcp"
}
```

## 🚀 本地开发部署

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/gqy20/article-mcp.git
cd article-mcp

# 安装依赖
uv sync --extra dev

# 运行服务器
uv run python -m article_mcp server

# 不同传输模式
uv run python -m article_mcp server --transport stdio
uv run python -m article_mcp server --transport sse --host 0.0.0.0 --port 9000
uv run python -m article_mcp server --transport streamable-http --host 0.0.0.0 --port 9000
```

### 开发配置

#### Claude Desktop开发配置
```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/article-mcp",
        "python",
        "-m",
        "article_mcp",
        "server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "EASYSCHOLAR_SECRET_KEY": "your_dev_key_here"
      }
    }
  }
}
```

## 🔧 配置管理

### 环境变量
```bash
export PYTHONUNBUFFERED=1     # 禁用Python输出缓冲
export UV_LINK_MODE=copy      # uv链接模式(可选)
export EASYSCHOLAR_SECRET_KEY=your_secret_key  # EasyScholar API密钥(可选)
```

### MCP配置集成 (v0.1.1+)

项目支持从MCP客户端配置文件中读取EasyScholar API密钥：

#### 配置优先级
1. **MCP配置文件**中的密钥（最高优先级）
2. **函数参数**中的密钥
3. **环境变量**中的密钥

#### 支持的配置路径
- `~/.config/claude-desktop/config.json`
- `~/.config/claude/config.json`
- `~/.claude/config.json`

## 📋 部署检查清单

### 发布前检查
- [ ] 项目代码已推送到GitHub
- [ ] 版本号已更新（语义化版本）
- [ ] CHANGELOG.md已更新
- [ ] 所有测试通过
- [ ] 文档示例已验证

### PyPI发布检查
- [ ] PyPI账号已配置
- [ ] API Token有效
- [ ] 包名可用
- [ ] 构建成功

### 魔搭部署检查
- [ ] 使用uvx命令（非uv run）
- [ ] 包名正确
- [ ] 标签准确
- [ ] 环境变量配置正确

## 🔄 版本管理

### 语义化版本控制
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 发布流程
1. 更新版本号（`pyproject.toml`）
2. 更新CHANGELOG.md
3. 运行完整测试套件
4. 构建包
5. 发布到平台
6. 更新文档

## 🐛 故障排除

### 常见问题

#### PyPI发布问题
- **错误**: `403 Forbidden`
  - **解决**: 检查PyPI API Token是否有效

- **错误**: `包名已存在`
  - **解决**: 使用不同的包名或联系包的所有者

#### 魔搭部署问题
- **错误**: `自动化检测失败`
  - **解决**: 确保使用`uvx`而非`uv run`

- **错误**: `命令无法执行`
  - **解决**: 检查包名和版本是否正确

#### 配置问题
- **错误**: `EASYSCHOLAR_SECRET_KEY not found`
  - **解决**: 检查MCP配置文件或环境变量

- **错误**: `模块导入失败`
  - **解决**: 检查Python版本和依赖安装

### 调试技巧

#### 启用详细日志
```bash
# 设置详细日志
export PYTHONUNBUFFERED=1
uv run python -m article_mcp server --log-level DEBUG
```

#### 测试配置
```bash
# 测试MCP服务器
uv run python -m article_mcp test

# 检查配置
uv run python -m article_mcp info
```

## 📞 支持和资源

### 官方资源
- **GitHub仓库**: https://github.com/gqy20/article-mcp
- **PyPI包**: https://pypi.org/project/article-mcp/
- **问题反馈**: https://github.com/gqy20/article-mcp/issues

### 社区资源
- **文档**: 查看README和源代码注释
- **讨论**: GitHub Discussions
- **魔搭广场**: ModelScope MCP广场

---

**最后更新**: 2025-10-27
**维护者**: Claude Code
**支持平台**: PyPI, NPM, 魔搭MCP广场
