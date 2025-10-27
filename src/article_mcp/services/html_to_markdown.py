#!/usr/bin/env python3

"""
HTML转Markdown功能模块
使用markdownify库实现专业的HTML到Markdown转换
"""

import logging
from typing import Any

from markdownify import markdownify as md


def html_to_markdown(html_content: str, **options) -> str | None:
    """将HTML内容转换为Markdown格式

    功能说明：
    - 使用markdownify库将HTML内容转换为Markdown格式
    - 支持自定义转换选项
    - 处理复杂的HTML结构（表格、列表、链接等）

    参数说明：
    - html_content: 必需，HTML内容字符串
    - **options: 可选，markdownify转换选项

    返回值说明：
    - 转换后的Markdown内容
    - 如果输入为空或转换失败则返回None

    使用场景：
    - 将PMC XML内容转换为Markdown格式
    - 提取网页内容并保存为Markdown
    - 学术文献的格式转换

    技术特点：
    - 基于markdownify库，转换质量高
    - 支持自定义转换规则
    - 处理复杂的HTML结构
    """
    if not html_content:
        return None

    try:
        # 默认配置选项
        default_options = {
            "heading_style": "ATX",  # 使用#风格的标题
            "convert": [
                "a",
                "b",
                "strong",
                "i",
                "em",
                "code",
                "pre",
                "p",
                "br",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ul",
                "ol",
                "li",
                "blockquote",
                "table",
                "thead",
                "tbody",
                "tr",
                "th",
                "td",
            ],
            "default_title": False,  # 不添加默认标题
        }

        # 合并用户自定义选项
        final_options = {**default_options, **options}

        # 执行转换
        markdown_content = md(html_content, **final_options)

        # 清理多余的空行
        markdown_content = "\n".join(line.rstrip() for line in markdown_content.split("\n"))
        markdown_content = markdown_content.strip()

        return markdown_content

    except Exception as e:
        logging.error(f"HTML转Markdown时发生错误: {e}")
        return None


def html_to_text(html_content: str) -> str | None:
    """将HTML内容转换为纯文本（兼容原有函数）

    功能说明：
    - 使用markdownify的strip功能将HTML转换为纯文本
    - 保持与原有函数的接口兼容性

    参数说明：
    - html_content: 必需，HTML内容字符串

    返回值说明：
    - 转换后的纯文本内容
    - 如果输入为空则返回None
    """
    if not html_content:
        return None

    try:
        # 使用markdownify的纯文本模式
        text_content = md(
            html_content,
            strip=[
                "a",
                "b",
                "strong",
                "i",
                "em",
                "code",
                "pre",
                "p",
                "br",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ul",
                "ol",
                "li",
                "blockquote",
                "table",
                "thead",
                "tbody",
                "tr",
                "th",
                "td",
                "script",
                "style",
            ],
            heading_style="ATX",
        )

        # 清理多余的空行和空格
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]
        text_content = "\n".join(lines)

        return text_content

    except Exception as e:
        logging.error(f"HTML转文本时发生错误: {e}")
        return None


def extract_structured_content(
    html_content: str, output_format: str = "markdown"
) -> dict[str, Any]:
    """从HTML中提取结构化内容

    功能说明：
    - 从HTML内容中提取标题、正文等结构化信息
    - 支持输出为Markdown或纯文本格式

    参数说明：
    - html_content: 必需，HTML内容字符串
    - output_format: 可选，输出格式 ('markdown' 或 'text')

    返回值说明：
    - 包含提取内容的字典
    """
    if not html_content:
        return {"title": None, "content": None, "format": output_format, "error": "HTML内容为空"}

    try:
        # 提取标题（从title标签或h1标签）
        import re

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
        )
        if not title_match:
            title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "无标题"

        # 根据输出格式转换内容
        if output_format == "markdown":
            content = html_to_markdown(html_content)
        else:
            content = html_to_text(html_content)

        return {"title": title, "content": content, "format": output_format, "error": None}

    except Exception as e:
        return {
            "title": None,
            "content": None,
            "format": output_format,
            "error": f"提取结构化内容时发生错误: {str(e)}",
        }


