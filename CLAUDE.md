# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Article MCP is a high-performance literature search server based on FastMCP framework that integrates multiple academic databases including Europe PMC, arXiv, and PubMed. It provides comprehensive literature search, reference management, and quality evaluation tools for academic research.

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **Core Services** (`src/`): Service layer for API integrations and business logic
- **Tool Modules** (`tool_modules/`): MCP tool registration and implementations
- **Main Entry Point** (`main.py`): Server creation and CLI interface

### Core Services Architecture

The service layer implements dependency injection pattern with these key services:

- `EuropePMCService` (`src/europe_pmc.py`): Europe PMC API integration with caching and performance optimizations
- `ReferenceService` (`src/reference_service.py`): Reference management and DOI resolution
- `PubMedService` (`src/pubmed_search.py`): PubMed search and literature retrieval
- `LiteratureRelationService` (`src/literature_relation_service.py`): Literature relationship analysis
- `ArXivSearchService` (`src/arxiv_search.py`): arXiv preprint search functionality

### Tool Module Organization

Each tool module contains specific MCP tool implementations:

- `search_tools.py`: Literature search tools (Europe PMC, arXiv)
- `article_detail_tools.py`: Article detail retrieval
- `reference_tools.py`: Reference management and batch processing
- `relation_tools.py`: Literature relationship analysis
- `quality_tools.py`: Journal quality evaluation

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

# Local development
uv run main.py server

# Alternative transport modes
uv run main.py server --transport stdio
uv run main.py server --transport sse --host 0.0.0.0 --port 9000
uv run main.py server --transport streamable-http --host 0.0.0.0 --port 9000
```

### Testing
```bash
# Run functional tests
uv run main.py test

# View project info
uv run main.py info
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
All services are registered in `main.py:create_mcp_server()` using dependency injection:
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
├── main.py              # Entry point with CLI interface
├── pyproject.toml       # Project configuration and dependencies
├── src/                 # Core services
│   ├── europe_pmc.py    # Europe PMC integration
│   ├── reference_service.py  # Reference management
│   ├── pubmed_search.py # PubMed search
│   ├── literature_relation_service.py  # Literature analysis
│   └── arxiv_search.py  # arXiv integration
├── tool_modules/        # MCP tool implementations
│   ├── search_tools.py
│   ├── article_detail_tools.py
│   ├── reference_tools.py
│   ├── relation_tools.py
│   └── quality_tools.py
└── tests/               # Test suite
```

## Testing Strategy

The project uses functional testing through the main CLI:
- `main.py test` runs integrated functional tests
- No separate test framework required
- Tests verify API integration and MCP tool functionality