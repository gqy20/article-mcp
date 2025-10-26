# Article MCP 测试脚本

这个目录包含了用于测试 article-mcp 项目各种功能的脚本。

## 脚本列表

### 🚀 主要测试脚本

1. **`run_all_tests.py`** - 运行所有测试的主脚本
   - 执行所有测试脚本
   - 提供完整的测试报告
   - 推荐用于完整的项目验证

2. **`quick_test.py`** - 快速测试脚本
   - 运行最重要的核心测试
   - 快速验证项目基本功能
   - 推荐用于日常快速检查

### 📋 分类测试脚本

3. **`test_basic_functionality.py`** - 基础功能测试
   - 测试包导入
   - 测试服务器创建
   - 测试模块导入
   - 测试包结构完整性

4. **`test_cli_functions.py`** - CLI功能测试
   - 测试命令行接口
   - 测试各种CLI命令
   - 测试参数处理
   - 测试环境变量

5. **`test_service_modules.py`** - 服务模块测试
   - 测试所有服务类
   - 测试服务初始化
   - 测试异步服务功能
   - 测试错误处理

6. **`test_integration.py`** - 集成测试
   - 测试完整包集成
   - 测试异步集成
   - 测试依赖注入
   - 测试工具注册

7. **`test_performance.py`** - 性能测试
   - 测试导入性能
   - 测试内存使用
   - 测试并发性能
   - 测试大数据处理

## 使用方法

### 快速开始

```bash
# 快速测试项目状态
python scripts/quick_test.py

# 运行完整测试套件
python scripts/run_all_tests.py
```

### 运行特定测试

```bash
# 运行基础功能测试
python scripts/test_basic_functionality.py

# 运行CLI功能测试
python scripts/test_cli_functions.py

# 运行服务模块测试
python scripts/test_service_modules.py

# 运行集成测试
python scripts/test_integration.py

# 运行性能测试
python scripts/test_performance.py
```

### 使用PYTHONPATH

如果遇到导入错误，可以显式设置PYTHONPATH：

```bash
PYTHONPATH=src python scripts/quick_test.py
```

## 测试说明

### ✅ 通过条件

- **基础功能测试**: 所有核心模块可以正常导入和初始化
- **CLI功能测试**: 命令行接口正常工作，包括帮助和信息显示
- **服务模块测试**: 所有服务类可以创建，基本方法存在
- **集成测试**: 各模块之间可以正确协作
- **性能测试**: 响应时间在合理范围内，内存使用正常

### ⚠️ 性能基准

- 导入时间 < 1秒
- 服务器创建时间 < 2秒
- 内存增长 < 50MB
- 异步操作 < 1秒
- 大数据处理 < 5秒

### 🔧 测试策略

1. **Mock测试**: 使用模拟对象避免实际API调用
2. **隔离测试**: 每个测试脚本独立运行
3. **超时保护**: 设置合理的超时时间
4. **错误处理**: 捕获并报告所有异常
5. **性能监控**: 监控内存使用和执行时间

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ModuleNotFoundError: No module named 'article_mcp'
   ```
   解决方案:
   ```bash
   export PYTHONPATH=src:$PYTHONPATH
   python scripts/quick_test.py
   ```

2. **超时错误**
   ```
   subprocess.TimeoutExpired
   ```
   解决方案: 检查系统性能，可能需要增加超时时间

3. **权限错误**
   ```
   Permission denied
   ```
   解决方案:
   ```bash
   chmod +x scripts/*.py
   ```

### 调试模式

如果测试失败，可以查看详细的错误信息：

```bash
# 运行单个测试查看详细输出
python scripts/test_basic_functionality.py

# 或者使用python -m 模式
python -m scripts.test_basic_functionality
```

## 持续集成

这些测试脚本适合集成到CI/CD流程中：

```yaml
# GitHub Actions 示例
- name: Run Tests
  run: |
    python scripts/quick_test.py
    python scripts/run_all_tests.py
```

## 贡献指南

在提交代码前，请确保：

1. 运行快速测试：`python scripts/quick_test.py`
2. 运行完整测试：`python scripts/run_all_tests.py`
3. 所有测试都应该通过
4. 性能测试结果应该在合理范围内

## 更新日志

- v1.0.0 - 初始版本，包含所有基本测试功能
- v1.1.0 - 添加性能测试和内存监控
- v1.2.0 - 改进错误处理和报告格式