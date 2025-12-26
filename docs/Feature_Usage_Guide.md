# Article MCP 功能使用指南

## 📋 概述

Article MCP提供了一套完整的学术文献搜索和分析工具，支持文献搜索、详情获取、参考文献管理、关系分析和质量评估等功能。

## 🔍 核心功能列表

### 1. 文献搜索工具
- **工具名称**: `search_literature`
- **功能**: 统一多源文献搜索
- **数据源**: Europe PMC、PubMed、arXiv、CrossRef、OpenAlex

### 2. 文章详情工具
- **工具名称**: `get_article_details`
- **功能**: 获取文献详细信息
- **支持标识符**: DOI、PMID、PMCID

### 3. 参考文献工具
- **工具名称**: `get_references`
- **功能**: 获取参考文献列表
- **数据源**: CrossRef、Europe PMC

### 4. 文献关系分析工具
- **工具名称**: `get_literature_relations`
- **功能**: 获取文献的所有关联信息
- **包含**: 参考文献、相似文献、引用文献

### 5. 期刊质量评估工具
- **工具名称**: `get_journal_quality`
- **功能**: 期刊质量评估
- **指标**: 影响因子、分区、JCI指数

### 6. 批量处理工具
- **工具名称**: `batch_search_literature`
- **功能**: 批量文献搜索和处理

## 🚀 快速开始

### 基本使用流程

1. **搜索文献** → 2. **获取详情** → 3. **分析关系** → 4. **评估质量**

### 示例工作流

```json
// 1. 搜索文献
{
  "tool": "search_literature",
  "arguments": {
    "keyword": "machine learning cancer detection",
    "max_results": 10
  }
}

// 2. 获取文献详情
{
  "tool": "get_article_details",
  "arguments": {
    "identifier": "10.1000/xyz123",
    "id_type": "doi"
  }
}

// 3. 分析文献关系
{
  "tool": "get_literature_relations",
  "arguments": {
    "identifier": "10.1000/xyz123",
    "id_type": "doi",
    "relation_types": ["references", "similar", "citing"]
  }
}
```

## 📖 详细功能说明

### 1. 文献搜索 (`search_literature`)

#### 功能概述
统一搜索多个学术数据库，提供全面的文献检索功能。

#### 主要参数
- `keyword` (必需): 搜索关键词
- `sources` (可选): 数据源列表
  - `"europe_pmc"` - Europe PMC数据库
  - `"pubmed"` - PubMed数据库
  - `"arxiv"` - arXiv预印本
  - `"crossref"` - CrossRef数据库
  - `"openalex"` - OpenAlex数据库
- `max_results` (可选): 最大结果数，默认10

#### 使用示例

##### 基本搜索
```json
{
  "keyword": "artificial intelligence in healthcare",
  "max_results": 20
}
```

##### 指定数据源搜索
```json
{
  "keyword": "COVID-19 vaccine",
  "sources": ["europe_pmc", "pubmed"],
  "max_results": 15
}
```

##### 日期范围搜索
```json
{
  "keyword": "machine learning",
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "max_results": 25
}
```

#### 返回数据格式
```json
{
  "success": true,
  "keyword": "machine learning",
  "total_count": 15,
  "articles": [
    {
      "pmid": "12345678",
      "title": "Machine Learning in Healthcare: Applications and Challenges",
      "authors": ["Author A", "Author B"],
      "journal_name": "Journal Name",
      "publication_date": "2023-05-15",
      "abstract": "Article abstract...",
      "doi": "10.1000/journal.2023.12345",
      "pmid_link": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
      "source": "europe_pmc"
    }
  ],
  "sources_used": ["europe_pmc", "pubmed"],
  "processing_time": 2.34
}
```

### 2. 文章详情获取 (`get_article_details`)

#### 功能概述
根据文献标识符获取详细的文献信息，支持多种标识符类型。

#### 主要参数
- `identifier` (必需): 文献标识符
- `id_type` (可选): 标识符类型
  - `"pmid"` (默认): PubMed ID
  - `"doi"`: Digital Object Identifier
  - `"pmcid"`: PubMed Central ID
  - `"auto"`: 自动识别类型
- `mode` (可选): 获取模式
  - `"sync"` (默认): 同步模式
  - `"async"`: 异步模式，性能更优

