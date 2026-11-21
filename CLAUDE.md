# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Article MCP is a high-performance literature search server based on FastMCP framework that integrates multiple academic databases including Europe PMC, arXiv, PubMed, CrossRef, and OpenAlex. It provides comprehensive literature search, reference management, and quality evaluation tools for academic research.

## Architecture

The project follows a standard Python src layout with layered architecture:

- **CLI Layer** (`cli.py`): Main CLI entry point and MCP server creation via `create_mcp_server()`
- **Tool Layer** (`tools/core/`): 5 core MCP tool registrations
- **Service Layer** (`services/`): API integrations using dependency injection pattern
- **Middleware Layer** (`middleware/`): Error handling, logging, and performance monitoring
- **Resource Layer** (`resources/`): MCP resources for config and journal data
- **Entry Points** (`__main__.py`): `python -m article_mcp` 入口，转发到 `cli.py`

### The 5 Core Tools

All tools are registered in `cli.py:create_mcp_server()` with their respective service dependencies:

1. **search_literature** (`tools/core/search_tools.py`): Multi-source literature search
2. **get_article_details** (`tools/core/article_tools.py`): Article details by identifier
3. **get_references** (`tools/core/reference_tools.py`): Reference list retrieval
4. **get_literature_relations** (`tools/core/relation_tools.py`): Citation relationship analysis
5. **get_journal_quality** (`tools/core/quality_tools.py`): Journal quality assessment

Note: The test file `test_six_tools.py` is a legacy name - it tests these 5 core tools.

### Service Injection Pattern

Services are created in `create_mcp_server()` and passed to tool registrars:
```python
pubmed_service = create_pubmed_service(logger)
europe_pmc_service = create_europe_pmc_service(logger, pubmed_service)
# ... other services
register_search_tools(mcp, {"europe_pmc": europe_pmc_service, ...}, logger)
```

### Middleware System

Three middlewares are added to the MCP server in `create_mcp_server()`:

- **MCPErrorHandlingMiddleware** (`middleware/`): Converts exceptions to MCP standard errors
- **LoggingMiddleware** (`middleware/logging.py`): Request/response logging
- **TimingMiddleware** (`middleware/logging.py`): Performance stats collection

Access global performance stats via `middleware.get_global_performance_stats()`.

## Development Commands

### Environment Setup
```bash
# Install dependencies (Python 3.11+)
uv sync --extra dev

# Or using pip
pip install "fastmcp>=4.2.4" requests python-dateutil urllib3 aiohttp markdownify filelock
```

### Running the Server
```bash
# Production (recommended)
uvx article-mcp server

# Local development - using new CLI
uv run python -m article_mcp server

# Alternative transport modes
uv run python -m article_mcp server --transport stdio
uv run python -m article_mcp server --transport sse --host 0.0.0.0 --port 9000
uv run python -m article_mcp server --transport streamable-http --host 0.0.0.0 --port 9000
```

### Testing
```bash
# 全量测试
uv run pytest

# 跳过打真实外部 API 的用例（CI 用的就是这个）
uv run pytest -m "not network"

# 只跑单元测试
uv run pytest tests/unit/

# 单个用例
uv run pytest tests/unit/test_six_tools.py -k test_all_tools_registered
```

### Quality Checks
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src          # 类型检查（CI 与 pre-commit 都会跑）
uv run python scripts/test_fastmcp_compliance.py   # FastMCP 合规性（CI smoke 作业）
```

> `scripts/` 下只保留不属于测试套件的辅助脚本（合规性检查、客户端兼容性模拟、清理工具），
> 索引见 `scripts/README.md`。
pytest tests/unit/        # Unit tests only
pytest -m integration     # Integration tests only
pytest -m "not slow"      # Exclude slow tests
pytest tests/unit/test_six_tools.py  # Test all 5 core tools (legacy filename)
```

### Code Quality
```bash
# Format code (Ruff formatter - 100x faster than black)
uv run ruff format .

# Lint (Ruff linter - replaces flake8, isort)
uv run ruff check .
uv run ruff check . --fix  # Auto-fix issues

# Type checking
uv run mypy src

# All quality checks
uv run ruff check . && uv run ruff format --check . && uv run mypy src

# Pre-commit hooks (install)
uv run pre-commit install
```

> ruff 0.17 起会一并格式化 Markdown 里的 Python 代码块，因此 `ruff format .` 与
> CI 的 `ruff format --check .` 覆盖范围一致（含 `docs/`）。

### Package Management
```bash
python -m build           # Build package
uvx --from . article-mcp server  # Install from local
uvx article-mcp server      # Test PyPI package
```

