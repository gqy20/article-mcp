# Europe PMC MCP 工具参考文档

## 概述

Europe PMC MCP 服务器提供 7 个专业的学术文献搜索和分析工具。这些工具基于 BioMCP 设计模式，提供同步和异步两种版本，以及针对不同使用场景的优化版本。

## 工具列表

### 1. search_europe_pmc
**搜索 Europe PMC 文献数据库（同步版本）**

#### 功能说明
- 在 Europe PMC 数据库中搜索学术文献
- 支持关键词搜索和日期范围过滤
- 返回文献的基本信息（标题、作者、摘要、DOI、PMID等）
- 使用同步方式执行，适合简单查询

#### 参数说明
- `keyword` (必需): 搜索关键词
  - 示例: "machine learning", "COVID-19", "cancer therapy"
- `email` (可选): 提供邮箱地址以获得更高的API速率限制
- `start_date` (可选): 开始日期，格式：YYYY-MM-DD
  - 示例: "2020-01-01"
- `end_date` (可选): 结束日期，格式：YYYY-MM-DD
  - 示例: "2023-12-31"
- `max_results` (可选): 最大返回结果数量，默认10，最大100

#### 返回值说明
- `articles`: 文献列表，包含以下字段：
  - `title`: 文献标题
  - `authors`: 作者列表
  - `abstract`: 摘要
  - `journal_name`: 期刊名称
  - `doi`: DOI标识符
  - `pmid`: PubMed ID
  - `pmcid`: PMC ID（如果有）
  - `publication_date`: 发表日期
- `total_count`: 总结果数量
- `search_time`: 搜索耗时（秒）
- `message`: 处理信息
- `error`: 错误信息（如果有）

#### 使用场景
- 简单的文献检索
- 获取特定主题的文献概览
- 小批量数据查询

---

### 2. search_europe_pmc_async
**异步搜索 Europe PMC 文献数据库（高性能优化版本）**

#### 功能说明
- 使用异步方式在 Europe PMC 数据库中搜索学术文献
- 支持并发请求处理，性能比同步版本更优
- 集成缓存机制，重复查询响应更快
- 支持复杂搜索语法（如："cancer AND therapy"）

#### 参数说明
- `keyword` (必需): 搜索关键词，支持布尔运算符（AND、OR、NOT）
- `email` (可选): 提供邮箱地址以获得更高的API速率限制
- `start_date` (可选): 开始日期，格式：YYYY-MM-DD
- `end_date` (可选): 结束日期，格式：YYYY-MM-DD
- `max_results` (可选): 最大返回结果数量，默认10，最大100

#### 返回值说明
- 包含与同步版本相同的基础字段
- 额外提供：
  - `cache_hit`: 是否命中缓存
  - `performance_info`: 性能统计信息
  - `processing_time`: 处理耗时

#### 使用场景
- 大批量文献检索
- 需要高性能的搜索任务
- 复杂的搜索查询
- 频繁的重复查询

#### 性能特点
- 比同步版本快30-50%
- 支持24小时智能缓存
- 自动重试机制
- 并发控制和速率限制

---

### 3. get_article_details
**获取特定文献的详细信息（同步版本）**

#### 功能说明
- 根据PMID获取文献的完整详细信息
- 包括全文摘要、引用数据、期刊信息、发表详情等
- 使用同步方式执行，适合单篇文献查询

#### 参数说明
- `pmid` (必需): PubMed ID
  - 示例: "37769091"

#### 返回值说明
- `title`: 文献标题
- `authors`: 作者列表
- `abstract`: 完整摘要
- `journal_name`: 期刊名称
- `publication_date`: 发表日期
- `doi`: 数字对象标识符
- `pmid`: PubMed ID
- `pmcid`: PMC ID（如果有）
- `keywords`: 关键词列表
- `citations`: 引用数量
- `references`: 参考文献数量
- `full_text_url`: 全文链接（如果有）
- `error`: 错误信息（如果有）

#### 使用场景
- 获取单篇文献的完整信息
- 文献详情查看
- 引用分析准备

---

