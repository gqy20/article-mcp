# Article MCP 测试脚本使用指南

## 📋 概述

本目录包含了用于测试 article-mcp 项目各种功能的脚本。这些脚本可以帮助你验证项目的完整性、功能和性能。

## 🚀 快速开始

### 最简单的测试
```bash
# 测试核心工作功能（推荐日常使用）
uv run python scripts/test_working_functions.py
```

### 完整测试套件
```bash
# 运行所有测试（耗时较长）
uv run python scripts/run_all_tests.py
```

## 📁 测试脚本详细说明

### 1. 核心功能测试

#### `test_working_functions.py` ⭐ 推荐
- **用途**: 测试已知可以工作的核心功能
- **特点**: 快速、可靠、专注于最重要的功能
- **耗时**: ~1秒
- **适用场景**: 日常开发检查、CI/CD快速验证

```bash
uv run python scripts/test_working_functions.py
```

**测试内容**:
- ✅ 包导入功能
- ✅ CLI show_info功能
- ✅ 包结构完整性
- ✅ Europe PMC服务
- ✅ 基本CLI命令
- ✅ 版本信息

### 2. 分类测试脚本

#### `test_basic_functionality.py`
- **用途**: 测试基础功能
- **特点**: 全面的基础测试
- **耗时**: ~5-10秒

#### `test_cli_functions.py`
- **用途**: 测试CLI功能
- **特点**: 命令行接口专项测试
- **耗时**: ~10-15秒

#### `test_service_modules.py`
- **用途**: 测试服务模块
- **特点**: 包含异步测试
- **耗时**: ~15-20秒

#### `test_integration.py`
- **用途**: 测试集成功能
- **特点**: 模块间协作测试
- **耗时**: ~20-30秒

#### `test_performance.py`
- **用途**: 测试性能指标
- **特点**: 内存和性能监控
- **耗时**: ~30-60秒

#### `test_fastmcp_compliance.py`
- **用途**: FastMCP规范合规性测试
- **特点**: 验证不同传输模式下的MCP规范符合性
- **耗时**: ~60-120秒

### 3. 综合测试脚本

#### `run_all_tests.py`
- **用途**: 运行所有测试
- **特点**: 最全面的测试覆盖
- **耗时**: ~2-5分钟

#### `quick_test.py`
- **用途**: 快速检查（部分功能可能有问题）
- **状态**: 部分功能需要修复
- **建议**: 使用 `test_working_functions.py` 替代

### 4. 架构测试脚本

#### `test_architecture_fixes.py`
- **用途**: 测试架构修复效果
- **特点**: 验证新的包结构

#### `test_module_imports.py`
- **用途**: 测试模块导入
- **特点**: 验证包导入的正确性

#### `test_simple_imports.py`
- **用途**: 简单导入测试
- **特点**: 快速验证基本导入功能

## 🛠️ 使用建议

### 日常开发
```bash
# 快速检查核心功能
uv run python scripts/test_working_functions.py
```

### 代码提交前
```bash
# 运行工作功能测试
uv run python scripts/test_working_functions.py

# 如果有更多时间，运行基础功能测试
uv run python scripts/test_basic_functionality.py
```

### 发布前验证
```bash
# 运行完整测试套件
uv run python scripts/run_all_tests.py
```

### 故障排除
```bash
# 如果遇到问题，先测试最基础的功能
uv run python scripts/test_working_functions.py

# 然后逐个运行分类测试
uv run python scripts/test_basic_functionality.py
uv run python scripts/test_cli_functions.py
```

## 📊 测试结果解读

### 成功标准
- ✅ **工作功能测试**: 6/6 通过表示核心功能正常
- ✅ **基础功能测试**: 大部分通过表示基本结构正常
- ✅ **完整测试**: 所有测试通过表示项目完全正常

### 常见问题
1. **导入错误**: 确保在项目根目录运行脚本
2. **超时错误**: 系统性能问题或网络问题
3. **部分失败**: 某些服务模块可能依赖问题，但核心功能仍可用

## 🔧 FastMCP合规性测试

### 概述

`test_fastmcp_compliance.py` 是一个专门用于验证Article MCP服务器是否符合FastMCP规范的测试工具。该脚本会测试不同传输模式（STDIO、HTTP、SSE）下的MCP规范符合性。

### 测试内容

#### 🔍 核心测试项目

1. **STDIO模式测试**
   - 服务器创建验证
   - 工具注册检查（6个核心工具）
   - 工具元数据验证
   - 资源访问测试
   - 错误处理验证
   - 响应格式检查

2. **HTTP模式测试**
   - HTTP服务器启动
   - HTTP传输稳定性
   - 工具访问验证
   - 资源访问测试

3. **SSE模式测试**
   - SSE服务器启动
   - SSE传输稳定性
   - 基本功能验证

### 使用方法

```bash
# 运行FastMCP合规性测试
uv run python scripts/test_fastmcp_compliance.py
```

### 评分标准

- **90-100分**：优秀 - 项目完全符合FastMCP规范
- **80-89分**：良好 - 项目基本符合FastMCP规范
- **60-79分**：合格 - 项目部分符合FastMCP规范
- **0-59分**：不合格 - 项目不符合FastMCP规范

## 🔧 高级用法

### 自定义测试环境
```bash
# 设置PYTHONPATH
export PYTHONPATH=src:$PYTHONPATH
uv run python scripts/test_working_functions.py
```

### 详细输出
```bash
# 查看详细测试输出
uv run python scripts/test_working_functions.py 2>&1 | tee test_output.log
```

## 📝 版本管理

### 统一版本管理方案

本项目采用 **单一权威源 + 自动同步** 的版本管理策略：

- **权威版本源**: `pyproject.toml` 中的 `version` 字段
- **同步工具**: `scripts/sync_version.py`
- **管理工具**: `uv version` 命令

### 日常版本更新

```bash
# 使用uv直接更新（推荐）
uv version --bump patch    # 补丁版本 (0.1.5 -> 0.1.6)
uv version --bump minor    # 次版本 (0.1.5 -> 0.2.0)
uv version --bump major    # 主版本 (0.1.5 -> 1.0.0)

# 同步到所有相关文件
uv run python scripts/sync_version.py sync
```

### 检查版本一致性

```bash
# 检查所有文件版本号是否一致
uv run python scripts/sync_version.py check
```

## 🤝 贡献

欢迎贡献新的测试脚本或改进现有脚本：

1. 确保测试脚本的可靠性
2. 添加适当的文档
3. 遵循现有代码风格
4. 测试在多种环境下的兼容性

## 📞 支持

如果遇到问题：

1. 首先运行 `uv run python scripts/test_working_functions.py`
2. 查看具体的错误信息
3. 检查Python环境和依赖
4. 确保在项目根目录运行脚本

---

**注意**: 随着项目的发展，某些测试可能需要更新。建议定期检查测试脚本的有效性。
