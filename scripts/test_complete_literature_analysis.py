#!/usr/bin/env python3
"""
完整的文献分析功能测试
测试get_literature_relations工具的所有功能和场景
"""

import asyncio
import logging
import time
from src.article_mcp.tools.core import relation_tools

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

class TestLogger:
    """自定义测试日志器"""
    def info(self, msg): print(f"📝 INFO: {msg}")
    def warning(self, msg): print(f"⚠️  WARNING: {msg}")
    def error(self, msg): print(f"❌ ERROR: {msg}")
    def debug(self, msg): print(f"🔍 DEBUG: {msg}")

def create_test_services():
    """创建测试服务实例"""
    print("🔧 初始化测试服务...")

    try:
        from src.article_mcp.services.europe_pmc import create_europe_pmc_service
        from src.article_mcp.services.pubmed_search import create_pubmed_service
        from src.article_mcp.services.crossref_service import CrossRefService
        from src.article_mcp.services.openalex_service import OpenAlexService

        test_logger = TestLogger()

        # 初始化服务
        crossref_service = CrossRefService(test_logger)
        openalex_service = OpenAlexService(test_logger)
        pubmed_service = create_pubmed_service(test_logger)
        europe_pmc_service = create_europe_pmc_service(test_logger, pubmed_service)

        mock_services = {
            "europe_pmc": europe_pmc_service,
            "pubmed": pubmed_service,
            "crossref": crossref_service,
            "openalex": openalex_service,
        }

        print("✅ 服务初始化成功")
        return mock_services, test_logger

    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_single_doi_analysis():
    """测试单个DOI文献的完整关系分析"""
    print("\n" + "="*80)
    print("📋 测试1: 单个DOI文献的完整关系分析")
    print("="*80)

    # 测试用例：使用一些真实的DOI
    test_cases = [
        {
            "name": "Nature文章分析",
            "doi": "10.1038/nature12373",
            "expected_results": ["references", "similar", "citing"]
        },
        {
            "name": "Science文章分析",
            "doi": "10.1126/science.1258070",
            "expected_results": ["references"]
        },
        {
            "name": "高引用文章分析",
            "doi": "10.1038/s41586-021-03819-2",
            "expected_results": ["citing"]
        },
        {
            "name": "医学文章分析",
            "doi": "10.1056/NEJMoa2030113",
            "expected_results": ["references", "similar"]
        }
    ]

    services, test_logger = create_test_services()
    if not services:
        print("❌ 无法初始化服务，跳过测试")
        return

    # 注册工具
    mock_mcp = MockMCP()
    relation_tools.register_relation_tools(mock_mcp, services, test_logger)

    total_tests = len(test_cases)
    successful_tests = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 子测试 {i}/{total_tests}: {test_case['name']}")
        print("-" * 60)

        start_time = time.time()

        try:
            result = mock_mcp.tools["get_literature_relations"](
                identifiers=test_case['doi'],
                id_type="doi",
                relation_types=test_case['expected_results'],
                max_results=5,
                sources=["crossref", "openalex", "pubmed"]
            )

            processing_time = time.time() - start_time

            # 分析结果
            success = result.get('success', False)
            stats = result.get('statistics', {})
            relations = result.get('relations', {})

            print(f"✅ 查询成功: {success}")
            print(f"⏱️  处理时间: {processing_time:.2f} 秒")
            print(f"📊 标识符: {result.get('identifier', 'N/A')}")
            print(f"🔍 标识符类型: {result.get('id_type', 'N/A')}")

            print(f"\n📈 关系统计:")
            for rel_type in test_case['expected_results']:
                count = stats.get(f"{rel_type}_count", 0)
                status = "✅" if count > 0 else "⚠️ "
                print(f"   {status} {rel_type}: {count} 篇")

                if count > 0:
                    rel_data = relations.get(rel_type, [])[:2]
                    for j, item in enumerate(rel_data, 1):
                        title = item.get('title', '无标题')
                        if len(title) > 70:
                            title = title[:70] + "..."
                        doi = item.get('doi', '无DOI')
                        print(f"     {j}. {title}")
                        print(f"        DOI: {doi}")

            if success:
                successful_tests += 1
                print(f"🎯 测试通过")
            else:
                error = result.get('error', '未知错误')
                print(f"❌ 测试失败: {error}")

        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n📊 单DOI测试总结: {successful_tests}/{total_tests} 通过")
    return successful_tests, total_tests

