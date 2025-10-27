#!/usr/bin/env python3
"""
测试get_literature_relations工具的API集成效果
"""

import asyncio
import logging
from src.article_mcp.tools.core import relation_tools

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建模拟的MCP对象
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

def test_relation_tools():
    """测试关系分析工具"""
    print("=" * 80)
    print("🚀 测试get_literature_relations工具API集成效果")
    print("=" * 80)

    # 创建服务实例
    from src.article_mcp.cli import create_mcp_server

    # 获取实际的服务实例
    from src.article_mcp.services.europe_pmc import create_europe_pmc_service
    from src.article_mcp.services.pubmed_search import create_pubmed_service
    from src.article_mcp.services.crossref_service import CrossRefService
    from src.article_mcp.services.openalex_service import OpenAlexService
    # 初始化服务
    crossref_service = CrossRefService(logger)
    openalex_service = OpenAlexService(logger)
    pubmed_service = create_pubmed_service(logger)
    europe_pmc_service = create_europe_pmc_service(logger, pubmed_service)

    # 注册服务到relation_tools
    mock_services = {
        "europe_pmc": europe_pmc_service,
        "pubmed": pubmed_service,
        "crossref": crossref_service,
        "openalex": openalex_service,
    }

    # 注册工具
    mock_mcp = MockMCP()
    relation_tools.register_relation_tools(mock_mcp, mock_services, logger)

    # 测试用例
    test_cases = [
        {
            "name": "DOI查询 - Nature文章",
            "params": {
                "identifiers": "10.1038/nature12373",
                "id_type": "doi",
                "relation_types": ["references", "similar", "citing"],
                "max_results": 5,
                "sources": ["crossref", "openalex", "pubmed"]
            }
        },
        {
            "name": "DOI查询 - Science文章",
            "params": {
                "identifiers": "10.1126/science.1258070",
                "id_type": "doi",
                "relation_types": ["references"],
                "max_results": 3,
                "sources": ["crossref"]
            }
        },
        {
            "name": "DOI查询 - 仅引用文献",
            "params": {
                "identifiers": "10.1038/s41586-021-03819-2",
                "id_type": "doi",
                "relation_types": ["citing"],
                "max_results": 3,
                "sources": ["openalex"]
            }
        },
        {
            "name": "DOI查询 - 仅相似文献",
            "params": {
                "identifiers": "10.1038/nature12373",
                "id_type": "doi",
                "relation_types": ["similar"],
                "max_results": 3,
                "sources": ["pubmed"]
            }
        }
    ]

    # 执行测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print("-" * 60)

        try:
            result = mock_mcp.tools["get_literature_relations"](**test_case['params'])

            # 分析结果
            success = result.get('success', False)
            stats = result.get('statistics', {})
            relations = result.get('relations', {})
            processing_time = result.get('processing_time', 0)

            print(f"✅ 查询成功: {success}")
            print(f"⏱️  处理时间: {processing_time} 秒")
            print(f"📊 统计信息:")

            for rel_type in ["references", "similar", "citing"]:
                count = stats.get(f"{rel_type}_count", 0)
                if count > 0:
                    print(f"   - {rel_type}: {count} 篇")

                    # 显示前2个结果的标题
                    rel_data = relations.get(rel_type, [])[:2]
                    for j, item in enumerate(rel_data, 1):
                        title = item.get('title', '无标题')
                        if len(title) > 80:
                            title = title[:80] + "..."
                        print(f"     {j}. {title}")

            if not stats:
                print("   ⚠️  未找到关系数据")

            if not success:
                error = result.get('error', '未知错误')
                print(f"❌ 错误: {error}")

        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()

    # 测试标识符转换功能
    print(f"\n🔄 测试标识符转换功能")
    print("-" * 60)

    conversion_tests = [
        {"id": "25763415", "type": "pmid"},
        {"id": "PMC1234567", "type": "pmcid"},
    ]

    for test in conversion_tests:
        print(f"\n🔍 测试转换: {test['type']} -> {test['id']}")
        doi = relation_tools._convert_to_doi(test['id'], test['type'], logger)
        if doi:
            print(f"✅ 转换成功: {doi}")
        else:
            print(f"❌ 转换失败")

    print("\n" + "=" * 80)
    print("🎯 测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_relation_tools()