#### 使用示例

##### 使用DOI获取详情
```json
{
  "identifier": "10.1038/nature12373",
  "id_type": "doi"
}
```

##### 使用PMID获取详情
```json
{
  "identifier": "23903748",
  "id_type": "pmid"
}
```

##### 自动识别标识符类型
```json
{
  "identifier": "PMC7138149",
  "id_type": "auto"
}
```

##### 异步模式获取详情
```json
{
  "identifier": "12345678",
  "id_type": "pmid",
  "mode": "async"
}
```

#### 返回数据格式
```json
{
  "success": true,
  "article": {
    "pmid": "12345678",
    "title": "Article Title",
    "authors": ["Author A", "Author B", "Author C"],
    "journal_name": "Journal Name",
    "publication_date": "2023-05-15",
    "volume": "15",
    "issue": "3",
    "pages": "123-145",
    "abstract": "Detailed abstract text...",
    "doi": "10.1000/journal.2023.12345",
    "pmcid": "PMC1234567",
    "pmid_link": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
    "full_text_link": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "source": "europe_pmc",
    "processing_time": 1.23
  }
}
```

### 3. 参考文献获取 (`get_references`)

#### 功能概述
获取指定文献的参考文献列表，支持多个数据源获取完整信息。

#### 主要参数
- `identifier` (必需): 文献标识符
- `id_type` (可选): 标识符类型，默认"auto"
- `max_results` (可选): 最大参考文献数量，默认20

#### 使用示例

##### 获取参考文献
```json
{
  "identifier": "10.1038/nature12373",
  "id_type": "doi",
  "max_results": 15
}
```

#### 返回数据格式
```json
{
  "success": true,
  "identifier": "10.1038/nature12373",
  "references": [
    {
      "title": "Reference Article 1",
      "authors": ["Ref Author 1", "Ref Author 2"],
      "journal": "Reference Journal",
      "year": "2020",
      "doi": "10.1000/ref.journal.2020.111",
      "pmid": "98765432",
      "url": "https://doi.org/10.1000/ref.journal.2020.111"
    }
  ],
  "total_count": 15,
  "sources_used": ["crossref", "europe_pmc"],
  "processing_time": 2.56
}
```

### 4. 文献关系分析 (`get_literature_relations`)

#### 功能概述
获取文献的所有关联信息，包括参考文献、相似文献和引用文献。

> **注意**: `references` 功能内部调用工具3 (`get_references`)，享受相同的智能去重和多源合并能力，支持 Europe PMC、CrossRef、PubMed 数据源。

#### 主要参数
- `identifier` (必需): 文献标识符
- `id_type` (可选): 标识符类型，默认"auto"
- `relation_types` (可选): 关系类型列表
  - `"references"` - 参考文献
  - `"similar"` - 相似文献
  - `"citing"` - 引用文献
- `max_results` (可选): 每种关系的最大结果数，默认20
- `sources` (可选): 数据源列表
- `analysis_type` (可选): 分析类型
  - `"basic"` (默认) - 基本分析
  - `"comprehensive"` - 综合分析
  - `"network"` - 网络分析

#### 使用示例

##### 获取所有关联信息
```json
{
  "identifier": "10.1038/nature12373",
  "id_type": "doi",
  "relation_types": ["references", "similar", "citing"],
  "max_results": 10
}
```

##### 只获取参考文献
```json
{
  "identifier": "10.1038/nature12373",
  "id_type": "doi",
  "relation_types": ["references"]
}
```

##### 网络分析
```json
{
  "identifiers": ["10.1038/nature12373", "10.1000/journal.45678"],
  "analysis_type": "network",
  "max_depth": 2,
  "max_results": 20
}
```

#### 返回数据格式
```json
{
  "success": true,
  "identifier": "10.1038/nature12373",
  "relations": {
    "references": [
      {
        "title": "Reference Article",
        "authors": ["Author A"],
        "doi": "10.1000/ref.journal.2020.111",
        "year": "2020",
        "journal": "Reference Journal"
      }
    ],
    "similar": [
      {
        "title": "Similar Article",
        "authors": ["Author B"],
        "pmid": "87654321",
        "similarity_score": 0.85
      }
    ],
    "citing": [
      {
        "title": "Citing Article",
        "authors": ["Author C"],
        "doi": "10.1000/cite.journal.2024.222",
        "year": "2024"
      }
    ]
  },
  "statistics": {
    "references_count": 10,
    "similar_count": 8,
    "citing_count": 15
  },
  "processing_time": 5.67
}
```

