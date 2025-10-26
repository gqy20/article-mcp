"""
arXiv 文献搜索服务
基于 arXiv API 的学术文献搜索功能
"""

import logging
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import requests
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ArXiv Atom feed namespace
ATOM_NS = "{http://www.w3.org/2005/Atom}"

# 创建日志记录器
logger = logging.getLogger(__name__)


def create_retry_session() -> requests.Session:
    """创建带重试策略的requests会话"""
    retry_strategy = Retry(
        total=5,  # 最多重试5次
        backoff_factor=1,  # 指数退避（1, 2, 4, 8, 16秒）
        status_forcelist=[429, 500, 502, 503, 504],  # arXiv 常用 503
        allowed_methods=["GET"],  # arXiv API 主要是 GET
        raise_on_status=False,  # 让 raise_for_status() 处理最终错误
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    # arXiv 使用 http 和 https, 都挂载适配器
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def parse_date(date_str: str) -> datetime:
    """解析日期字符串并返回datetime对象"""
    # 尝试多种格式解析（YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD）
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"无法解析日期格式: {date_str}")


def process_arxiv_entry(entry) -> dict[str, Any] | None:
    """处理单个 arXiv 条目并提取信息"""
    try:
        # 提取 arXiv ID 和链接
        entry_id_text = entry.findtext(f"{ATOM_NS}id")
        arxiv_id = (
            entry_id_text.split("/abs/")[-1]
            if entry_id_text and "/abs/" in entry_id_text
            else "N/A"
        )

        # 获取摘要页链接
        link_elem = entry.find(f"{ATOM_NS}link[@rel='alternate'][@type='text/html']")
        link = link_elem.attrib["href"] if link_elem is not None else entry_id_text

        # 提取标题
        title = entry.findtext(f"{ATOM_NS}title", "无标题").strip()

        # 提取作者
        authors = [
            author.findtext(f"{ATOM_NS}name", "").strip()
            for author in entry.findall(f"{ATOM_NS}author")
            if author.findtext(f"{ATOM_NS}name")
        ]

        # 提取发表日期
        published_str = entry.findtext(f"{ATOM_NS}published")
        publication_date = "日期未知"
        if published_str:
            try:
                # arXiv 日期格式为 "YYYY-MM-DDTHH:MM:SSZ"
                pub_dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
                publication_date = pub_dt.strftime("%Y-%m-%d")
            except ValueError:
                logger.warning(f"无法解析发表日期: {published_str}")

        # 提取摘要
        summary = entry.findtext(f"{ATOM_NS}summary", "无摘要").strip()

        # 提取主要 arXiv 分类
        primary_category_elem = entry.find("{http://arxiv.org/schemas/atom}primary_category")
        category = (
            primary_category_elem.attrib.get("term", "N/A")
            if primary_category_elem is not None
            else "N/A"
        )

        # 提取PDF链接
        pdf_link_elem = entry.find(f"{ATOM_NS}link[@title='pdf']")
        pdf_link = pdf_link_elem.attrib["href"] if pdf_link_elem is not None else None

        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "category": category,
            "publication_date": publication_date,
            "abstract": summary,
            "arxiv_link": link,
            "pdf_link": pdf_link,
        }

    except Exception as e:
        logger.warning(f"处理 arXiv 条目时发生错误: {str(e)}")
        return None