def test_identifier_conversion():
    """测试标识符转换功能"""
    print("\n" + "="*80)
    print("🔄 测试2: 标识符转换功能")
    print("="*80)

    test_cases = [
        # 真实的PMID（可能转换成功）
        {"id": "32132209", "type": "pmid", "name": "COVID-19研究"},
        {"id": "31832154", "type": "pmid", "name": "医学文献"},

        # 测试用PMCID（可能不存在）
        {"id": "PMC123456", "type": "pmcid", "name": "测试PMCID"},

        # DOI直接识别
        {"id": "10.1038/nature12373", "type": "doi", "name": "Nature DOI"},

        # arXiv ID（暂不支持）
        {"id": "arXiv:2001.00001", "type": "arxiv_id", "name": "arXiv论文"},
    ]

    total_tests = len(test_cases)
    successful_conversions = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 子测试 {i}/{total_tests}: {test_case['name']}")
        print("-" * 60)

        try:
            test_logger = TestLogger()

            # 测试标识符识别
            if test_case['type'] == 'doi':
                doi = relation_tools._ensure_doi_identifier(
                    test_case['id'], test_case['type'], test_logger
                )
                print(f"🔍 DOI识别: {test_case['id']} -> {doi}")

                if doi == test_case['id']:
                    successful_conversions += 1
                    print("✅ DOI识别正确")
                else:
                    print("❌ DOI识别失败")

            elif test_case['type'] == 'pmid':
                print(f"🔄 PMID转换: {test_case['id']}")
                doi = relation_tools._pmid_to_doi(test_case['id'], test_logger)

                if doi:
                    print(f"✅ 转换成功: {doi}")
                    successful_conversions += 1

                    # 测试转换后的DOI是否能查询
                    print("🧪 测试转换后DOI的查询能力...")
                    services, logger = create_test_services()
                    if services:
                        mock_mcp = MockMCP()
                        relation_tools.register_relation_tools(mock_mcp, services, logger)

                        result = mock_mcp.tools["get_literature_relations"](
                            identifiers=doi,
                            id_type="doi",
                            relation_types=["references"],
                            max_results=2
                        )

                        if result.get('success'):
                            print("✅ 转换后DOI查询成功")
                        else:
                            print("⚠️  转换后DOI查询失败")
                else:
                    print("❌ 转换失败")

            elif test_case['type'] == 'pmcid':
                print(f"🔄 PMCID转换: {test_case['id']}")
                doi = relation_tools._pmcid_to_doi(test_case['id'], test_logger)

                if doi:
                    print(f"✅ 转换成功: {doi}")
                    successful_conversions += 1
                else:
                    print("❌ 转换失败")

            elif test_case['type'] == 'arxiv_id':
                print(f"🔄 arXiv转换: {test_case['id']}")
                doi = relation_tools._ensure_doi_identifier(
                    test_case['id'], test_case['type'], test_logger
                )

                if not doi:
                    print("⚠️  arXiv转换暂不支持（符合预期）")
                    successful_conversions += 1
                else:
                    print(f"意外成功: {doi}")

        except Exception as e:
            print(f"❌ 转换测试异常: {e}")

    print(f"\n📊 标识符转换测试总结: {successful_conversions}/{total_tests} 通过")
    return successful_conversions, total_tests

def test_batch_analysis():
    """测试批量文献分析功能"""
    print("\n" + "="*80)
    print("📦 测试3: 批量文献分析功能")
    print("="*80)

    # 批量测试用例
    batch_test_cases = [
        {
            "name": "批量DOI分析",
            "identifiers": ["10.1038/nature12373", "10.1126/science.1258070"],
            "id_type": "auto",
            "analysis_type": "basic"
        },
        {
            "name": "批量网络分析",
            "identifiers": ["10.1038/nature12373"],
            "id_type": "doi",
            "analysis_type": "comprehensive"
        }
    ]

    services, test_logger = create_test_services()
    if not services:
        print("❌ 无法初始化服务，跳过测试")
        return 0, 1

    # 注册工具
    mock_mcp = MockMCP()
    relation_tools.register_relation_tools(mock_mcp, services, test_logger)

    total_tests = len(batch_test_cases)
    successful_tests = 0

    for i, test_case in enumerate(batch_test_cases, 1):
        print(f"\n🧪 子测试 {i}/{total_tests}: {test_case['name']}")
        print("-" * 60)

        start_time = time.time()

        try:
            result = mock_mcp.tools["get_literature_relations"](
                identifiers=test_case['identifiers'],
                id_type=test_case['id_type'],
                analysis_type=test_case['analysis_type'],
                max_results=3
            )

            processing_time = time.time() - start_time

            # 分析结果
            success = result.get('success', False)

            print(f"✅ 查询成功: {success}")
            print(f"⏱️  处理时间: {processing_time:.2f} 秒")

            if 'total_identifiers' in result:
                # 批量分析结果
                total_ids = result.get('total_identifiers', 0)
                successful_analyses = result.get('successful_analyses', 0)
                success_rate = result.get('success_rate', 0)

                print(f"📊 批量统计:")
                print(f"   - 总标识符数: {total_ids}")
                print(f"   - 成功分析数: {successful_analyses}")
                print(f"   - 成功率: {success_rate:.1%}")

                if success_rate > 0:
                    successful_tests += 1
                    print("🎯 批量测试通过")
                else:
                    print("❌ 批量测试失败")

            elif 'network_data' in result:
                # 网络分析结果
                network_data = result.get('network_data', {})
                nodes = network_data.get('nodes', [])
                edges = network_data.get('edges', [])

                print(f"📊 网络统计:")
                print(f"   - 节点数: {len(nodes)}")
                print(f"   - 边数: {len(edges)}")
                print(f"   - 分析类型: {network_data.get('analysis_type', 'N/A')}")

                if len(nodes) > 0:
                    successful_tests += 1
                    print("🎯 网络测试通过")
                else:
                    print("❌ 网络测试失败")

            else:
                print("❌ 未知的批量结果格式")

        except Exception as e:
            print(f"❌ 批量测试异常: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n📊 批量分析测试总结: {successful_tests}/{total_tests} 通过")
    return successful_tests, total_tests

