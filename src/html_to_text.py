#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的HTML转文本功能
"""

import re
from typing import Optional


def html_to_text(html_content: str) -> Optional[str]:
    """将HTML内容转换为纯文本
    
    功能说明：
    - 将HTML内容转换为纯文本格式
    - 移除HTML标签和特殊字符
    - 保留基本的段落和换行结构
    
    参数说明：
    - html_content: 必需，HTML内容字符串
    
    返回值说明：
    - 转换后的纯文本内容
    - 如果输入为空则返回None
    
    使用场景：
    - 将PMC XML内容转换为可读文本
    - 提取网页正文内容
    - 清理HTML格式的文献内容
    
    技术特点：
    - 简单高效的HTML标签移除
    - 保留基本的文本结构
    - 处理特殊字符和编码
    """
    if not html_content:
        return None
    
    try:
        # 创建文本副本进行处理
        text = html_content
        
        # 移除HTML注释
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # 移除script和style标签及其内容
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 将重要的HTML标签替换为换行符
        text = re.sub(r'</(div|h[1-6]|p|br|li|tr)>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<(td|th)[^>]*>', ' ', text, flags=re.IGNORECASE)
        
        # 移除所有剩余的HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 解码常见的HTML实体
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&#39;': "'",
            '&rsquo;': "'",
            '&lsquo;': "'",
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&hellip;': '...',
            '&ndash;': '-',
            '&mdash;': '--',
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        # 移除多余的空白行，但保留单个换行
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 保留段落间距
        text = re.sub(r'[ \t]+', ' ', text)      # 合并多个空格为单个空格
        
        # 去除首尾空白
        text = text.strip()
        
        return text
        
    except Exception as e:
        print(f"HTML转文本时发生错误: {e}")
        return None


def extract_structured_content(html_content: str) -> dict:
    """从HTML中提取结构化内容
    
    功能说明：
    - 从HTML内容中提取标题、作者、摘要等结构化信息
    - 提供更高级的内容提取功能
    
    参数说明：
    - html_content: 必需，HTML内容字符串
    
    返回值说明：
    - 包含提取内容的字典
    """
    if not html_content:
        return {
            "title": None,
            "authors": [],
            "abstract": None,
            "body": None,
            "error": "HTML内容为空"
        }
    
    try:
        # 提取标题（简化版）
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "无标题"
        
        # 提取正文内容
        body_text = html_to_text(html_content)
        
        return {
            "title": title,
            "authors": [],  # 在PMC XML中需要专门解析
            "abstract": None,  # 在PMC XML中需要专门解析
            "body": body_text,
            "error": None
        }
        
    except Exception as e:
        return {
            "title": None,
            "authors": [],
            "abstract": None,
            "body": None,
            "error": f"提取结构化内容时发生错误: {str(e)}"
        }


# 测试代码
if __name__ == "__main__":
    # 简单测试
    test_html = """
    <html>
    <head><title>测试标题</title></head>
    <body>
        <h1>主标题</h1>
        <p>这是一个<strong>重要</strong>的段落。</p>
        <p>这是另一个段落，包含&nbsp;空格和&lt;特殊&gt;字符。</p>
        <ul>
            <li>列表项1</li>
            <li>列表项2</li>
        </ul>
    </body>
    </html>
    """
    
    print("测试HTML转文本功能:")
    print("=" * 40)
    result = html_to_text(test_html)
    print(result)
    
    print("\n\n测试结构化内容提取:")
    print("=" * 40)
    structured = extract_structured_content(test_html)
    print(f"标题: {structured['title']}")
    print(f"正文长度: {len(structured['body']) if structured['body'] else 0} 字符")
    print(f"错误信息: {structured['error']}")