def search_arxiv(
    keyword: str,
    email: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    搜索 arXiv 文献数据库

    参数:
        keyword: 搜索关键词
        email: 联系邮箱（可选）
        start_date: 开始日期，格式：YYYY-MM-DD（可选）
        end_date: 结束日期，格式：YYYY-MM-DD（可选）
        max_results: 最大返回结果数量，默认10

    返回:
        包含搜索结果的字典
    """
    try:
        # 验证关键词
        if not keyword or not keyword.strip():
            return {
                "articles": [],
                "total_count": 0,
                "message": "关键词不能为空",
                "error": "关键词不能为空",
            }

        # 验证最大结果数
        if not isinstance(max_results, int) or max_results < 1:
            return {
                "articles": [],
                "total_count": 0,
                "message": "max_results必须为大于等于1的整数",
                "error": "max_results必须为大于等于1的整数",
            }

        # 初始化带重试策略的会话
        session = create_retry_session()

        # 构建基础查询
        search_query_parts = [f"all:{keyword.strip()}"]

        # 处理日期参数
        if start_date or end_date:
            try:
                # 解析日期
                end_dt = parse_date(end_date) if end_date else datetime.now()
                start_dt = parse_date(start_date) if start_date else end_dt - relativedelta(years=3)

                # 检查时间范围有效性
                if start_dt > end_dt:
                    return {
                        "articles": [],
                        "total_count": 0,
                        "message": "起始时间不能晚于终止时间",
                        "error": "起始时间不能晚于终止时间",
                    }

                # 格式化为arXiv日期范围查询条件
                start_str = start_dt.strftime("%Y%m%d") + "0000"
                end_str = end_dt.strftime("%Y%m%d") + "2359"
                date_filter = f"submittedDate:[{start_str} TO {end_str}]"
                search_query_parts.append(date_filter)

            except ValueError as e:
                return {
                    "articles": [],
                    "total_count": 0,
                    "message": f"日期参数错误: {str(e)}",
                    "error": f"日期参数错误: {str(e)}",
                }

        # 组合查询字符串
        full_query = " AND ".join(search_query_parts)
        encoded_query = urllib.parse.quote_plus(full_query)

        base_url = "http://export.arxiv.org/api/query?"
        articles = []
        start_index = 0
        results_per_page = min(100, max_results)  # arXiv 推荐每次不超过100条

        logger.info(f"开始搜索 arXiv: {keyword}")

        while len(articles) < max_results:
            num_to_fetch = min(results_per_page, max_results - len(articles))
            if num_to_fetch <= 0:
                break

            # 构建请求URL
            url = (
                f"{base_url}search_query={encoded_query}"
                f"&start={start_index}"
                f"&max_results={num_to_fetch}"
                f"&sortBy=submittedDate&sortOrder=descending"
            )

            # 设置请求头
            headers = {
                "User-Agent": (
                    f"Europe-PMC-MCP-Server/1.0 (contact: {email})"
                    if email
                    else "Europe-PMC-MCP-Server/1.0"
                )
            }

            response = session.get(url, headers=headers, timeout=45)
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get("Content-Type", "")
            if "application/atom+xml" not in content_type:
                logger.error(f"意外的响应内容类型: {content_type}")
                return {
                    "articles": [],
                    "total_count": 0,
                    "message": "arXiv API 返回了非预期的内容",
                    "error": "arXiv API 返回了非预期的内容",
                }

            # 解析XML响应
            root = ET.fromstring(response.content)
            entries = root.findall(f"{ATOM_NS}entry")

            # 如果当前页没有结果，停止获取
            if not entries:
                logger.info("arXiv API 返回了空结果页，停止获取")
                break

            # 处理本页文献
            for entry in entries:
                if len(articles) >= max_results:
                    break

                article_info = process_arxiv_entry(entry)
                if article_info:
                    articles.append(article_info)

            # 更新起始索引
            start_index += len(entries)

            # 如果获取到的数量少于请求的数量，说明是最后一页
            if len(entries) < num_to_fetch:
                logger.info("获取到的结果数少于请求数，认为是最后一页")
                break

        logger.info(f"成功获取 {len(articles)} 篇 arXiv 文献")

        return {
            "articles": articles,
            "total_count": len(articles),
            "message": (
                f"找到 {len(articles)} 篇相关文献" if articles else "未找到与查询匹配的相关文献"
            ),
            "error": None,
            "search_info": {
                "keyword": keyword,
                "date_range": (
                    f"{start_date} 到 {end_date}" if start_date or end_date else "无日期限制"
                ),
                "max_results": max_results,
            },
        }

    except requests.exceptions.Timeout:
        logger.error("arXiv API 请求超时")
        return {
            "articles": [],
            "total_count": 0,
            "message": "请求 arXiv API 超时",
            "error": "请求 arXiv API 超时",
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"arXiv API 网络请求错误: {str(e)}")
        return {
            "articles": [],
            "total_count": 0,
            "message": f"网络请求错误: {str(e)}",
            "error": f"网络请求错误: {str(e)}",
        }

    except ET.ParseError as e:
        logger.error(f"解析 arXiv XML 响应失败: {str(e)}")
        return {
            "articles": [],
            "total_count": 0,
            "message": "解析 arXiv 返回的 XML 数据时出错",
            "error": "解析 arXiv 返回的 XML 数据时出错",
        }

    except Exception as e:
        logger.error(f"处理 arXiv 搜索时发生未知错误: {str(e)}")
        return {
            "articles": [],
            "total_count": 0,
            "message": f"处理错误: {str(e)}",
            "error": f"处理错误: {str(e)}",
        }


class ArXivSearchService:
    """arXiv搜索服务类"""

    def __init__(self, logger):
        self.logger = logger

    def search(self, keyword: str, max_results: int = 10, **kwargs) -> dict[str, Any]:
        """搜索arXiv文献"""
        return search_arxiv(keyword=keyword, max_results=max_results, logger=self.logger, **kwargs)

    def fetch(self, identifier: str, id_type: str = "arxiv_id", **kwargs) -> dict[str, Any]:
        """获取arXiv文献详情"""
        if id_type != "arxiv_id":
            return {
                "success": False,
                "error": f"arXiv服务不支持标识符类型: {id_type}",
                "article": None,
            }

        # 通过arXiv ID搜索获取详情
        result = search_arxiv(keyword=f"id:{identifier}", max_results=1, logger=self.logger)

        if result.get("articles"):
            return {"success": True, "article": result["articles"][0], "source": "arxiv"}
        else:
            return {"success": False, "error": f"未找到arXiv文献: {identifier}", "article": None}


def create_arxiv_service(logger):
    """创建arXiv服务实例"""
    return ArXivSearchService(logger)
