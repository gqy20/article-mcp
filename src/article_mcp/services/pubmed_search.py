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
    async def get_citing_articles_async(
        self, pmid: str, email: str | None = None, max_results: int = 20
    ) -> dict[str, Any]:
        """异步获取引用该 PMID 的文献信息（Semantic Scholar → PubMed 补全）"""
        import time
        import xml.etree.ElementTree as ET

        import aiohttp

        start_time = time.time()
        try:
            if not pmid or not pmid.isdigit():
                return {"citing_articles": [], "error": "PMID 无效", "message": None}
            if email and not self._validate_email(email):
                email = None

            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 1. 使用 Semantic Scholar Graph API 获取引用列表
                ss_url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}/citations"
                ss_params = {
                    "fields": "title,year,authors,venue,externalIds,publicationDate",
                    "limit": max_results,
                }
                self.logger.info(f"Semantic Scholar 查询引用: {ss_url}")

                async with session.get(ss_url, params=ss_params) as ss_resp:
                    if ss_resp.status != 200:
                        return {
                            "citing_articles": [],
                            "error": f"Semantic Scholar 错误 {ss_resp.status}",
                            "message": None,
                        }

                    ss_data = await ss_resp.json()

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

                    async with session.get(
                        self.base_url + "efetch.fcgi",
                        params=efetch_params,
                        headers=self.headers,
                    ) as r2:
                        r2.raise_for_status()
                        efetch_content = await r2.text()

                    root = ET.fromstring(efetch_content.encode())
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

        except aiohttp.ClientError as e:
            return {"citing_articles": [], "error": f"网络请求错误: {e}", "message": None}
        except Exception as e:
            return {"citing_articles": [], "error": f"处理错误: {e}", "message": None}

    # 保留同步版本作为向后兼容
    def get_citing_articles(
        self, pmid: str, email: str | None = None, max_results: int = 20
    ) -> dict[str, Any]:
        """获取引用该 PMID 的文献信息（同步版本，已废弃）

        注意：此函数保留仅为向后兼容，请使用 get_citing_articles_async() 代替。
        """
        import asyncio

        self.logger.warning(
            "get_citing_articles() 是同步版本，已废弃。请使用 get_citing_articles_async()"
        )

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，使用 asyncio.create_task
                import warnings

                warnings.warn(
                    "在异步上下文中调用同步方法，请使用 get_citing_articles_async()",
                    DeprecationWarning,
                    stacklevel=2,
                )
                # 无法在运行的循环中运行，返回错误
                return {
                    "citing_articles": [],
                    "error": "请在异步上下文中使用 get_citing_articles_async()",
                    "message": None,
                }
            else:
                return loop.run_until_complete(
                    self.get_citing_articles_async(pmid, email, max_results)
                )
        except Exception as e:
            return {"citing_articles": [], "error": f"同步包装器错误: {e}", "message": None}

    def _extract_sections_from_xml(
        self,
        xml_content: str,
        requested_sections: list[str],
        section_mapping: dict[str, list[str]],
        sections_found: list[str],
        sections_missing: list[str],
    ) -> str:
        """从 XML 中提取指定的章节内容

        Args:
            xml_content: 原始 XML 内容
            requested_sections: 请求的章节名称列表（已转为小写）
            section_mapping: 章节名称映射表
            sections_found: 输出参数，找到的章节列表
            sections_missing: 输出参数，未找到的章节列表

        Returns:
            只包含指定章节的 XML 内容
        """
        import xml.etree.ElementTree as ET

        try:
            # 解析 XML
            root = ET.fromstring(xml_content)

            # 收集所有匹配的章节元素
            matched_sections: list[ET.Element] = []

            # 特殊处理：abstract 不在 body 内，而是独立的 abstract 元素
            if "abstract" in requested_sections:
                abstract_elem = root.find(".//abstract")
                if abstract_elem is not None:
                    matched_sections.append(abstract_elem)
                    sections_found.append("abstract")
                else:
                    sections_missing.append("abstract")

            # 查找 body 元素
            body = root.find(".//body")
            if body is None:
                # 如果找不到 body 且没有找到 abstract，返回空内容
                if not matched_sections:
                    sections_missing.extend(
                        [s for s in requested_sections if s not in sections_found]
                    )
                # 只有 abstract 的情况，直接构建 XML
                root_elem = ET.Element("root")
                for section in matched_sections:
                    root_elem.append(section)
                result_parts = []
                for child in root_elem:
                    result_parts.append(ET.tostring(child, encoding="unicode"))
                return "".join(result_parts)

            # 在 body 内查找其他章节
            for section_elem in body.findall(".//sec"):
                # 获取 sec-type 属性和标题
                sec_type = section_elem.get("sec-type", "").lower()
                title_elem = section_elem.find("./title")
                title_text = (
                    title_elem.text.lower() if title_elem is not None and title_elem.text else ""
                )

                # 检查此章节是否匹配任何请求的章节
                for requested in requested_sections:
                    # 获取该章节的所有可能名称
                    possible_names = section_mapping.get(requested, [requested])

                    # 检查是否匹配（通过 sec-type 或 title）
                    if sec_type in possible_names or title_text in possible_names:
                        matched_sections.append(section_elem)
                        if requested not in sections_found:
                            sections_found.append(requested)
                        break

            # 记录未找到的章节
            for requested in requested_sections:
                if requested not in sections_found:
                    sections_missing.append(requested)

            # 如果没有找到任何章节，返回空字符串
            if not matched_sections:
                return ""

            # 构建只包含匹配章节的 XML
            # abstract 和其他章节（在 body 内）分开处理
            # 创建根元素
            root_elem = ET.Element("root")

            # 提取 abstract（在根级别）
            body_sections = []
            for section in matched_sections:
                if section.tag == "abstract":
                    root_elem.append(section)
                else:
                    body_sections.append(section)

            # 如果有 body 内的章节，创建 body 元素
            if body_sections:
                body_elem = ET.Element("body")
                for section in body_sections:
                    body_elem.append(section)
                root_elem.append(body_elem)

            # 转换回字符串（只返回子元素的内容，不包含 root 标签）
            result_parts = []
            for child in root_elem:
                result_parts.append(ET.tostring(child, encoding="unicode"))
            return "".join(result_parts)

        except ET.ParseError as e:
            self.logger.warning(f"XML 解析失败: {e}")
            sections_missing.extend(requested_sections)
            return ""
        except Exception as e:
            self.logger.warning(f"章节提取失败: {e}")
            sections_missing.extend(requested_sections)
            return ""

    async def get_pmc_fulltext_html_async(
        self, pmc_id: str, sections: list[str] | None = None
    ) -> dict[str, Any]:
        """异步通过 PMC ID 获取全文内容（三种格式）

        设计原则：
        - 必须有 PMCID 才能获取全文
        - 无 PMCID 直接返回错误，不降级
        - 只返回全文格式，不返回元数据（其他工具负责）
        - 支持按章节提取内容

        参数说明：
        - pmc_id: 必需，PMC 标识符（如："PMC1234567" 或 "1234567"）
        - sections: 可选，要提取的章节名称列表（如：["methods", "discussion"]）
                   None 表示返回全部章节（默认）

        返回值说明：
        - pmc_id: PMC 标识符（标准化格式）
        - fulltext_xml: 原始 XML 格式（或指定章节的 XML）
        - fulltext_markdown: Markdown 格式
        - fulltext_text: 纯文本格式
        - fulltext_available: 是否可获取全文
        - sections_requested: 请求的章节列表（仅在指定章节时返回）
        - sections_found: 找到的章节列表（仅在指定章节时返回）
        - sections_missing: 未找到的章节列表（仅在指定章节时返回）
        - error: 错误信息（如果有）

        使用场景：
        - 获取开放获取文章的全文内容
        - 与 get_article_details 配合获取完整信息
        - 提取特定章节（如 Methods、Discussion）
        """

        # 章节名称映射表：处理命名变体
        SECTION_MAPPING = {
            # 方法类
            "methods": ["methods", "methodology", "materials and methods", "materials"],
            "introduction": ["introduction", "intro", "background"],
            "results": ["results", "findings"],
            "discussion": ["discussion", "conclusions"],
            "conclusion": ["conclusion", "conclusions"],
            "abstract": ["abstract", "summary"],
            "references": ["references", "bibliography"],
            "appendix": ["appendix", "supplementary"],
        }

        import aiohttp

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

            self.logger.info(f"异步请求 PMC 全文: {normalized_pmc_id}")

            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(xml_url, params=params) as response:
                    if response.status != 200:
                        return {
                            "pmc_id": pmc_id if pmc_id else None,
                            "fulltext_xml": None,
                            "fulltext_markdown": None,
                            "fulltext_text": None,
                            "fulltext_available": False,
                            "error": f"HTTP 错误: {response.status}",
                        }
                    fulltext_xml = await response.text()

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

            # ==================== 章节提取逻辑 ====================
            sections_requested: list[str] | None = None
            sections_found: list[str] = []
            sections_missing: list[str] = []

            if sections is not None:
                # 规范化请求的章节名称（转为小写）
                sections_requested = [s.strip().lower() for s in sections if s and s.strip()]

                # 如果请求了章节，进行提取
                # 注意：空列表被视为有效的"请求空章节"，应该返回空内容
                if sections_requested or sections == []:
                    # 空列表直接返回空内容
                    if sections == []:
                        fulltext_xml = ""
                        sections_requested = []
                    else:
                        fulltext_xml = self._extract_sections_from_xml(
                            fulltext_xml,
                            sections_requested,
                            SECTION_MAPPING,
                            sections_found,
                            sections_missing,
                        )

            # 转换为 Markdown 和 纯文本
            fulltext_markdown = None
            fulltext_text = None

            # 如果 XML 为空（如请求空章节列表），直接设置空字符串
            if not fulltext_xml or not fulltext_xml.strip():
                fulltext_markdown = ""
                fulltext_text = ""
            else:
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

            # 构建返回值
            result = {
                "pmc_id": normalized_pmc_id,
                "fulltext_xml": fulltext_xml,
                "fulltext_markdown": fulltext_markdown,
                "fulltext_text": fulltext_text,
                "fulltext_available": True,
                "error": None,
            }

            # 如果请求了特定章节，添加章节信息
            if sections_requested is not None:
                result["sections_requested"] = sections_requested
                result["sections_found"] = sections_found
                result["sections_missing"] = sections_missing

            return result

        except aiohttp.ClientError as e:
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

    # 保留同步版本作为向后兼容
    def get_pmc_fulltext_html(
        self, pmc_id: str, sections: list[str] | None = None
    ) -> dict[str, Any]:
        """通过 PMC ID 获取全文内容（同步版本，已废弃）

        注意：此函数保留仅为向后兼容，请使用 get_pmc_fulltext_html_async() 代替。
        """
        import asyncio

        self.logger.warning(
            "get_pmc_fulltext_html() 是同步版本，已废弃。请使用 get_pmc_fulltext_html_async()"
        )

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，返回错误
                return {
                    "pmc_id": None,
                    "fulltext_xml": None,
                    "fulltext_markdown": None,
                    "fulltext_text": None,
                    "fulltext_available": False,
                    "error": "请在异步上下文中使用 get_pmc_fulltext_html_async()",
                }
            else:
                return loop.run_until_complete(self.get_pmc_fulltext_html_async(pmc_id, sections))
        except Exception as e:
            return {
                "pmc_id": pmc_id if pmc_id else None,
                "fulltext_xml": None,
                "fulltext_markdown": None,
                "fulltext_text": None,
                "fulltext_available": False,
                "error": f"同步包装器错误: {str(e)}",
            }


def create_pubmed_service(logger: logging.Logger | None = None) -> PubMedService:
    """工厂函数，保持接口一致"""
    return PubMedService(logger)
