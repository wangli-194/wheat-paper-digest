"""
OpenAlex Fetcher - 覆盖最全的开放学术数据库
无需 API Key，免费使用
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


class OpenAlexFetcher(BaseFetcher):
    """OpenAlex 论文检索"""

    API_BASE = "https://api.openalex.org/works"

    def __init__(self, source_name="OpenAlex", max_results=50, **kwargs):
        super().__init__(source_name=source_name, max_results=max_results)

    def fetch(self, keywords: list[str], lookback_days: int = 7) -> list[PaperMetadata]:
        today      = date.today()
        start_date = today - timedelta(days=lookback_days)

        # 核心关键词，取最相关的避免结果太泛
        core_kws = [
            "wheat rust", "stripe rust", "wheat resistance",
            "wheat powdery mildew", "Fusarium head blight",
            "Puccinia striiformis", "Blumeria graminis",
            "wheat NLR", "wheat R gene",
            "Triticum aestivum resistance",
            "plant immunity", "plant disease resistance",
            "NLR protein", "effector triggered immunity",
            "plant pathogen resistance",
        ]

        all_papers: dict[str, PaperMetadata] = {}

        for kw in core_kws:
            papers = self._search(kw, start_date, today)
            for p in papers:
                if p.unique_id not in all_papers:
                    all_papers[p.unique_id] = p
            if papers:
                logger.info("[%s] 关键词'%s'找到%d篇", self.source_name, kw, len(papers))
            time.sleep(0.2)

        result = list(all_papers.values())
        result.sort(key=lambda p: p.published_date or date.min, reverse=True)
        logger.info("[%s] 共检索到 %d 篇", self.source_name, len(result))
        return result[:self.max_results]

    def _search(self, keyword: str, start: date, end: date) -> list[PaperMetadata]:
        params = {
            "search": keyword,
            "filter": f"from_publication_date:{start.isoformat()},to_publication_date:{end.isoformat()}",
            "sort": "publication_date:desc",
            "per-page": "25",
            "select": "id,title,abstract_inverted_index,authorships,publication_date,primary_location,doi,concepts",
            "mailto": "paper-digest@example.com",
        }
        url = f"{self.API_BASE}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PaperDigest/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug("[%s] 搜索失败(%s): %s", self.source_name, keyword, e)
            return []

        papers = []
        for item in data.get("results", []):
            p = self._parse(item)
            if p:
                papers.append(p)
        return papers

    def _parse(self, item: dict) -> Optional[PaperMetadata]:
        try:
            title = item.get("title", "").strip()
            if not title:
                return None

            # 还原摘要（OpenAlex 用倒排索引存储）
            abstract = self._restore_abstract(item.get("abstract_inverted_index"))

            # 作者和机构
            authors, affiliations = [], []
            for auth in item.get("authorships", [])[:10]:
                name = auth.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)
                for inst in auth.get("institutions", []):
                    inst_name = inst.get("display_name", "")
                    if inst_name and inst_name not in affiliations:
                        affiliations.append(inst_name)

            # DOI 和 URL
            doi = (item.get("doi") or "").replace("https://doi.org/", "").strip()
            url = f"https://doi.org/{doi}" if doi else item.get("id", "")

            # 期刊
            loc = item.get("primary_location") or {}
            source = loc.get("source") or {}
            journal = source.get("display_name", "") or "OpenAlex"

            # 日期
            date_str = item.get("publication_date", "")
            pub_date = self._parse_date(date_str) if date_str else None

            return PaperMetadata(
                title=title,
                source=journal,
                authors=authors,
                affiliations=affiliations[:5],
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

    def _restore_abstract(self, inverted_index: Optional[dict]) -> str:
        """从倒排索引还原摘要文本"""
        if not inverted_index:
            return ""
        try:
            word_pos = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_pos.append((pos, word))
            word_pos.sort(key=lambda x: x[0])
            return " ".join(w for _, w in word_pos)
        except Exception:
            return ""