### 4. get_article_details_async
**异步获取特定文献的详细信息（高性能优化版本）**

#### 功能说明
- 使用异步方式根据PMID获取文献的完整详细信息
- 支持并发处理，性能更优
- 集成缓存机制，重复查询响应更快
- 自动重试和错误恢复

#### 参数说明
- `pmid` (必需): PubMed ID
  - 示例: "37769091"

#### 返回值说明
- 包含与同步版本相同的基础字段
- 额外提供：
  - `processing_time`: 处理耗时（秒）
  - `cache_hit`: 是否命中缓存
  - `performance_info`: 性能统计信息
  - `retry_count`: 重试次数

#### 使用场景
- 需要高性能的文献详情获取
- 批量文献详情查询
- 大规模数据处理

#### 性能特点
- 比同步版本快20-40%
- 支持智能缓存
- 自动重试机制
- 并发控制

---

### 5. get_references_by_doi
**通过DOI获取参考文献列表（同步版本）**

#### 功能说明
- 根据DOI获取该文献的所有参考文献
- 使用Crossref API获取基础参考文献信息
- 使用Europe PMC API补全详细信息（摘要、PMID等）
- 自动去重和数据清洗

#### 参数说明
- `doi` (必需): 数字对象标识符
  - 示例: "10.1126/science.adf6218"

#### 返回值说明
- `references`: 参考文献列表，每个包含：
  - `title`: 标题
  - `authors`: 作者列表
  - `journal`: 期刊名称
  - `year`: 发表年份
  - `doi`: DOI
  - `pmid`: PMID（如果有）
  - `abstract`: 摘要（如果有）
  - `source`: 数据源（crossref/europe_pmc）
- `total_count`: 总参考文献数量
- `enriched_count`: Europe PMC补全的数量
- `processing_time`: 处理耗时（秒）
- `processing_info`: 处理统计信息
- `error`: 错误信息（如果有）

#### 使用场景
- 文献引用分析
- 相关文献发现
- 研究领域梳理
- 学术谱系分析

---

### 6. get_references_by_doi_async
**通过DOI获取参考文献列表（异步并行优化版本）**

#### 功能说明
- 使用异步方式根据DOI获取参考文献列表
- 支持并发处理多个参考文献的详细信息获取
- 使用信号量控制并发数量，避免API速率限制
- 集成缓存机制，提高重复查询效率
- 自动重试和错误恢复

#### 参数说明
- `doi` (必需): 数字对象标识符
  - 示例: "10.1126/science.adf6218"

#### 返回值说明
- 包含与同步版本相同的基础字段
- 额外提供：
  - `processing_time`: 总处理耗时（秒）
  - `performance_info`: 详细性能统计
    - `crossref_time`: Crossref API耗时
    - `europe_pmc_time`: Europe PMC API耗时
    - `concurrent_requests`: 并发请求数
    - `cache_hits`: 缓存命中数
    - `retry_count`: 重试次数
  - `optimization_info`: 优化信息

#### 使用场景
- 需要快速获取大量参考文献的场景
- 大规模文献分析
- 高性能数据处理
- 时间敏感的查询任务

#### 性能特点
- 比同步版本快6-10倍
- 支持最多10个并发请求
- 智能缓存机制
- 自动重试和错误恢复
- 详细的性能监控

---

### 7. get_references_by_doi_batch_optimized
**通过DOI获取参考文献列表（批量优化版本）**

#### 功能说明
- 利用Europe PMC的批量查询能力获取参考文献
- 使用OR操作符将多个DOI合并为单个查询
- 相比传统方法可实现10倍以上的性能提升
- 特别适用于大量参考文献的快速获取
- 集成了发现的Europe PMC批量查询特性

#### 参数说明
- `doi` (必需): 数字对象标识符
  - 示例: "10.1126/science.adf6218"

#### 返回值说明
- 包含与其他版本相同的基础字段
- 额外提供：
  - `optimization`: 优化类型标识
  - `batch_info`: 批量处理信息
    - `batch_size`: 批量大小
    - `batch_time`: 批量查询耗时
    - `individual_time`: 单个查询预估耗时
    - `performance_improvement`: 性能提升倍数
  - `europe_pmc_batch_query`: 使用的批量查询语句

