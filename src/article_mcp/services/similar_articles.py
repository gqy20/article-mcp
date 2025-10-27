import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
from typing import Any

import requests

# 创建日志记录器
logger = logging.getLogger(__name__)

# 月份名称到数字的映射
MONTH_MAP = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}

# NCBI E-utils 配置
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TOOL_NAME = "europe_pmc_mcp_server"
EFETCH_BATCH_SIZE = 100  # 每次批量获取的文章数量


def parse_pubmed_article(article_xml: ET.Element) -> dict[str, Any] | None:
    """解析PubMed文章XML元素"""
    if article_xml is None:
        return None

    pmid = None
    try:
        medline_citation = article_xml.find("./MedlineCitation")
        pubmed_data = article_xml.find("./PubmedData")

        if medline_citation is None:
            return None

        pmid = medline_citation.findtext("./PMID")
        article = medline_citation.find("./Article")

        if article is None or pmid is None:
            return None

        # 提取标题
        title_element = article.find("./ArticleTitle")
        title = (
            "".join(title_element.itertext()).strip() if title_element is not None else "未找到标题"
        )

        # 提取作者
        author_list = []
        author_elements = article.findall("./AuthorList/Author")
        for author in author_elements:
            last_name = author.findtext("LastName")
            fore_name = author.findtext("ForeName")
            collective_name = author.findtext("CollectiveName")

            if collective_name:
                author_list.append(collective_name.strip())
            elif last_name:
                name_parts = []
                if fore_name:
                    name_parts.append(fore_name.strip())
                name_parts.append(last_name.strip())
                author_list.append(" ".join(name_parts))

        # 提取摘要
        abstract_parts = []
        abstract_elements = article.findall("./Abstract/AbstractText")
        if abstract_elements:
            for part in abstract_elements:
                label = part.get("Label")
                text = "".join(part.itertext()).strip()
                if label and text:
                    abstract_parts.append(f"{label.upper()}: {text}")
                elif text:
                    abstract_parts.append(text)

        abstract = "\n".join(abstract_parts) if abstract_parts else None

        # 提取PMCID
        pmcid = None
        pmcid_link = None
        if pubmed_data is not None:
            pmc_element = pubmed_data.find("./ArticleIdList/ArticleId[@IdType='pmc']")
            if pmc_element is not None and pmc_element.text:
                pmcid_raw = pmc_element.text.strip().upper()
                if pmcid_raw.startswith("PMC"):
                    pmcid = pmcid_raw
                    pmcid_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"

        # 提取期刊名称
        journal_title_raw = article.findtext("./Journal/Title")
        journal_name = None
        if journal_title_raw:
            journal_name = re.sub(r"\s*\(.*?\)\s*", "", journal_title_raw).strip()
            if not journal_name:
                journal_name = journal_title_raw.strip()

        # 提取发表日期
        pub_date_element = article.find("./Journal/JournalIssue/PubDate")
        publication_date = None
        if pub_date_element is not None:
            year = pub_date_element.findtext("Year")
            if year and year.isdigit():
                month = pub_date_element.findtext("Month", "01")
                day = pub_date_element.findtext("Day", "01")

                # 处理月份名称
                if month in MONTH_MAP:
                    month = MONTH_MAP[month]
                elif month.isdigit():
                    month = month.zfill(2)
                else:
                    month = "01"

                day = day.zfill(2) if day.isdigit() else "01"
                publication_date = f"{year}-{month}-{day}"

        return {
            "title": title,
            "authors": author_list if author_list else None,
            "journal": journal_name,
            "publication_date": publication_date,
            "pmid": pmid,
            "pmid_link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "pmcid": pmcid,
            "pmcid_link": pmcid_link,
            "abstract": abstract,
        }
    except Exception as e:
        logger.error(f"解析文章 PMID {pmid or 'UNKNOWN'} 时出错: {e}")
        return None


