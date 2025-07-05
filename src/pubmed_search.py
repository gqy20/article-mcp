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

            return {
                "pmid": pmid or "N/A",
                "pmid_link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                "title": title,
                "authors": authors,
                "journal_name": journal,
                "publication_date": pub_date,
                "abstract": abstract
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


def create_pubmed_service(logger=None):
    """工厂函数，保持接口一致"""
    return PubMedService(logger) 