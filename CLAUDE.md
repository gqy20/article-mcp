# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Article MCP is a high-performance literature search server based on FastMCP framework that integrates multiple academic databases including Europe PMC, arXiv, and PubMed. It provides comprehensive literature search, reference management, and quality evaluation tools for academic research.

## Architecture

The project follows a standard Python src layout architecture with clear separation of concerns:

- **Core Package** (`src/article_mcp/`): Main package following Python packaging best practices
- **Service Layer** (`src/article_mcp/services/`): Service layer for API integrations and business logic
- **Tool Layer** (`src/article_mcp/tools/`): MCP tool registration and implementations
- **Compatibility Layer** (`main.py`): Backward-compatible CLI interface

### Core Package Structure

The main package (`src/article_mcp/`) follows Python packaging standards with:

- `__init__.py`: Package initialization and clean API exports
- `cli.py`: Main CLI entry point and MCP server creation
- `__main__.py`: Python module execution support

### Service Layer Architecture

The service layer (`src/article_mcp/services/`) implements dependency injection pattern with these key services:

- `EuropePMCService` (`europe_pmc.py`): Europe PMC API integration with caching and performance optimizations
- `ReferenceService` (`reference_service.py`): Reference management and DOI resolution
- `PubMedService` (`pubmed_search.py`): PubMed search and literature retrieval
- `LiteratureRelationService` (`literature_relation_service.py`): Literature relationship analysis
- `ArXivSearchService` (`arxiv_search.py`): arXiv preprint search functionality
- `CrossRefService` (`crossref_service.py`): CrossRef API integration
- `OpenAlexService` (`openalex_service.py`): OpenAlex API integration

**Supporting Services:**
- `api_utils.py`: API client utilities and common patterns
- `mcp_config.py`: MCP configuration management
- `error_utils.py`: Error handling utilities
- `html_to_markdown.py`: HTML to Markdown conversion
- `merged_results.py`: Result merging and deduplication
- `similar_articles.py`: Similar article finding algorithms

### Tool Layer Organization

The tool layer (`src/article_mcp/tools/`) contains MCP tool implementations:

**Core Tool Modules** (`src/article_mcp/tools/core/`):
- `search_tools.py`: Literature search tools registration
- `article_tools.py`: Article detail tools registration
- `reference_tools.py`: Reference management tools registration
- `relation_tools.py`: Literature relationship analysis tools registration
- `quality_tools.py`: Journal quality evaluation tools registration
- `batch_tools.py`: Batch processing tools registration

**Additional Tool Modules:**
- `article_detail_tools.py`: Article detail retrieval tools
- `quality_tools.py`: Quality assessment tools
- `reference_tools.py`: Reference processing tools
- `relation_tools.py`: Relationship analysis tools
- `search_tools.py`: Search functionality tools
- `legacy/`: Backward compatibility support

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
The project provides a comprehensive test suite:

```bash
# Core functionality tests (recommended for daily use)
uv run python scripts/test_working_functions.py

# Quick test for basic validation
uv run python scripts/quick_test.py

# Complete test suite
uv run python scripts/run_all_tests.py

# Individual test categories
uv run python scripts/test_basic_functionality.py  # Basic functionality
uv run python scripts/test_cli_functions.py       # CLI functions
uv run python scripts/test_service_modules.py     # Service modules
uv run python scripts/test_integration.py         # Integration tests
uv run python scripts/test_performance.py         # Performance tests

# View project info
uv run python -m article_mcp info
```

### Package Management
```bash
# Build package
python -m build

# Install from local
uvx --from . article-mcp server

# Test PyPI package
uvx article-mcp server
```

## Key Development Patterns

### Service Registration Pattern
All services are registered in `src/article_mcp/cli.py:create_mcp_server()` using dependency injection:
```python
pubmed_service = create_pubmed_service(logger)
europe_pmc_service = create_europe_pmc_service(logger, pubmed_service)
```

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
Comprehensive error handling includes:
- Network timeouts and retries
- API limit handling
- Graceful degradation for partial failures
- Detailed error messages in responses

## Configuration

### Environment Variables
```bash
PYTHONUNBUFFERED=1     # Disable Python output buffering
UV_LINK_MODE=copy      # uv link mode (optional)
EASYSCHOLAR_SECRET_KEY=your_secret_key  # EasyScholar API key (optional)
```