def get_similar_articles_by_doi(
    doi: str, email: str = None, max_results: int = 20
) -> dict[str, Any]:
    """根据DOI获取相似文章"""
    try:
        # 验证DOI
        if not doi or not doi.strip():
            return {
                "original_article": None,
                "similar_articles": [],
                "total_similar_count": 0,
                "retrieved_count": 0,
                "error": "DOI不能为空",
            }

        if not email:
            email = "user@example.com"

        headers = {"User-Agent": f"{TOOL_NAME}/1.0 ({email})"}

        # 步骤1：通过DOI获取初始文章的PMID
        logger.info(f"正在为 DOI {doi} 搜索 PMID")
        esearch_params = {
            "db": "pubmed",
            "term": doi,
            "retmax": 1,
            "retmode": "xml",
            "email": email,
            "tool": TOOL_NAME,
        }

        response = requests.get(
            f"{NCBI_BASE_URL}esearch.fcgi", params=esearch_params, headers=headers
        )
        response.raise_for_status()

        esearch_xml = ET.fromstring(response.content)
        ids = esearch_xml.findall(".//Id")

        if not ids:
            return {
                "original_article": None,
                "similar_articles": [],
                "total_similar_count": 0,
                "message": f"未找到 DOI: {doi} 对应的 PubMed 记录",
            }

        initial_pmid = ids[0].text
        logger.info(f"找到初始文章 PMID: {initial_pmid}")

        # 步骤2：获取初始文章详情
        efetch_params = {
            "db": "pubmed",
            "id": initial_pmid,
            "rettype": "xml",
            "retmode": "xml",
            "email": email,
            "tool": TOOL_NAME,
        }

        response = requests.get(
            f"{NCBI_BASE_URL}efetch.fcgi", params=efetch_params, headers=headers
        )
        response.raise_for_status()

        efetch_xml = ET.fromstring(response.content)
        original_article_xml = efetch_xml.find(".//PubmedArticle")
        original_article = parse_pubmed_article(original_article_xml)

        if not original_article:
            return {
                "original_article": None,
                "similar_articles": [],
                "total_similar_count": 0,
                "error": f"无法解析初始 PMID: {initial_pmid} 的文章信息",
            }

        # 步骤3：使用elink查找相关文章
        elink_params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": initial_pmid,
            "linkname": "pubmed_pubmed",
            "cmd": "neighbor_history",
            "email": email,
            "tool": TOOL_NAME,
        }

        response = requests.get(f"{NCBI_BASE_URL}elink.fcgi", params=elink_params, headers=headers)
        response.raise_for_status()

        elink_xml = ET.fromstring(response.content)
        webenv_elink = elink_xml.findtext(".//WebEnv")
        query_key_elink = elink_xml.findtext(".//LinkSetDbHistory/QueryKey")

        if not webenv_elink or not query_key_elink:
            return {
                "original_article": original_article,
                "similar_articles": [],
                "total_similar_count": 0,
                "message": "找到了原始文章，但未找到相关文章",
            }

        # 步骤4：使用日期过滤获取相关文章
        today = datetime.now()
        five_years_ago = today - timedelta(days=5 * 365.25)
        min_date = five_years_ago.strftime("%Y/%m/%d")
        max_date = today.strftime("%Y/%m/%d")

        esearch_params2 = {
            "db": "pubmed",
            "query_key": query_key_elink,
            "WebEnv": webenv_elink,
            "retmax": str(max_results),
            "retmode": "xml",
            "datetype": "pdat",
            "mindate": min_date,
            "maxdate": max_date,
            "email": email,
            "tool": TOOL_NAME,
            "usehistory": "y",
        }

        response = requests.get(
            f"{NCBI_BASE_URL}esearch.fcgi", params=esearch_params2, headers=headers
        )
        response.raise_for_status()

        esearch_xml2 = ET.fromstring(response.content)
        total_count = int(esearch_xml2.findtext(".//Count", "0"))
        webenv_filtered = esearch_xml2.findtext(".//WebEnv")
        query_key_filtered = esearch_xml2.findtext(".//QueryKey")

        if total_count == 0:
            return {
                "original_article": original_article,
                "similar_articles": [],
                "total_similar_count": 0,
                "message": "在最近5年内未找到相关文章",
            }

        # 步骤5：批量获取相关文章详情
        similar_articles = []
        actual_fetch_count = min(total_count, max_results)

        efetch_params_batch = {
            "db": "pubmed",
            "query_key": query_key_filtered,
            "WebEnv": webenv_filtered,
            "retstart": "0",
            "retmax": str(actual_fetch_count),
            "rettype": "xml",
            "retmode": "xml",
            "email": email,
            "tool": TOOL_NAME,
        }

        response = requests.get(
            f"{NCBI_BASE_URL}efetch.fcgi", params=efetch_params_batch, headers=headers
        )
        response.raise_for_status()

        efetch_xml_batch = ET.fromstring(response.content)
        article_elements = efetch_xml_batch.findall(".//PubmedArticle")

        for article_xml in article_elements:
            article_details = parse_pubmed_article(article_xml)
            if article_details:
                similar_articles.append(article_details)

        logger.info(f"成功获取了 {len(similar_articles)} 篇相关文章")

        return {
            "original_article": original_article,
            "similar_articles": similar_articles,
            "total_similar_count": total_count,
            "retrieved_count": len(similar_articles),
            "message": f"成功找到并获取了 {len(similar_articles)} 篇相关文章",
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {e}")
        return {"error": f"网络请求错误: {e}"}
    except ET.ParseError as e:
        logger.error(f"XML解析错误: {e}")
        return {"error": f"XML解析错误: {e}"}
    except Exception as e:
        logger.error(f"获取相似文章时出错: {e}")
        return {"error": f"获取相似文章时出错: {e}"}