### 5. 期刊质量评估 (`get_journal_quality`)

#### 功能概述
获取期刊的质量评估信息，包括影响因子、分区信息等。

#### 主要参数
- `journal_name` (必需): 期刊名称
- `secret_key` (可选): EasyScholar API密钥
- `include_metrics` (可选): 包含的指标类型

#### 使用示例

##### 基本质量评估
```json
{
  "journal_name": "Nature",
  "secret_key": "your_easyscholar_api_key"
}
```

##### 指定评估指标
```json
{
  "journal_name": "Nature",
  "secret_key": "your_easyscholar_api_key",
  "include_metrics": ["impact_factor", "quartile", "jci"]
}
```

#### 返回数据格式
```json
{
  "success": true,
  "journal_name": "Nature",
  "quality_metrics": {
    "impact_factor": 69.504,
    "quartile": "Q1",
    "jci": 25.8,
    "分区": "中科院一区",
    "issn": "0028-0836",
    "publisher": "Nature Publishing Group"
  },
  "data_source": "easyscholar",
  "processing_time": 1.23
}
```

### 6. 批量处理 (`batch_search_literature`)

#### 功能概述
批量处理多个文献搜索或DOI补全任务。

#### 主要参数
- `identifiers` (必需): 标识符列表
- `operations` (可选): 操作类型列表
- `parallel` (可选): 是否并行处理，默认true
- `max_concurrent` (可选): 最大并发数，默认10

#### 使用示例

##### 批量DOI补全
```json
{
  "identifiers": [
    "10.1038/nature12373",
    "10.1126/science.1258070",
    "10.1056/NEJMoa2030113"
  ],
  "operations": ["details", "quality"],
  "parallel": true
}
```

#### 返回数据格式
```json
{
  "success": true,
  "total_identifiers": 3,
  "successful_operations": 3,
  "results": {
    "10.1038/nature12373": {
      "details": { /* 文章详情 */ },
      "quality": { /* 期刊质量 */ }
    },
    "10.1126/science.1258070": {
      "details": { /* 文章详情 */ },
      "quality": { /* 期刊质量 */ }
    }
  },
  "processing_time": 8.45
}
```

## 🔧 高级功能

### 标识符转换

项目支持多种标识符类型的自动转换：

- **PMID → DOI**: 使用Europe PMC、CrossRef、NCBI API
- **PMCID → DOI**: 使用Europe PMC JSON/XML API、NCBI OA API
- **DOI → PMID/PMCID**: 通过相关数据库查找

### 缓存机制

- **24小时智能缓存**: 避免重复API调用
- **缓存统计**: 返回缓存命中信息
- **性能提升**: 30-50%的性能改进

### 并发处理

- **异步执行**: 使用async/await模式
- **并发控制**: 信号量控制并发数量
- **超时管理**: 智能超时和重试机制

## 📊 性能特性

- **批量处理**: 支持最多20个DOI同时处理
- **智能缓存**: 24小时缓存，减少重复请求
- **自动重试**: 网络异常自动重试
- **性能监控**: 内置性能统计和监控

## ⚠️ 注意事项

### API限制
- **Europe PMC**: 1 request/second (保守策略)
- **CrossRef**: 50 requests/second (需要邮箱)
- **arXiv**: 3 seconds/request (官方限制)

### 速率控制
- 项目内置智能速率控制
- 自动调整请求间隔
- 优雅的降级处理

### 错误处理
- 完善的错误处理机制
- 详细的错误信息返回
- 部分失败时的优雅降级

## 🔗 相关文档

- **[Deployment Guide](./Deployment_Guide.md)** - 详细的部署配置说明
- **[Cherry Studio Configuration Guide](./Cherry_Studio_Configuration_Guide.md)** - 客户端特定配置
- **[MCP Configuration Integration](./MCP_Configuration_Integration.md)** - 配置文件集成说明

---

**最后更新**: 2025-10-27
**维护者**: Claude Code
**功能数量**: 6个核心工具