### MCP Configuration Integration (v0.1.1+)

The project now supports reading EasyScholar API keys from MCP client configuration files:

**Configuration Priority:**
1. MCP config file keys (highest priority)
2. Function parameter keys
3. Environment variable keys

**Supported Configuration Paths:**
- `~/.config/claude-desktop/config.json`
- `~/.config/claude/config.json`
- `~/.claude/config.json`

**Example Configuration:**
```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "EASYSCHOLAR_SECRET_KEY": "your_easyscholar_api_key_here"
      }
    }
  }
}
```

### MCP Client Configuration
The project supports multiple AI client configurations (Claude Desktop, Cherry Studio) with different transport modes.

## Performance Characteristics

- **Batch Processing**: Supports up to 20 DOIs simultaneously
- **Parallel Execution**: Async/await pattern with semaphore control
- **Smart Caching**: 24-hour cache with hit tracking
- **Retry Logic**: Automatic retry for network failures
- **Performance Monitoring**: Built-in performance statistics

## Data Flow

1. **Request Processing**: FastMCP receives tool calls
2. **Service Layer**: Appropriate service handles the request
3. **API Integration**: Service calls external APIs with caching
4. **Response Processing**: Data is formatted and returned with metadata
5. **Cache Management**: Results are cached for future requests

## Package Structure

```
article-mcp/
├── main.py              # Compatibility entry point (redirects to new CLI)
├── pyproject.toml       # Project configuration and dependencies
├── src/                 # Source code root
│   └── article_mcp/     # Main package (standard Python src layout)
│       ├── __init__.py  # Package initialization
│       ├── cli.py       # Main CLI entry point and MCP server creation
│       ├── __main__.py  # Python module execution support
│       ├── services/    # Service layer
│       │   ├── europe_pmc.py    # Europe PMC integration
│       │   ├── reference_service.py  # Reference management
│       │   ├── pubmed_search.py # PubMed search
│       │   ├── literature_relation_service.py  # Literature analysis
│       │   ├── arxiv_search.py  # arXiv integration
│       │   ├── crossref_service.py  # CrossRef service
│       │   ├── openalex_service.py  # OpenAlex service
│       │   └── [other utility modules...]
│       ├── tools/       # Tool layer (MCP tool implementations)
│       │   ├── core/    # Core tool registration modules
│       │   ├── search_tools.py
│       │   ├── article_detail_tools.py
│       │   ├── reference_tools.py
│       │   ├── relation_tools.py
│       │   ├── quality_tools.py
│       │   └── [other tool modules...]
│       └── legacy/      # Backward compatibility support
├── src/resource/        # Resource files
│   └── journal_info.json
├── tests/               # Comprehensive test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── utils/           # Test utilities
├── scripts/             # Test scripts
│   ├── test_working_functions.py  # Core functionality tests
│   ├── test_basic_functionality.py # Basic functionality tests
│   ├── test_cli_functions.py      # CLI function tests
│   ├── test_service_modules.py    # Service module tests
│   ├── test_integration.py        # Integration tests
│   ├── test_performance.py        # Performance tests
│   ├── run_all_tests.py           # Complete test suite
│   └── quick_test.py              # Quick validation
└── docs/                # Documentation
```

## Testing Strategy

The project uses a comprehensive testing approach:

### Test Scripts (scripts/)
- **Core Functionality Tests**: `test_working_functions.py` - Essential functionality validation
- **Test Categories**: Individual test modules for different aspects
- **Complete Suite**: `run_all_tests.py` - Full project validation
- **Quick Tests**: `quick_test.py` - Fast basic validation

### Test Suite (tests/)
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component functionality
- **Performance Tests**: Performance benchmarks
- **Test Utilities**: Helper functions and fixtures

### Running Tests
```bash
# Recommended daily usage
uv run python scripts/test_working_functions.py

# Complete validation
uv run python scripts/run_all_tests.py

# Individual testing
uv run python scripts/test_basic_functionality.py
```

The testing approach verifies:
- Package imports and structure integrity
- CLI functionality and command processing
- Service module initialization and basic operations
- MCP server creation and tool registration
- Integration between components
- Performance characteristics