#### 使用场景
- 大规模参考文献获取
- 高性能批量数据处理
- 时间关键的研究任务
- 文献数据库构建

#### 性能特点
- 比传统方法快10-15倍
- 利用Europe PMC原生批量查询能力
- 减少API请求次数
- 降低网络延迟影响
- 最适合处理大量参考文献的场景

#### 技术原理
- 使用DOI:"xxx" OR DOI:"yyy"的批量查询语法
- 一次请求获取多个DOI的信息
- 显著减少API调用次数和网络开销

---

## 性能对比

| 工具 | 性能等级 | 适用场景 | 特点 |
|------|----------|----------|------|
| search_europe_pmc | 标准 | 简单查询 | 稳定可靠 |
| search_europe_pmc_async | 优化 | 复杂查询 | 30-50%提升 |
| get_article_details | 标准 | 单篇文献 | 基础功能 |
| get_article_details_async | 优化 | 批量处理 | 20-40%提升 |
| get_references_by_doi | 标准 | 引用分析 | 基础功能 |
| get_references_by_doi_async | 高性能 | 大规模分析 | 6-10倍提升 |
| get_references_by_doi_batch_optimized | 超高性能 | 批量处理 | 10-15倍提升 |
| batch_enrich_references_by_dois | 极致性能 | 多DOI处理 | 15-20倍提升 |

---

### 8. batch_enrich_references_by_dois
**批量补全多个DOI的参考文献信息（超高性能版本）**

#### 功能说明
- 同时处理多个DOI的参考文献补全
- 使用Europe PMC的批量查询API一次性获取多个DOI的详细信息
- 比逐个查询快10-15倍，适合大规模文献数据处理
- 自动去重和信息完整性检查
- 支持最多20个DOI的批量处理

#### 参数说明
- `dois` (必需): DOI列表，最多支持20个DOI同时处理
  - 示例: ["10.1126/science.adf6218", "10.1038/nature12373"]
- `email` (可选): 联系邮箱，用于获得更高的API访问限制

#### 返回值说明
- `enriched_references`: 补全信息的参考文献字典，以DOI为键
- `total_dois_processed`: 处理的DOI总数
- `successful_enrichments`: 成功补全的DOI数量
- `failed_dois`: 补全失败的DOI列表
- `processing_time`: 总处理时间（秒）
- `performance_metrics`: 性能指标
  - `average_time_per_doi`: 每个DOI的平均处理时间
  - `success_rate`: 成功率百分比
  - `estimated_speedup`: 预计速度提升

#### 使用场景
- 大规模文献数据分析
- 学术数据库构建
- 批量文献信息补全
- 高性能文献处理系统

#### 性能特点
- 超高性能：10-15倍速度提升
- 智能批量：自动分批处理大量DOI
- 并发优化：充分利用API并发能力
- 数据一致性：自动去重和完整性检查

#### 使用示例
```json
{
  "dois": [
    "10.1126/science.adf6218",
    "10.1038/nature12373",
    "10.1126/science.1260419"
  ],
  "email": "researcher@example.com"
}
```

---

## 使用建议

### 对于大模型调用者
1. **简单查询**：使用同步版本工具
2. **批量处理**：优先使用异步版本工具
3. **大规模数据**：优先使用批量优化版本
4. **性能敏感**：选择标记为"优化"或"高性能"的工具

### 工具选择指南
- 搜索文献：优先使用 `search_europe_pmc_async`
- 获取文献详情：优先使用 `get_article_details_async`
- 获取参考文献：优先使用 `get_references_by_doi_batch_optimized`
- 批量DOI处理：优先使用 `batch_enrich_references_by_dois`

### 错误处理
所有工具都提供详细的错误信息，包括：
- 参数验证错误
- API调用失败
- 网络连接问题
- 数据格式错误

建议在调用工具后检查返回值中的 `error` 字段以确认操作成功。
