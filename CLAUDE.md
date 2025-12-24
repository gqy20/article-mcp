# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Article MCP is a high-performance literature search server based on FastMCP framework that integrates multiple academic databases including Europe PMC, arXiv, PubMed, CrossRef, and OpenAlex. It provides comprehensive literature search, reference management, and quality evaluation tools for academic research.

## Architecture

The project follows a standard Python src layout with layered architecture:

- **CLI Layer** (`cli.py`): Main CLI entry point and MCP server creation via `create_mcp_server()`
- **Tool Layer** (`tools/core/`): 6 core MCP tool registrations
- **Service Layer** (`services/`): API integrations using dependency injection pattern
- **Middleware Layer** (`middleware/`): Error handling, logging, and performance monitoring
- **Resource Layer** (`resources/`): MCP resources for config and journal data
- **Compatibility Layer** (`main.py`): Backward-compatible CLI entry point

### The 6 Core Tools

All tools are registered in `cli.py:create_mcp_server()` with their respective service dependencies:

1. **search_literature** (`tools/core/search_tools.py`): Multi-source literature search
2. **get_article_details** (`tools/core/article_tools.py`): Article details by identifier
3. **get_references** (`tools/core/reference_tools.py`): Reference list retrieval
4. **get_literature_relations** (`tools/core/relation_tools.py`): Citation relationship analysis
5. **get_journal_quality** (`tools/core/quality_tools.py`): Journal quality assessment
6. **export_batch_results** (`tools/core/batch_tools.py`): Batch result export

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
# Install dependencies
uv sync

# Or using pip
pip install fastmcp requests python-dateutil aiohttp markdownify
```

### Running the Server
```bash
# Production (recommended)
uvx article-mcp server

# Local development - using new CLI
uv run python -m article_mcp server

# Compatibility through main.py (still works)
uv run main.py server

# Alternative transport modes
uv run python -m article_mcp server --transport stdio
uv run python -m article_mcp server --transport sse --host 0.0.0.0 --port 9000
uv run python -m article_mcp server --transport streamable-http --host 0.0.0.0 --port 9000
```

### Testing
```bash
# Core functionality (recommended for daily use)
uv run python scripts/test_working_functions.py

# Quick validation
uv run python scripts/quick_test.py

# Complete test suite
uv run python scripts/run_all_tests.py

# Individual tests
uv run python scripts/test_basic_functionality.py
uv run python scripts/test_cli_functions.py
uv run python scripts/test_service_modules.py
uv run python scripts/test_integration.py
uv run python scripts/test_performance.py

# Pytest-based tests
pytest                    # Run all tests
pytest tests/unit/        # Unit tests only
pytest -m integration     # Integration tests only
pytest -m "not slow"      # Exclude slow tests
```

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/

# All quality checks
ruff check src/ tests/ && mypy src/ && black --check src/ tests/
```

### Package Management
```bash
python -m build           # Build package
uvx --from . article-mcp server  # Install from local
uvx article-mcp server      # Test PyPI package
```

## Key Development Patterns

### Caching Strategy
The project implements intelligent caching with 24-hour expiry:
- Cache keys are generated from API endpoints and parameters
- Cache hit information is included in response metadata
- Performance gains: 30-50% faster than traditional methods

### Rate Limiting
Different APIs have different rate limits:
- Europe PMC: 1 request/second (conservative)
- Crossref: 50 requests/second (with email)
- arXiv: 3 seconds/request (official limit)

### Error Handling
Comprehensive error handling via middleware:
- `MCPErrorHandlingMiddleware` converts exceptions to MCP standard errors
- User input errors become `ToolError` with friendly messages
- System errors become `McpError` with error codes

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