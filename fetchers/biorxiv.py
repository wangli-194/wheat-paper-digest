"""
bioRxiv paper fetcher - 按关键词搜索，只拉取相关论文
"""

import logging
import time
from datetime import date, timedelta
from typing import Optional

import requests

from .base import BaseFetcher, PaperMetadata

logger = logging.getLogger(__name__)


class BioRxivFetcher(BaseFetcher):
    """Fetcher for bioRxiv preprint server."""

    API_BASE    = "https://api.biorxiv.org"
    SEARCH_BASE = "https://api.biorxiv.org/search"   # 搜索端点

    def __init__(
        self,
        source_name: str = "bioRxiv",
        server: str = "biorxiv",
        max_results: int = 50,
        **kwargs,
    ):
        super().__init__(source_name=source_name, max_results=max_results)
        self.server = server
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PaperDigest/1.0 (mailto:paper-digest@example.com)",
            "Accept": "application/json",
        })

    def fetch(self, keywords: list[str], lookback_days: int = 7) -> list[PaperMetadata]:
        today      = date.today()
        start_date = today - timedelta(days=max(lookback_days, 3))

        # 核心关键词：只取最相关的，避免搜索结果太泛
        core_keywords = [
            "wheat rust", "stripe rust", "wheat resistance",
            "wheat powdery mildew", "Fusarium head blight",
            "Puccinia", "Blumeria graminis",
            "wheat NLR", "wheat R gene", "Triticum aestivum resistance",
            "plant immunity", "plant resistance", "NLR protein",
            "effector triggered immunity", "plant pathogen",
            "Magnaporthe", "Phytophthora resistance",
        ]

        all_papers: dict[str, PaperMetadata] = {}

        # 方法1：用搜索 API 按关键词搜索（每次搜一个关键词）
        logger.info("[%s] 使用搜索API检索，关键词数: %d", self.source_name, len(core_keywords))
        for kw in core_keywords:
            papers = self._search_keyword(kw, start_date, today)
            for p in papers:
                if p.unique_id not in all_papers:
                    all_papers[p.unique_id] = p
            if papers:
                logger.info("[%s] 关键词'%s'找到%d篇", self.source_name, kw, len(papers))
            time.sleep(0.3)

        # 方法2：兜底，从 plant_biology 分类拉取并过滤
        if not all_papers:
            logger.info("[%s] 搜索API无结果，改用分类API兜底", self.source_name)
            raw = self._fetch_date_range(start_date, today)
            filtered = self._filter_by_keywords(raw, keywords)
            for p in filtered:
                all_papers[p.unique_id] = p

        result = list(all_papers.values())
        result.sort(key=lambda p: p.published_date or date.min, reverse=True)
        logger.info("[%s] 共检索到 %d 篇相关论文", self.source_name, len(result))
        return result[:self.max_results]

    def _search_keyword(self, keyword: str, start: date, end: date) -> list[PaperMetadata]:
        """用 bioRxiv 搜索API按单个关键词搜索"""
        # bioRxiv 搜索 API: /search/{server}/{term}/{start}/{end}/{cursor}
        cursor = 0
        papers = []
        term = keyword.replace(" ", "%20")
        date_str = f"{start.isoformat()}/{end.isoformat()}"

        for _ in range(2):  # 最多翻2页
            url = f"{self.SEARCH_BASE}/{self.server}/{term}/{date_str}/{cursor}/25"
            try:
                resp = self.session.get(url, timeout=20)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.debug("[%s] 搜索失败(%s): %s", self.source_name, keyword, e)
                break

            collection = data.get("collection", [])
            if not collection:
                break

            for item in collection:
                p = self._parse_item(item)
                if p:
                    papers.append(p)

            messages = data.get("messages", [])
            cursor = messages[0].get("cursor", 0) if messages else 0
            if cursor == 0:
                break
            time.sleep(0.2)

        return papers

    def _fetch_date_range(self, start: date, end: date) -> list[PaperMetadata]:
        """按日期范围拉取（兜底方法）"""
        papers = []
        cursor = 0
        date_interval = f"{start.isoformat()}/{end.isoformat()}"

        for _ in range(3):
            url = f"{self.API_BASE}/details/{self.server}/{date_interval}/{cursor}/100"
            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error("[%s] API request failed: %s", self.source_name, e)
                break

            collection = data.get("collection", [])
            if not collection:
                break

            for item in collection:
                p = self._parse_item(item)
                if p:
                    papers.append(p)

            messages = data.get("messages", [])
            cursor = messages[0].get("cursor", 0) if messages else 0
            if cursor == 0:
                break
            time.sleep(0.5)

        return papers

    def _parse_item(self, item: dict) -> Optional[PaperMetadata]:
        try:
            title = item.get("title", "").strip()
            if not title:
                return None

            doi          = item.get("doi", "")
            abstract     = item.get("abstract", "").strip()
            authors_str  = item.get("authors", "")
            authors      = [a.strip() for a in authors_str.split(";") if a.strip()]
            institution  = item.get("author_corresponding_institution", "")
            affiliations = [institution.strip()] if institution else []
            date_str     = item.get("date", "") or item.get("server_date", "")
            pub_date     = self._parse_date(date_str) if date_str else None
            category     = item.get("category", "")
            url          = f"https://doi.org/{doi}" if doi else ""

            return PaperMetadata(
                title=title,
                source=self.source_name,
                authors=authors,
                affiliations=affiliations,
                abstract=abstract,
                doi=doi,
                url=url,
                published_date=pub_date,
                keywords=[category] if category else [],
                category=category,
                pdf_url=f"https://www.biorxiv.org/content/{doi}.pdf" if doi else "",
            )
        except Exception as e:
            logger.warning("[%s] Failed to parse item: %s", self.source_name, e)
            return None