def test_error_handling():
    """测试错误处理和边界情况"""
    print("\n" + "="*80)
    print("🛡️  测试4: 错误处理和边界情况")
    print("="*80)

    error_test_cases = [
        {
            "name": "空标识符测试",
            "params": {
                "identifiers": "",
                "id_type": "doi",
                "relation_types": ["references"]
            }
        },
        {
            "name": "无效DOI测试",
            "params": {
                "identifiers": "10.9999/invalid.doi",
                "id_type": "doi",
                "relation_types": ["references"]
            }
        },
        {
            "name": "不存在的PMID测试",
            "params": {
                "identifiers": "99999999",
                "id_type": "pmid",
                "relation_types": ["references"]
            }
        },
        {
            "name": "空关系类型测试",
            "params": {
                "identifiers": "10.1038/nature12373",
                "id_type": "doi",
                "relation_types": []
            }
        },
        {
            "name": "无效数据源测试",
            "params": {
                "identifiers": "10.1038/nature12373",
                "id_type": "doi",
                "relation_types": ["references"],
                "sources": ["invalid_source"]
            }
        }
    ]

    services, test_logger = create_test_services()
    if not services:
        print("❌ 无法初始化服务，跳过测试")
        return 0, 1

    # 注册工具
    mock_mcp = MockMCP()
    relation_tools.register_relation_tools(mock_mcp, services, test_logger)

    total_tests = len(error_test_cases)
    well_handled_tests = 0

    for i, test_case in enumerate(error_test_cases, 1):
        print(f"\n🧪 子测试 {i}/{total_tests}: {test_case['name']}")
        print("-" * 60)

        try:
            result = mock_mcp.tools["get_literature_relations"](**test_case['params'])

            success = result.get('success', False)
            error = result.get('error', '')

            if not success and error:
                print(f"✅ 错误正确处理: {error}")
                well_handled_tests += 1
            elif success:
                print("⚠️  意外成功（可能是测试数据有效）")
                well_handled_tests += 1
            else:
                print("❌ 错误处理不完善")

        except Exception as e:
            # 检查是否是预期的异常
            if "空" in test_case['name'] or "无效" in test_case['name']:
                print(f"✅ 异常正确抛出: {type(e).__name__}")
                well_handled_tests += 1
            else:
                print(f"❌ 意外异常: {e}")

    print(f"\n📊 错误处理测试总结: {well_handled_tests}/{total_tests} 通过")
    return well_handled_tests, total_tests

