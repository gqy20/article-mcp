import asyncio
import logging
from typing import Any


class PubMedService:
    """PubMed 关键词搜索服务 (控制在 500 行以内)"""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        import logging
        import re

        self.logger = logger or logging.getLogger(__name__)
        self.re = re  # 保存模块引用，方便内部使用
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.headers = {"User-Agent": "PubMedSearch/1.0"}
        self.MONTH_MAP = {
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

        # 速率限制：PubMed 要求每秒最多3个请求（无API key时）
        self._request_semaphore: Any = None  # 延迟初始化，异步方法中创建

    # ------------------------ 公共辅助方法 ------------------------ #
    @staticmethod
    def _validate_email(email: str) -> bool:
        return bool(email and "@" in email and "." in email.split("@")[-1])

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        """构建 PubMed 日期过滤语句 (PDAT)"""
        from datetime import datetime

        fmt_in = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]

        def _parse(d: str | None) -> Any:
            if not d:
                return None
            for f in fmt_in:
                try:
                    return datetime.strptime(d, f)
                except ValueError:
                    continue
            return None

        start_dt, end_dt = _parse(start_date), _parse(end_date)
        if not (start_dt or end_dt):
            return ""
        if start_dt and not end_dt:
            end_dt = datetime.now()
        if end_dt and not start_dt:
            # PubMed 允许 1800 年起查找，这里简单使用 1800-01-01
            start_dt = datetime.strptime("1800-01-01", "%Y-%m-%d")
        if start_dt > end_dt:
            start_dt, end_dt = end_dt, start_dt
        return f"({start_dt.strftime('%Y/%m/%d')}[PDAT] : {end_dt.strftime('%Y/%m/%d')}[PDAT])"

    # ------------------------ 核心解析逻辑 ------------------------ #
    def _process_article(self, article_xml: Any) -> dict[str, Any] | None:
        if article_xml is None:
            return None
        try:
            medline = article_xml.find("./MedlineCitation")
            if medline is None:
                return None
            pmid = medline.findtext("./PMID")
            article = medline.find("./Article")
            if article is None:
                return None

            title_elem = article.find("./ArticleTitle")
            title = "".join(title_elem.itertext()).strip() if title_elem is not None else "无标题"

            # 作者
            authors = []
            for author in article.findall("./AuthorList/Author"):
                last = author.findtext("LastName", "").strip()
                fore = author.findtext("ForeName", "").strip()
                coll = author.findtext("CollectiveName")
                if coll:
                    authors.append(coll.strip())
                elif last or fore:
                    authors.append(f"{fore} {last}".strip())

            # 期刊
            journal_raw = article.findtext("./Journal/Title", "未知期刊")
            journal = self.re.sub(r"\s*\(.*?\)\s*", "", journal_raw).strip() or journal_raw

            # 发表日期
            pub_date_elem = article.find("./Journal/JournalIssue/PubDate")
            pub_date = "日期未知"
            if pub_date_elem is not None:
                year = pub_date_elem.findtext("Year")
                month = pub_date_elem.findtext("Month", "01")
                day = pub_date_elem.findtext("Day", "01")
                if month in self.MONTH_MAP:
                    month = self.MONTH_MAP[month]
                month = month.zfill(2) if month.isdigit() else "01"
                day = day.zfill(2) if day.isdigit() else "01"
                if year and year.isdigit():
                    pub_date = f"{year}-{month}-{day}"

            # 摘要
            abs_parts = [
                "".join(n.itertext()).strip() for n in article.findall("./Abstract/AbstractText")
            ]
            abstract = " ".join([p for p in abs_parts if p]) if abs_parts else "无摘要"

            # 提取 DOI（从 PubmedData 或 Article 中）
            doi = None
            doi_link = None
            pmc_id = None
            pmc_link = None
            pubmed_data = article_xml.find("./PubmedData")
            if pubmed_data is not None:
                # 提取 DOI
                doi_elem = pubmed_data.find("./ArticleIdList/ArticleId[@IdType='doi']")
                if doi_elem is not None and doi_elem.text:
                    doi = doi_elem.text.strip()
                    doi_link = f"https://doi.org/{doi}"

                # 提取 PMC ID
                pmc_elem = pubmed_data.find("./ArticleIdList/ArticleId[@IdType='pmc']")
                if pmc_elem is not None and pmc_elem.text:
                    pmc_id = pmc_elem.text.strip()
                    if pmc_id.startswith("PMC"):
                        pmc_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"

            return {
                "pmid": pmid or "N/A",
                "pmid_link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                "title": title,
                "authors": authors,
                "journal_name": journal,
                "publication_date": pub_date,
                "abstract": abstract,
                "doi": doi,
                "doi_link": doi_link,
                "pmc_id": pmc_id,
                "pmc_link": pmc_link,
                "arxiv_id": None,
                "arxiv_link": None,
                "semantic_scholar_id": None,
                "semantic_scholar_link": None,
            }
        except Exception as e:
            self.logger.warning(f"解析文献失败: {e}")
            return None

    # ------------------------ 期刊质量评估 ------------------------ #
    def _query_easyscholar_api(self, journal_name: str, secret_key: str) -> dict[str, Any] | None:
        """调用 EasyScholar API 获取期刊信息"""
        import requests

        try:
            url = "https://www.easyscholar.cc/open/getPublicationRank"
            params = {"secretKey": secret_key, "publicationName": journal_name}

            self.logger.info(f"调用 EasyScholar API 查询期刊: {journal_name}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 200 and data.get("data"):
                return data["data"]  # type: ignore[no-any-return]
            else:
                self.logger.warning(f"EasyScholar API 返回错误: {data.get('msg', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"EasyScholar API 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"EasyScholar API 处理错误: {e}")
            return None

    def _extract_quality_metrics(self, rank_data: Any) -> dict[str, Any]:
        """从期刊排名数据中提取质量指标"""
        if not rank_data:
            return {}

        metrics = {}

        # 提取影响因子
        if "sciif" in rank_data:
            metrics["impact_factor"] = rank_data["sciif"]

        # 提取分区信息
        if "sci" in rank_data:
            metrics["sci_quartile"] = rank_data["sci"]

        if "sciUp" in rank_data:
            metrics["sci_zone"] = rank_data["sciUp"]

        if "sciUpSmall" in rank_data:
            metrics["sci_zone_detail"] = rank_data["sciUpSmall"]

        # 提取JCI
        if "jci" in rank_data:
            metrics["jci"] = rank_data["jci"]

        # 提取5年影响因子
        if "sciif5" in rank_data:
            metrics["impact_factor_5year"] = rank_data["sciif5"]

        return metrics

    def get_journal_quality(
        self, journal_name: str, secret_key: str | None = None
    ) -> dict[str, Any]:
        """获取期刊质量评估信息（影响因子、分区等）

        注意：此方法仅供兼容保留，建议使用 quality_tools 中的 get_journal_quality
        """
        if not journal_name or not journal_name.strip():
            return {"error": "期刊名称不能为空"}

        journal_name = journal_name.strip()

        # 如果提供了 API 密钥，则调用 EasyScholar API
        if secret_key:
            api_data = self._query_easyscholar_api(journal_name, secret_key)
            if api_data:
                # 构建排名数据
                rank_data = {}

                # 处理官方排名数据
                if "officialRank" in api_data:
                    official = api_data["officialRank"]
                    if "select" in official:
                        rank_data.update(official["select"])
                    elif "all" in official:
                        rank_data.update(official["all"])

                # 处理自定义排名数据
                if "customRank" in api_data:
                    custom = api_data["customRank"]
                    if "rankInfo" in custom and "rank" in custom:
                        # 解析自定义排名
                        rank_info_map = {info["uuid"]: info for info in custom["rankInfo"]}
                        for rank_entry in custom["rank"]:
                            if "&&&" in rank_entry:
                                uuid, rank_level = rank_entry.split("&&&", 1)
                                if uuid in rank_info_map:
                                    info = rank_info_map[uuid]
                                    abbr_name = info.get("abbName", "")
                                    rank_text = ""
                                    if rank_level == "1":
                                        rank_text = info.get("oneRankText", "")
                                    elif rank_level == "2":
                                        rank_text = info.get("twoRankText", "")
                                    elif rank_level == "3":
                                        rank_text = info.get("threeRankText", "")
                                    elif rank_level == "4":
                                        rank_text = info.get("fourRankText", "")
                                    elif rank_level == "5":
                                        rank_text = info.get("fiveRankText", "")

                                    if abbr_name and rank_text:
                                        rank_data[abbr_name.lower()] = rank_text

                # 提取质量指标
                metrics = self._extract_quality_metrics(rank_data)
                self.logger.info(f"从 EasyScholar API 获取期刊信息: {journal_name}")
                return {
                    "journal_name": journal_name,
                    "source": "easyscholar_api",
                    "quality_metrics": metrics,
                    "error": None,
                }

        # 未找到或未提供 API 密钥
        return {
            "journal_name": journal_name,
            "source": None,
            "quality_metrics": {},
            "error": "未找到期刊质量信息"
            + ("（未提供 EasyScholar API 密钥）" if not secret_key else ""),
        }

    def evaluate_articles_quality(
        self, articles: list[dict[str, Any]], secret_key: str | None = None
    ) -> list[dict[str, Any]]:
        """批量评估文献的期刊质量"""
        if not articles:
            return []

        evaluated_articles = []
        for article in articles:
            journal_name = article.get("journal_name")
            if journal_name:
                quality_info = self.get_journal_quality(journal_name, secret_key)
                article_copy = article.copy()
                article_copy["journal_quality"] = quality_info
                evaluated_articles.append(article_copy)
            else:
                article_copy = article.copy()
                article_copy["journal_quality"] = {
                    "journal_name": None,
                    "source": None,
                    "quality_metrics": {},
                    "error": "无期刊信息",
                }
                evaluated_articles.append(article_copy)

        return evaluated_articles

    # ------------------------ 异步搜索接口 ------------------------ #
    async def search_async(
        self,
        keyword: str,
        email: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """异步关键词搜索 PubMed，返回与 Europe PMC 一致的结构

        与同步 search() 方法的区别：
        - 使用 aiohttp 替代 requests 进行异步 HTTP 请求
        - 使用 semaphore 进行速率限制（每秒最多3个请求）
        - ESearch 和 EFetch 请求可以并发执行（与其他服务）

        参数说明：
        - keyword: 搜索关键词
        - email: 可选的邮箱地址（用于 API 请求）
        - start_date: 起始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - max_results: 最大返回结果数

        返回值：
        - articles: 文章列表
        - error: 错误信息（如果有）
        - message: 状态消息
        - processing_time: 处理时间（秒）
        """
        import time
        import xml.etree.ElementTree as ET

        import aiohttp

        start_time = time.time()

        # 速率限制
        if self._request_semaphore is None:
            self._request_semaphore = asyncio.Semaphore(3)

        async with self._request_semaphore:
            try:
                if email and not self._validate_email(email):
                    self.logger.info("邮箱格式不正确，将不在请求中携带 email 参数")
                    email = None

                # 构建查询语句
                term = keyword.strip()
                date_filter = self._format_date_range(
                    start_date or "",
                    end_date or "",
                )
                if date_filter:
                    term = f"{term} AND {date_filter}"

                # ESEARCH 请求参数
                esearch_params = {
                    "db": "pubmed",
                    "term": term,
                    "retmax": str(max_results),
                    "retmode": "xml",
                }
                if email:
                    esearch_params["email"] = email

                self.logger.info(f"PubMed 异步 ESearch: {term}")

                # 使用 aiohttp 进行异步请求
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # ESEARCH
                    async with session.get(
                        self.base_url + "esearch.fcgi", params=esearch_params, headers=self.headers
                    ) as response:
                        if response.status != 200:
                            return {
                                "articles": [],
                                "error": f"ESearch HTTP {response.status}",
                                "message": None,
                            }
                        esearch_content = await response.text()

                    ids = ET.fromstring(esearch_content).findall(".//Id")
                    if not ids:
                        return {"articles": [], "message": "未找到相关文献", "error": None}
                    pmids = [elem.text for elem in ids[:max_results] if elem.text]

                    # EFETCH 请求参数
                    efetch_params = {
                        "db": "pubmed",
                        "id": ",".join(pmids),
                        "retmode": "xml",
                        "rettype": "xml",
                    }
                    if email:
                        efetch_params["email"] = email

                    self.logger.info(f"PubMed 异步 EFetch {len(pmids)} 篇文献")

                    # EFETCH
                    async with session.get(
                        self.base_url + "efetch.fcgi", params=efetch_params, headers=self.headers
                    ) as response:
                        if response.status != 200:
                            return {
                                "articles": [],
                                "error": f"EFetch HTTP {response.status}",
                                "message": None,
                            }
                        efetch_content = await response.text()

                    root = ET.fromstring(efetch_content)

                    articles = []
                    for art in root.findall(".//PubmedArticle"):
                        info = self._process_article(art)
                        if info:
                            articles.append(info)

                    return {
                        "articles": articles,
                        "error": None,
                        "message": f"找到 {len(articles)} 篇相关文献"
                        if articles
                        else "未找到相关文献",
                        "processing_time": round(time.time() - start_time, 2),
                    }

            except asyncio.TimeoutError:
                return {"articles": [], "error": "请求超时", "message": None}
            except aiohttp.ClientError as e:
                return {"articles": [], "error": f"网络请求错误: {e}", "message": None}
            except Exception as e:
                return {"articles": [], "error": f"处理错误: {e}", "message": None}

    # ------------------------ 引用文献获取 ------------------------ #
    def get_citing_articles(
        self, pmid: str, email: str | None = None, max_results: int = 20
    ) -> dict[str, Any]:
        """获取引用该 PMID 的文献信息（Semantic Scholar → PubMed 补全）"""
        import time
        import xml.etree.ElementTree as ET

        import requests

        start_time = time.time()
        try:
            if not pmid or not pmid.isdigit():
                return {"citing_articles": [], "error": "PMID 无效", "message": None}
            if email and not self._validate_email(email):
                email = None

            # 1. 使用 Semantic Scholar Graph API 获取引用列表
            ss_url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}/citations"
            ss_params = {
                "fields": "title,year,authors,venue,externalIds,publicationDate",
                "limit": max_results,
            }
            self.logger.info(f"Semantic Scholar 查询引用: {ss_url}")
            ss_resp = requests.get(ss_url, params=ss_params, timeout=20)  # type: ignore[arg-type]
            if ss_resp.status_code != 200:
                return {
                    "citing_articles": [],
                    "error": f"Semantic Scholar 错误 {ss_resp.status_code}",
                    "message": None,
                }

            ss_data = ss_resp.json()
            ss_items = ss_data.get("data", [])
            if not ss_items:
                return {
                    "citing_articles": [],
                    "total_count": 0,
                    "message": "未找到引用文献",
                    "error": None,
                }

            pmid_list = []
            interim_articles = []
            for item in ss_items:
                paper = item.get("citingPaper") or item.get("paper") or {}
                ext_ids = paper.get("externalIds", {})
                ss_pmid = ext_ids.get("PubMed") or ext_ids.get("PMID")
                if ss_pmid and str(ss_pmid).isdigit():
                    pmid_list.append(str(ss_pmid))
                else:
                    # 为没有PMID的文献构建完整信息
                    doi = ext_ids.get("DOI")
                    arxiv_id = ext_ids.get("ArXiv")
                    ss_paper_id = paper.get("paperId")

                    # 构建各种链接
                    doi_link = f"https://doi.org/{doi}" if doi else None
                    arxiv_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
                    ss_link = (
                        f"https://www.semanticscholar.org/paper/{ss_paper_id}"
                        if ss_paper_id
                        else None
                    )

                    # 优先级：DOI > ArXiv > Semantic Scholar
                    primary_link = doi_link or arxiv_link or ss_link

                    interim_articles.append(
                        {
                            "pmid": None,
                            "pmid_link": primary_link,
                            "title": paper.get("title"),
                            "authors": (
                                [a.get("name") for a in paper.get("authors", [])]
                                if paper.get("authors")
                                else None
                            ),
                            "journal_name": paper.get("venue"),
                            "publication_date": paper.get("publicationDate")
                            or str(paper.get("year")),
                            "abstract": None,
                            "doi": doi,
                            "doi_link": doi_link,
                            "arxiv_id": arxiv_id,
                            "arxiv_link": arxiv_link,
                            "semantic_scholar_id": ss_paper_id,
                            "semantic_scholar_link": ss_link,
                        }
                    )

            # 2. 使用 PubMed EFetch 批量补全
            citing_articles = []
            if pmid_list:
                efetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmid_list),
                    "retmode": "xml",
                    "rettype": "xml",
                }
                if email:
                    efetch_params["email"] = email
                r2 = requests.get(
                    self.base_url + "efetch.fcgi",
                    params=efetch_params,
                    headers=self.headers,
                    timeout=20,
                )
                r2.raise_for_status()
                root = ET.fromstring(r2.content)
                for art in root.findall(".//PubmedArticle"):
                    info = self._process_article(art)
                    if info:
                        citing_articles.append(info)

            citing_articles.extend(interim_articles)
            return {
                "citing_articles": citing_articles,
                "total_count": len(ss_items),
                "error": None,
                "message": f"获取 {len(citing_articles)} 条引用文献 (Semantic Scholar + PubMed)",
                "processing_time": round(time.time() - start_time, 2),
            }
        except requests.exceptions.RequestException as e:
            return {"citing_articles": [], "error": f"网络请求错误: {e}", "message": None}
        except Exception as e:
            return {"citing_articles": [], "error": f"处理错误: {e}", "message": None}

    def get_pmc_fulltext_html(self, pmc_id: str) -> dict[str, Any]:
        """通过 PMC ID 获取全文内容（三种格式）

        设计原则：
        - 必须有 PMCID 才能获取全文
        - 无 PMCID 直接返回错误，不降级
        - 只返回全文格式，不返回元数据（其他工具负责）

        参数说明：
        - pmc_id: 必需，PMC 标识符（如："PMC1234567" 或 "1234567"）

        返回值说明：
        - pmc_id: PMC 标识符（标准化格式）
        - fulltext_xml: 原始 XML 格式
        - fulltext_markdown: Markdown 格式
        - fulltext_text: 纯文本格式
        - fulltext_available: 是否可获取全文
        - error: 错误信息（如果有）

        使用场景：
        - 获取开放获取文章的全文内容
        - 与 get_article_details 配合获取完整信息
        """
        import requests

        try:
            # 前置条件：必须有 PMCID
            if not pmc_id or not pmc_id.strip():
                return {
                    "pmc_id": None,
                    "fulltext_xml": None,
                    "fulltext_markdown": None,
                    "fulltext_text": None,
                    "fulltext_available": False,
                    "error": "需要 PMCID 才能获取全文",
                }

            # 标准化 PMC ID
            normalized_pmc_id = pmc_id.strip()
            if not normalized_pmc_id.startswith("PMC"):
                normalized_pmc_id = f"PMC{normalized_pmc_id}"

            # 请求 PMC XML
            xml_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {"db": "pmc", "id": normalized_pmc_id, "rettype": "xml", "retmode": "xml"}

            self.logger.info(f"请求 PMC 全文: {normalized_pmc_id}")
            response = requests.get(xml_url, params=params, timeout=30)
            response.raise_for_status()

            # 原始 XML
            fulltext_xml = response.text

            # 检查是否为空内容
            if not fulltext_xml or not fulltext_xml.strip():
                return {
                    "pmc_id": normalized_pmc_id,
                    "fulltext_xml": None,
                    "fulltext_markdown": None,
                    "fulltext_text": None,
                    "fulltext_available": False,
                    "error": "PMC 返回内容为空",
                }

            # 转换为 Markdown 和 纯文本
            fulltext_markdown = None
            fulltext_text = None

            try:
                # 抑制 BeautifulSoup 的 XML 解析警告
                import re
                import warnings

                from bs4 import XMLParsedAsHTMLWarning

                warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

                from article_mcp.services.html_to_markdown import (
                    html_to_markdown,
                    html_to_text,
                )

                # 只提取正文部分（<body>），不包含标题、作者、摘要等元数据
                body_match = re.search(r"<body[^>]*>(.*?)</body>", fulltext_xml, re.DOTALL)
                body_content = body_match.group(1) if body_match else fulltext_xml

                # 转换为 Markdown（只包含正文）
                fulltext_markdown = html_to_markdown(body_content)

                # 转换为纯文本（也只包含正文）
                fulltext_text = html_to_text(body_content)

            except Exception as conversion_error:
                self.logger.warning(f"全文格式转换失败，使用原始 XML: {conversion_error}")
                fulltext_markdown = fulltext_xml
                fulltext_text = fulltext_xml

            return {
                "pmc_id": normalized_pmc_id,
                "fulltext_xml": fulltext_xml,
                "fulltext_markdown": fulltext_markdown,
                "fulltext_text": fulltext_text,
                "fulltext_available": True,
                "error": None,
            }

        except requests.exceptions.RequestException as e:
            return {
                "pmc_id": pmc_id if pmc_id else None,
                "fulltext_xml": None,
                "fulltext_markdown": None,
                "fulltext_text": None,
                "fulltext_available": False,
                "error": f"网络请求错误: {str(e)}",
            }
        except Exception as e:
            self.logger.error(f"获取 PMC 全文时发生错误: {str(e)}")
            return {
                "pmc_id": pmc_id if pmc_id else None,
                "fulltext_xml": None,
                "fulltext_markdown": None,
                "fulltext_text": None,
                "fulltext_available": False,
                "error": f"处理错误: {str(e)}",
            }


def create_pubmed_service(logger: logging.Logger | None = None) -> PubMedService:
    """工厂函数，保持接口一致"""
    return PubMedService(logger)
