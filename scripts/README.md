# Article MCP 脚本索引

本目录只保留**不属于 pytest 测试套件**的脚本。常规开发与 CI 验证请直接用 pytest：

```bash
uv sync --extra dev

uv run pytest                      # 全量测试
uv run pytest -m "not network"     # 跳过打真实外部 API 的用例（CI 用这个）
uv run ruff check . && uv run ruff format --check .
uv run mypy src
```

## 目录内容

| 脚本 | 用途 | 何时用 |
|------|------|--------|
| `test_fastmcp_compliance.py` | FastMCP 规范合规性检查（stdio / HTTP / SSE 三档） | CI 的 smoke 作业；改动 server 初始化或传输方式后 |
| `simulate_cherry_studio.py` | 模拟 Cherry Studio 客户端发起 initialize / tools/list | 排查 MCP 客户端兼容性（stdio 握手、工具描述长度） |
| `clean_pytest_cache.py` | 清理 pytest 残留的临时目录 | 本地测试跑崩后收拾现场 |
| `manual/http_client_check.py` | 完整 HTTP 客户端脚本，需要本地先起 streamable-http 服务 | 手工验证 HTTP 传输 |
| `manual/relation_tools_check.py` | 关系分析工具的联调脚本（打真实 API） | 手工验证 `get_literature_relations` |

## 手动脚本

`manual/` 下的脚本需要额外前置条件（本地服务、真实 API），**不在 CI 中执行**，也因此被移出了 `tests/` 目录：

```bash
# 1) 先起服务
uv run article-mcp server --transport streamable-http --port 9007

# 2) 再跑客户端脚本
uv run python scripts/manual/http_client_check.py
```

## 合规性检查

```bash
uv run python scripts/test_fastmcp_compliance.py
```

会在 `scripts/fastmcp_compliance_report.txt` 生成报告（该文件已在 `.gitignore` 中），CI 校验总体得分不低于 80。
