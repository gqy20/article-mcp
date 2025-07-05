class PubMedService:
    """PubMed 关键词搜索服务 (控制在 500 行以内)"""

    def __init__(self, logger=None):
        import logging, re
        from datetime import datetime
        self.logger = logger or logging.getLogger(__name__)
        self.re = re  # 保存模块引用，方便内部使用
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.headers = {"User-Agent": "PubMedSearch/1.0"}
        self.MONTH_MAP = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
            "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

    # ------------------------ 公共辅助方法 ------------------------ #
    @staticmethod
    def _validate_email(email: str) -> bool:
        return bool(email and "@" in email and "." in email.split("@")[-1])

    def _format_date_range(self, start_date: str, end_date: str) -> str:
        """构建 PubMed 日期过滤语句 (PDAT)"""
        from datetime import datetime
        fmt_in = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]
        def _parse(d):
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
    def _process_article(self, article_xml):
        import xml.etree.ElementTree as ET
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
            abs_parts = ["".join(n.itertext()).strip() for n in article.findall("./Abstract/AbstractText")]
            abstract = " ".join([p for p in abs_parts if p]) if abs_parts else "无摘要"

            # 提取 DOI（从 PubmedData 或 Article 中）
            doi = None
            doi_link = None
            pubmed_data = article_xml.find("./PubmedData")
            if pubmed_data is not None:
                doi_elem = pubmed_data.find("./ArticleIdList/ArticleId[@IdType='doi']")
                if doi_elem is not None and doi_elem.text:
                    doi = doi_elem.text.strip()
                    doi_link = f"https://doi.org/{doi}"

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
                "arxiv_id": None,
                "arxiv_link": None,
                "semantic_scholar_id": None,
                "semantic_scholar_link": None
            }
        except Exception as e:
            self.logger.warning(f"解析文献失败: {e}")
            return None

    # ------------------------ 对外接口 ------------------------ #
    def search(self, keyword: str, email: str = None, start_date: str = None, end_date: str = None, max_results: int = 10):
        """关键词搜索 PubMed，返回与 Europe PMC 一致的结构"""
        import requests, xml.etree.ElementTree as ET, time
        start_time = time.time()
        try:
            if email and not self._validate_email(email):
                self.logger.info("邮箱格式不正确，将不在请求中携带 email 参数")
                email = None

            # 构建查询语句
            term = keyword.strip()
            date_filter = self._format_date_range(start_date, end_date)
            if date_filter:
                term = f"{term} AND {date_filter}"

            esearch_params = {
                "db": "pubmed",
                "term": term,
                "retmax": str(max_results),
                "retmode": "xml"
            }
            if email:
                esearch_params["email"] = email

            self.logger.info(f"PubMed ESearch: {term}")
            r = requests.get(self.base_url + "esearch.fcgi", params=esearch_params, headers=self.headers, timeout=15)
            r.raise_for_status()

            ids = ET.fromstring(r.content).findall(".//Id")
            if not ids:
                return {"articles": [], "message": "未找到相关文献", "error": None}
            pmids = [elem.text for elem in ids[:max_results]]

            # EFETCH
            efetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "xml"
            }
            if email:
                efetch_params["email"] = email

            self.logger.info(f"PubMed EFetch {len(pmids)} 篇文献")
            r2 = requests.get(self.base_url + "efetch.fcgi", params=efetch_params, headers=self.headers, timeout=20)
            r2.raise_for_status()
            root = ET.fromstring(r2.content)

            articles = []
            for art in root.findall(".//PubmedArticle"):
                info = self._process_article(art)
                if info:
                    articles.append(info)
            return {
                "articles": articles,
                "error": None,
                "message": f"找到 {len(articles)} 篇相关文献" if articles else "未找到相关文献",
                "processing_time": round(time.time() - start_time, 2)
            }
        except requests.exceptions.RequestException as e:
            return {"articles": [], "error": f"网络请求错误: {e}", "message": None}
        except Exception as e:
            return {"articles": [], "error": f"处理错误: {e}", "message": None}

    # ------------------------ 引用文献获取 ------------------------ #
    def get_citing_articles(self, pmid: str, email: str = None, max_results: int = 20):
        """获取引用该 PMID 的文献信息（Semantic Scholar → PubMed 补全）"""
        import requests, xml.etree.ElementTree as ET, time
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
                "limit": max_results
            }
            self.logger.info(f"Semantic Scholar 查询引用: {ss_url}")
            ss_resp = requests.get(ss_url, params=ss_params, timeout=20)
            if ss_resp.status_code != 200:
                return {"citing_articles": [], "error": f"Semantic Scholar 错误 {ss_resp.status_code}", "message": None}

            ss_data = ss_resp.json()
            ss_items = ss_data.get("data", [])
            if not ss_items:
                return {"citing_articles": [], "total_count": 0, "message": "未找到引用文献", "error": None}

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
                    pmid_link = None
                    doi_link = f"https://doi.org/{doi}" if doi else None
                    arxiv_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
                    ss_link = f"https://www.semanticscholar.org/paper/{ss_paper_id}" if ss_paper_id else None
                    
                    # 优先级：DOI > ArXiv > Semantic Scholar
                    primary_link = doi_link or arxiv_link or ss_link
                    
                    interim_articles.append({
                        "pmid": None,
                        "pmid_link": primary_link,
                        "title": paper.get("title"),
                        "authors": [a.get("name") for a in paper.get("authors", [])] if paper.get("authors") else None,
                        "journal_name": paper.get("venue"),
                        "publication_date": paper.get("publicationDate") or str(paper.get("year")),
                        "abstract": None,
                        "doi": doi,
                        "doi_link": doi_link,
                        "arxiv_id": arxiv_id,
                        "arxiv_link": arxiv_link,
                        "semantic_scholar_id": ss_paper_id,
                        "semantic_scholar_link": ss_link
                    })

            # 2. 使用 PubMed EFetch 批量补全
            citing_articles = []
            if pmid_list:
                efetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmid_list),
                    "retmode": "xml",
                    "rettype": "xml"
                }
                if email:
                    efetch_params["email"] = email
                r2 = requests.get(self.base_url + "efetch.fcgi", params=efetch_params, headers=self.headers, timeout=20)
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
                "processing_time": round(time.time() - start_time, 2)
            }
        except requests.exceptions.RequestException as e:
            return {"citing_articles": [], "error": f"网络请求错误: {e}", "message": None}
        except Exception as e:
            return {"citing_articles": [], "error": f"处理错误: {e}", "message": None}


def create_pubmed_service(logger=None):
    """工厂函数，保持接口一致"""
    return PubMedService(logger) 