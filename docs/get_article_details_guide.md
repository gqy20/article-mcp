# get_article_details 使用指南

## 功能概述

`get_article_details` 工具用于根据文献标识符获取特定文献的详细信息。该工具支持多种标识符类型（PMID、DOI、PMCID）和同步/异步两种模式，以满足不同性能需求。

## 参数说明

- `identifier` (必需): 文献标识符，可以是 PMID、DOI 或 PMCID
- `id_type` (可选): 标识符类型
  - `"pmid"` (默认): PubMed ID
  - `"doi"`: Digital Object Identifier
  - `"pmcid"`: PubMed Central ID
- `mode` (可选): 获取模式
  - `"sync"` (默认): 同步模式
  - `"async"`: 异步模式，性能更优

## 返回值

工具返回包含以下字段的字典：

- `article`: 文献详细信息
- `error`: 错误信息（如果有）
- `processing_time`: 处理耗时（秒）
- `cache_hit`: 是否命中缓存

## 使用示例

### 通过 PMID 获取文献详情

```json
{
  "identifier": "12345678",
  "id_type": "pmid"
}
```

### 通过 DOI 获取文献详情

```json
{
  "identifier": "10.1000/xyz123",
  "id_type": "doi"
}
```

### 通过 PMCID 获取文献详情

```json
{
  "identifier": "PMC1234567",
  "id_type": "pmcid"
}
```

### 异步模式获取文献详情

```json
{
  "identifier": "12345678",
  "id_type": "pmid",
  "mode": "async"
}
```

## 错误处理

该工具具有完善的错误处理机制：

- **网络错误**: 自动重试最多3次，使用指数退避策略
- **超时处理**: 同步和异步模式都有超时控制
- **详细错误信息**: 提供具体的错误描述，包括标识符类型和值
- **API错误**: 正确处理各种HTTP状态码（如429速率限制、503服务不可用等）

## 性能特点

- 异步模式比同步模式快 20-40%
- 支持智能缓存，重复查询响应更快
- 自动重试机制，提高获取成功率

## 注意事项

1. 请确保提供的标识符有效
2. 异步模式在批量处理场景下优势更明显
3. 缓存有效期为 24 小时
4. 向后兼容旧的调用方式（仅提供 PMID 参数）