def convert_pmc_xml_to_markdown(xml_content: str) -> str | None:
    """专门处理PMC XML内容的转换

    功能说明：
    - 针对PMC XML格式优化的转换函数
    - 处理学术文献特有的标签结构
    - 增强对front matter和section结构的解析

    参数说明：
    - xml_content: 必需，PMC XML内容字符串

    返回值说明：
    - 转换后的Markdown内容
    """
    if not xml_content:
        return None

    try:
        # 首先进行XML预处理，提取关键结构
        import re

        # 提取文章标题
        title_match = re.search(
            r"<article-title[^>]*>(.*?)</article-title>", xml_content, re.DOTALL
        )
        title = title_match.group(1).strip() if title_match else ""

        # 提取作者信息
        authors = []
        author_matches = re.findall(
            r'<contrib[^>]*contrib-type="author"[^>]*>(.*?)</contrib>', xml_content, re.DOTALL
        )
        for author_match in author_matches:
            surname = re.search(r"<surname>([^<]+)</surname>", author_match)
            given_names = re.search(r"<given-names>([^<]+)</given-names>", author_match)
            if surname and given_names:
                authors.append(f"{given_names.group(1)} {surname.group(1)}")

        # 提取摘要
        abstract_match = re.search(r"<abstract[^>]*>(.*?)</abstract>", xml_content, re.DOTALL)
        abstract = abstract_match.group(1).strip() if abstract_match else ""

        # 提取关键词
        keywords = re.findall(r"<kwd>([^<]+)</kwd>", xml_content)

        # 提取正文内容
        body_match = re.search(r"<body[^>]*>(.*?)</body>", xml_content, re.DOTALL)
        body_content = body_match.group(1).strip() if body_match else xml_content

        # 处理section标题
        def process_sections(content):
            # 将section标题转换为Markdown格式
            content = re.sub(r"<sec[^>]*>.*?<title>([^<]+)</title>", r"\n\n## \1\n\n", content)
            # 处理子section
            content = re.sub(r"<sec[^>]*>.*?<title>([^<]+)</title>", r"\n\n### \1\n\n", content)
            return content

        body_content = process_sections(body_content)

        # 处理引用链接
        def process_references(content):
            # 处理文献引用
            content = re.sub(r'<xref[^>]*ref-type="bibr"[^>]*>([^<]+)</xref>', r"[\1]", content)
            # 处理图表引用
            content = re.sub(r'<xref[^>]*ref-type="fig"[^>]*>([^<]+)</xref>', r"\1", content)
            return content

        body_content = process_references(body_content)

        # 构建增强的转换选项
        pmc_options = {
            "heading_style": "ATX",
            "convert": [
                "title",
                "abstract",
                "sec",
                "p",
                "bold",
                "italic",
                "underline",
                "sc",
                "monospace",
                "sub",
                "sup",
                "table",
                "thead",
                "tbody",
                "tr",
                "th",
                "td",
                "list",
                "list-item",
                "email",
                "ext-link",
            ],
            "default_title": False,
        }

        # 转换正文内容
        body_markdown = html_to_markdown(body_content, **pmc_options)

        # 构建完整的Markdown文档
        markdown_parts = []

        if title:
            markdown_parts.append(f"# {title}")
            markdown_parts.append("")

        if authors:
            markdown_parts.append("**Authors:** " + ", ".join(authors))
            markdown_parts.append("")

        if keywords:
            markdown_parts.append("**Keywords:** " + ", ".join(keywords))
            markdown_parts.append("")

        if abstract:
            # 转换摘要
            abstract_markdown = html_to_markdown(abstract, **pmc_options)
            if abstract_markdown:
                markdown_parts.append("## Abstract")
                markdown_parts.append(abstract_markdown)
                markdown_parts.append("")

        if body_markdown:
            markdown_parts.append(body_markdown)

        return "\n".join(markdown_parts)

    except Exception as e:
        logging.error(f"PMC XML转Markdown时发生错误: {e}")
        # 如果增强转换失败，回退到基础转换
        return html_to_markdown(xml_content)


# 测试代码
if __name__ == "__main__":
    # 测试HTML
    test_html = """
    <html>
    <head><title>测试学术文献</title></head>
    <body>
        <h1>研究背景</h1>
        <p>这是一个<strong>重要</strong>的学术研究，涉及<em>机器学习</em>和<a href="http://example.com">深度学习</a>技术。</p>

        <h2>实验方法</h2>
        <p>我们使用了以下方法：</p>
        <ul>
            <li>数据预处理</li>
            <li>模型训练</li>
            <li>结果评估</li>
        </ul>

        <h2>实验结果</h2>
        <table>
            <thead>
                <tr>
                    <th>方法</th>
                    <th>准确率</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>方法A</td>
                    <td>95.2%</td>
                </tr>
                <tr>
                    <td>方法B</td>
                    <td>97.8%</td>
                </tr>
            </tbody>
        </table>

        <blockquote>
            <p>这是一段重要的引用内容。</p>
        </blockquote>
    </body>
    </html>
    """

    print("测试HTML转Markdown功能:")
    print("=" * 50)
    markdown_result = html_to_markdown(test_html)
    print(markdown_result)

    print("\n\n测试HTML转文本功能:")
    print("=" * 50)
    text_result = html_to_text(test_html)
    print(text_result)

    print("\n\n测试结构化内容提取:")
    print("=" * 50)
    structured = extract_structured_content(test_html, output_format="markdown")
    print(f"标题: {structured['title']}")
    print(f"格式: {structured['format']}")
    print(f"内容长度: {len(structured['content']) if structured['content'] else 0} 字符")
    print(f"错误信息: {structured['error']}")