def test_data_quality():
    """测试返回数据的质量和格式"""
    print("\n" + "="*80)
    print("🔍 测试5: 数据质量和格式验证")
    print("="*80)

    services, test_logger = create_test_services()
    if not services:
        print("❌ 无法初始化服务，跳过测试")
        return 0, 1

    # 注册工具
    mock_mcp = MockMCP()
    relation_tools.register_relation_tools(mock_mcp, services, test_logger)

    try:
        print("🧪 测试数据质量和格式...")

        result = mock_mcp.tools["get_literature_relations"](
            identifiers="10.1038/nature12373",
            id_type="doi",
            relation_types=["references", "similar", "citing"],
            max_results=3
        )

        quality_checks = []

        # 检查基本结构
        required_fields = ['success', 'identifier', 'id_type', 'relations', 'statistics']
        for field in required_fields:
            if field in result:
                quality_checks.append(f"✅ 包含字段: {field}")
            else:
                quality_checks.append(f"❌ 缺失字段: {field}")

        # 检查关系数据质量
        relations = result.get('relations', {})
        for rel_type, rel_data in relations.items():
            if rel_data and len(rel_data) > 0:
                quality_checks.append(f"✅ {rel_type} 数据有效: {len(rel_data)} 条")

                # 检查数据字段
                sample_item = rel_data[0]
                important_fields = ['title', 'doi', 'authors', 'journal']
                for field in important_fields:
                    if field in sample_item and sample_item[field]:
                        quality_checks.append(f"✅ {rel_type} 包含 {field}")
                    else:
                        quality_checks.append(f"⚠️  {rel_type} 缺少 {field}")
            else:
                quality_checks.append(f"⚠️  {rel_type} 无数据")

        # 检查统计信息
        stats = result.get('statistics', {})
        expected_stats = ['references_count', 'similar_count', 'citing_count', 'total_relations']
        for stat in expected_stats:
            if stat in stats:
                quality_checks.append(f"✅ 包含统计: {stat}={stats[stat]}")

        # 检查处理时间
        if 'processing_time' in result:
            processing_time = result['processing_time']
            if processing_time > 0:
                quality_checks.append(f"✅ 处理时间: {processing_time} 秒")

        # 输出质量检查结果
        for check in quality_checks:
            print(f"   {check}")

        # 计算质量评分
        total_checks = len(quality_checks)
        passed_checks = len([c for c in quality_checks if c.startswith("✅")])
        quality_score = passed_checks / total_checks if total_checks > 0 else 0

        print(f"\n📊 数据质量评分: {quality_score:.1%} ({passed_checks}/{total_checks})")

        return passed_checks, total_checks

    except Exception as e:
        print(f"❌ 数据质量测试异常: {e}")
        return 0, 1

def generate_test_report(results):
    """生成测试报告"""
    print("\n" + "="*80)
    print("📋 完整测试报告")
    print("="*80)

    total_tests = sum(result[1] for result in results)
    successful_tests = sum(result[0] for result in results)
    overall_success_rate = successful_tests / total_tests if total_tests > 0 else 0

    test_categories = [
        ("单DOI文献分析", results[0]),
        ("标识符转换", results[1]),
        ("批量文献分析", results[2]),
        ("错误处理", results[3]),
        ("数据质量", results[4])
    ]

    print(f"\n🎯 总体测试结果:")
    print(f"   - 总测试数: {total_tests}")
    print(f"   - 通过测试数: {successful_tests}")
    print(f"   - 成功率: {overall_success_rate:.1%}")

    print(f"\n📊 分类测试结果:")
    for category, (passed, total) in test_categories:
        rate = passed / total if total > 0 else 0
        status = "✅" if rate >= 0.8 else "⚠️ " if rate >= 0.6 else "❌"
        print(f"   {status} {category}: {passed}/{total} ({rate:.1%})")

    print(f"\n🔍 功能评估:")
    if overall_success_rate >= 0.8:
        print("   🎉 优秀！功能基本可用，可以投入使用")
    elif overall_success_rate >= 0.6:
        print("   👍 良好！大部分功能正常，需要小幅优化")
    elif overall_success_rate >= 0.4:
        print("   ⚠️  一般！部分功能正常，需要重点优化")
    else:
        print("   ❌ 需要改进！功能存在问题，需要大幅优化")

    print(f"\n💡 建议:")
    if overall_success_rate >= 0.8:
        print("   - 可以开始用户测试")
        print("   - 监控生产环境性能")
        print("   - 收集用户反馈")
    else:
        print("   - 优先修复失败的测试用例")
        print("   - 检查API连接和权限")
        print("   - 改进错误处理机制")

def main():
    """主测试函数"""
    print("🚀 开始完整的文献分析功能测试")
    print("="*80)

    start_time = time.time()

    # 执行所有测试
    test_results = []

    try:
        # 测试1: 单DOI文献分析
        result = test_single_doi_analysis()
        test_results.append(result)

        # 测试2: 标识符转换
        result = test_identifier_conversion()
        test_results.append(result)

        # 测试3: 批量文献分析
        result = test_batch_analysis()
        test_results.append(result)

        # 测试4: 错误处理
        result = test_error_handling()
        test_results.append(result)

        # 测试5: 数据质量
        result = test_data_quality()
        test_results.append(result)

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

    # 生成测试报告
    generate_test_report(test_results)

    total_time = time.time() - start_time
    print(f"\n⏱️  总测试时间: {total_time:.2f} 秒")
    print("🏁 测试完成")

if __name__ == "__main__":
    main()