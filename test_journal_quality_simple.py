#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期刊质量评估功能简化测试脚本
"""

import os
import sys
import json
import logging
from src.pubmed_search import create_pubmed_service

def test_journal_quality_simple():
    """简化测试期刊质量评估功能"""
    print("期刊质量评估功能测试")
    print("=" * 50)
    
    # 创建日志记录器
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 创建PubMed服务
    pubmed_service = create_pubmed_service(logger)
    
    # 1. 检查本地缓存
    print("\n1. 检查本地缓存")
    print("-" * 30)
    
    try:
        cache_path = os.path.join("src", "resource", "journal_info.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            print(f"[OK] 本地缓存文件存在，包含 {len(cache_data)} 个期刊")
            
            # 显示部分缓存内容
            count = 0
            for journal_name, info in cache_data.items():
                if count >= 3:
                    break
                rank_info = info.get('rank', {})
                impact_factor = rank_info.get('sciif', 'N/A')
                print(f"  - {journal_name}: IF={impact_factor}")
                count += 1
        else:
            print("[ERROR] 本地缓存文件不存在")
            
    except Exception as e:
        print(f"[ERROR] 读取缓存失败: {e}")
    
    # 2. 检查环境变量
    print("\n2. 检查环境变量")
    print("-" * 30)
    
    secret_key = os.getenv('EASYSCHOLAR_SECRET_KEY')
    if secret_key:
        print(f"[OK] 检测到API密钥: {secret_key[:10]}...")
    else:
        print("[WARN] 未检测到API密钥")
    
    # 3. 测试期刊质量查询
    print("\n3. 测试期刊质量查询")
    print("-" * 30)
    
    test_journals = ["Nature", "Science", "Cell"]
    
    for journal in test_journals:
        print(f"\n测试期刊: {journal}")
        try:
            result = pubmed_service.get_journal_quality(journal, secret_key)
            print(f"  期刊: {result.get('journal_name', 'N/A')}")
            print(f"  来源: {result.get('source', 'N/A')}")
            print(f"  错误: {result.get('error', 'None')}")
            
            metrics = result.get('quality_metrics', {})
            if metrics:
                print(f"  质量指标:")
                for key, value in metrics.items():
                    print(f"    {key}: {value}")
                
                # 检查影响因子
                if 'impact_factor' in metrics:
                    print(f"  [OK] 影响因子: {metrics['impact_factor']}")
                else:
                    print(f"  [WARN] 未获取到影响因子")
            else:
                print(f"  [WARN] 无质量指标")
                
        except Exception as e:
            print(f"  [ERROR] 测试失败: {e}")
    
    # 4. 测试批量评估
    print("\n4. 测试批量评估")
    print("-" * 30)
    
    test_articles = [
        {"pmid": "123", "title": "Test 1", "journal_name": "Nature"},
        {"pmid": "456", "title": "Test 2", "journal_name": "Science"},
        {"pmid": "789", "title": "Test 3", "journal_name": "Unknown Journal"}
    ]
    
    try:
        evaluated = pubmed_service.evaluate_articles_quality(test_articles, secret_key)
        print(f"[OK] 批量评估成功，处理 {len(evaluated)} 篇文献")
        
        impact_count = 0
        for i, article in enumerate(evaluated):
            quality = article.get('journal_quality', {})
            metrics = quality.get('quality_metrics', {})
            if 'impact_factor' in metrics:
                impact_count += 1
                print(f"  文献 {i+1}: {article['journal_name']} - IF={metrics['impact_factor']}")
        
        print(f"[OK] 获取影响因子成功率: {impact_count}/{len(evaluated)} ({impact_count/len(evaluated)*100:.1f}%)")
        
    except Exception as e:
        print(f"[ERROR] 批量评估失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("\n关键检查:")
    print("1. 本地缓存文件是否存在且有数据")
    print("2. 影响因子是否能从缓存获取")
    print("3. 批量评估功能是否正常")
    print("4. 如有API密钥，是否能从API获取新数据")

if __name__ == "__main__":
    test_journal_quality_simple() 