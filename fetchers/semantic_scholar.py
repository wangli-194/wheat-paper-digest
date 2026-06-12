"""
Semantic Scholar Fetcher
免费 API，AI 驱动搜索，覆盖广
"""

import logging
import time
from datetime import date, timedelta
from typing import Optional
import urllib.request
import urllib.parse
import json

from .base import BaseFetcher, PaperMetadata

logger = logging.getLogger(__name__)


class SemanticScholarFetcher(BaseFetcher):
    """Semantic Scholar 论文检索"""

    API_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, source_name="Semantic Scholar", max_results=50, **kwargs):
        super().__init__(source_name=source_name, max_results=max_results)

    def fetch(self, keywords: list[str], lookback_days: int = 7) -> list[PaperMetadata]:
        today      = date.today()
        start_date = today - timedelta(days=lookback_days)
        start_year = start_date.year

        core_kws = [
            "wheat stripe rust resistance",
            "wheat powdery mildew resistance",
            "wheat Fusarium resistance",
            "wheat NLR resistance gene",
            "Triticum aestivum disease resistance",
            "plant NLR immunity",
            "plant effector triggered immunity",
            "plant disease resistance mechanism",
        ]

        all_papers: dict[str, PaperMetadata] = {}

        for kw in core_kws:
            papers = self._search(kw, start_year)
            for p in papers:
                # 日期过滤
                if p.published_date and p.published_date >= start_date:
                    if p.unique_id not in all_papers:
                        all_papers[p.unique_id] = p
            if papers:
                logger.info("[%s] 关键词'%s'找到%d篇", self.source_name, kw, len(papers))
            time.sleep(0.5)  # Semantic Scholar 限速较严

        result = list(all_papers.values())
        result.sort(key=lambda p: p.published_date or date.min, reverse=True)
        logger.info("[%s] 共检索到 %d 篇", self.source_name, len(result))
        return result[:self.max_results]

    def _search(self, query: str, year: int) -> list[PaperMetadata]:
        params = {
            "query": query,
            "fields": "title,abstract,authors,year,publicationDate,journal,externalIds,publicationVenue",
            "limit": "25",
            "year": f"{year}-",  # 当年及之后
        }
        url = f"{self.API_BASE}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "PaperDigest/1.0",
                    "Accept": "application/json",
                }
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug("[%s] 搜索失败(%s): %s", self.source_name, query, e)
            return []

        papers = []
        for item in data.get("data", []):
            p = self._parse(item)
            if p:
                papers.append(p)
        return papers

    def _parse(self, item: dict) -> Optional[PaperMetadata]:
        try:
            title = (item.get("title") or "").strip()
            if not title:
                return None

            abstract = (item.get("abstract") or "").strip()
            authors  = [a.get("name", "") for a in item.get("authors", [])[:10] if a.get("name")]

            # DOI
            ext_ids = item.get("externalIds") or {}
            doi     = ext_ids.get("DOI", "")
            url     = f"https://doi.org/{doi}" if doi else ""

            # 期刊
            venue   = item.get("publicationVenue") or {}
            journal = venue.get("name") or (item.get("journal") or {}).get("name") or "Semantic Scholar"

            # 日期
            date_str = item.get("publicationDate") or str(item.get("year") or "")
            pub_date = self._parse_date(date_str) if date_str else None

            return PaperMetadata(
                title=title,
                source=journal,
                authors=authors,
                affiliations=[],
                abstract=abstract,
                doi=doi,
                url=url,
                published_date=pub_date,
                keywords=[],
                category="",
            )
        except Exception as e:
            logger.warning("[%s] 解析失败: %s", self.source_name, e)
            return None
