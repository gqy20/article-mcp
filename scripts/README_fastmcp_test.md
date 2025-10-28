# FastMCP规范合规性测试工具

## 概述

`test_fastmcp_compliance.py` 是一个专门用于验证Article MCP服务器是否符合FastMCP规范的测试工具。该脚本会测试不同传输模式（STDIO、HTTP、SSE）下的MCP规范符合性。

## 测试内容

### 🔍 核心测试项目

#### 1. STDIO模式测试
- **服务器创建**：验证MCP服务器能正常创建
- **工具注册**：检查所有6个核心工具是否正确注册
- **工具元数据**：验证工具的annotations和tags是否符合规范
- **资源访问**：测试配置和期刊资源的可访问性
- **错误处理**：验证错误处理中间件的工作状态
- **响应格式**：检查响应格式标准化程度
- **annotations类型**：确认使用ToolAnnotations类型

#### 2. HTTP模式测试
- **服务器启动**：验证HTTP服务器能正常启动
- **HTTP传输**：测试HTTP传输的稳定性
- **工具访问**：通过HTTP客户端访问工具
- **资源访问**：通过HTTP客户端访问资源
- **错误处理**：验证HTTP模式下的错误处理

#### 3. SSE模式测试
- **服务器启动**：验证SSE服务器能正常启动
- **SSE传输**：测试SSE传输的稳定性
- **基本功能**：验证SSE模式下的基本功能

## 使用方法

### 基本用法

```bash
# 进入scripts目录
cd scripts

# 运行FastMCP合规性测试
uv run python test_fastmcp_compliance.py
```

### 高级用法

```bash
# 查看详细输出
uv run python test_fastmcp_compliance.py

# 测试特定模式（可扩展）
uv run python test_fastmcp_compliance.py --mode stdio
uv run python test_fastmcp_compliance.py --mode http
uv run python test_fastmcp_compliance.py --mode sse
```

## 测试标准

### 📊 评分标准

- **90-100分**：优秀 - 项目完全符合FastMCP规范
- **80-89分**：良好 - 项目基本符合FastMCP规范
- **60-79分**：合格 - 项目部分符合FastMCP规范
- **0-59分**：不合格 - 项目不符合FastMCP规范

### ✅ 必须通过的测试

1. **服务器创建** - 所有传输模式下都必须能正常创建服务器
2. **工具注册** - 所有6个核心工具都必须正确注册
3. **元数据规范** - 工具必须使用ToolAnnotations类型
4. **错误处理** - 必须有适当的错误处理机制

## 测试报告

测试完成后会生成详细的报告，包括：

- 📊 各传输模式的合规性得分
- ✅/❌ 每个测试项目的通过状态
- 📋 具体的改进建议
- 📄 报告文件（`fastmcp_compliance_report.txt`）

### 报告示例

```
🧪 FastMCP规范合规性测试报告
============================================================

📡 STDIO 传输模式
   状态: ✅ 通过
   得分: 95/100

   测试详情:
     ✅ server_creation
     ✅ tool_registration
     ✅ tool_metadata
     ✅ error_handling
     ✅ resource_access
     ✅ response_format
     ✅ annotations

📡 HTTP 传输模式
   状态: ✅ 通过
   得分: 85/100

   测试详情:
     ✅ server_startup
     ✅ http_transport
     ✅ tool_access
     ✅ resource_access
     ✅ error_handling

📊 总体合规性得分: 90/100

🎉 优秀！项目完全符合FastMCP规范
```

## 故障排除

### 常见问题

#### 1. 导入错误
```
❌ 导入失败: No module named 'fastmcp'
```
**解决方案**：
```bash
pip install fastmcp
```

#### 2. 端口冲突
```
❌ HTTP服务器启动失败
Address already in use
```
**解决方案**：
- 修改脚本中的端口号（9001、9002）
- 停止占用端口的进程

#### 3. 服务器启动超时
```
❌ HTTP服务器启动失败
```
**解决方案**：
- 检查服务器启动日志
- 增加等待时间
- 确保没有其他服务占用端口

### 调试模式

如果测试失败，可以查看详细日志：

```bash
# 启用详细日志
uv run python test_fastmcp_compliance.py

# 手动测试STDIO模式
uv run python -m article_mcp test
```

## 扩展测试

### 自定义测试

可以通过修改 `FastMCPComplianceTester` 类来添加自定义测试：

```python
class CustomComplianceTester(FastMCPComplianceTester):
    async def test_custom_feature(self):
        """自定义功能测试"""
        # 添加你的测试逻辑
        pass

    async def run_custom_tests(self):
        """运行自定义测试"""
        await self.test_custom_feature()
```

### 环境变量配置

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 设置测试超时
export TEST_TIMEOUT=30
```

## 技术细节

### 依赖要求

- Python 3.10+
- fastmcp
- article-mcp（本地开发版本）

### 测试架构

1. **异步测试**：使用asyncio进行异步测试
2. **多进程测试**：每个传输模式在独立进程中测试
3. **超时处理**：防止测试卡死
4. **错误恢复**：测试失败时正确清理资源

### 安全考虑

- 测试进程会自动清理，不会留下僵尸进程
- 使用本地端口避免网络冲突
- 测试数据不会影响生产环境

## 集成到CI/CD

### GitHub Actions示例

```yaml
name: FastMCP Compliance Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install fastmcp
        pip install -e .
    - name: Run compliance tests
      run: |
        cd scripts
        uv run python test_fastmcp_compliance.py
    - name: Upload test report
      uses: actions/upload-artifact@v3
      with:
        name: compliance-report
        path: scripts/fastmcp_compliance_report.txt
```

## 贡献指南

如果你发现了测试问题或有改进建议：

1. **问题报告**：创建issue描述具体问题
2. **改进建议**：提交PR描述改进方案
3. **新测试**：添加新的测试用例

### 提交PR时

确保：
- [ ] 新代码通过所有合规性测试
- [ ] 测试覆盖率不降低
- [ ] 更新相关文档

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- 📧 GitHub Issues
- 📧 项目维护者
- 📧 FastMCP社区

**注意**：本测试工具专门针对FastMCP规范设计，确保项目符合MCP协议标准。