## Key Development Patterns

### TDD Approach

New features should be implemented using TDD methodology:
1. Write test file first in `tests/unit/`
2. Implement feature to pass tests
3. Example: `OpenAlexMetricsService` was implemented with `test_openalex_metrics_service.py` (15 tests)

### Caching Strategy

The project implements intelligent caching with 24-hour expiry:
- Cache file: `.cache/journal_quality/journal_data.json` (unified cache)
- OpenAlex and EasyScholar share the same cache file with merged data structure:
  ```json
  {
    "journals": {
      "Nature": {
        "data": {...},           // EasyScholar data
        "openalex_metrics": {...}, // OpenAlex metrics
        "timestamp": 1234567890.0
      }
    }
  }
  ```
- Cache hit information is included in response metadata
- Performance gains: 30-50% faster than traditional methods

### Rate Limiting
Different APIs have different rate limits:
- Europe PMC: 1 request/second (conservative)
- Crossref: 50 requests/second (with email)
- arXiv: 3 seconds/request (official limit)
- OpenAlex: No rate limit (polite usage recommended)

### Error Handling
Comprehensive error handling via middleware:
- `MCPErrorHandlingMiddleware` converts exceptions to MCP standard errors
- User input errors become `ToolError` with friendly messages
- System errors become `McpError` with error codes

### Async Patterns

The codebase is transitioning to async/await patterns:
- Services use `async def` methods with `aiohttp` for HTTP requests
- Tool functions are declared `async` and FastMCP handles the event loop
- Some services still have sync methods for backward compatibility
- `_batch_literature_relations` in `relation_tools.py` is fully async
- Tests use `pytest.mark.asyncio` and `AsyncMock`

## Configuration

### Environment Variables
```bash
PYTHONUNBUFFERED=1       # Disable Python output buffering
PYTHONIOENCODING=utf-8   # Required for Cherry Studio Unicode support
EASYSCHOLAR_SECRET_KEY=your_secret_key  # Optional: for journal quality tools
```

### MCP Client Configuration

**PyPI package (recommended):**
```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
        "EASYSCHOLAR_SECRET_KEY": "your_key_here"
      }
    }
  }
}
```

**Local development:**
```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/article-mcp", "python", "-m", "article_mcp", "server"],
      "env": {"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
    }
  }
}
```

**Configuration paths searched:** `~/.config/claude-desktop/config.json`, `~/.config/claude/config.json`, `~/.claude/config.json`

**Key priority:** MCP config > function parameter > environment variable

## Critical Implementation Details

### OpenAlex Integration

OpenAlex provides free metrics that complement EasyScholar:
- Service: `OpenAlexMetricsService` in `services/openalex_metrics_service.py`
- API: `https://api.openalex.org/sources`
- Metrics: `h_index`, `citation_rate`, `cited_by_count`, `works_count`, `i10_index`
- Integrated into both single and batch journal quality queries
- Cache merging is handled in `_save_to_file_cache()` and `_get_from_file_cache()` in `quality_tools.py`

### Quality Tools Architecture

`tools/core/quality_tools.py` is the single source of truth for journal quality:
- EasyScholar provides: `impact_factor`, `quartile`, `jci`, `cas_zone` variants
- OpenAlex provides: `h_index`, `citation_rate`, `cited_by_count`, `works_count`, `i10_index`
- Reserved metrics (not available): `acceptance_rate`, `eigenfactor`, `sjr`, `snip`
- Cache is at `.cache/journal_quality/journal_data.json`
- Deprecated `get_journal_quality()` in `pubmed_search.py` - use quality_tools instead

### Relation Tools Async Refactoring

`tools/core/relation_tools.py` has been partially refactored to async:
- Single literature analysis: `_single_literature_relations()` (sync)
- Batch literature analysis: `_batch_literature_relations()` (async)
- Network analysis: `_analyze_literature_network()` (async)
- When modifying, prefer async patterns for new code

### Tool Registration Pattern

All tools follow the registration pattern in `cli.py`:
```python
def register_X_tools(mcp: FastMCP, services: dict[str, Any], logger: Any) -> None:
    @mcp.tool(description="...")
    async def tool_function(...) -> dict[str, Any]:
        # Implementation
```

### Ruff Toolchain

The project has migrated from black+isort+flake8 to pure Ruff:
- Formatter: `ruff format` (replaces `black`)
- Linter: `ruff check` (replaces `flake8`, `isort`)
- Config in `.pre-commit-config.yaml` and `pyproject.toml [tool.ruff]`
- MyPy is still used for type checking
