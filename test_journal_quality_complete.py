#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期刊质量评估功能完整测试脚本
测试本地缓存查询和EasyScholar API调用
确保影响因子信息能够正确获取
"""

import os
import sys
import json
import logging
from src.pubmed_search import create_pubmed_service

def test_journal_quality_complete():
    """完整测试期刊质量评估功能"""
    print("期刊质量评估功能完整测试")
    print("=" * 60)
    
    # 创建日志记录器
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    # 创建PubMed服务
    pubmed_service = create_pubmed_service(logger)
    
    # 检查本地缓存文件
    print("1. 检查本地缓存文件")
    print("-" * 40)
    
    try:
        cache_path = os.path.join("src", "resource", "journal_info.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            print(f"[OK] 本地缓存文件存在: {cache_path}")
            print(f"[OK] 缓存包含 {len(cache_data)} 个期刊")
            
            # 显示缓存中的期刊
            print("缓存中的期刊样例:")
            for i, (journal_name, info) in enumerate(cache_data.items()):
                if i >= 5:  # 只显示前5个
                    break
                rank_info = info.get('rank', {})
                impact_factor = rank_info.get('sciif', 'N/A')
                print(f"  - {journal_name}: IF={impact_factor}")
            
            if len(cache_data) > 5:
                print(f"  ... 还有 {len(cache_data) - 5} 个期刊")
                
        else:
            print(f"[ERROR] 本地缓存文件不存在: {cache_path}")
            
    except Exception as e:
        print(f"[ERROR] 读取本地缓存失败: {e}")
    
    # 检查环境变量
    print("\n2. 检查环境变量配置")
    print("-" * 40)
    
    secret_key = os.getenv('EASYSCHOLAR_SECRET_KEY')
    if secret_key:
        print(f"[OK] 检测到EasyScholar API密钥: {secret_key[:10]}...")
        api_available = True
    else:
        print("[WARN] 未检测到EasyScholar API密钥")
        print("  环境变量 EASYSCHOLAR_SECRET_KEY 未设置")
        api_available = False
    
    # 测试本地缓存查询
    print("\n3. 测试本地缓存查询")
    print("-" * 40)
    
    # 从缓存中选择一些期刊进行测试
    cache_test_journals = ["Nature", "Science", "Cell"]
    
    for journal in cache_test_journals:
        print(f"\n测试期刊: {journal}")
        try:
            result = pubmed_service.get_journal_quality(journal, None)  # 不提供API密钥，只测试缓存
            print(f"  期刊名称: {result.get('journal_name', 'N/A')}")
            print(f"  数据来源: {result.get('source', 'N/A')}")
            print(f"  错误信息: {result.get('error', 'None')}")
            
            metrics = result.get('quality_metrics', {})
            if metrics:
                print(f"  质量指标:")
                for key, value in metrics.items():
                    print(f"    {key}: {value}")
                
                # 特别检查影响因子
                if 'impact_factor' in metrics:
                    print(f"  ✓ 影响因子获取成功: {metrics['impact_factor']}")
                else:
                    print(f"  ⚠ 未获取到影响因子")
            else:
                print(f"  ⚠ 未获取到质量指标")
                
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
    
    # 测试API调用（如果有密钥）
    if api_available:
        print("\n4. 测试EasyScholar API调用")
        print("-" * 40)
        
        # 测试一些可能不在缓存中的期刊
        api_test_journals = ["Journal of Machine Learning Research", "不存在的期刊"]
        
        for journal in api_test_journals:
            print(f"\n测试期刊: {journal}")
            try:
                result = pubmed_service.get_journal_quality(journal, secret_key)
                print(f"  期刊名称: {result.get('journal_name', 'N/A')}")
                print(f"  数据来源: {result.get('source', 'N/A')}")
                print(f"  错误信息: {result.get('error', 'None')}")
                
                metrics = result.get('quality_metrics', {})
                if metrics:
                    print(f"  质量指标:")
                    for key, value in metrics.items():
                        print(f"    {key}: {value}")
                    
                    # 特别检查影响因子
                    if 'impact_factor' in metrics:
                        print(f"  ✓ 影响因子获取成功: {metrics['impact_factor']}")
                    else:
                        print(f"  ⚠ 未获取到影响因子")
                else:
                    print(f"  ⚠ 未获取到质量指标")
                    
            except Exception as e:
                print(f"  ✗ 测试失败: {e}")
    else:
        print("\n4. 跳过EasyScholar API测试（未提供密钥）")
    
    # 测试批量评估
    print("\n5. 测试批量文献质量评估")
    print("-" * 40)
    
    # 创建测试文献列表，包含缓存中的期刊
    test_articles = [
        {
            "pmid": "123456",
            "title": "Test Article 1",
            "journal_name": "Nature",
            "authors": ["Author 1", "Author 2"]
        },
        {
            "pmid": "789012",
            "title": "Test Article 2", 
            "journal_name": "Science",
            "authors": ["Author 3", "Author 4"]
        },
        {
            "pmid": "345678",
            "title": "Test Article 3",
            "journal_name": "Cell",
            "authors": ["Author 5", "Author 6"]
        },
        {
            "pmid": "999999",
            "title": "Test Article 4",
            "journal_name": "Unknown Journal",
            "authors": ["Author 7", "Author 8"]
        }
    ]
    
    try:
        evaluated_articles = pubmed_service.evaluate_articles_quality(test_articles, secret_key)
        print(f"✓ 成功评估 {len(evaluated_articles)} 篇文献")
        
        impact_factor_count = 0
        for i, article in enumerate(evaluated_articles, 1):
            print(f"\n文献 {i}:")
            print(f"  标题: {article.get('title', 'N/A')}")
            print(f"  期刊: {article.get('journal_name', 'N/A')}")
            
            quality = article.get('journal_quality', {})
            print(f"  质量评估:")
            print(f"    数据来源: {quality.get('source', 'N/A')}")
            print(f"    错误信息: {quality.get('error', 'None')}")
            
            metrics = quality.get('quality_metrics', {})
            if metrics:
                print(f"    质量指标:")
                for key, value in metrics.items():
                    print(f"      {key}: {value}")
                
                # 统计影响因子
                if 'impact_factor' in metrics:
                    impact_factor_count += 1
                    print(f"    ✓ 影响因子: {metrics['impact_factor']}")
            else:
                print(f"    ⚠ 无质量指标")
        
        print(f"\n批量评估总结:")
        print(f"  - 总文献数: {len(evaluated_articles)}")
        print(f"  - 获取影响因子数: {impact_factor_count}")
        print(f"  - 成功率: {impact_factor_count/len(evaluated_articles)*100:.1f}%")
                
    except Exception as e:
        print(f"✗ 批量评估失败: {e}")
    
    # 测试缓存更新功能
    print("\n6. 测试缓存更新功能")
    print("-" * 40)
    
    try:
        # 尝试保存缓存
        test_cache = {"Test Journal": {"rank": {"sciif": 1.23, "sci": "Q2"}}}
        pubmed_service._save_journal_cache(test_cache)
        print("✓ 缓存保存功能正常")
        
        # 尝试加载缓存
        loaded_cache = pubmed_service._load_journal_cache()
        if "Test Journal" in loaded_cache:
            print("✓ 缓存加载功能正常")
        else:
            print("⚠ 缓存加载可能有问题")
            
    except Exception as e:
        print(f"✗ 缓存功能测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("\n关键检查点:")
    print("1. 本地缓存文件是否存在且包含期刊数据")
    print("2. 环境变量 EASYSCHOLAR_SECRET_KEY 是否正确设置")
    print("3. 影响因子信息是否能从缓存或API获取")
    print("4. 批量评估功能是否正常工作")
    print("5. 缓存更新功能是否正常")

if __name__ == "__main__":
    test_journal_quality_complete() 