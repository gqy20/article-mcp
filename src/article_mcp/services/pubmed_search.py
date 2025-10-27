from typing import Any


class PubMedService:
    """PubMed 关键词搜索服务 (控制在 500 行以内)"""

    def __init__(self, logger=None):
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
    def _load_journal_cache(self):
        """加载本地期刊信息缓存"""
        import json
        import os

        try:
            cache_path = os.path.join(os.path.dirname(__file__), "resource", "journal_info.json")
            if os.path.exists(cache_path):
                with open(cache_path, encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.warning(f"加载期刊缓存失败: {e}")
            return {}

    def _save_journal_cache(self, cache_data):
        """保存期刊信息到本地缓存"""
        import json
        import os

        try:
            cache_path = os.path.join(os.path.dirname(__file__), "resource", "journal_info.json")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"保存期刊缓存失败: {e}")

    def _query_easyscholar_api(self, journal_name: str, secret_key: str):
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
                return data["data"]
            else:
                self.logger.warning(f"EasyScholar API 返回错误: {data.get('msg', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"EasyScholar API 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"EasyScholar API 处理错误: {e}")
            return None

    def _extract_quality_metrics(self, rank_data):
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

    def get_journal_quality(self, journal_name: str, secret_key: str = None):
        """获取期刊质量评估信息（影响因子、分区等）"""
        if not journal_name or not journal_name.strip():
            return {"error": "期刊名称不能为空"}

        journal_name = journal_name.strip()

        # 1. 先从本地缓存查询
        cache = self._load_journal_cache()
        if journal_name in cache:
            rank_data = cache[journal_name].get("rank", {})
            metrics = self._extract_quality_metrics(rank_data)
            if metrics:
                self.logger.info(f"从本地缓存获取期刊信息: {journal_name}")
                return {
                    "journal_name": journal_name,
                    "source": "local_cache",
                    "quality_metrics": metrics,
                    "error": None,
                }

        # 2. 如果本地没有且提供了API密钥，则调用EasyScholar API
        if secret_key:
            api_data = self._query_easyscholar_api(journal_name, secret_key)
            if api_data:
                # 保存到缓存
                if journal_name not in cache:
                    cache[journal_name] = {}
                cache[journal_name]["rank"] = {}

                # 处理官方排名数据
                if "officialRank" in api_data:
                    official = api_data["officialRank"]
                    if "select" in official:
                        cache[journal_name]["rank"].update(official["select"])
                    elif "all" in official:
                        cache[journal_name]["rank"].update(official["all"])

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
                                        cache[journal_name]["rank"][abbr_name.lower()] = rank_text

                self._save_journal_cache(cache)

                # 提取质量指标
                metrics = self._extract_quality_metrics(cache[journal_name]["rank"])
                self.logger.info(f"从 EasyScholar API 获取期刊信息: {journal_name}")
                return {
                    "journal_name": journal_name,
                    "source": "easyscholar_api",
                    "quality_metrics": metrics,
                    "error": None,
                }

        # 3. 都没有找到
        return {
            "journal_name": journal_name,
            "source": None,
            "quality_metrics": {},
            "error": "未找到期刊质量信息"
            + ("（未提供 EasyScholar API 密钥）" if not secret_key else ""),
        }

    def evaluate_articles_quality(self, articles: list, secret_key: str = None):
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

    # ------------------------ 对外接口 ------------------------ #
    def search(
        self,
        keyword: str,
        email: str = None,
        start_date: str = None,
        end_date: str = None,
        max_results: int = 10,
    ):
        """关键词搜索 PubMed，返回与 Europe PMC 一致的结构"""
        import time
        import xml.etree.ElementTree as ET

        import requests

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
                "retmode": "xml",
            }
            if email:
                esearch_params["email"] = email

            self.logger.info(f"PubMed ESearch: {term}")
            r = requests.get(
                self.base_url + "esearch.fcgi",
                params=esearch_params,
                headers=self.headers,
                timeout=15,
            )
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
                "rettype": "xml",
            }
            if email:
                efetch_params["email"] = email

            self.logger.info(f"PubMed EFetch {len(pmids)} 篇文献")
            r2 = requests.get(
                self.base_url + "efetch.fcgi",
                params=efetch_params,
                headers=self.headers,
                timeout=20,
            )
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
                "processing_time": round(time.time() - start_time, 2),
            }
        except requests.exceptions.RequestException as e:
            return {"articles": [], "error": f"网络请求错误: {e}", "message": None}
        except Exception as e:
            return {"articles": [], "error": f"处理错误: {e}", "message": None}

    # ------------------------ 引用文献获取 ------------------------ #
    def get_citing_articles(self, pmid: str, email: str = None, max_results: int = 20):
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
            ss_resp = requests.get(ss_url, params=ss_params, timeout=20)
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
        """通过PMC ID获取全文HTML内容

        功能说明：
        - 通过PMC ID从PMC数据库获取文章的完整HTML内容
        - 支持开放获取的文章全文获取
        - 返回文章的基本信息和HTML全文内容

        参数说明：
        - pmc_id: 必需，PMC标识符（如："PMC1234567"）

        返回值说明：
        - pmc_id: PMC标识符
        - pmc_link: PMC文章链接
        - title: 文章标题
        - authors: 作者列表
        - journal_name: 期刊名称
        - publication_date: 发表日期
        - abstract: 摘要
        - fulltext_html: 完整的HTML全文内容
        - fulltext_available: 是否可获取全文
        - error: 错误信息（如果有）

        使用场景：
        - 获取开放获取文章的全文内容
        - 文献内容深度分析
        - 学术研究资料收集

        技术特点：
        - 基于PMC官方API
        - 支持开放获取文章全文获取
        - 完整的错误处理机制
        """
        import xml.etree.ElementTree as ET

        import requests

        try:
            # 验证PMC ID格式
            if not pmc_id or not pmc_id.strip():
                return {
                    "pmc_id": None,
                    "pmc_link": None,
                    "title": None,
                    "authors": [],
                    "journal_name": None,
                    "publication_date": None,
                    "abstract": None,
                    "fulltext_html": None,
                    "fulltext_available": False,
                    "error": "PMC ID不能为空",
                }

            # 标准化PMC ID格式
            normalized_pmc_id = pmc_id.strip()
            if not normalized_pmc_id.startswith("PMC"):
                normalized_pmc_id = f"PMC{normalized_pmc_id}"

            # 构建PMC链接
            pmc_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{normalized_pmc_id}/"

            # 请求PMC全文XML
            xml_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {"db": "pmc", "id": normalized_pmc_id, "rettype": "xml", "retmode": "xml"}

            self.logger.info(f"请求PMC全文: {normalized_pmc_id}")
            response = requests.get(xml_url, params=params, timeout=30)
            response.raise_for_status()

            # 解析XML
            root = ET.fromstring(response.content)

            # 提取基本信息
            title = root.findtext(".//article-title")
            if not title:
                title = root.findtext(".//article-title", "无标题")

            # 提取作者
            authors = []
            for author_elem in root.findall(".//contrib[@contrib-type='author']"):
                name = author_elem.findtext(".//name/surname")
                forename = author_elem.findtext(".//name/given-names")
                if name and forename:
                    authors.append(f"{forename} {name}")
                elif name:
                    authors.append(name)

            # 提取期刊信息
            journal_name = root.findtext(".//journal-title")
            if not journal_name:
                journal_name = root.findtext(".//journal-id", "未知期刊")

            # 提取发表日期
            pub_date = root.findtext(".//pub-date/year")
            if pub_date:
                month = root.findtext(".//pub-date/month", "01")
                day = root.findtext(".//pub-date/day", "01")
                pub_date = f"{pub_date}-{month.zfill(2)}-{day.zfill(2)}"

            # 提取摘要
            abstract = root.findtext(".//abstract")
            if not abstract:
                abstract_parts = [
                    "".join(elem.itertext()).strip() for elem in root.findall(".//abstract//p")
                ]
                abstract = (
                    " ".join([p for p in abstract_parts if p]) if abstract_parts else "无摘要"
                )

            # 提取全文HTML
            # PMC XML通常不直接包含完整的HTML，需要另外获取
            fulltext_available = True
            fulltext_html = response.text  # 这是XML格式，不是HTML

            return {
                "pmc_id": normalized_pmc_id,
                "pmc_link": pmc_link,
                "title": title,
                "authors": authors,
                "journal_name": journal_name,
                "publication_date": pub_date,
                "abstract": abstract,
                "fulltext_html": fulltext_html,
                "fulltext_available": fulltext_available,
                "error": None,
            }

        except requests.exceptions.RequestException as e:
            return {
                "pmc_id": pmc_id,
                "pmc_link": (
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else None
                ),
                "title": None,
                "authors": [],
                "journal_name": None,
                "publication_date": None,
                "abstract": None,
                "fulltext_html": None,
                "fulltext_available": False,
                "error": f"网络请求错误: {str(e)}",
            }
        except ET.ParseError as e:
            return {
                "pmc_id": pmc_id,
                "pmc_link": (
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else None
                ),
                "title": None,
                "authors": [],
                "journal_name": None,
                "publication_date": None,
                "abstract": None,
                "fulltext_html": None,
                "fulltext_available": False,
                "error": f"XML解析错误: {str(e)}",
            }
        except Exception as e:
            self.logger.error(f"获取PMC全文时发生错误: {str(e)}")
            return {
                "pmc_id": pmc_id,
                "pmc_link": (
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else None
                ),
                "title": None,
                "authors": [],
                "journal_name": None,
                "publication_date": None,
                "abstract": None,
                "fulltext_html": None,
                "fulltext_available": False,
                "error": f"处理错误: {str(e)}",
            }


def create_pubmed_service(logger=None):
    """工厂函数，保持接口一致"""
    return PubMedService(logger)
